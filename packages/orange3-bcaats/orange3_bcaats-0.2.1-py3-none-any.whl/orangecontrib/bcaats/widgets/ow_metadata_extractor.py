import os
import fnmatch
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from AnyQt.QtWidgets import QFileDialog
from AnyQt.QtCore import Qt

from Orange.widgets.widget import OWWidget, Output
from Orange.widgets.settings import Setting
from Orange.widgets import gui
from Orange.data import Table, Domain, StringVariable, ContinuousVariable, TimeVariable

from .._meta_extractors import extract_one, ExtractOptions



class OWMetadataExtractor(OWWidget):
    name = "File Metadata Extractor"
    description = "Ekstrak metadata file dari sebuah folder (rekursif; Office/PDF/EXIF/Audio/Video opsional)."
    icon = "icons/meta_extract.png"
    priority = 30
    keywords = ["metadata", "file", "hash", "exif", "pdf", "office", "audio", "video", "audit"]
    
    want_main_area = False


    class Outputs:
        data = Output("Data", Table)

    # Settings tersimpan antar sesi
    folder_path: str = Setting("")
    recursive: bool = Setting(True)
    glob_pattern: str = Setting("*")
    max_workers: int = Setting(8)

    do_md5: bool = Setting(False)
    do_sha256: bool = Setting(False)
    do_exif: bool = Setting(True)
    do_pdf: bool = Setting(True)
    do_office: bool = Setting(True)
    do_audio: bool = Setting(True)
    do_video: bool = Setting(False)   # aktifkan jika pymediainfo terpasang
    do_xattrs: bool = Setting(False)
    auto_run: bool = Setting(False)

    def __init__(self):
        super().__init__()
        self.files: List[str] = []
        self.results: List[Dict] = []

        # --- UI ---
        box_src = gui.widgetBox(self.controlArea, "Sumber Folder")
        self.le_path = gui.lineEdit(box_src, self, "folder_path", label="Folder:", orientation=Qt.Horizontal)
        gui.button(box_src, self, "Browse…", callback=self.browse_folder)

        box_scan = gui.widgetBox(self.controlArea, "Pemindaian")
        gui.checkBox(box_scan, self, "recursive", "Scan subfolder (recursive)")
        gui.lineEdit(box_scan, self, "glob_pattern", label="Filter glob:", placeholderText="*.pdf, *.jpg, data_*.csv")
        gui.spin(box_scan, self, "max_workers", 1, 32, label="Parallel workers")
        gui.checkBox(box_scan, self, "auto_run", "Jalankan otomatis saat konfigurasi berubah")

        box_feat = gui.widgetBox(self.controlArea, "Fitur Metadata")
        gui.checkBox(box_feat, self, "do_md5", "Hitung MD5 (lambat)")
        gui.checkBox(box_feat, self, "do_sha256", "Hitung SHA256 (lambat)")
        gui.checkBox(box_feat, self, "do_exif", "EXIF Gambar (Pillow)")
        gui.checkBox(box_feat, self, "do_pdf", "PDF (PyPDF2)")
        gui.checkBox(box_feat, self, "do_office", "Office docx/xlsx/pptx (core & app props)")
        gui.checkBox(box_feat, self, "do_audio", "Audio tags (mutagen)")
        gui.checkBox(box_feat, self, "do_video", "Video (MediaInfo) – opsional")
        gui.checkBox(box_feat, self, "do_xattrs", "Extended attributes (Linux/macOS)")

        gui.button(self.controlArea, self, "Scan Folder Sekarang", callback=self.scan_now)
        self.infoa = gui.label(self.controlArea, self, "Status: siap.")
        self.progressBarInit()

    # ----- UI actions -----
    def browse_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Pilih Folder", self.folder_path or os.path.expanduser("~"))
        if d:
            self.folder_path = d
            if self.auto_run:
                self.scan_now()

    # ----- Core -----
    def _collect_files(self) -> List[str]:
        pat = (self.glob_pattern or "*").strip()
        files = []
        if not self.folder_path or not os.path.isdir(self.folder_path):
            return files

        if self.recursive:
            for root, _, fnames in os.walk(self.folder_path):
                for f in fnames:
                    if fnmatch.fnmatch(f, pat):
                        files.append(os.path.join(root, f))
        else:
            for f in os.listdir(self.folder_path):
                p = os.path.join(self.folder_path, f)
                if os.path.isfile(p) and fnmatch.fnmatch(f, pat):
                    files.append(p)
        return files

    def scan_now(self):
        self.infoa.setText("Status: mengumpulkan file…")
        self.progressBarSet(0)
        self.files = self._collect_files()
        n = len(self.files)
        if n == 0:
            self.infoa.setText("Status: tidak ada file yang cocok.")
            self.Outputs.data.send(None)
            self.progressBarFinished()
            return

        self.infoa.setText(f"Status: memindai {n} file…")
        opts = ExtractOptions(
            compute_md5=self.do_md5,
            compute_sha256=self.do_sha256,
            include_exif=self.do_exif,
            include_pdf=self.do_pdf,
            include_office=self.do_office,
            include_audio=self.do_audio,
            include_video=self.do_video,
            include_xattrs=self.do_xattrs,
            glob_pattern=self.glob_pattern or "*",
        )

        out: List[Dict] = []
        done = 0
        with ThreadPoolExecutor(max_workers=int(self.max_workers)) as ex:
            futs = [ex.submit(extract_one, p, opts) for p in self.files]
            for fut in as_completed(futs):
                try:
                    out.append(fut.result())
                except Exception as e:
                    out.append({"path": "unknown", "error": str(e)})
                done += 1
                self.progressBarSet(int(done * 100 / n))

        self.results = out
        self.infoa.setText(f"Status: selesai. {len(out)} baris.")
        self.progressBarFinished()

        table = self._to_orange_table(out)
        self.Outputs.data.send(table)

    def _to_orange_table(self, rows: List[Dict]) -> Table:
        # kumpulkan semua kolom
        keys = set()
        for r in rows:
            keys.update(r.keys())

        preferred = [
            # filesystem
            "path", "dir", "name", "ext", "mime", "size_bytes", "mode", "is_readonly",
            "owner", "ctime", "mtime", "atime", "md5", "sha256", "is_symlink", "error",
            # Office core props
            "office_title", "office_subject", "office_creator", "office_created",
            "office_modified", "office_lastModifiedBy", "office_revision",
            "office_keywords", "office_category", "office_status", "office_description",
            "office_language", "office_publisher", "office_contributor", "office_identifier",
            # Office app props
            "application_name", "application_version", "office_company", "office_manager", "office_security",
            "hyperlinks_changed", "links_up_to_date", "shared_doc", "links_dirty", "scale", "template",
            "edit_time", "last_printed",
            "char_count", "char_with_spaces_count", "word_count", "line_count", "paragraph_count",
            "page_count", "slide_count", "note_count", "hidden_slide_count", "multimedia_clip_count",
            # PDF
            "pdf_author", "pdf_creator", "pdf_producer", "pdf_title", "pdf_subject",
            "pdf_creation_date", "pdf_mod_date", "pdf_pages",
            # EXIF
            "exif_make", "exif_model", "exif_datetime", "exif_software", "exif_artist", "exif_width", "exif_height",
            # Audio/Video
            "audio_title", "audio_artist", "audio_album", "audio_genre", "audio_date", "audio_tracknumber",
            "audio_length_seconds", "audio_bitrate", "audio_sample_rate", "audio_channels",
            "video_container", "video_duration_ms", "video_width", "video_height", "video_fps", "video_codec",
            "video_audio_channels", "video_audio_samplerate", "video_audio_format",
        ]
        cols = [c for c in preferred if c in keys] + [c for c in sorted(keys) if c not in preferred]

        # tipe kolom
        numeric_cols = {
            "size_bytes",
            "char_count", "char_with_spaces_count", "word_count", "line_count", "paragraph_count",
            "page_count", "slide_count", "note_count", "hidden_slide_count", "multimedia_clip_count",
            "pdf_pages",
            "exif_width", "exif_height",
            "audio_length_seconds", "audio_bitrate", "audio_sample_rate", "audio_channels",
            "video_duration_ms", "video_width", "video_height", "video_fps",
        }
        time_cols = {"ctime", "mtime", "atime"}

        # buat domain
        str_vars: List[tuple] = []
        num_vars: List[tuple] = []
        time_vars: List[tuple] = []

        for c in cols:
            if c in numeric_cols:
                num_vars.append((c, ContinuousVariable(c)))
            elif c in time_cols:
                time_vars.append((c, TimeVariable(c)))
            else:
                str_vars.append((c, StringVariable(c)))

        domain = Domain(
            [v for _, v in num_vars] + [v for _, v in time_vars],
            metas=[v for _, v in str_vars]
        )

        # isi data
        import numpy as np

        def to_epoch(iso):
            import datetime
            if not iso:
                return np.nan
            try:
                return datetime.datetime.fromisoformat(iso).timestamp()
            except Exception:
                return np.nan

        X = []
        metas = []
        for r in rows:
            xn = [float(r.get(c)) if r.get(c) not in (None, "") else np.nan for c, _ in num_vars]
            xt = [to_epoch(r.get(c)) for c, _ in time_vars]
            X.append(xn + xt)
            metas.append([str(r.get(c, "")) if r.get(c) is not None else "" for c, _ in str_vars])

        return Table.from_numpy(domain, np.asarray(X, dtype=float), metas=np.asarray(metas, dtype=object))
