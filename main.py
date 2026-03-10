import tkinter as tk
import random
import time
import threading

#colour palette ───────────────────────────────────────────────────────────
BG        = "#0d0d0d"
BAR_DEF   = "#1e90ff" #default
BAR_MIN   = "#ff4d4d" #current minimum found
BAR_CMP   = "#ffd700" #element being compared
BAR_SWAP  = "#ff8c00" #swapping
BAR_SCAN  = "#c740f5" #scanning boundary
BAR_DONE  = "#00e676" #sorted
TXT       = "#e0e0e0"
ACC       = "#1e90ff"

FONT_TITLE = ("Courier New", 20, "bold")
FONT_CODE  = ("Courier New", 11)
FONT_STAT  = ("Courier New", 12, "bold")

CODE_LINES = [
    "def selection_sort(arr):",
    "    n = len(arr)",
    "    for i in range(n - 1):",
    "        min_idx = i",
    "        for j in range(i + 1, n):",
    "            if arr[j] < arr[min_idx]:",
    "                min_idx = j",
    "        if min_idx != i:",
    "            arr[i], arr[min_idx] = arr[min_idx], arr[i]",
]

LINE = {
    "fn"       : 0,
    "n_len"    : 1,
    "for_i"    : 2,
    "min_idx"  : 3,
    "for_j"    : 4,
    "if_cmp"   : 5,
    "upd_min"  : 6,
    "if_swap"  : 7,
    "swap"     : 8,
}


