from __future__ import annotations
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from AnyQt.QtWidgets import QListView, QComboBox
from Orange.data import ContinuousVariable, Domain, StringVariable, Table, Variable
from Orange.widgets import gui, settings
from Orange.widgets.utils.itemmodels import DomainModel
from Orange.widgets.widget import Input, Output, OWWidget


@dataclass
class SeqRow:
    row_index: int
    raw_text: str
    group: str
    value: Optional[int]  # nilai urutan yg dipakai untuk cek (int) atau None kalau gagal parse


class OWSequenceChecker(OWWidget):
    # Metadata
    name = "Sequence Checker"
    description = "Mendeteksi nomor lompat/tidak urut, duplikasi, dan nomor tak terbaca."
    icon = "icons/sequence.png"
    priority = 30
    keywords = ["sequence", "gap", "missing", "invoice", "nota", "urut", "checker"]

    class Inputs:
        data = Input("Data", Table)

    class Outputs:
        data = Output("Data + anotasi", Table)             # data asli + kolom meta
        gaps = Output("Gaps (missing ranges)", Table)      # ringkasan rentang hilang
        duplicates = Output("Duplicates", Table)           # ringkasan duplikat
        summary = Output("Summary per group", Table)       # min/max dan ringkasan
        missing_rows = Output("Missing (expanded)", Table) # setiap nomor hilang = 1 baris

    # -------- Settings (disimpan) --------
    # Pra-filter (opsional)
    prefilter = settings.Setting(False)               # aktif/nonaktif
    prefilter_mode = settings.Setting("contains")     # contains|startswith|endswith|regex
    prefilter_pattern = settings.Setting("")          # pola atau regex
    prefilter_case = settings.Setting(False)          # case-sensitive?

    # kolom target
    column_name: str = settings.Setting("")

    # mode ekstraksi nomor: 0=digits, 1=split
    parse_mode: int = settings.Setting(0)
    # mode=digits: ambil digit pertama; group by prefix non-digit sebelum angka?
    group_by_prefix: bool = settings.Setting(True)
    # mode=split: delimiter & token index (1-based)
    delimiters: str = settings.Setting("/-")
    token_index: int = settings.Setting(1)

    # properti cek urutan
    expected_step: int = settings.Setting(1)
    sort_output: bool = settings.Setting(True)

    want_main_area = False

    def __init__(self):
        super().__init__()
        self.data: Optional[Table] = None
        self.info_label = gui.widgetLabel(self.controlArea, "Tidak ada data.")

        # --- pilih kolom ---
        box_col = gui.widgetBox(self.controlArea, "Kolom target")
        self.var_model = DomainModel(
            order=DomainModel.ATTRIBUTES | DomainModel.METAS,
            separators=False,
        )
        gui.widgetLabel(box_col, "Kolom nomor")
        self.var_combo = QComboBox()
        self.var_combo.setModel(self.var_model)
        v: QListView = QListView(self.var_combo)
        v.setUniformItemSizes(True)
        self.var_combo.setView(v)
        self.var_combo.currentIndexChanged.connect(self._on_column_changed)
        box_col.layout().addWidget(self.var_combo)

        # --- cara ekstraksi nomor ---
        box_parse = gui.widgetBox(self.controlArea, "Cara membaca nomor")
        gui.radioButtons(
            box_parse, self, "parse_mode",
            btnLabels=("Digit pertama (regex)", "Split delimiters"),
            callback=self._on_mode_changed
        )
        self.cb_group_prefix = gui.checkBox(
            gui.indentedBox(box_parse), self, "group_by_prefix",
            "Kelompokkan per prefix non-digit sebelum angka"
        )
        ibox = gui.indentedBox(box_parse)
        gui.lineEdit(ibox, self, "delimiters", label="Delimiters", placeholderText="/-._| ")
        gui.spin(ibox, self, "token_index", 1, 20, step=1, label="Token ke-")

        # --- Pra-filter ---
        box_pre = gui.widgetBox(self.controlArea, "Pra-filter (opsional)")
        gui.checkBox(box_pre, self, "prefilter", "Aktifkan pra-filter")
        gui.comboBox(
            box_pre, self, "prefilter_mode",
            items=["contains", "startswith", "endswith", "regex"],
            label="Mode",
            sendSelectedValue=True,
        )
        gui.lineEdit(box_pre, self, "prefilter_pattern", label="Pola")
        gui.checkBox(box_pre, self, "prefilter_case", "Case sensitive")

        # --- parameter cek ---
        box_chk = gui.widgetBox(self.controlArea, "Parameter cek")
        gui.spin(box_chk, self, "expected_step", 1, 999999, step=1, label="Step yang diharapkan")
        gui.checkBox(box_chk, self, "sort_output", "Urutkan output menurut grup & nilai")

        gui.button(self.controlArea, self, "Jalankan", callback=self.commit)

    # ---------- handlers ----------
    def _on_column_changed(self, *_):
        idx = self.var_combo.currentIndex()
        if 0 <= idx < self.var_model.rowCount():
            var = self.var_model[idx]
            self.column_name = var.name if var is not None else ""
        else:
            self.column_name = ""

    @Inputs.data
    def set_data(self, data: Optional[Table]):
        self.data = data
        if data is None or len(data) == 0:
            self.var_model.set_domain(None)
            self.info_label.setText("Tidak ada data.")
            self.Outputs.data.send(None)
            self.Outputs.gaps.send(None)
            self.Outputs.duplicates.send(None)
            self.Outputs.summary.send(None)
            self.Outputs.missing_rows.send(None)
            return

        self.var_model.set_domain(data.domain)

        from Orange.data import Variable as _Var
        if isinstance(self.column_name, _Var):
            self.column_name = self.column_name.name

        if not self.column_name:
            names = [v.name for v in list(data.domain.metas) + list(data.domain.attributes)]
            self.column_name = names[0] if names else ""

        def _find_idx_by_name(name: str) -> int:
            for i in range(self.var_model.rowCount()):
                v = self.var_model[i]
                if v is not None and v.name == name:
                    return i
            return 0

        self.var_combo.blockSignals(True)
        self.var_combo.setCurrentIndex(_find_idx_by_name(self.column_name))
        self.var_combo.blockSignals(False)

        self.info_label.setText(f"Baris: {len(data)} | Kolom terpilih: {self.column_name or '-'}")

    def _on_mode_changed(self):
        pass

    # ---------- pra-filter ----------
    def _pass_prefilter(self, s: str) -> bool:
        if not self.prefilter or not self.prefilter_pattern:
            return True
        txt = "" if s is None else str(s)
        if self.prefilter_mode == "regex":
            flags = 0 if self.prefilter_case else re.IGNORECASE
            return bool(re.search(self.prefilter_pattern, txt, flags))
        a = txt if self.prefilter_case else txt.lower()
        b = self.prefilter_pattern if self.prefilter_case else self.prefilter_pattern.lower()
        if self.prefilter_mode == "contains":
            return b in a
        if self.prefilter_mode == "startswith":
            return a.startswith(b)
        if self.prefilter_mode == "endswith":
            return a.endswith(b)
        return True

    # ---------- parsing ----------
    def _split_tokens(self, s: str) -> List[str]:
        dels = "".join(sorted(set(self.delimiters))) or " "
        return re.split(f"[{re.escape(dels)}]+", s)

    def _parse_value_and_group(self, s: str) -> Tuple[Optional[int], str]:
        s = "" if s is None else str(s)
        if self.parse_mode == 0:  # digits
            m = re.search(r"(\d+)", s)
            if not m:
                return None, ""
            value = int(m.group(1))
            grp = s[:m.start()] if self.group_by_prefix else ""
            grp = grp.strip()
            return value, grp
        else:  # split
            toks = self._split_tokens(s)
            idx = max(1, int(self.token_index)) - 1
            token = toks[idx] if idx < len(toks) else ""
            m = re.search(r"(\d+)", token)
            val = int(m.group(1)) if m else None
            grp = " ".join(toks[:idx]).strip()
            return val, grp

    # ---------- komputasi ----------
    def commit(self):
        data = self.data
        if data is None or len(data) == 0 or not self.column_name:
            self.Outputs.data.send(None)
            self.Outputs.gaps.send(None)
            self.Outputs.duplicates.send(None)
            self.Outputs.summary.send(None)
            self.Outputs.missing_rows.send(None)
            return

        var_by_name: Dict[str, Variable] = {
            v.name: v for v in list(data.domain.attributes) + list(data.domain.metas)
        }
        src_var = var_by_name.get(self.column_name)
        if src_var is None:
            self.info_label.setText("Kolom tidak ditemukan.")
            self.Outputs.data.send(None)
            self.Outputs.gaps.send(None)
            self.Outputs.duplicates.send(None)
            self.Outputs.summary.send(None)
            self.Outputs.missing_rows.send(None)
            return

        col = data.get_column(src_var)
        rows: List[SeqRow] = []
        included: List[bool] = []
        for i, raw in enumerate(col):
            raw_text = "" if raw is None else str(raw)
            inc = self._pass_prefilter(raw_text)
            if inc:
                val, grp = self._parse_value_and_group(raw_text)
            else:
                val, grp = None, ""
            included.append(inc)
            rows.append(SeqRow(i, raw_text, grp, val))

        by_grp: Dict[str, List[SeqRow]] = defaultdict(list)
        for r in rows:
            by_grp[r.group].append(r)

        step = max(1, int(self.expected_step))

        duplicate_records: List[Tuple[str, int, int]] = []
        gaps_records: List[Tuple[str, int, int, int, Optional[int], Optional[int]]] = []
        # summary per group
        summary_records: List[Tuple[str, float, float, float, float, float]] = []
        # missing expanded
        expanded_records: List[Tuple[str, int, Optional[int], Optional[int]]] = []

        flag = ["filtered-out" if not inc else "" for inc in included]
        gap_to_prev = [np.nan] * len(rows)

        for grp, items in by_grp.items():
            items_num = [r for r in items if r.value is not None and included[r.row_index]]
            if not items_num:
                for r in items:
                    if included[r.row_index] and r.value is None and flag[r.row_index] != "filtered-out":
                        flag[r.row_index] = "non-numeric"
                continue

            # urut nilai
            items_num.sort(key=lambda r: (r.value, r.row_index))

            counts = Counter(r.value for r in items_num)
            for v, c in counts.items():
                if c > 1:
                    duplicate_records.append((grp, v, c))
            dup_values = {v for v, c in counts.items() if c > 1}

            prev_v: Optional[int] = None
            for r in items_num:
                if flag[r.row_index] != "filtered-out":
                    flag[r.row_index] = "duplicate" if r.value in dup_values else "ok"
                if prev_v is None:
                    gap_to_prev[r.row_index] = np.nan
                else:
                    gap_to_prev[r.row_index] = float(r.value - prev_v)
                prev_v = r.value

            for r in items:
                if included[r.row_index] and r.value is None and flag[r.row_index] != "filtered-out":
                    flag[r.row_index] = "non-numeric"

            present = sorted(set(r.value for r in items_num))
            vmin, vmax = present[0], present[-1]
            expect = set(range(vmin, vmax + 1, step))
            missing = sorted(expect.difference(present))

            # summary
            expected_total = (vmax - vmin) // step + 1
            count_present = float(len(present))
            count_missing = float(len(missing))
            pct_missing = 100.0 * count_missing / expected_total if expected_total > 0 else 0.0
            summary_records.append((grp, float(vmin), float(vmax),
                                    count_present, count_missing, float(pct_missing)))

            # kompres ke rentang & buat expanded
            if missing:
                start = prev = missing[0]
                for x in missing[1:] + [None]:
                    if x is None or x != prev + step:
                        miss_from, miss_to = start, prev
                        cnt = (miss_to - miss_from) // step + 1
                        lower = max([p for p in present if p < miss_from], default=None)
                        higher = min([p for p in present if p > miss_to], default=None)
                        gaps_records.append((grp, miss_from, miss_to, cnt, lower, higher))
                        # expanded
                        vv = miss_from
                        while vv <= miss_to:
                            expanded_records.append((grp, vv, lower, higher))
                            vv += step
                        if x is not None:
                            start = x
                    prev = x if x is not None else prev

        # --------- Data + anotasi ----------
        seq_group_var = StringVariable("seq_group")
        seq_value_var = ContinuousVariable("seq_value")
        seq_flag_var = StringVariable("seq_flag")
        seq_gap_prev_var = ContinuousVariable("seq_gap_to_prev")

        new_domain = Domain(
            data.domain.attributes,
            data.domain.class_vars,
            data.domain.metas + (seq_group_var, seq_value_var, seq_flag_var, seq_gap_prev_var),
        )
        out_data = Table.from_table(new_domain, data)
        out_data.metas[:, -4] = np.array([r.group for r in rows], dtype=object)
        seq_vals = np.array([float(r.value) if r.value is not None else np.nan for r in rows], dtype=float)
        out_data.metas[:, -3] = seq_vals.astype(object)
        out_data.metas[:, -2] = np.array(flag, dtype=object)
        out_data.metas[:, -1] = np.array(gap_to_prev, dtype=float)

        if self.sort_output:
            order = np.lexsort((
                np.array([r.value if (r.value is not None and included[r.row_index]) else np.inf for r in rows]),
                np.array([r.group for r in rows], dtype=object),
            ))
            out_data = out_data[order, :]

        # --------- Gaps (ranges) ----------
        if gaps_records:
            g_group = StringVariable("seq_group")
            g_from  = ContinuousVariable("missing_from")
            g_to    = ContinuousVariable("missing_to")
            g_cnt   = ContinuousVariable("count_missing")
            g_prev  = ContinuousVariable("prev_present")
            g_next  = ContinuousVariable("next_present")
            gaps_domain = Domain((), (), (g_group, g_from, g_to, g_cnt, g_prev, g_next))
            N = len(gaps_records)
            gaps_tbl = Table.from_numpy(
                gaps_domain,
                X=np.empty((N, 0)),
                metas=np.array([
                    [gr, float(mf), float(mt), float(cnt),
                     (float(pp) if pp is not None else np.nan),
                     (float(nn) if nn is not None else np.nan)]
                    for (gr, mf, mt, cnt, pp, nn) in gaps_records
                ], dtype=object),
            )
        else:
            gaps_tbl = None

        # --------- Duplicates ----------
        if duplicate_records:
            d_group = StringVariable("seq_group")
            d_val   = ContinuousVariable("seq_value")
            d_cnt   = ContinuousVariable("count")
            dup_domain = Domain((), (), (d_group, d_val, d_cnt))
            N = len(duplicate_records)
            duplicates_tbl = Table.from_numpy(
                dup_domain,
                X=np.empty((N, 0)),
                metas=np.array([
                    [gr, float(v), float(c)]
                    for (gr, v, c) in sorted(duplicate_records, key=lambda t: (t[0], t[1]))
                ], dtype=object),
            )
        else:
            duplicates_tbl = None

        # --------- Summary per group ----------
        if summary_records:
            s_group = StringVariable("seq_group")
            s_min   = ContinuousVariable("min_value")
            s_max   = ContinuousVariable("max_value")
            s_present = ContinuousVariable("count_present")
            s_missing = ContinuousVariable("count_missing")
            s_pct     = ContinuousVariable("pct_missing")
            sum_domain = Domain((), (), (s_group, s_min, s_max, s_present, s_missing, s_pct))
            N = len(summary_records)
            summary_tbl = Table.from_numpy(
                sum_domain,
                X=np.empty((N, 0)),
                metas=np.array([
                    [gr, mn, mx, cp, cm, pct]
                    for (gr, mn, mx, cp, cm, pct) in summary_records
                ], dtype=object),
            )
        else:
            summary_tbl = None

        # --------- Missing (expanded) ----------
        if expanded_records:
            m_group = StringVariable("seq_group")
            m_val   = ContinuousVariable("missing_value")
            m_prev  = ContinuousVariable("prev_present")
            m_next  = ContinuousVariable("next_present")
            miss_domain = Domain((), (), (m_group, m_val, m_prev, m_next))
            N = len(expanded_records)
            missing_tbl = Table.from_numpy(
                miss_domain,
                X=np.empty((N, 0)),
                metas=np.array([
                    [gr, float(v),
                     (float(pp) if pp is not None else np.nan),
                     (float(nn) if nn is not None else np.nan)]
                    for (gr, v, pp, nn) in expanded_records
                ], dtype=object),
            )
        else:
            missing_tbl = None

        # ---- kirim output ----
        self.Outputs.data.send(out_data)
        self.Outputs.gaps.send(gaps_tbl)
        self.Outputs.duplicates.send(duplicates_tbl)
        self.Outputs.summary.send(summary_tbl)
        self.Outputs.missing_rows.send(missing_tbl)

        # ---- info ringkas ----
        n_non = sum(1 for f in flag if f == "non-numeric")
        n_dup = sum(1 for f in flag if f == "duplicate")
        self.info_label.setText(
            f"Grup: {len(by_grp)} | Non-numeric: {n_non} | Rows duplicate: {n_dup} | "
            f"Gaps: {len(gaps_records)} range | Missing rows: {len(expanded_records)}"
        )
