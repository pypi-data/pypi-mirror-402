import math
from typing import List, Optional, Tuple

import numpy as np

from AnyQt.QtWidgets import QSizePolicy, QTextEdit
from AnyQt.QtCore import Qt

from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets.settings import Setting
from Orange.widgets import gui
from Orange.data import Table, Domain, ContinuousVariable, StringVariable

# Matplotlib untuk plot di mainArea
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ======== Util ========
BENFORD_P = np.array([math.log10(1 + 1/d) for d in range(1, 10)], dtype=float)  # 1..9


def _leading_first_digit(x: float) -> Optional[int]:
    """Ambil digit pertama signifikan (1..9) dari x; None untuk 0/NaN/inf."""
    if x is None or not np.isfinite(x):
        return None
    ax = abs(float(x))
    if ax <= 0.0:
        return None
    while ax >= 10.0:
        ax /= 10.0
    while ax < 1.0:
        ax *= 10.0
    d = int(ax)
    if 1 <= d <= 9:
        return d
    return None


def _benford_counts(values: np.ndarray, ignore_zero=True, ignore_negative=True) -> Tuple[np.ndarray, int]:
    """Hitung frekuensi digit pertama 1..9 pada array values."""
    counts = np.zeros(9, dtype=int)
    n = 0
    for v in values:
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            continue
        fv = float(v)
        if ignore_zero and fv == 0.0:
            continue
        if ignore_negative and fv < 0.0:
            continue
        d = _leading_first_digit(fv)
        if d is not None:
            counts[d - 1] += 1
            n += 1
    return counts, n


def _mad(actual_probs: np.ndarray) -> float:
    """Mean Absolute Deviation terhadap distribusi Benford."""
    return float(np.mean(np.abs(actual_probs - BENFORD_P)))


def _mad_grade(mad: float) -> str:
    """Klasifikasi MAD (Nigrini)."""
    if mad < 0.006:
        return "Close conformity"
    if mad < 0.012:
        return "Acceptable"
    if mad < 0.015:
        return "Marginal"
    return "Nonconformity"


def _chi_square(counts: np.ndarray, n: int) -> Tuple[float, float]:
    """Uji Chi-square goodness-of-fit; return (chi2, pvalue) df=8 (tanpa SciPy)."""
    if n == 0:
        return float("nan"), float("nan")
    expected = BENFORD_P * n
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.nansum((counts - expected) ** 2 / expected)

    # p-value via upper regularized gamma (df=8). Pakai mpmath jika tersedia.
    try:
        import mpmath as mp
        p = float(mp.gammainc(8/2, chi2/2, mp.inf) / mp.gamma(8/2))
    except Exception:
        p = float("nan")
    return float(chi2), p


