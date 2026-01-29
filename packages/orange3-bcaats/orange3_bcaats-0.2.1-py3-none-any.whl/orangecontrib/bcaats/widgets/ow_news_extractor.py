import os
import csv
import math
import socket
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple

from AnyQt.QtWidgets import QFileDialog
from AnyQt.QtCore import Qt

from Orange.widgets.widget import OWWidget, Output
from Orange.widgets.settings import Setting
from Orange.widgets import gui
from Orange.data import Table, Domain, StringVariable, ContinuousVariable, TimeVariable

# ---- newspaper3k ----
try:
    from newspaper import Article
except Exception as e:
    Article = None
    _IMPORT_ERROR = str(e)
else:
    _IMPORT_ERROR = None

# ---- Orange Text (Corpus) (opsional) ----
try:
    from orangecontrib.text.corpus import Corpus
except Exception:
    Corpus = None

# ---- sumy fallback summarizer (opsional) ----
try:
    from sumy.summarizers.lsa import LsaSummarizer
    from sumy.nlp.tokenizers import Tokenizer as SumyTokenizer
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.stemmers import Stemmer as SumyStemmer
    from sumy.utils import get_stop_words as sumy_get_stop_words
    _SUMY_OK = True
except Exception:
    _SUMY_OK = False


# =========================
# Helpers
# =========================

def _guess_csv_format(path: str) -> Tuple[str, bool]:
    """Tebak delimiter; return (delimiter, has_header)."""
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(8192)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
            has_header = csv.Sniffer().has_header(sample)
            return dialect.delimiter, has_header
        except Exception:
            return ",", True


def _read_urls_from_csv(path: str, colname: Optional[str]) -> List[str]:
    delim, has_header = _guess_csv_format(path)
    urls: List[str] = []
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=delim)
        rows = list(reader)

    if not rows:
        return urls

    header = None
    start_idx = 0
    if has_header:
        header = rows[0]
        start_idx = 1

    # kolom target
    idx = 0
    if header and colname:
        try:
            idx = header.index(colname)
        except ValueError:
            lowered = [h.lower() for h in header]
            idx = lowered.index("url") if "url" in lowered else 0
    elif header:
        lowered = [h.lower() for h in header]
        idx = lowered.index("url") if "url" in lowered else 0
    else:
        idx = 0

    for r in rows[start_idx:]:
        if not r:
            continue
        u = (r[idx] or "").strip()
        if u:
            urls.append(u)
    return urls


def _domain(u: str) -> str:
    try:
        return urlparse(u).netloc
    except Exception:
        return ""


def _fallback_summarize(text: str, language_code: str = "id", sentences: int = 3) -> str:
    """
    Ringkasan fallback yang lebih robust untuk bahasa non‑Snowball (termasuk Indonesia).
    - Tidak memakai stemmer (karena 'indonesian' tidak didukung Snowball).
    - Stop-words dipakai jika tersedia; kalau tidak, diabaikan.
    - Tokenizer 'english' dipakai sebagai netral untuk pemotongan kalimat.
    - Jika tetap gagal/kosong: ambil 2-3 kalimat pertama secara naive.
    """
    if not text or len(text) < 120:  # teks terlalu pendek → skip
        return ""

    # 1) coba sumy (jika tersedia)
    if _SUMY_OK:
        try:
            # pakai tokenizer 'english' sebagai netral (aman untuk ID/en)
            parser = PlaintextParser.from_string(text, SumyTokenizer("english"))

            from sumy.summarizers.lsa import LsaSummarizer
            summarizer = LsaSummarizer()  # tanpa stemmer

            # stop-words kalau ada
            try:
                lang_sw = "indonesian" if language_code.lower().startswith("id") else "english"
                summarizer.stop_words = sumy_get_stop_words(lang_sw)
            except Exception:
                pass

            sents = list(summarizer(parser.document, max(1, sentences)))
            res = " ".join(str(s) for s in sents).strip()
            if res:
                return res
        except Exception:
            pass

    # 2) fallback naive: ambil 2-3 kalimat pertama berdasarkan tanda baca umum
    try:
        import re
        # Pisah kalimat sederhana
        toks = re.split(r'(?<=[\.\?\!])\s+', text.strip())
        head = toks[:max(1, sentences)]
        res = " ".join(head).strip()
        return res
    except Exception:
        return ""



