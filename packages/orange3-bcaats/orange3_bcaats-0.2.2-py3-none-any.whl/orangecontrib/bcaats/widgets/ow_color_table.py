# caatslab/widgets/ow_color_table.py
from __future__ import annotations
from typing import Optional, List, Dict, Tuple
import colorsys
import html
import numpy as np

from AnyQt.QtWidgets import (
    QTableWidget, QTableWidgetItem, QTextBrowser
)
from AnyQt.QtGui import QColor, QBrush, QFont
from Orange.data import Table, StringVariable, DiscreteVariable, Domain, Variable
from Orange.widgets.widget import OWWidget, Input
from Orange.widgets import gui, settings
from AnyQt.QtWidgets import QComboBox, QListView
from AnyQt.QtCore import QPoint, Qt

class AnchoredComboBox(QComboBox):
    """
    ComboBox dengan popup nempel ke kiri + lebar dibatasi.
    - fixed_control_w: lebar kontrol (kotak combobox) di panel
    - min_popup_w/max_popup_w: batas lebar popup daftar
    """
    def __init__(self, fixed_control_w: int = 220,
                 min_popup_w: int = 200, max_popup_w: int = 260, parent=None):
        super().__init__(parent)
        self._fixed_control_w = int(fixed_control_w)
        self._min_popup_w = int(min_popup_w)
        self._max_popup_w = int(max_popup_w)

        # kontrol (kotak) dibuat lebar tetap agar rapi
        self.setMinimumWidth(self._fixed_control_w)
        self.setMaximumWidth(self._fixed_control_w)
        self.setMinimumContentsLength(18)
        self.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)

        # view popup: item berukuran seragam + elide teks panjang
        view = QListView(self)
        view.setUniformItemSizes(True)
        view.setTextElideMode(Qt.ElideRight)
        view.setMinimumWidth(self._min_popup_w)
        self.setView(view)

        # pastikan bukan fullscreen/centered popup
        self.setStyleSheet("QComboBox { combobox-popup: 0; }")

    def showPopup(self):
        super().showPopup()
        popup = self.view().window()
        w = max(self._min_popup_w, min(self._max_popup_w, self.width()))
        g = popup.geometry()
        g.setWidth(w)
        popup.setGeometry(g)
        # re-anchor: kiri kontrol, tepat di bawahnya
        popup.move(self.mapToGlobal(QPoint(0, self.height())))

PALETTES: Dict[str, List[str]] = {
    "Tab20": [
        "#4E79A7","#F28E2B","#E15759","#76B7B2","#59A14F",
        "#EDC948","#B07AA1","#FF9DA7","#9C755F","#BAB0AB",
        "#1F77B4","#FF7F0E","#2CA02C","#D62728","#9467BD",
        "#8C564B","#E377C2","#7F7F7F","#BCBD22","#17BECF",
    ],
    "Set3": [
        "#8DD3C7","#FFFFB3","#BEBADA","#FB8072","#80B1D3",
        "#FDB462","#B3DE69","#FCCDE5","#D9D9D9","#BC80BD",
        "#CCEBC5","#FFED6F",
    ],
    "Vivid": [
        "#E60049","#0BB4FF","#50E991","#E6D800","#9B19F5",
        "#FFA300","#DC0AB4","#B3D4FF","#00BFA0",
    ],
    "Pastel": [
        "#A1C9F4","#FFB482","#8DE5A1","#FF9F9B","#D0BBFF",
        "#DEBB9B","#FAB0E4","#CFCFCF","#FFFEA3","#B9F2F0",
    ],
}

def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def hsv_palette(n: int) -> List[Tuple[int, int, int]]:
    out = []
    for i in range(n):
        h = (i / max(1, n)) % 1.0
        s, v = 0.65, 0.95
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        out.append((int(r*255), int(g*255), int(b*255)))
    return out


