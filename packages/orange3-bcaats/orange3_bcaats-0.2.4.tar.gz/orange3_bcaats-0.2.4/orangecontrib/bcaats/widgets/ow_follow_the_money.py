# caatslab/widgets/ow_follow_the_money.py

from AnyQt import QtWidgets, QtCore
from AnyQt.QtCore import QPoint

from Orange.widgets.widget import OWWidget, Input, Msg
from orangewidget import gui
from orangewidget.settings import Setting
from Orange.data import Table
from Orange.data.pandas_compat import table_to_frame

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import cm

import numpy as np
import pandas as pd
import networkx as nx
from typing import Optional, List, Dict, Any


class OWFollowTheMoney(OWWidget):
    """
    Follow The Money

    Visualize money flow between entities (FROM -> TO) as a network / bubble chart.
    Expected columns:
        - from_entity
        - to_entity
        - value (numeric)
        - currency (optional)
        - description (optional)
    """

    name = "Follow The Money"
    id = "caatslab-follow-the-money"
    description = "Visualize money flow between entities (from → to)."
    icon = "icons/follow_money.png"
    priority = 50
    want_main_area = True

    class Inputs:
        Data = Input("Data", Table, auto_summary=True)

    class Error(OWWidget.Error):
        no_data = Msg("No data.")
        bad_mapping = Msg("Please select FROM, TO and VALUE fields.")
        no_rows = Msg("No rows after filtering.")
        plot_fail = Msg("Failed to draw graph: {}")

    class Info(OWWidget.Information):
        status = Msg("{}")

    # === Settings ===
    from_attr: str = Setting("")
    to_attr: str = Setting("")
    value_attr: str = Setting("")
    currency_attr: str = Setting("")
    description_attr: str = Setting("")

    currency_filter: str = Setting("All")
    top_n_sources: int = Setting(10)
    top_n_targets: int = Setting(10)

    def __init__(self):
        super().__init__()

        self.data: Optional[Table] = None

        # state untuk grafik & interaksi
        self._ax = None
        self._graph_has_data = False
        self._graph_nodes: List[str] = []
        self._graph_positions: Dict[str, tuple] = {}
        self._graph_node_sizes: Dict[str, float] = {}
        self._graph_node_colors: Dict[str, Any] = {}
        self._graph_agg: Optional[pd.DataFrame] = None
        self._graph_col_from: str = "from_"
        self._graph_col_to: str = "to_"
        self._graph_col_cur: Optional[str] = None

        # meta untuk tooltip & drag
        self._node_meta: Dict[str, Dict[str, Any]] = {}
        self._edge_meta: List[Dict[str, Any]] = []
        self._dragging_node: Optional[str] = None
        self._last_tooltip_text: str = ""

        # ---------- Controls ----------
        box_map = gui.widgetBox(self.controlArea, "Field Mapping")

        self.cb_from = gui.comboBox(
            box_map, self, "from_attr",
            label="From:",
            sendSelectedValue=True,
            callback=self._on_mapping_changed,
        )
        self.cb_to = gui.comboBox(
            box_map, self, "to_attr",
            label="To:",
            sendSelectedValue=True,
            callback=self._on_mapping_changed,
        )
        self.cb_value = gui.comboBox(
            box_map, self, "value_attr",
            label="Value:",
            sendSelectedValue=True,
            callback=self._on_mapping_changed,
        )
        self.cb_currency = gui.comboBox(
            box_map, self, "currency_attr",
            label="Currency:",
            sendSelectedValue=True,
            callback=self._on_mapping_changed,
        )
        self.cb_descr = gui.comboBox(
            box_map, self, "description_attr",
            label="Description:",
            sendSelectedValue=True,
            callback=self._on_mapping_changed,
        )

        box_f = gui.widgetBox(self.controlArea, "Filters")

        self.cmb_currency_filter = gui.comboBox(
            box_f, self, "currency_filter",
            label="Show currency:",
            sendSelectedValue=True,
            callback=self._on_filter_changed,
        )

        gui.spin(
            box_f, self, "top_n_sources",
            1, 1000, step=1,
            label="Top N senders (FROM):",
            callback=self._on_filter_changed,
        )
        gui.spin(
            box_f, self, "top_n_targets",
            1, 1000, step=1,
            label="Top N receivers (TO):",
            callback=self._on_filter_changed,
        )

        # ringkasan total per mata uang
        self.lbl_currency_summary = QtWidgets.QLabel("Totals (all currencies): -")
        self.lbl_currency_summary.setWordWrap(True)
        box_f.layout().addWidget(self.lbl_currency_summary)

        # ---------- Main area ----------
        if self.mainArea.layout() is None:
            self.mainArea.setLayout(QtWidgets.QVBoxLayout())
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        self.mainArea.layout().addWidget(self.canvas)

        # event interaktif
        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)

        # init UI
        self._refresh_field_combos()
        self._refresh_currency_filter([])
        self._draw_placeholder("Waiting for data…")

    # ================== Input ==================
    @Inputs.Data
    def set_data(self, data: Optional[Table]):
        self.data = data
        self.Error.clear()
        self.Info.clear()

        if data is None:
            self._refresh_field_combos()
            self._refresh_currency_filter([])
            self._graph_has_data = False
            self._draw_placeholder("No data.")
            self.Error.no_data()
            return

        self._refresh_field_combos()
        self._refresh_currency_list_from_data()
        self._auto_guess_mapping()
        self._update_plot()

    # ================== UI helpers ==================
    def _all_column_names(self) -> List[str]:
        if not self.data:
            return []
        dom = self.data.domain
        return [v.name for v in dom.attributes] + [m.name for m in dom.metas]

    def _refresh_field_combos(self):
        cols = self._all_column_names()
        for cb in (self.cb_from, self.cb_to, self.cb_value,
                   self.cb_currency, self.cb_descr):
            cb.blockSignals(True)
            cb.clear()
            cb.addItem("(not set)", "")
            for c in cols:
                cb.addItem(c, c)
            cb.blockSignals(False)

        def _restore(cb: QtWidgets.QComboBox, val: str):
            if not val:
                cb.setCurrentIndex(0)
                return
            idx = cb.findData(val)
            cb.setCurrentIndex(idx if idx >= 0 else 0)

        _restore(self.cb_from, self.from_attr)
        _restore(self.cb_to, self.to_attr)
        _restore(self.cb_value, self.value_attr)
        _restore(self.cb_currency, self.currency_attr)
        _restore(self.cb_descr, self.description_attr)

    def _refresh_currency_filter(self, currencies: List[str]):
        self.cmb_currency_filter.blockSignals(True)
        self.cmb_currency_filter.clear()
        self.cmb_currency_filter.addItem("All", "All")
        for cur in currencies:
            self.cmb_currency_filter.addItem(cur, cur)
        idx = self.cmb_currency_filter.findData(self.currency_filter)
        if idx < 0:
            idx = 0
            self.currency_filter = "All"
        self.cmb_currency_filter.setCurrentIndex(idx)
        self.cmb_currency_filter.blockSignals(False)

    def _refresh_currency_list_from_data(self):
        if not self.data or not self.currency_attr:
            self._refresh_currency_filter([])
            self.lbl_currency_summary.setText("Totals (all currencies): -")
            return
        df = table_to_frame(self.data)
        if self.currency_attr not in df.columns:
            self._refresh_currency_filter([])
            self.lbl_currency_summary.setText("Totals (all currencies): -")
            return
        uniq = (
            df[self.currency_attr]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
        )
        self._refresh_currency_filter(list(uniq))

        # ringkasan total per mata uang (semua data, sebelum filter)
        try:
            vals = pd.to_numeric(df[self.value_attr], errors="coerce")
            cur_totals = (
                pd.DataFrame({"cur": df[self.currency_attr].astype(str), "val": vals})
                .dropna()
                .groupby("cur")["val"]
                .sum()
            )
            if not cur_totals.empty:
                parts = [f"{c}={cur_totals[c]:,.2f}" for c in cur_totals.index]
                self.lbl_currency_summary.setText(
                    "Totals (all currencies): " + ", ".join(parts)
                )
            else:
                self.lbl_currency_summary.setText("Totals (all currencies): -")
        except Exception:
            self.lbl_currency_summary.setText("Totals (all currencies): -")

    def _auto_guess_mapping(self):
        if not self.data:
            return
        cols = self._all_column_names()

        def guess(keys, default=""):
            for key in keys:
                for name in cols:
                    if key in name.lower():
                        return name
            return default

        if not self.from_attr:
            self.from_attr = guess(["from", "source", "sender", "asal", "dari"])
        if not self.to_attr:
            self.to_attr = guess(["to", "target", "receiver", "tujuan", "ke"])
        if not self.value_attr:
            self.value_attr = guess(["value", "amount", "nilai", "jumlah", "amt"])
            if not self.value_attr:
                for v in self.data.domain.attributes:
                    if v.is_continuous:
                        self.value_attr = v.name
                        break
        if not self.currency_attr:
            self.currency_attr = guess(["currency", "curr", "mata_uang", "matauang"])
        if not self.description_attr:
            self.description_attr = guess(
                ["description", "desc", "keterangan", "ket"], default=""
            )
        self._refresh_field_combos()

    # ================== Event handlers ==================
    def _on_mapping_changed(self):
        # kalau mapping currency berubah, refresh daftar currency
        self._refresh_currency_list_from_data()
        self._update_plot()

    def _on_filter_changed(self):
        self._update_plot()

    # ================== Core plotting ==================
    def _update_plot(self):
        self.Error.clear()
        self.Info.clear()
        self._graph_has_data = False
        self._dragging_node = None
        self._last_tooltip_text = ""
        self._node_meta.clear()
        self._edge_meta.clear()

        if not self.data:
            self._draw_placeholder("No data.")
            self.Error.no_data()
            return

        if not (self.from_attr and self.to_attr and self.value_attr):
            self._draw_placeholder("Please select FROM, TO and VALUE fields.")
            self.Error.bad_mapping()
            return

        try:
            df = table_to_frame(self.data)
        except Exception as e:
            self._draw_placeholder(f"Failed to convert data: {e}")
            self.Error.plot_fail(str(e))
            return

        needed = [self.from_attr, self.to_attr, self.value_attr]
        for c in needed:
            if c not in df.columns:
                self._draw_placeholder(f"Column '{c}' not found.")
                self.Error.bad_mapping()
                return

        cols = [self.from_attr, self.to_attr, self.value_attr]
        has_cur = self.currency_attr and self.currency_attr in df.columns
        has_desc = self.description_attr and self.description_attr in df.columns
        if has_cur:
            cols.append(self.currency_attr)
        if has_desc:
            cols.append(self.description_attr)
        df = df[cols].copy()

        col_from = "from_"
        col_to = "to_"
        col_val = "value_"
        col_cur = "currency_" if has_cur else None
        col_desc = "descr_" if has_desc else None

        rename_map = {
            self.from_attr: col_from,
            self.to_attr: col_to,
            self.value_attr: col_val,
        }
        if has_cur:
            rename_map[self.currency_attr] = col_cur
        if has_desc:
            rename_map[self.description_attr] = col_desc
        df = df.rename(columns=rename_map)

        df[col_from] = df[col_from].astype(str)
        df[col_to] = df[col_to].astype(str)
        df[col_val] = pd.to_numeric(df[col_val], errors="coerce")
        df = df.dropna(subset=[col_val])

        if has_cur:
            df[col_cur] = df[col_cur].astype(str)

        # filter mata uang
        if col_cur and self.currency_filter != "All":
            df = df[df[col_cur] == self.currency_filter]

        if df.empty:
            self._draw_placeholder("No rows after filtering.")
            self.Error.no_rows()
            return

        group_cols = [col_from, col_to]
        if col_cur:
            group_cols.append(col_cur)

        agg_dict = {
            "total_value": (col_val, "sum"),
            "count": (col_val, "size"),
        }
        if col_desc:
            agg_dict["descr"] = (
                col_desc,
                lambda s: "; ".join(sorted({str(x) for x in s.dropna()}))[:500],
            )

        agg = (
            df.groupby(group_cols, dropna=False)
            .agg(**agg_dict)
            .reset_index()
        )

        outgoing = agg.groupby(col_from)["total_value"].sum()
        incoming = agg.groupby(col_to)["total_value"].sum()

        def top_keys(series: pd.Series, n: int) -> List[str]:
            if series.empty:
                return []
            return list(series.sort_values(ascending=False).head(max(1, n)).index)

        top_src = set(top_keys(outgoing, self.top_n_sources))
        top_dst = set(top_keys(incoming, self.top_n_targets))
        keep_nodes = top_src.union(top_dst)
        if not keep_nodes:
            keep_nodes = set(outgoing.index).union(set(incoming.index))

        mask = agg[col_from].isin(keep_nodes) | agg[col_to].isin(keep_nodes)
        agg = agg[mask]
        if agg.empty:
            self._draw_placeholder("No edges after top-N filter.")
            self.Error.no_rows()
            return

        nodes = sorted(set(agg[col_from]) | set(agg[col_to]))
        node_out = outgoing.reindex(nodes).fillna(0.0)
        node_in = incoming.reindex(nodes).fillna(0.0)
        node_total = node_out + node_in

        # --- layout pakai networkx spring_layout (lebih halus) ---
        G = nx.DiGraph()
        for _, row in agg.iterrows():
            G.add_edge(row[col_from], row[col_to], weight=float(row["total_value"]))
        if len(G.nodes) == 0:
            self._draw_placeholder("No edges to draw.")
            self.Error.no_rows()
            return

        pos = nx.spring_layout(G, weight="weight", seed=0)  # dict: node -> (x,y)
        positions = {n: tuple(pos.get(n, (0.0, 0.0))) for n in nodes}

        # ukuran node
        max_total = node_total.max()
        if max_total <= 0:
            node_sizes = {n: 300.0 for n in nodes}
        else:
            node_sizes = {
                n: 200.0 + 1800.0 * (node_total[n] / max_total)
                for n in nodes
            }

        # warna node: skala Reds sesuai total flow
        cmap = cm.get_cmap("Reds")
        if max_total <= 0:
            node_colors = {n: cmap(0.1) for n in nodes}
        else:
            node_colors = {
                n: cmap(0.2 + 0.8 * (node_total[n] / max_total))
                for n in nodes
            }

        # simpan state
        self._graph_has_data = True
        self._graph_nodes = nodes
        self._graph_positions = positions
        self._graph_node_sizes = node_sizes
        self._graph_node_colors = node_colors
        self._graph_agg = agg
        self._graph_col_from = col_from
        self._graph_col_to = col_to
        self._graph_col_cur = col_cur

        self._draw_graph()

        cur_txt = (
            self.currency_filter
            if (col_cur and self.currency_filter != "All")
            else "All currencies"
        )
        self.Info.status(
            f"Nodes: {len(nodes)}, Edges: {len(agg)}, "
            f"Currency: {cur_txt}, "
            f"Top senders: {self.top_n_sources}, "
            f"Top receivers: {self.top_n_targets}"
        )

    # ================== Drawing helper ==================
    def _draw_graph(self):
        if not self._graph_has_data or self._graph_agg is None:
            self._draw_placeholder("No data.")
            return

        agg = self._graph_agg
        nodes = self._graph_nodes
        positions = self._graph_positions
        node_sizes = self._graph_node_sizes
        node_colors = self._graph_node_colors
        col_from = self._graph_col_from
        col_to = self._graph_col_to
        col_cur = self._graph_col_cur

        outgoing = agg.groupby(col_from)["total_value"].sum()
        incoming = agg.groupby(col_to)["total_value"].sum()
        node_out = outgoing.reindex(nodes).fillna(0.0)
        node_in = incoming.reindex(nodes).fillna(0.0)
        node_total = node_out + node_in

        max_val = agg["total_value"].max()
        if max_val <= 0:
            edge_widths = [1.0] * len(agg)
        else:
            edge_widths = [
                0.5 + 4.5 * (v / max_val) for v in agg["total_value"]
            ]

        self._node_meta.clear()
        self._edge_meta.clear()

        try:
            self.figure.clear()
            self._ax = self.figure.add_subplot(111)
            ax = self._ax
            ax.set_aspect("equal")
            ax.axis("off")

            # edges (panah)
            for (idx, row), w in zip(agg.iterrows(), edge_widths):
                f = row[col_from]
                t = row[col_to]
                x1, y1 = positions[f]
                x2, y2 = positions[t]

                r1 = np.sqrt(node_sizes[f]) / 80.0
                r2 = np.sqrt(node_sizes[t]) / 80.0
                vx, vy = x2 - x1, y2 - y1
                dist = np.hypot(vx, vy) or 1.0
                ux, uy = vx / dist, vy / dist
                sx1, sy1 = x1 + ux * r1, y1 + uy * r1
                sx2, sy2 = x2 - ux * r2, y2 - uy * r2

                ax.annotate(
                    "",
                    xy=(sx2, sy2),
                    xytext=(sx1, sy1),
                    arrowprops=dict(
                        arrowstyle="->",
                        linewidth=w,
                        alpha=0.35,
                        color="tab:blue",
                    ),
                )

                cur = str(row[col_cur]) if (col_cur and col_cur in row) else ""
                descr = str(row.get("descr", "") or "")
                info = (
                    f"{f} → {t}\n"
                    f"Total: {row['total_value']:,.2f}"
                )
                if cur:
                    info += f" {cur}"
                info += f"\nCount: {int(row['count'])}"
                if descr:
                    info += f"\nDesc: {descr}"
                self._edge_meta.append(
                    dict(
                        from_=f,
                        to=t,
                        x1=sx1,
                        y1=sy1,
                        x2=sx2,
                        y2=sy2,
                        info=info,
                    )
                )

            # nodes
            xs = [positions[n][0] for n in nodes]
            ys = [positions[n][1] for n in nodes]
            sizes = [node_sizes[n] for n in nodes]
            colors = [node_colors[n] for n in nodes]
            ax.scatter(
                xs, ys,
                s=sizes,
                alpha=0.9,
                c=colors,
                edgecolor="k",
            )

            for n in nodes:
                x, y = positions[n]
                ax.text(
                    x, y,
                    n,
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="black",
                )

            for n in nodes:
                x, y = positions[n]
                tot = float(node_total[n])
                out = float(node_out[n])
                inn = float(node_in[n])
                size = float(node_sizes[n])
                radius = np.sqrt(size) / 80.0
                info = (
                    f"{n}\n"
                    f"Total in:  {inn:,.2f}\n"
                    f"Total out: {out:,.2f}\n"
                    f"Grand: {tot:,.2f}"
                )
                self._node_meta[n] = dict(
                    x=x,
                    y=y,
                    radius=radius,
                    info=info,
                )

            ax.set_title(
                f"Follow The Money\n{len(nodes)} nodes, {len(agg)} edges",
                fontsize=10,
            )
            self.canvas.draw_idle()

        except Exception as e:
            self._draw_placeholder(f"Failed to draw graph: {e}")
            self.Error.plot_fail(str(e))

    # ================== Placeholder ==================
    def _draw_placeholder(self, text: str):
        self.figure.clear()
        self._ax = self.figure.add_subplot(111)
        self._ax.axis("off")
        self._ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=10)
        self.canvas.draw_idle()

    # ================== Interaksi: drag & tooltip ==================
    def _find_node_at(self, x: float, y: float) -> Optional[str]:
        best_name = None
        best_d2 = None
        for name, meta in self._node_meta.items():
            dx = x - meta["x"]
            dy = y - meta["y"]
            d2 = dx * dx + dy * dy
            r2 = (meta["radius"] * 1.5) ** 2
            if d2 <= r2:
                if best_d2 is None or d2 < best_d2:
                    best_d2 = d2
                    best_name = name
        return best_name

    def _find_edge_near(self, x: float, y: float) -> Optional[Dict[str, Any]]:
        best_edge = None
        best_d2 = None
        for meta in self._edge_meta:
            x1, y1 = meta["x1"], meta["y1"]
            x2, y2 = meta["x2"], meta["y2"]
            vx, vy = x2 - x1, y2 - y1
            len2 = vx * vx + vy * vy
            if len2 == 0:
                continue
            t = ((x - x1) * vx + (y - y1) * vy) / len2
            t = max(0.0, min(1.0, t))
            px = x1 + t * vx
            py = y1 + t * vy
            dx = x - px
            dy = y - py
            d2 = dx * dx + dy * dy
            if d2 < 0.02 ** 2:
                if best_d2 is None or d2 < best_d2:
                    best_d2 = d2
                    best_edge = meta
        return best_edge

    def _on_press(self, event):
        if not self._graph_has_data or self._ax is None:
            return
        if event.button != 1 or event.inaxes is not self._ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        name = self._find_node_at(event.xdata, event.ydata)
        if name:
            self._dragging_node = name

    def _on_release(self, event):
        self._dragging_node = None

    def _on_motion(self, event):
        if not self._graph_has_data or self._ax is None:
            return
        if event.xdata is None or event.ydata is None:
            return

        # drag node
        if self._dragging_node and event.inaxes is self._ax and event.button == 1:
            n = self._dragging_node
            self._graph_positions[n] = (event.xdata, event.ydata)
            self._draw_graph()
            return

        # tooltip
        if event.inaxes is not self._ax:
            if self._last_tooltip_text:
                QtWidgets.QToolTip.hideText()
                self._last_tooltip_text = ""
            return

        x, y = event.xdata, event.ydata
        tooltip_text = ""
        node = self._find_node_at(x, y)
        if node:
            tooltip_text = self._node_meta[node]["info"]
        else:
            edge = self._find_edge_near(x, y)
            if edge:
                tooltip_text = edge["info"]

        if tooltip_text != self._last_tooltip_text:
            self._last_tooltip_text = tooltip_text
            if tooltip_text:
                pos = self.canvas.mapToGlobal(QPoint(int(event.x), int(event.y)))
                QtWidgets.QToolTip.showText(pos, tooltip_text, self.canvas)
            else:
                QtWidgets.QToolTip.hideText()

    # ================== Misc ==================
    def onDeleteWidget(self):
        super().onDeleteWidget()