def _extract_one(url: str, lang: str, run_nlp: bool, timeout: int, user_agent: Optional[str]) -> Dict:
    """
    Ekstrak 1 URL; tahan error. Return dict kolom-kolom yang siap ke Table/Corpus.
    """
    if Article is None:
        return {"url": url, "error": f"newspaper3k not available: {_IMPORT_ERROR}"}

    try:
        art = Article(url, language=lang or "id", memoize_articles=False, fetch_images=True)
        if user_agent:
            art.config.browser_user_agent = user_agent
        art.config.request_timeout = timeout
        art.download()
        art.parse()

        keywords = []
        summary = ""
        nlp_source = "newspaper"

        if run_nlp:
            try:
                art.nlp()
                keywords = art.keywords or []
                summary = art.summary or ""
            except Exception:
                # biarkan kosong, akan diisi fallback bila ada
                pass

        if not summary and art.text:
            fs = _fallback_summarize(art.text, language_code=lang, sentences=3)
            if fs:
                summary = fs
                nlp_source = "sumy"


        return {
            "url": url,
            "source_domain": _domain(url),
            "title": art.title or "",
            "authors": ", ".join(art.authors or []),
            "publish_date": art.publish_date.isoformat() if getattr(art, "publish_date", None) else "",
            "top_image": getattr(art, "top_image", "") or "",
            "movies": ", ".join(getattr(art, "movies", []) or []),
            "meta_keywords": ", ".join(getattr(art, "meta_keywords", []) or []),
            "meta_description": getattr(art, "meta_description", "") or "",
            "text": art.text or "",
            "keywords": ", ".join(keywords),
            "summary": summary,
            "summary_source": nlp_source if summary else "",
            "error": "",
        }
    except Exception as e:
        return {"url": url, "source_domain": _domain(url), "error": str(e)}


def _to_table(rows: List[Dict]) -> Table:
    preferred = [
        "url", "source_domain", "title", "authors", "publish_date",
        "meta_keywords", "meta_description", "top_image", "movies",
        "keywords", "summary", "summary_source", "text", "error",
    ]
    keys = set()
    for r in rows:
        keys.update(r.keys())
    cols = [c for c in preferred if c in keys] + [c for c in sorted(keys) if c not in preferred]

    str_vars, time_vars, num_vars = [], [], []
    for c in cols:
        if c == "publish_date":
            time_vars.append((c, TimeVariable(c)))
        else:
            str_vars.append((c, StringVariable(c)))

    domain = Domain([v for _, v in num_vars] + [v for _, v in time_vars], metas=[v for _, v in str_vars])

    import numpy as np
    def to_epoch(iso: str) -> float:
        import datetime
        if not iso:
            return math.nan
        try:
            return datetime.datetime.fromisoformat(iso).timestamp()
        except Exception:
            return math.nan

    X = []
    metas = []
    for r in rows:
        xt = [to_epoch(r.get("publish_date", ""))] if time_vars else []
        X.append(xt)
        metas.append([str(r.get(c, "")) for c, _ in str_vars])

    return Table.from_numpy(domain, np.asarray(X, dtype=float), metas=np.asarray(metas, dtype=object))


# =========================
# WIDGET
# =========================