class OWColorTable(OWWidget):
    name = "Color Table"
    description = "Tabel dengan background baris berwarna per grup/kelas."
    icon = "icons/color_table.png"
    priority = 99

    class Inputs:
        data = Input("Data", Table)

    want_main_area = True

    # ===== Settings (persist) =====
    max_rows = settings.Setting(2000)
    color_var_name = settings.Setting("")       # kosong = pakai class_var bila ada
    palette_name = settings.Setting("Tab20")    # pilihan PALETTES
    top_n_distinct = settings.Setting(20)       # Top-N grup diberi warna unik
    others_gray = settings.Setting(True)        # sisanya abu-abu
    sort_by_group = settings.Setting(True)      # urutkan output per grup
    font_pt = settings.Setting(10)
    row_height = settings.Setting(22)

    # runtime
    data: Optional[Table] = None
    legend_view: Optional[QTextBrowser] = None
    table: Optional[QTableWidget] = None

    def __init__(self):
        super().__init__()

        # --- Pewarnaan ---
        box_color = gui.widgetBox(self.controlArea, "Pewarnaan")
        # padding & spacing konsisten
        for _b in (box_color,):
            _b.layout().setContentsMargins(3, 3, 3, 3)
            _b.layout().setSpacing(3)

        gui.widgetLabel(box_color, "Variabel warna")
        self.cb_color = AnchoredComboBox(fixed_control_w=220, min_popup_w=200, max_popup_w=260)
        self.cb_color.currentTextChanged.connect(lambda t: setattr(self, "color_var_name", t))
        box_color.layout().addWidget(self.cb_color)

        gui.widgetLabel(box_color, "Palet")
        self.cb_palette = AnchoredComboBox(fixed_control_w=220, min_popup_w=200, max_popup_w=260)
        self.cb_palette.addItems(sorted(PALETTES.keys()))
        self.cb_palette.setCurrentText(self.palette_name)
        self.cb_palette.currentTextChanged.connect(lambda t: setattr(self, "palette_name", t))
        box_color.layout().addWidget(self.cb_palette)


        gui.spin(box_color, self, "top_n_distinct", 2, 2000, 1,
                label="Top-N grup diberi warna berbeda")
        gui.checkBox(box_color, self, "others_gray", "Grup di luar Top-N → abu-abu")
        gui.button(box_color, self, "Terapkan", callback=self.commit)

        # --- Tampilan ---
        box_view = gui.widgetBox(self.controlArea, "Tampilan")
        for _b in (box_view,):
            _b.layout().setContentsMargins(8, 8, 8, 8)
            _b.layout().setSpacing(6)

        gui.spin(box_view, self, "font_pt", 6, 24, 1, label="Ukuran font (pt)",
                callback=self._apply_table_style)
        gui.spin(box_view, self, "row_height", 14, 48, 1, label="Tinggi baris (px)",
                callback=self._apply_table_style)
        gui.checkBox(box_view, self, "sort_by_group", "Urutkan menurut grup",
                    callback=self.commit)

        # --- Batas tampilan ---
        box_lim = gui.widgetBox(self.controlArea, "Batas tampilan")
        for _b in (box_lim,):
            _b.layout().setContentsMargins(8, 8, 8, 8)
            _b.layout().setSpacing(6)

        gui.spin(box_lim, self, "max_rows", 100, 100000, 100, label="Maks baris ditampilkan")
        gui.button(box_lim, self, "Segarkan", callback=self.commit)

        # --- TABEL ---
        self.table = QTableWidget()
        self.mainArea.layout().addWidget(self.table)


    # ===== Inputs =====
    @Inputs.data
    def set_data(self, data: Optional[Table]):
        self.data = data
        self._refresh_color_var_items()
        self.commit()  # auto-refresh

    def _refresh_color_var_items(self):
        self.cb_color.blockSignals(True)
        self.cb_color.clear()
        if not self.data:
            self.cb_color.blockSignals(False)
            return

        dom = self.data.domain
        items = []
        if dom.class_var is not None:
            items.append(dom.class_var.name)
        for m in dom.metas:
            if isinstance(m, StringVariable):
                items.append(m.name)
        for a in dom.attributes:
            if isinstance(a, DiscreteVariable):
                items.append(a.name)

        # isikan & pilih current
        self.cb_color.addItems(items)
        if self.color_var_name and self.color_var_name in items:
            self.cb_color.setCurrentText(self.color_var_name)
        elif items:
            self.color_var_name = items[0]
            self.cb_color.setCurrentIndex(0)

        # rapikan lebar popup
        view = self.cb_color.view()
        if view is not None:
            view.setMinimumWidth(max(200, self.cb_color.width()))
        self.cb_color.blockSignals(False)



    # ===== Utility =====
    def _labels_from_var(self, data: Table, var_name: str) -> List[str]:
        dom = data.domain
        # class?
        if dom.class_var is not None and dom.class_var.name == var_name:
            v = dom.class_var
            vals = []
            Y = np.ravel(data.Y)
            for y in Y:
                if np.isnan(y):
                    vals.append("")
                else:
                    idx = int(y)
                    vals.append(v.values[idx] if 0 <= idx < len(v.values) else "")
            return vals
        # any variable by name (attrs/metas/class_vars)
        by_name: Dict[str, Variable] = {
            v.name: v for v in list(dom.attributes) + list(dom.metas) + list(dom.class_vars or [])
        }
        var = by_name.get(var_name)
        if var is None:
            return ["" for _ in range(len(data))]
        col = data.get_column(var)
        if isinstance(var, DiscreteVariable):
            out = []
            for x in col:
                if np.isnan(x):
                    out.append("")
                else:
                    idx = int(x)
                    out.append(var.values[idx] if 0 <= idx < len(var.values) else "")
            return out
        # treat as string-like
        return [str(x) if x is not None else "" for x in col]

    def _build_palette(self, n_class: int) -> List[QColor]:
        base_hex = PALETTES.get(self.palette_name, PALETTES["Tab20"])
        base = [QColor(*hex_to_rgb(h)) for h in base_hex]
        if n_class <= len(base):
            return base[:n_class]
        extra = n_class - len(base)
        extra_cols = [QColor(r, g, b) for (r, g, b) in hsv_palette(extra)]
        return base + extra_cols

    def _apply_table_style(self):
        if not self.table:
            return
        f = QFont()
        f.setPointSize(int(self.font_pt))
        self.table.setFont(f)
        self.table.verticalHeader().setDefaultSectionSize(int(self.row_height))
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.resizeColumnsToContents()


    def _refresh_legend(self, mapping: Dict[str, QColor] | None = None):
        self.legend_view.setVisible(self.show_legend)
        if not self.show_legend:
            return
        if mapping is None:
            self.legend_view.setHtml("")
            return
        # tampilkan maksimal 50 item agar tak kepanjangan
        items = list(mapping.items())[:50]
        parts = [
            "<style>.sw{display:inline-block;width:12px;height:12px;margin-right:6px;border:1px solid #666;}</style>",
            "<div style='line-height:1.5'>"
        ]
        for label, qcol in items:
            parts.append(
                f"<div><span class='sw' style='background: rgb({qcol.red()},{qcol.green()},{qcol.blue()})'></span>"
                f"{html.escape(str(label))}</div>"
            )
        if len(mapping) > 50:
            parts.append(f"<div>… {len(mapping)-50} lainnya</div>")
        parts.append("</div>")
        self.legend_view.setHtml("".join(parts))

    # ===== Main render =====
    def commit(self):
        self.table.clear()
        if not self.data or len(self.data) == 0:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self._refresh_legend(None)
            return

        data = self.data
        n_total = len(data)

        # --- tentukan variabel warna yang akan dipakai & labelnya ---
        color_var_header = ""
        if self.color_var_name:
            color_var_header = self.color_var_name
        elif data.domain.class_var is not None:
            color_var_header = data.domain.class_var.name
        labels = self._labels_from_var(data, color_var_header) if color_var_header else [""] * n_total

        # --- hitung Top-N & siapkan peta warna ---
        from collections import Counter
        cnt = Counter(labels)
        ordered_labels = sorted(cnt.keys(), key=lambda k: (-cnt[k], k))
        top_labels = ordered_labels[: max(1, int(self.top_n_distinct))]

        palette = self._build_palette(len(top_labels))
        label2color = {lab: palette[i] for i, lab in enumerate(top_labels)}
        gray = QColor(220, 220, 220)

        if self.others_gray:
            for lab in ordered_labels[len(top_labels):]:
                label2color[lab] = gray
        else:
            need = max(0, len(ordered_labels) - len(top_labels))
            if need:
                ext = self._build_palette(need)
                for i, lab in enumerate(ordered_labels[len(top_labels):]):
                    label2color[lab] = ext[i]

        # --- urutkan baris (opsional) ---
        row_indices = list(range(n_total))
        if self.sort_by_group:
            order_map = {lab: i for i, lab in enumerate(ordered_labels)}
            row_indices.sort(key=lambda i: (order_map.get(labels[i], 10**9), i))

        # --- limit baris yang ditampilkan ---
        row_indices = row_indices[: int(self.max_rows)]

        # --- siapkan header: kolom warna di paling kiri + semua kolom lain (tanpa duplikasi) ---
        attrs = list(data.domain.attributes)
        metas = list(data.domain.metas)
        headers = []
        include_color_col = bool(color_var_header)
        if include_color_col:
            headers.append(color_var_header)

        headers += [v.name for v in attrs if v.name != color_var_header]
        headers += [v.name for v in metas if v.name != color_var_header]

        self.table.setRowCount(len(row_indices))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # --- style umum ---
        self._apply_table_style()
        self.table.setUpdatesEnabled(False)

        # --- render sel + background per baris ---
        name_to_attr = {v.name: v for v in attrs}
        name_to_meta = {v.name: v for v in metas}

        for r, i in enumerate(row_indices):
            bg = QBrush(label2color.get(labels[i], gray))
            col = 0

            # kolom variabel warna (label grup) di kiri
            if include_color_col:
                item = QTableWidgetItem(str(labels[i]))
                item.setBackground(bg)
                self.table.setItem(r, col, item)
                col += 1

            # attributes
            for v in attrs:
                if v.name == color_var_header:
                    continue
                val = data[i, v]
                item = QTableWidgetItem(str(val))
                item.setBackground(bg)
                self.table.setItem(r, col, item)
                col += 1

            # metas
            for v in metas:
                if v.name == color_var_header:
                    continue
                val = data[i, v]
                item = QTableWidgetItem(str(val))
                item.setBackground(bg)
                self.table.setItem(r, col, item)
                col += 1

        self.table.setUpdatesEnabled(True)
        self.table.resizeColumnsToContents()
