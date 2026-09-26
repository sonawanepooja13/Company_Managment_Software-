"""Circular graphical report for Company Sorting (pure Tkinter)."""
import datetime
import tkinter as tk
from tkinter import ttk

PIE_COLORS = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0",
              "#F44336", "#00BCD4", "#FFC107", "#795548",
              "#607D8B", "#E91E63", "#8BC34A", "#3F51B5",
              "#009688", "#CDDC39"]


class CompanyGraphMixin:
    def show_company_graph(self):
        for w in self.view_container.winfo_children():
            w.destroy()
        ttk.Label(self.view_container,
            text="Company Sorting - Graphical Report",
            font=("Helvetica", 12, "bold")).pack(pady=4)
        top = ttk.Frame(self.view_container, padding="6")
        top.pack(fill="x", padx=10, pady=4)
        ttk.Label(top, text="Report:").pack(side="left", padx=4)
        self.graph_cat_var = tk.StringVar(
            value="Product & System")
        cats = ["Product & System", "Company Valuation",
                "Activity & Communication",
                "Next Meeting (Month-wise)", "Enquiry"]
        cb = ttk.Combobox(top, textvariable=self.graph_cat_var,
            values=cats, width=26, state="readonly")
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>",
                lambda e: self.refresh_company_graph())
        ttk.Button(top, text="Refresh",
            command=self.refresh_company_graph).pack(
                side="left", padx=8)
        self.graph_count_label = ttk.Label(
            top, text="", font=("Helvetica", 10, "bold"))
        self.graph_count_label.pack(side="right", padx=10)
        body = ttk.Frame(self.view_container)
        body.pack(fill="both", expand=True, padx=10, pady=4)
        left = ttk.LabelFrame(body, text=" Circular Chart ", padding="8")
        left.pack(side="left", fill="both", expand=True)
        self.graph_canvas = tk.Canvas(
            left, width=380, height=380, bg="white",
            highlightthickness=1, highlightbackground="#ccc")
        self.graph_canvas.pack(expand=True)
        right = ttk.LabelFrame(body, text=" Colour Legend ", padding="8")
        right.pack(side="right", fill="both", expand=True)
        self.graph_legend = ttk.Frame(right)
        self.graph_legend.pack(fill="both", expand=True)
        try:
            self.ensure_crm_csv_exists()
            self._reload_all_rows_silent()
        except Exception:
            pass
        self.refresh_company_graph()

    def _graph_rows(self):
        try:
            self._reload_all_rows_silent()
        except Exception:
            pass
        headers = self.get_crm_headers()
        idx = {}
        for h in headers:
            try:
                idx[h] = headers.index(h)
            except Exception:
                pass
        return list(getattr(self, "all_rows", [])), idx

    def _graph_val(self, row, idx, key, default=""):
        i = idx.get(key, -1)
        if 0 <= i < len(row):
            return row[i]
        return default

    def _graph_distribution(self):
        rows, idx = self._graph_rows()
        cat = self.graph_cat_var.get()
        dist = {}
        if cat == "Product & System":
            prods = ["Booster Pump System", "STP",
                     "Water Meter", "BMS", "WTP", "RO",
                     "FIRE PANEL", "De-watering Panel",
                     "Water Softener", "Choice A",
                     "Pump Skid", "Pump Sensor Panel"]
            dist = {p: 0 for p in prods}
            dist["Other / None"] = 0
            for r in rows:
                s = str(self._graph_val(
                    r, idx, "products_selected", "")).lower()
                hit = False
                for p in prods:
                    if p.lower() in s and s.strip():
                        dist[p] += 1
                        hit = True
                if not hit:
                    dist["Other / None"] += 1
        elif cat == "Company Valuation":
            vals = ["Work in VFD Panel", "Work in Dewatering",
                    "Distributor", "Dealer", "Serious Base"]
            dist = {v: 0 for v in vals}
            dist["Other / None"] = 0
            for r in rows:
                s = str(self._graph_val(
                    r, idx, "company_valuation", "")).lower()
                hit = False
                for v in vals:
                    if v.lower() in s and s.strip():
                        dist[v] += 1
                        hit = True
                if not hit:
                    dist["Other / None"] += 1
        elif cat == "Activity & Communication":
            dist = {"Active (count>0)": 0, "No Activity": 0,
                    "With Communication": 0,
                    "Without Communication": 0}
            for r in rows:
                a = str(self._graph_val(
                    r, idx, "activity_count", "0")).strip()
                try:
                    n = 0 if a in ("", "No", "None") else int(float(a))
                except Exception:
                    n = 0
                c = str(self._graph_val(
                    r, idx, "communication_details", "")).strip()
                if n > 0:
                    dist["Active (count>0)"] += 1
                else:
                    dist["No Activity"] += 1
                if c:
                    dist["With Communication"] += 1
                else:
                    dist["Without Communication"] += 1
        elif cat == "Next Meeting (Month-wise)":
            dist = {}
            for r in rows:
                nxt = str(self._graph_val(
                    r, idx, "next_meeting_datetime", "")
                    or self._graph_val(
                        r, idx, "meeting_schedule_time",
                        "")).strip()
                mt = self.parse_meeting_dt(nxt) if nxt else None
                if mt:
                    k = mt.strftime("%b %Y")
                else:
                    k = "No Meeting"
                dist[k] = dist.get(k, 0) + 1
            try:
                dated = []
                plain = []
                for k, v in dist.items():
                    try:
                        d = datetime.datetime.strptime(k, "%b %Y")
                        dated.append((d, k, v))
                    except Exception:
                        plain.append((k, v))
                dated.sort()
                dist = {}
                for _, k, v in dated:
                    dist[k] = v
                for k, v in plain:
                    dist[k] = v
            except Exception:
                pass
        else:
            dist = {"Enquiry Yes": 0, "Enquiry No": 0}
            types = {}
            for r in rows:
                e = str(self._graph_val(
                    r, idx, "enquiry_received", "No")).strip()
                if e == "Yes":
                    dist["Enquiry Yes"] += 1
                else:
                    dist["Enquiry No"] += 1
                t = str(self._graph_val(
                    r, idx, "enquiry_type", "")).strip()
                if e == "Yes" and t:
                    types[t] = types.get(t, 0) + 1
            for k, v in types.items():
                dist["Type: " + k] = v
        dist = {k: v for k, v in dist.items() if v > 0}
        if not dist:
            dist = {"No Data": 1}
        return dist, len(rows)

    def refresh_company_graph(self):
        if not hasattr(self, "graph_canvas"):
            return
        try:
            if not self.graph_canvas.winfo_exists():
                return
        except Exception:
            return
        dist, total = self._graph_distribution()
        cv = self.graph_canvas
        cv.delete("all")
        labels = list(dist.keys())
        values = [dist[k] for k in labels]
        grand = sum(values) or 1
        cx, cy, rad = 190, 175, 130
        start = 90.0
        import math
        for i, (lab, val) in enumerate(zip(labels, values)):
            frac = val / grand
            extent = frac * 360.0
            col = PIE_COLORS[i % len(PIE_COLORS)]
            cv.create_arc(cx - rad, cy - rad, cx + rad, cy + rad,
                          start=start, extent=extent,
                          fill=col, outline="white", width=2)
            mid = math.radians(start + extent / 2.0)
            pct = frac * 100.0
            if pct >= 4:
                tx = cx + math.cos(mid) * rad * 0.62
                ty = cy - math.sin(mid) * rad * 0.62
                cv.create_text(tx, ty,
                               text="%d\n%.1f%%" % (val, pct),
                               font=("Helvetica", 8, "bold"))
            start += extent
        cv.create_oval(cx - 28, cy - 28, cx + 28, cy + 28,
                       fill="white", outline="#ccc")
        cv.create_text(cx, cy - 6, text=str(total),
                       font=("Helvetica", 14, "bold"))
        cv.create_text(cx, cy + 12, text="Companies",
                       font=("Helvetica", 8))
        for w in self.graph_legend.winfo_children():
            w.destroy()
        for i, (lab, val) in enumerate(zip(labels, values)):
            col = PIE_COLORS[i % len(PIE_COLORS)]
            pct = (val / grand) * 100.0
            row = ttk.Frame(self.graph_legend)
            row.pack(fill="x", pady=2)
            box = tk.Canvas(row, width=16, height=16,
                            highlightthickness=0)
            box.create_rectangle(0, 0, 16, 16,
                                 fill=col, outline="black")
            box.pack(side="left", padx=(2, 6))
            ttk.Label(row,
                      text="%s : %d (%.1f%%)" % (lab, val, pct),
                      font=("Helvetica", 9)).pack(
                          side="left")
            ttk.Label(row, text="  %s" % col,
                      font=("Helvetica", 7),
                      foreground="gray").pack(side="right")
        try:
            self.graph_count_label.config(
                text="%s | Total: %d" % (
                    self.graph_cat_var.get(), total))
        except Exception:
            pass


