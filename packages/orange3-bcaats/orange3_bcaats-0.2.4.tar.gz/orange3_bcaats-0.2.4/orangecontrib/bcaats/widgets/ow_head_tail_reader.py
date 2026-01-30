# CAATsLab/caatslab/widgets/ow_head_tail_reader.py
import os
from typing import List, Tuple, Optional

from AnyQt.QtWidgets import QFileDialog
from AnyQt.QtCore import Qt

from Orange.widgets.widget import OWWidget, Output
from Orange.widgets.settings import Setting
from Orange.widgets import gui
from Orange.data import Table, Domain, StringVariable, ContinuousVariable

# Opsional: autodetect encoding
try:
    import chardet
except Exception:
    chardet = None


# =========================
#   HELPERS (FAST & SAFE)
# =========================

def _detect_encoding(path: str, default: str = "utf-8") -> str:
    """
    Deteksi encoding dengan chardet (opsional).
    Fallback ke default ('utf-8').
    """
    if chardet is None:
        return default
    try:
        with open(path, "rb") as f:
            raw = f.read(1024 * 128)  # 128 KB cukup untuk deteksi
        res = chardet.detect(raw) or {}
        enc = res.get("encoding") or default
        return enc
    except Exception:
        return default


def read_head(path: str, n: int, encoding: str, skip_empty: bool = False) -> List[str]:
    """
    Baca N baris pertama dengan streaming ringan.
    Tidak memuat seluruh file ke memori.
    """
    out = []
    if n <= 0:
        return out
    with open(path, "r", encoding=encoding, errors="replace", newline="") as f:
        for line in f:
            if skip_empty and (line == "" or line == "\n" or line == "\r\n"):
                continue
            out.append(line.rstrip("\r\n"))
            if len(out) >= n:
                break
    return out


def read_tail(path: str, n: int, encoding: str, block_bytes: int = 1024 * 1024) -> List[str]:
    """
    Baca N baris terakhir dengan membaca blok dari belakang.
    Efisien untuk file besar (GB).
    """
    if n <= 0:
        return []
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        buffer = bytearray()
        pos = file_size

        needed_newlines = n + 1  # +1 untuk jaga2 baris terakhir tanpa newline

        while pos > 0 and buffer.count(b"\n") < needed_newlines:
            read_size = min(block_bytes, pos)
            pos -= read_size
            f.seek(pos, os.SEEK_SET)
            chunk = f.read(read_size)
            buffer[:0] = chunk  # prepend

        lines_bytes = buffer.splitlines()
        if len(lines_bytes) <= n:
            picked = lines_bytes
        else:
            picked = lines_bytes[-n:]

        return [b.decode(encoding, errors="replace") for b in picked]


def build_table(path: str, mode: str, lines: List[str]) -> Table:
    """
    Bangun Orange Table dengan kolom:
    - line_no (1..N)
    - text (meta string)
    - path (meta string)
    - mode (meta string) ['head'/'tail']
    """
    line_no = ContinuousVariable("line_no")
    text_var = StringVariable("text")
    path_var = StringVariable("path")
    mode_var = StringVariable("mode")

    domain = Domain([line_no], metas=[text_var, path_var, mode_var])

    import numpy as np
    X = np.arange(1, len(lines) + 1, dtype=float).reshape(-1, 1)
    metas = np.array([[s, path, mode] for s in lines], dtype=object)

    return Table.from_numpy(domain, X, metas=metas)


# =========================
#   WIDGET
# =========================

