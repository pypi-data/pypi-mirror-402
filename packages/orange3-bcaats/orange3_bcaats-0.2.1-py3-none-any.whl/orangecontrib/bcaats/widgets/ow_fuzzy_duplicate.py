from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import math
import numpy as np
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QListView
from Orange.data import Table, Domain, StringVariable, DiscreteVariable, ContinuousVariable, Variable
from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui, settings
from Orange.widgets.utils.itemmodels import DomainModel

# ======== Kemiripan string =========
try:
    from rapidfuzz import fuzz
    def str_sim(a: str, b: str, method: str) -> float:
        a = (a or "").strip()
        b = (b or "").strip()
        if not a and not b:
            return 1.0
        if method == "token_sort":
            return fuzz.token_sort_ratio(a, b) / 100.0
        elif method == "partial":
            return fuzz.partial_ratio(a, b) / 100.0
        else:  # 'ratio'
            return fuzz.ratio(a, b) / 100.0
    HAS_RAPIDFUZZ = True
except Exception:
    import difflib
    def str_sim(a: str, b: str, method: str) -> float:
        a = (a or "").strip()
        b = (b or "").strip()
        if not a and not b:
            return 1.0
        # difflib SequenceMatcher ~ mirip Levenshtein normalized
        return difflib.SequenceMatcher(None, a, b).ratio()
    HAS_RAPIDFUZZ = False

# ======== Kemiripan numerik sederhana =========
def num_sim(x: float | None, y: float | None) -> float:
    if x is None or y is None:
        return 0.0
    try:
        ax, ay = float(x), float(y)
    except Exception:
        return 0.0
    denom = max(abs(ax), abs(ay), 1.0)
    d = min(abs(ax - ay) / denom, 1.0)
    return 1.0 - d

# ======== Union-Find utk clustering =========
class DSU:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0]*n
    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    def union(self, a: int, b: int):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