class OWNewsExtractor(OWWidget):
    name = "News Extractor (newspaper)"
    description = "Ekstrak berita dari URL tunggal atau CSV daftar URL (title, text, keywords, summary)."
    icon = "icons/scrape.png"
    priority = 40
    keywords = ["news", "article", "web", "scrape", "newspaper3k", "berita"]
    want_main_area = False

    class Outputs:
        data = Output("Data", Table)
        corpus = Output("Corpus", object)  # kirim Corpus bila Orange Text terpasang

    # Settings
    mode_index: int = Setting(0)  # 0 = Single URL, 1 = CSV
    single_url: str = Setting("")
    csv_path: str = Setting("")
    csv_url_column: str = Setting("")   # kosong = auto-detect
    language: str = Setting("id")
    run_nlp: bool = Setting(True)
    timeout_sec: int = Setting(20)
    max_workers: int = Setting(6)
    user_agent: str = Setting("")

    def __init__(self):
        super().__init__()

        # ===== UI =====
        box_mode = gui.widgetBox(self.controlArea, "Mode")
        gui.radioButtons(box_mode, self, "mode_index",
                         btnLabels=["URL tunggal", "CSV (banyak URL)"],
                         callback=self._mode_changed)

        self.box_single = gui.widgetBox(self.controlArea, "URL tunggal")
        gui.lineEdit(self.box_single, self, "single_url", label="URL:", placeholderText="https://...")

        self.box_csv = gui.widgetBox(self.controlArea, "CSV (daftar URL)")
        gui.lineEdit(self.box_csv, self, "csv_path", label="File CSV:", orientation=Qt.Horizontal)
        gui.button(self.box_csv, self, "Browse…", callback=self._browse_csv)
        gui.lineEdit(self.box_csv, self, "csv_url_column", label="Kolom URL (opsional):", placeholderText="(kosongkan untuk auto-detect)")

        box_opt = gui.widgetBox(self.controlArea, "Opsi ekstraksi")
        gui.lineEdit(box_opt, self, "language", label="Kode bahasa:", placeholderText="id / en / ...")
        gui.checkBox(box_opt, self, "run_nlp", "Run NLP (keywords & summary)")
        gui.spin(box_opt, self, "timeout_sec", 5, 120, label="Timeout (detik)")
        gui.spin(box_opt, self, "max_workers", 1, 16, label="Parallel workers")
        gui.lineEdit(box_opt, self, "user_agent", label="Custom User-Agent:", placeholderText="(opsional)")

        gui.button(self.controlArea, self, "Ekstrak Sekarang", callback=self.run_now)
        self.infoa = gui.label(self.controlArea, self, "Status: siap.")
        self.progressBarInit()
        self._mode_changed()

        if _IMPORT_ERROR:
            self.infoa.setText(f"Peringatan: newspaper3k tidak tersedia: {_IMPORT_ERROR}")

    # ----- UI handlers -----
    def _mode_changed(self):
        self.box_single.setDisabled(self.mode_index != 0)
        self.box_csv.setDisabled(self.mode_index != 1)

    def _browse_csv(self):
        path = QFileDialog.getOpenFileName(
            self, "Pilih CSV", self.csv_path or os.path.expanduser("~"),
            "CSV Files (*.csv);;All Files (*)")[0]
        if path:
            self.csv_path = path

    # ----- Core -----
    def _extract_batch(self, urls: List[str]) -> List[Dict]:
        rows: List[Dict] = []
        total = len(urls)
        done = 0
        self.progressBarSet(0)
        socket.setdefaulttimeout(self.timeout_sec)

        with ThreadPoolExecutor(max_workers=int(self.max_workers)) as pool:
            futs = [pool.submit(
                _extract_one, u, self.language.strip() or "id",
                self.run_nlp, int(self.timeout_sec), self.user_agent.strip() or None
            ) for u in urls]
            for fut in as_completed(futs):
                try:
                    rows.append(fut.result())
                except Exception as e:
                    rows.append({"url": "", "error": str(e)})
                done += 1
                self.progressBarSet(int(done * 100 / max(total, 1)))
        self.progressBarFinished()
        return rows

    def run_now(self):
        if Article is None:
            self.infoa.setText(f"Error: newspaper3k tidak tersedia: {_IMPORT_ERROR}")
            self.Outputs.data.send(None)
            self.Outputs.corpus.send(None)
            return

        # Kumpulkan URL
        if self.mode_index == 0:
            url = (self.single_url or "").strip()
            if not url:
                self.infoa.setText("Masukkan URL dulu.")
                self.Outputs.data.send(None)
                self.Outputs.corpus.send(None)
                return
            self.infoa.setText("Memproses 1 URL…")
            urls = [url]
        else:
            path = (self.csv_path or "").strip()
            if not path or not os.path.isfile(path):
                self.infoa.setText("Pilih file CSV yang valid.")
                self.Outputs.data.send(None)
                self.Outputs.corpus.send(None)
                return
            self.infoa.setText("Membaca CSV…")
            try:
                urls = _read_urls_from_csv(path, self.csv_url_column.strip() or None)
            except Exception as e:
                self.infoa.setText(f"Gagal membaca CSV: {e}")
                self.Outputs.data.send(None)
                self.Outputs.corpus.send(None)
                return
            if not urls:
                self.infoa.setText("Tidak ada URL di CSV.")
                self.Outputs.data.send(None)
                self.Outputs.corpus.send(None)
                return
            self.infoa.setText(f"Memproses {len(urls)} URL…")

        # Ekstrak
        rows = self._extract_batch(urls)

        # Table
        table = _to_table(rows)
        self.Outputs.data.send(table)

        # Corpus (jika modul tersedia)
        if Corpus is not None:
            try:
                corpus = Corpus.from_table(table.domain, table)
            except Exception:
                corpus = None
            self.Outputs.corpus.send(corpus)
        else:
            self.Outputs.corpus.send(None)

        ok = sum(1 for r in rows if not (r.get("error")))
        fail = len(rows) - ok
        # info sumber ringkasan
        n_sumy = sum(1 for r in rows if r.get("summary_source") == "sumy")
        extra = f" | summary by sumy: {n_sumy}" if n_sumy else ""
        self.infoa.setText(f"Selesai: {ok} OK, {fail} gagal.{extra}")