class OWHeadTailReader(OWWidget):
    name = "File Head/Tail Reader"
    description = "Ambil N baris teratas (Head) atau terbawah (Tail) dari file besar."
    icon = "icons/file_head.png"
    priority = 31
    keywords = ["head", "tail", "sample", "first lines", "last lines", "text", "sql", "log"]

    want_main_area = False

    class Outputs:
        data = Output("Data", Table)

    # Settings
    file_path: str = Setting("")
    mode_index: int = Setting(0)        # 0=Head, 1=Tail
    n_lines: int = Setting(100)
    encoding_mode: int = Setting(0)     # 0=Auto, 1=UTF-8, 2=Latin-1, 3=Custom
    custom_encoding: str = Setting("utf-8")
    skip_empty: bool = Setting(False)
    block_mb: int = Setting(4)          # untuk tail: ukuran blok baca (MB)

    def __init__(self):
        super().__init__()

        # ==== UI ====
        box_src = gui.widgetBox(self.controlArea, "Sumber File")
        self.le_path = gui.lineEdit(box_src, self, "file_path", label="File:", orientation=Qt.Horizontal)
        gui.button(box_src, self, "Browse…", callback=self.browse_file)

        box_opt = gui.widgetBox(self.controlArea, "Parameter")
        self.rb_mode = gui.radioButtons(
            box_opt, self, "mode_index",
            btnLabels=["Head (awal file)", "Tail (akhir file)"],
            tooltips=["Ambil baris dari awal file", "Ambil baris dari akhir file"],
        )
        gui.spin(box_opt, self, "n_lines", 1, 1000000, label="Jumlah baris (N)")

        box_enc = gui.widgetBox(self.controlArea, "Encoding")
        gui.comboBox(
            box_enc, self, "encoding_mode",
            items=["Auto (chardet)", "UTF-8", "Latin-1 (ISO-8859-1)", "Custom…"],
            label="Mode:",
            callback=self._encoding_changed
        )
        self.le_custom_enc = gui.lineEdit(
            box_enc, self, "custom_encoding", label="Custom:", orientation=Qt.Horizontal
        )
        self.le_custom_enc.setDisabled(self.encoding_mode != 3)

        box_more = gui.widgetBox(self.controlArea, "Lainnya")
        gui.checkBox(box_more, self, "skip_empty", "Lewati baris kosong (mode Head)")
        gui.spin(box_more, self, "block_mb", 1, 128, label="Ukuran blok Tail (MB)")

        self.btn_run = gui.button(self.controlArea, self, "Ambil Baris Sekarang", callback=self.run_now)
        self.infoa = gui.label(self.controlArea, self, "Status: siap.")
        self.progressBarInit()

    # ----- UI handlers -----
    def _encoding_changed(self):
        self.le_custom_enc.setDisabled(self.encoding_mode != 3)

    def browse_file(self):
        d = QFileDialog.getOpenFileName(self, "Pilih File", self.file_path or os.path.expanduser("~"))[0]
        if d:
            self.file_path = d

    # ----- Core -----
    def _resolve_encoding(self, path: str) -> str:
        if self.encoding_mode == 0:
            return _detect_encoding(path, default="utf-8")
        if self.encoding_mode == 1:
            return "utf-8"
        if self.encoding_mode == 2:
            return "latin-1"
        return self.custom_encoding or "utf-8"

    def _do_read(self) -> Tuple[Optional[Table], str]:
        path = self.file_path
        if not path or not os.path.isfile(path):
            return None, "File tidak valid atau tidak ditemukan."

        mode = "head" if self.mode_index == 0 else "tail"
        enc = self._resolve_encoding(path)

        try:
            if mode == "head":
                lines = read_head(path, self.n_lines, enc, skip_empty=self.skip_empty)
            else:
                lines = read_tail(path, self.n_lines, enc, block_bytes=self.block_mb * 1024 * 1024)

            tbl = build_table(path, mode, lines)
            status = f"Selesai: {len(lines)} baris ({mode}) dari: {os.path.basename(path)} | encoding={enc}"
            return tbl, status
        except Exception as e:
            return None, f"Error: {e}"

    def run_now(self):
        if not self.file_path:
            self.infoa.setText("Pilih file terlebih dahulu.")
            self.Outputs.data.send(None)
            return

        self.infoa.setText("Memproses…")
        self.progressBarSet(25)

        table, status = self._do_read()
        self.Outputs.data.send(table)
        self.infoa.setText(status)
        self.progressBarFinished()
        print("[HeadTailReader] run_now: table is None?", table is None)