# ======== Widget =========
class OWFuzzyDuplicate(OWWidget):
    # Metadata
    name = "Fuzzy Duplicate"
    description = "Kelompokkan baris yang mirip berdasarkan kolom terpilih (fuzzy match)."
    icon = "icons/fuzzy.png"
    priority = 2
    keywords = ["duplicate", "fuzzy", "similarity", "near-duplicate", "match"]

    class Inputs:
        data = Input("Data", Table)

    class Outputs:
        data = Output("Data + fuzzy_group", Table)

    # Settings (persist)
    threshold = settings.Setting(90)                 # 0..100
    method = settings.Setting("token_sort")          # 'token_sort'|'ratio'|'partial' (difflib akan pakai 'ratio')
    blocking = settings.Setting("prefix3")           # 'none'|'firstchar'|'prefix3'|'len±2'
    max_pairs_softlimit = settings.Setting(2_000_000)  # batasi O(n^2)
    
    # NEW:
    colorize_by_group = settings.Setting(True)       # jadikan fuzzy_group sbg class utk warna
    sort_by_group = settings.Setting(True)        

    selected_rows = settings.Setting([])             # simpan selection index (optional)

    want_main_area = False

    def __init__(self):
        super().__init__()
        self.data: Optional[Table] = None

        # --- Panel: kolom target ---
        box_cols = gui.widgetBox(self.controlArea, "Pilih Kolom untuk Dicek")
        self.var_model = DomainModel(
            order=DomainModel.ATTRIBUTES | DomainModel.METAS,
            separators=False,
            valid_types=(StringVariable, DiscreteVariable, ContinuousVariable),
        )

        self.var_view = gui.listView(box_cols, self, model=self.var_model)
        self.var_view.setSelectionMode(QListView.ExtendedSelection)

        gui.button(box_cols, self, "Pilih Kolom Teks (Auto)", callback=self._auto_select_text)

        # --- Panel: parameter ---
        box_param = gui.widgetBox(self.controlArea, "Parameter")
        self.slider = gui.hSlider(
            box_param, self, "threshold", minValue=50, maxValue=100, step=1,
            label="Threshold kemiripan (%)", ticks=True, callback=self._on_params_changed
        )
        self.cb_method = gui.comboBox(
            box_param, self, "method",
            items=["token_sort", "ratio", "partial"],  # jika difflib, 'partial' akan sama saja
            label="Metode kemiripan", callback=self._on_params_changed
        )
        if not HAS_RAPIDFUZZ:
            gui.widgetLabel(
                box_param,
                "RapidFuzz tidak terpasang, fallback ke difflib (lebih lambat)."
            )

        self.cb_block = gui.comboBox(
            box_param, self, "blocking",
            items=["none", "firstchar", "prefix3", "len±2"],
            label="Blocking (percepat pencarian)", callback=self._on_params_changed
        )
        
        # NEW:
        gui.checkBox(
            box_param, self, "colorize_by_group",
            "Warnai per grup (jadikan 'fuzzy_group' sebagai class)",
            callback=self._on_params_changed
        )
        gui.checkBox(
            box_param, self, "sort_by_group",
            "Urutkan output menurut grup",
            callback=self._on_params_changed
        )

        gui.separator(self.controlArea)
        self.info_label = gui.widgetLabel(self.controlArea, "Tidak ada data.")
        gui.button(self.controlArea, self, "Jalankan", callback=self.commit)

    # ====== Input handler ======
    @Inputs.data
    def set_data(self, data: Optional[Table]):
        self.data = data
        if data is None:
            self.var_model.set_domain(None)
            self.info_label.setText("Tidak ada data.")
            self.Outputs.data.send(None)
            return

        self.var_model.set_domain(self.data.domain)
        self.info_label.setText(f"Baris: {len(data)} | Fitur: {len(data.domain.attributes)}")
        # Optional: auto pilih kolom teks saat pertama kali
        if not self.var_view.selectionModel().selectedRows():
            self._auto_select_text()

    def _on_params_changed(self):
        pass  # jalankan manual via tombol

    def _auto_select_text(self):
        # pilih semua String/Discrete(treat as text) kolom (attr+meta+class)
        sel_model = self.var_view.selectionModel()
        sel_model.clearSelection()
        for row in range(self.var_model.rowCount()):
            var = self.var_model[row]
            if isinstance(var, (StringVariable, DiscreteVariable)):
                idx = self.var_model.index(row, 0)
                sel_model.select(idx, sel_model.Select | sel_model.Rows)

    # ====== Algoritma ======
    def _selected_vars(self) -> List[Variable]:
        return [self.var_model[idx.row()]
                for idx in self.var_view.selectionModel().selectedRows()]

    def _norm_text(self, v) -> str:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return ""
        return str(v).strip().lower()

    def _blocking_key(self, row_vals: List[Tuple[Variable, object]]) -> str:
        # row_vals = [(var, value), ...] untuk kolom terpilih
        if self.blocking == "none":
            return ""
        # gabungkan nilai string untuk key sederhana
        joined = " ".join(self._norm_text(v) for _, v in row_vals if v is not None)
        if self.blocking == "firstchar":
            t = joined.split()
            return (t[0][0] if t and t[0] else "") if joined else ""
        elif self.blocking == "prefix3":
            t = joined.split()
            head = t[0] if t else ""
            return head[:3] if head else ""
        elif self.blocking == "len±2":
            return f"len:{len(joined)}"
        return ""

    def _pairwise_similarity(
        self, row_i: Dict[str, object], row_j: Dict[str, object], vars: List[Variable]
    ) -> float:
        sims = []
        for var in vars:
            vi = row_i.get(var.name, None)
            vj = row_j.get(var.name, None)
            if isinstance(var, ContinuousVariable):
                si = num_sim(vi, vj)
            else:
                si = str_sim(self._norm_text(vi), self._norm_text(vj), self.method)
            sims.append(si)
        return float(np.mean(sims)) if sims else 0.0

    
    def commit(self):
        data = self.data
        if data is None or len(data) == 0:
            self.Outputs.data.send(None)
            return

        vars_sel = self._selected_vars()
        if not vars_sel:
            self.info_label.setText("Pilih minimal satu kolom untuk dicek.")
            self.Outputs.data.send(None)
            return

        n = len(data)
        # siapkan view dict per baris untuk akses cepat
        # ambil nilai via Table's functions:
        # untuk keseragaman, pakai Table.to_numpy untuk X dan metas + DataFrame? Kita langsung pakai Table.metas dll.
        # lebih mudah: gunakan Table instance indexing; untuk performa, ini cukup untuk ribuan baris.
        rows: List[Dict[str, object]] = []
        for i in range(n):
            rec = {}
            for var in vars_sel:
                try:
                    val = data.get_column(var)[i]
                except Exception:
                    # fallback untuk metas/string
                    val = data[i][var]
                # cast numpy/scalars ke python native
                if isinstance(val, np.generic):
                    val = np.asscalar(val) if hasattr(np, "asscalar") else val.item()
                rec[var.name] = val
            rows.append(rec)

        # Blocking buckets
        buckets: Dict[str, List[int]] = {}
        for i in range(n):
            row_vals = [(v, rows[i].get(v.name, None)) for v in vars_sel]
            key = self._blocking_key(row_vals)
            buckets.setdefault(key, []).append(i)

        # Estimasi jumlah pasangan
        est_pairs = sum(len(b)*(len(b)-1)//2 for b in buckets.values())
        if self.blocking == "none" and est_pairs > self.max_pairs_softlimit:
            self.info_label.setText(
                f"Pasangan ∼ {est_pairs:,}. Terlalu besar. "
                f"Ganti blocking atau kurangi data terlebih dulu."
            )
            self.Outputs.data.send(None)
            return

        # Build graph (Union-Find)
        dsu = DSU(n)
        thr = self.threshold / 100.0

        for key, idxs in buckets.items():
            m = len(idxs)
            if m <= 1:
                continue
            # bandingkan semua pasangan dalam bucket
            for ii in range(m):
                i = idxs[ii]
                for jj in range(ii+1, m):
                    j = idxs[jj]
                    s = self._pairwise_similarity(rows[i], rows[j], vars_sel)
                    if s >= thr:
                        dsu.union(i, j)

        # Bentuk group id
        root_to_gid: Dict[int, int] = {}
        gid_counter = 0
        group_labels = [""] * n
        for i in range(n):
            r = dsu.find(i)
            if r not in root_to_gid:
                gid_counter += 1
                root_to_gid[r] = gid_counter
            g = root_to_gid[r]
            # label "G1", "G2", ... ; jika semua singleton, tetap G#
            group_labels[i] = f"G{g}"
            
        # (Opsional) urutkan baris menurut nomor grup agar rapat di Data Table
        if self.sort_by_group:
            def _grp_num(lbl: str) -> int:
                # ekstrak angka setelah 'G' agar urut G1, G2, ...
                return int(lbl[1:]) if len(lbl) > 1 and lbl[1:].isdigit() else 10**9
            order = np.argsort(np.array([_grp_num(g) for g in group_labels]))
            data = self.data[order]
            group_labels = [group_labels[i] for i in order]
        else:
            data = self.data
            
        import colorsys

        def hex_to_rgb(hexcode: str) -> tuple[int, int, int]:
            hexcode = hexcode.lstrip("#")
            r = int(hexcode[0:2], 16)
            g = int(hexcode[2:4], 16)
            b = int(hexcode[4:6], 16)
            return (r, g, b)

        def hsv_palette(n: int) -> list[tuple[int, int, int]]:
            # Palet banyak warna stabil (HSV wheel) → n warna unik
            # S = 0.55..0.75 biar tidak terlalu pucat; V tinggi agar terang di Data Table
            out = []
            for i in range(n):
                h = (i / max(1, n)) % 1.0
                s = 0.65
                v = 0.95
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                out.append((int(r * 255), int(g * 255), int(b * 255)))
            return out
        

        # Siapkan domain & tabel keluar
        # --- sesudah blok sorting (order) ---
        # Bangun urutan label unik yg stabil: G1, G2, ...
        def _grp_num(lbl: str) -> int:
            return int(lbl[1:]) if len(lbl) > 1 and lbl[1:].isdigit() else 10**9

        labels_sorted = sorted(set(group_labels), key=_grp_num)

        if self.colorize_by_group:
            # Jadikan fuzzy_group sbg CLASS (Discrete)
            disc = DiscreteVariable("fuzzy_group", values=labels_sorted)

            # === Palet warna: panjangnya = jumlah grup ===
            import colorsys
            def hex_to_rgb(h: str):
                h = h.lstrip("#")
                return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

            BASE_HEX = [
                "#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f",
                "#edc948","#b07aa1","#ff9da7","#9c755f","#bab0ab",
                "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
                "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"
            ]
            base = [hex_to_rgb(h) for h in BASE_HEX]

            def hsv_palette(n: int):
                out = []
                for i in range(n):
                    h = (i / max(1, n)) % 1.0
                    s, v = 0.65, 0.95
                    r, g, b = colorsys.hsv_to_rgb(h, s, v)
                    out.append((int(r*255), int(g*255), int(b*255)))
                return out

            if len(labels_sorted) <= len(base):
                colors = base[:len(labels_sorted)]
            else:
                colors = base + hsv_palette(len(labels_sorted) - len(base))

            # Penting: list of (r,g,b) tuples
            disc.colors = colors

            # Bersihkan attribute "colors" di metadata agar header tidak menampilkan teks panjang
            try:
                attrs = dict(getattr(disc, "attributes", {}))
                attrs.pop("colors", None)
                disc.attributes = attrs
            except Exception:
                pass

            # Domain dengan class = fuzzy_group
            new_domain = Domain(
                data.domain.attributes,
                (disc,),
                data.domain.metas
            )
            out = Table.from_table(new_domain, data)

            # Map label -> indeks kelas (float sesuai konvensi Orange)
            label_to_index = {lab: i for i, lab in enumerate(labels_sorted)}
            out.Y = np.array([label_to_index[lab] for lab in group_labels], dtype=float)

        else:
            # Simpan sebagai meta String (tanpa pewarnaan otomatis)
            fuzzy_var = StringVariable("fuzzy_group")
            new_domain = Domain(
                data.domain.attributes,
                data.domain.class_vars,
                data.domain.metas + (fuzzy_var,)
            )
            out = Table.from_table(new_domain, data)
            out.metas[:, -1] = np.array(group_labels, dtype=object)


        self.info_label.setText(
            f"Groups: {len(labels_sorted)} | Threshold: {self.threshold}% | "
            f"Blocking: {self.blocking} | Metode: {self.method}"
        )
        self.Outputs.data.send(out)
        # DEBUG (sementara, boleh dihapus setelah cek)
        # cv = out.domain.class_var
        # print("DEBUG fuzzy_group class?", cv is not None, "values:", len(getattr(cv, "values", [])))
        # print("DEBUG colors len:", len(getattr(cv, "colors", [])))
        # print("DEBUG first 5 colors:", getattr(cv, "colors", [])[:5])