class SelectionSortVisualizer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Selection Sort Visualizer — Pure Python")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.n           = 40
        self.speed       = 0.05
        self.arr         : list[int] = []
        self.colors      : list[str] = []
        self.comparisons = 0
        self.swaps       = 0
        self.running     = False
        self._stop       = False
        self._thread     = None

        self._build_ui()
        self._new_array()

    #UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        tk.Label(self.root, text="◈  SELECTION SORT VISUALIZER",
                 font=FONT_TITLE, fg=ACC, bg=BG, pady=12
                 ).grid(row=0, column=0, columnspan=2, sticky="ew")

        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=8)

        right = tk.Frame(self.root, bg=BG)
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 16), pady=8)
        right.rowconfigure(0, weight=0)
        right.rowconfigure(1, weight=1)

        #stats
        sf = tk.LabelFrame(right, text=" Statistics ",
                           fg=ACC, bg=BG,
                           font=("Courier New", 10, "bold"),
                           bd=1, relief="solid")
        sf.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.lbl_n      = tk.Label(sf, text="Elements    : 40",
                                   font=FONT_STAT, fg=TXT,      bg=BG, anchor="w")
        self.lbl_cmp    = tk.Label(sf, text="Comparisons : 0",
                                   font=FONT_STAT, fg=BAR_CMP,  bg=BG, anchor="w")
        self.lbl_swp    = tk.Label(sf, text="Swaps       : 0",
                                   font=FONT_STAT, fg=BAR_SWAP, bg=BG, anchor="w")
        self.lbl_time   = tk.Label(sf, text="Time        : 0.000s",
                                   font=FONT_STAT, fg=BAR_DONE, bg=BG, anchor="w")
        self.lbl_pass   = tk.Label(sf, text="Pass        : 0 / 0",
                                   font=FONT_STAT, fg=BAR_SCAN, bg=BG, anchor="w")
        self.lbl_status = tk.Label(sf, text="● IDLE",
                                   font=FONT_STAT, fg="#888",   bg=BG, anchor="w")
        for w in (self.lbl_n, self.lbl_cmp, self.lbl_swp,
                  self.lbl_time, self.lbl_pass, self.lbl_status):
            w.pack(fill="x", padx=8, pady=2)

        #code panel
        cf = tk.LabelFrame(right, text=" Code ",
                           fg=ACC, bg=BG,
                           font=("Courier New", 10, "bold"),
                           bd=1, relief="solid")
        cf.grid(row=1, column=0, sticky="nsew")

        self.code_labels: list[tk.Label] = []
        for line in CODE_LINES:
            lbl = tk.Label(cf, text=f"  {line}",
                           font=FONT_CODE,
                           fg="#666" if line == "" else TXT,
                           bg=BG, anchor="w", justify="left", padx=4)
            lbl.pack(fill="x")
            self.code_labels.append(lbl)

        #controls
        ctrl = tk.Frame(self.root, bg=BG)
        ctrl.grid(row=2, column=0, columnspan=2,
                  sticky="ew", padx=16, pady=(0, 12))

        btn_cfg = dict(font=("Courier New", 11, "bold"),
                       relief="flat", cursor="hand2", pady=6, padx=14)

        self.btn_start = tk.Button(ctrl, text="▶  START",
                                   bg=ACC, fg="white",
                                   activebackground="#1070cc",
                                   command=self._start, **btn_cfg)
        self.btn_stop  = tk.Button(ctrl, text="■  STOP",
                                   bg="#cc2222", fg="white",
                                   activebackground="#991111",
                                   state="disabled",
                                   command=self._stop_sort, **btn_cfg)
        self.btn_reset = tk.Button(ctrl, text="↺  NEW ARRAY",
                                   bg="#333", fg=TXT,
                                   activebackground="#555",
                                   command=self._new_array, **btn_cfg)

        tk.Label(ctrl, text="Size:", font=FONT_CODE,
                 fg=TXT, bg=BG).pack(side="left", padx=(0, 4))
        self.sl_size = tk.Scale(ctrl, from_=10, to=120,
                                orient="horizontal", length=130,
                                bg=BG, fg=TXT, troughcolor="#222",
                                highlightthickness=0,
                                font=("Courier New", 9),
                                command=self._on_size)
        self.sl_size.set(self.n)
        self.sl_size.pack(side="left", padx=(0, 20))

        tk.Label(ctrl, text="Speed:", font=FONT_CODE,
                 fg=TXT, bg=BG).pack(side="left", padx=(0, 4))
        self.sl_speed = tk.Scale(ctrl, from_=1, to=100,
                                 orient="horizontal", length=130,
                                 bg=BG, fg=TXT, troughcolor="#222",
                                 highlightthickness=0,
                                 font=("Courier New", 9),
                                 command=self._on_speed)
        self.sl_speed.set(50)
        self.sl_speed.pack(side="left", padx=(0, 20))

        for b in (self.btn_start, self.btn_stop, self.btn_reset):
            b.pack(side="left", padx=4)

        lf = tk.Frame(ctrl, bg=BG)
        lf.pack(side="right", padx=8)
        for color, label in [
            (BAR_DEF,  "Default"),
            (BAR_MIN,  "Minimum"),
            (BAR_CMP,  "Comparing"),
            (BAR_SWAP, "Swapping"),
            (BAR_SCAN, "Boundary"),
            (BAR_DONE, "Sorted"),
        ]:
            tk.Label(lf, text=f"■ {label}",
                     font=("Courier New", 9), fg=color, bg=BG
                     ).pack(side="left", padx=5)

    #array helpers ────────────────────────────────────────────────────────
    def _new_array(self):
        if self.running:
            return
        self.arr    = [random.randint(5, 99) for _ in range(self.n)]
        self.colors = [BAR_DEF] * self.n
        self.comparisons = 0
        self.swaps       = 0
        self._update_stats(0.0, 0)
        self._set_status("IDLE", "#888")
        self._highlight_code(-1)
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()  or 700
        h = self.canvas.winfo_height() or 420
        if not self.arr:
            return
        n   = len(self.arr)
        gap = 2
        bw  = max(2, (w - gap * (n + 1)) / n)
        mx  = max(self.arr) or 1
        for i, val in enumerate(self.arr):
            x0 = gap + i * (bw + gap)
            bh = int((val / mx) * (h - 30))
            y0 = h - bh
            self.canvas.create_rectangle(x0, y0, x0 + bw, h,
                                         fill=self.colors[i], outline="")
            if bw > 18 and n <= 60:
                self.canvas.create_text(
                    x0 + bw / 2, y0 - 6,
                    text=str(val), fill=TXT,
                    font=("Courier New", max(7, int(bw * 0.5))))

    #stats/highlight ────────────────────────────────────────────────────
    def _update_stats(self, elapsed: float, pass_i: int = 0):
        self.lbl_n.config(  text=f"Elements    : {self.n}")
        self.lbl_cmp.config(text=f"Comparisons : {self.comparisons}")
        self.lbl_swp.config(text=f"Swaps       : {self.swaps}")
        self.lbl_time.config(text=f"Time        : {elapsed:.3f}s")
        self.lbl_pass.config(text=f"Pass        : {pass_i} / {self.n - 1}")

    def _set_status(self, text: str, color: str):
        self.lbl_status.config(text=f"● {text}", fg=color)

    def _highlight_code(self, idx: int):
        for i, lbl in enumerate(self.code_labels):
            if i == idx:
                lbl.config(bg="#1a2a3a", fg="#ffff88")
            else:
                lbl.config(bg=BG, fg="#666" if CODE_LINES[i] == "" else TXT)

    #controls ─────────────────────────────────────────────────────────────
    def _start(self):
        if self.running:
            return
        self.running     = True
        self._stop       = False
        self.comparisons = 0
        self.swaps       = 0
        self.colors      = [BAR_DEF] * self.n
        self.btn_start.config(state="disabled")
        self.btn_stop.config( state="normal")
        self.btn_reset.config(state="disabled")
        self._set_status("RUNNING", BAR_CMP)
        self._thread = threading.Thread(target=self._sort_thread, daemon=True)
        self._thread.start()

    def _stop_sort(self):
        self._stop = True

    #sort thread ──────────────────────────────────────────────────────────
    def _sort_thread(self):
        t0 = time.time()
        n  = len(self.arr)

        self._hl(LINE["fn"]);    self._sleep()
        self._hl(LINE["n_len"]); self._sleep()
        self._hl(LINE["for_i"]); self._sleep()

        for i in range(n - 1):
            if self._stop:
                break

            #mark boundary
            self.colors[i] = BAR_SCAN
            self._refresh(time.time() - t0, i + 1)

            self._hl(LINE["min_idx"]); self._sleep()
            min_idx = i
            self.colors[i] = BAR_MIN
            self._refresh(time.time() - t0, i + 1)

            self._hl(LINE["for_j"]); self._sleep()

            for j in range(i + 1, n):
                if self._stop:
                    break

                self._hl(LINE["if_cmp"])
                self.comparisons += 1
                self.colors[j] = BAR_CMP
                self._refresh(time.time() - t0, i + 1); self._sleep()

                if self.arr[j] < self.arr[min_idx]:
                    self._hl(LINE["upd_min"])
                    # restore old min colour
                    if min_idx != i:
                        self.colors[min_idx] = BAR_DEF
                    min_idx = j
                    self.colors[min_idx] = BAR_MIN
                    self._refresh(time.time() - t0, i + 1); self._sleep()
                else:
                    self.colors[j] = BAR_DEF
                    self._refresh(time.time() - t0, i + 1)

            if self._stop:
                break

            self._hl(LINE["if_swap"]); self._sleep()
            if min_idx != i:
                self._hl(LINE["swap"])
                self.colors[i]       = BAR_SWAP
                self.colors[min_idx] = BAR_SWAP
                self._refresh(time.time() - t0, i + 1); self._sleep()
                self.arr[i], self.arr[min_idx] = self.arr[min_idx], self.arr[i]
                self.swaps += 1
                self.colors[min_idx] = BAR_DEF
            else:
                self.colors[i] = BAR_DEF

            self.colors[i] = BAR_DONE
            self._refresh(time.time() - t0, i + 1)

        elapsed = time.time() - t0
        if not self._stop:
            #last element is always sorted
            self.colors[n - 1] = BAR_DONE
            self._refresh(elapsed, n - 1)
            self._hl(-1)
            self.root.after(0, lambda: self._set_status("DONE ✓", BAR_DONE))
        else:
            self.root.after(0, lambda: self._set_status("STOPPED", "#ff4444"))
        self.root.after(0, self._reset_buttons)

    #helpers ──────────────────────────────────────────────────────────────
    def _hl(self, line: int):
        self.root.after(0, lambda l=line: self._highlight_code(l))

    def _sleep(self):
        time.sleep(self.speed)

    def _refresh(self, elapsed: float = 0.0, pass_i: int = 0):
        self.root.after(0, lambda e=elapsed, p=pass_i: (
            self._draw(), self._update_stats(e, p)))

    def _reset_buttons(self):
        self.running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config( state="disabled")
        self.btn_reset.config(state="normal")

    def _on_size(self, val):
        if self.running:
            return
        self.n = int(val)
        self._new_array()

    def _on_speed(self, val):
        self.speed = 0.5 - (int(val) - 1) * (0.499 / 99)


def main():
    root = tk.Tk()
    root.geometry("1180x700")
    root.minsize(900, 520)
    app = SelectionSortVisualizer(root)
    root.bind("<Configure>", lambda e: app._draw())
    root.mainloop()


if __name__ == "__main__":
    main()