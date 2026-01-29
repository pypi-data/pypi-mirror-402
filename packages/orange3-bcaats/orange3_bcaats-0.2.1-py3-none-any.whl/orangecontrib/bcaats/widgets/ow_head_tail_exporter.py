# CAATsLab/caatslab/widgets/ow_head_tail_exporter.py
from typing import Optional, List

import os
from pathlib import Path

from AnyQt import QtWidgets
from AnyQt.QtWidgets import QFileDialog

from Orange.widgets.widget import OWWidget, Input
from Orange.widgets.settings import Setting
from Orange.widgets import gui
from Orange.data import Table


class OWHeadTailExporter(OWWidget):
    name = "Head/Tail Exporter"
    description = "Export hasil File Head/Tail Reader ke file eksternal."
    icon = "icons/file_head.png"
    priority = 32
    want_main_area = False

    class Inputs:
        data = Input("Data", Table)

    # 0 = txt, 1 = csv sederhana
    export_format: int = Setting(0)
    last_dir: str = Setting("")

    def __init__(self):
        super().__init__()

        # ---------- Info ----------
        box_info = gui.widgetBox(self.controlArea, "Info")

        self.lbl_file = QtWidgets.QLabel("File: -")
        self.lbl_mode = QtWidgets.QLabel("Mode: -")
        self.lbl_lines = QtWidgets.QLabel("Lines: -")

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(self.lbl_file)
        lay.addWidget(self.lbl_mode)
        lay.addWidget(self.lbl_lines)
        box_info.layout().addLayout(lay)

        # ---------- Export options ----------
        box_exp = gui.widgetBox(self.controlArea, "Export Options")

        self.combo_fmt = gui.comboBox(
            box_exp, self, "export_format",
            items=["Plain text (.txt)", "CSV sederhana (.csv)"],
            label="Format:"
        )

        self.btn_save = gui.button(
            box_exp, self, "Save...",
            callback=self._save_clicked
        )
        self.btn_save.setEnabled(False)

        # ---------- Status ----------
        # PENTING: jangan pakai nama atribut `info` di sini
        self.status_label = gui.label(
            self.controlArea, self,
            "Status: belum ada data (hubungkan dari File Head/Tail Reader)."
        )

        # state data
        self._table: Optional[Table] = None
        self._lines: List[str] = []
        self._src_path: str = ""
        self._mode: str = ""

    # ===== Input handler =====
    @Inputs.data
    def set_data(self, data: Optional[Table]):
        """Terima Table dari OWHeadTailReader."""
        self._table = data
        self._lines = []
        self._src_path = ""
        self._mode = ""

        if data is None or len(data) == 0:
            self.lbl_file.setText("File: -")
            self.lbl_mode.setText("Mode: -")
            self.lbl_lines.setText("Lines: -")
            self.btn_save.setEnabled(False)
            self.status_label.setText(
                "Status: belum ada data (hubungkan dari File Head/Tail Reader)."
            )
            return

        # Ambil metas: text, path, mode
        # urutan sesuai build_table(): metas = [text, path, mode]
        metas = data.metas
        if metas.shape[1] < 3:
            # format tidak sesuai
            self.btn_save.setEnabled(False)
            self.status_label.setText(
                "Status: format data tidak sesuai (metas < 3 kolom)."
            )
            return

        texts = metas[:, 0].tolist()
        paths = metas[:, 1].tolist()
        modes = metas[:, 2].tolist()

        # pakai path & mode dari baris pertama
        self._lines = [str(t) for t in texts]
        self._src_path = str(paths[0]) if paths else ""
        self._mode = str(modes[0]) if modes else ""

        fname = os.path.basename(self._src_path) if self._src_path else "-"
        self.lbl_file.setText(f"File: {fname}")
        self.lbl_mode.setText(f"Mode: {self._mode or '-'}")
        self.lbl_lines.setText(f"Lines: {len(self._lines)}")

        self.btn_save.setEnabled(True)
        self.status_label.setText("Status: siap untuk export.")

    # ===== Save handler =====
    def _suggest_default_name(self) -> str:
        """Nama file default berdasarkan sumber + mode."""
        base = os.path.basename(self._src_path) or "headtail"
        stem, _ext = os.path.splitext(base)
        suffix = f"_{self._mode}" if self._mode else ""
        if self.export_format == 0:
            ext = ".txt"
        else:
            ext = ".csv"
        return stem + suffix + ext

    def _save_clicked(self):
        if not self._lines:
            self.status_label.setText("Status: tidak ada data untuk disimpan.")
            return

        start_dir = self.last_dir or str(Path.home())
        suggested = self._suggest_default_name()
        full_suggest = os.path.join(start_dir, suggested)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan hasil Head/Tail",
            full_suggest,
            "Text files (*.txt);;CSV files (*.csv);;All files (*.*)",
        )
        if not path:
            # user cancel
            return

        self.last_dir = os.path.dirname(path)

        try:
            if self.export_format == 0:
                # plain text: satu baris per line
                with open(path, "w", encoding="utf-8", errors="replace") as f:
                    for line in self._lines:
                        f.write(str(line) + "\n")
            else:
                # csv sederhana: line_no,text
                import csv
                with open(path, "w", encoding="utf-8", errors="replace", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["line_no", "text"])
                    for i, line in enumerate(self._lines, start=1):
                        writer.writerow([i, line])

            self.status_label.setText(f"Status: tersimpan ke {path}")
        except Exception as e:
            self.status_label.setText(f"Status: Gagal menyimpan: {e}")