# ======== Widget ========
class OWBenfordsLaw(OWWidget):
    name = "Benford's Law Test"
    description = "Uji kesesuaian digit pertama (1–9) terhadap Hukum Benford untuk kolom numerik."
    icon = "icons/bendford.png"
    priority = 50
    keywords = ["benford", "first digit", "audit", "forensic"]

    class Inputs:
        data = Input("Data", Table)

    class Outputs:
        table = Output("Distribusi Benford", Table)

    # Settings
    attr_index: int = Setting(0)
    ignore_zero: bool = Setting(True)
    ignore_negative: bool = Setting(True)
    show_percent: bool = Setting(False)   # tampilkan grafik sebagai %
    auto_run: bool = Setting(True)

    want_main_area = True

    def __init__(self):
        super().__init__()
        self.data: Optional[Table] = None
        self.numeric_attrs: List[ContinuousVariable] = []

        # --- UI kiri (controlArea) ---
        box_in = gui.widgetBox(self.controlArea, "Input & Kolom")
        self.cb_attr = gui.comboBox(box_in, self, "attr_index", label="Kolom numerik:", callback=self._maybe_autorun)
        gui.checkBox(box_in, self, "ignore_zero", "Abaikan 0", callback=self._maybe_autorun)
        gui.checkBox(box_in, self, "ignore_negative", "Abaikan negatif", callback=self._maybe_autorun)

        box_disp = gui.widgetBox(self.controlArea, "Tampilan")
        gui.checkBox(box_disp, self, "show_percent", "Tampilkan sebagai persentase (%)", callback=self._maybe_autorun)
        gui.checkBox(box_disp, self, "auto_run", "Jalankan otomatis saat berubah")

        gui.button(self.controlArea, self, "Hitung Benford Sekarang", callback=self.run_now)

        # Kotak ringkasan (bullet) di bawah
        self.summary_box = QTextEdit()
        self.summary_box.setReadOnly(True)
        self.summary_box.setMinimumHeight(90)
        self.controlArea.layout().addWidget(self.summary_box)

        # --- UI kanan (mainArea) → Matplotlib canvas ---
        self.fig = Figure(figsize=(5, 3), tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainArea.layout().addWidget(self.canvas)

        self._clear_plot()
        self._update_summary_box(None, None, None, None, None)

    # ===== Inputs =====
    @Inputs.data
    def set_data(self, data: Optional[Table]):
        self.data = data
        self._populate_numeric_attrs()
        self._clear_plot()
        if data is None or len(self.numeric_attrs) == 0:
            self._update_summary_box(None, None, None, None, None)
            self.Outputs.table.send(None)
            return
        if self.auto_run:
            self.run_now()
        else:
            self._update_summary_box(self.numeric_attrs[self.attr_index].name, 0, float("nan"), float("nan"), "—")

    # ===== Helpers =====
    def _populate_numeric_attrs(self):
        self.numeric_attrs = []
        self.cb_attr.clear()
        if not self.data:
            return
        for var in self.data.domain.attributes:
            if isinstance(var, ContinuousVariable):
                self.numeric_attrs.append(var)
        for var in self.numeric_attrs:
            self.cb_attr.addItem(var.name)
        if self.numeric_attrs:
            self.attr_index = min(self.attr_index, len(self.numeric_attrs) - 1)
        else:
            self.attr_index = 0

    def _maybe_autorun(self):
        if self.auto_run and self.data is not None:
            self.run_now()

    def _clear_plot(self):
        self.ax.clear()
        self.ax.set_xlabel("Digit pertama")
        self.ax.set_ylabel("Proporsi")
        self.ax.set_xticks(range(1, 10))
        self.ax.set_ylim(0, 0.35)
        self.ax.grid(True, alpha=0.2)
        self.ax.plot(range(1, 10), BENFORD_P, marker="o", linestyle="-", label="Expected (Benford)")
        self.ax.legend(loc="best")
        self.canvas.draw_idle()

    def _update_summary_box(self, colname: Optional[str], n: Optional[int],
                        mad: Optional[float], chi2: Optional[float],
                        ptxt: Optional[str], unit: Optional[str] = None):
        """Tampilkan ringkasan sebagai bullet list."""
        bullets = []
        if colname is None:
            bullets.append("• Tidak ada data atau tidak ada kolom numerik.")
        else:
            bullets.append(f"• Kolom dianalisis: {colname} (n={n})")
            if mad is not None and not (mad != mad):  # not NaN
                grade = _mad_grade(mad)
                bullets.append(f"• MAD = {mad:.4f} → {grade}")
            else:
                bullets.append("• MAD = NA")
            if chi2 is not None and not (chi2 != chi2):
                bullets.append(f"• χ² = {chi2:.2f}, p = {ptxt}")
            else:
                bullets.append("• χ²/p-value = NA")
            if unit:
                bullets.append(f"• Tampilan grafik: {unit}")
        self.summary_box.setPlainText("\n".join(bullets))

    # ===== Core =====
    def run_now(self):
        if self.data is None or not self.numeric_attrs:
            self._update_summary_box(None, None, None, None, None)
            self.Outputs.table.send(None)
            self._clear_plot()
            return

        var = self.numeric_attrs[self.attr_index]
        col = self.data.get_column_view(var)[0]  # numpy array
        counts, n = _benford_counts(col, ignore_zero=self.ignore_zero, ignore_negative=self.ignore_negative)
        if n == 0:
            self._update_summary_box(var.name, 0, float("nan"), float("nan"), "NA", "%" if self.show_percent else "proporsi")
            self.Outputs.table.send(None)
            self._clear_plot()
            return

        actual_p = counts / n
        mad = _mad(actual_p)
        chi2, pval = _chi_square(counts, n)

        # ----- plot -----
        self.ax.clear()
        xs = np.arange(1, 10)
        scale = 100.0 if self.show_percent else 1.0
        y_label = "Persentase (%)" if self.show_percent else "Proporsi"
        actual_for_plot = actual_p * scale
        expected_for_plot = BENFORD_P * scale

        self.ax.bar(xs, actual_for_plot, alpha=0.7, label="Actual")
        self.ax.plot(xs, expected_for_plot, marker="o", linestyle="-", label="Expected (Benford)")
        self.ax.set_xticks(xs)
        ymax = max(actual_for_plot.max(), expected_for_plot.max()) * 1.15
        self.ax.set_ylim(0, max(35 if self.show_percent else 0.35, float(ymax)))
        self.ax.set_xlabel("Digit pertama")
        self.ax.set_ylabel(y_label)
        self.ax.grid(True, alpha=0.2)
        self.ax.legend(loc="best")
        self.canvas.draw_idle()

        # ----- table output -----
        domain = Domain(
            [
                ContinuousVariable("digit"),
                ContinuousVariable("count"),
                ContinuousVariable("actual_prop"),
                ContinuousVariable("expected_prop"),
                ContinuousVariable("difference"),
                ContinuousVariable("zscore"),
                ContinuousVariable("actual_pct"),
                ContinuousVariable("expected_pct"),
                ContinuousVariable("difference_pct"),
            ],
            metas=[StringVariable("column"), StringVariable("notes")]
        )
        denom = np.sqrt(BENFORD_P * (1 - BENFORD_P) / n)
        with np.errstate(divide="ignore", invalid="ignore"):
            z = (actual_p - BENFORD_P) / denom

        X = np.column_stack([
            xs.astype(float),
            counts.astype(float),
            actual_p.astype(float),
            BENFORD_P.astype(float),
            (actual_p - BENFORD_P).astype(float),
            z.astype(float),
            (actual_p * 100.0).astype(float),
            (BENFORD_P * 100.0).astype(float),
            ((actual_p - BENFORD_P) * 100.0).astype(float),
        ])
        ptxt = f"{pval:.4f}" if not np.isnan(pval) else "NA (SciPy/MPMath tidak tersedia)"
        notes = f"n={n}; MAD={mad:.4f} ({_mad_grade(mad)}); χ²={chi2:.2f}; p={ptxt}"
        metas = np.array([[var.name, notes]], dtype=object)
        out = Table.from_numpy(domain, X, metas=np.repeat(metas, repeats=9, axis=0))
        self.Outputs.table.send(out)

        # ----- ringkasan bawah -----
        self._update_summary_box(var.name, n, mad, chi2, ptxt, "%" if self.show_percent else "proporsi")
