import tkinter as tk
from tkinter import ttk
import random
import time
import threading

# ── colour palette ──────────────────────────────────────────────────────────
BG        = "#0d0d0d"
BAR_DEF   = "#1e90ff"   # default bar
BAR_PIV   = "#ff4d4d"   # pivot
BAR_CMP   = "#ffd700"   # comparing
BAR_DONE  = "#00e676"   # sorted / done
BAR_SWAP  = "#ff8c00"   # being swapped
TXT       = "#e0e0e0"
ACC       = "#1e90ff"

FONT_TITLE = ("Courier New", 20, "bold")
FONT_CODE  = ("Courier New", 11)
FONT_STAT  = ("Courier New", 12, "bold")

# ── quicksort source (shown in the sidebar) ─────────────────────────────────
CODE_LINES = [
    "def quicksort(arr, lo, hi):",
    "    if lo < hi:",
    "        p = partition(arr, lo, hi)",
    "        quicksort(arr, lo, p - 1)",
    "        quicksort(arr, p + 1, hi)",
    "",
    "def partition(arr, lo, hi):",
    "    pivot = arr[hi]",
    "    i = lo - 1",
    "    for j in range(lo, hi):",
    "        if arr[j] <= pivot:",
    "            i += 1",
    "            arr[i], arr[j] = arr[j], arr[i]",
    "    arr[i+1], arr[hi] = arr[hi], arr[i+1]",
    "    return i + 1",
]

# line → index mapping used to highlight the code
LINE = {
    "fn_qs"        : 0,
    "if_lo_hi"     : 1,
    "p_partition"  : 2,
    "rec_left"     : 3,
    "rec_right"    : 4,
    "fn_part"      : 6,
    "pivot"        : 7,
    "i_init"       : 8,
    "for_j"        : 9,
    "if_cmp"       : 10,
    "i_inc"        : 11,
    "swap_ij"      : 12,
    "swap_pivot"   : 13,
    "return"       : 14,
}


class QuickSortVisualizer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Quicksort Visualizer — Pure Python")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.n          = 40
        self.speed      = 0.05          # seconds between steps
        self.arr        : list[int] = []
        self.colors     : list[str] = []
        self.comparisons = 0
        self.swaps       = 0
        self.running     = False
        self._stop       = False
        self._thread     = None
        self._active_line = -1

        self._build_ui()
        self._new_array()

    # ── UI construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        # title bar
        title = tk.Label(self.root, text="◈  QUICKSORT VISUALIZER",
                         font=FONT_TITLE, fg=ACC, bg=BG, pady=12)
        title.grid(row=0, column=0, columnspan=2, sticky="ew")

        # canvas (bars)
        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=8)

        # right panel
        right = tk.Frame(self.root, bg=BG)
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 16), pady=8)
        right.rowconfigure(0, weight=0)
        right.rowconfigure(1, weight=1)

        # statistics
        stats_frame = tk.LabelFrame(right, text=" Statistics ",
                                    fg=ACC, bg=BG,
                                    font=("Courier New", 10, "bold"),
                                    bd=1, relief="solid")
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.lbl_n    = tk.Label(stats_frame, text="Elements : 40",
                                 font=FONT_STAT, fg=TXT, bg=BG, anchor="w")
        self.lbl_cmp  = tk.Label(stats_frame, text="Comparisons : 0",
                                 font=FONT_STAT, fg=BAR_CMP, bg=BG, anchor="w")
        self.lbl_swp  = tk.Label(stats_frame, text="Swaps : 0",
                                 font=FONT_STAT, fg=BAR_SWAP, bg=BG, anchor="w")
        self.lbl_time = tk.Label(stats_frame, text="Time : 0.000s",
                                 font=FONT_STAT, fg=BAR_DONE, bg=BG, anchor="w")
        self.lbl_status = tk.Label(stats_frame, text="● IDLE",
                                   font=FONT_STAT, fg="#888", bg=BG, anchor="w")
        for w in (self.lbl_n, self.lbl_cmp, self.lbl_swp,
                  self.lbl_time, self.lbl_status):
            w.pack(fill="x", padx=8, pady=2)

        # code display
        code_frame = tk.LabelFrame(right, text=" Code ",
                                   fg=ACC, bg=BG,
                                   font=("Courier New", 10, "bold"),
                                   bd=1, relief="solid")
        code_frame.grid(row=1, column=0, sticky="nsew")

        self.code_labels: list[tk.Label] = []
        for i, line in enumerate(CODE_LINES):
            lbl = tk.Label(code_frame,
                           text=f"  {line}",
                           font=FONT_CODE,
                           fg="#666" if line == "" else TXT,
                           bg=BG,
                           anchor="w",
                           justify="left",
                           padx=4)
            lbl.pack(fill="x")
            self.code_labels.append(lbl)

        # controls
        ctrl = tk.Frame(self.root, bg=BG)
        ctrl.grid(row=2, column=0, columnspan=2,
                  sticky="ew", padx=16, pady=(0, 12))

        btn_cfg = dict(font=("Courier New", 11, "bold"),
                       relief="flat", cursor="hand2",
                       pady=6, padx=14)

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

        # size slider
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

        # speed slider
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

        # legend
        legend_frame = tk.Frame(ctrl, bg=BG)
        legend_frame.pack(side="right", padx=8)
        for color, label in [(BAR_DEF, "Default"), (BAR_PIV, "Pivot"),
                              (BAR_CMP, "Comparing"), (BAR_SWAP, "Swapping"),
                              (BAR_DONE, "Sorted")]:
            dot = tk.Label(legend_frame, text="■ " + label,
                           font=("Courier New", 9), fg=color, bg=BG)
            dot.pack(side="left", padx=6)

    # ── array helpers ────────────────────────────────────────────────────────
    def _new_array(self):
        if self.running:
            return
        self.arr    = [random.randint(5, 99) for _ in range(self.n)]
        self.colors = [BAR_DEF] * self.n
        self.comparisons = 0
        self.swaps       = 0
        self._update_stats(0.0)
        self._set_status("IDLE", "#888")
        self._highlight_code(-1)
        self._draw()

    def _draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()  or 700
        h = self.canvas.winfo_height() or 420
        if not self.arr:
            return
        n    = len(self.arr)
        gap  = 2
        bw   = max(2, (w - gap * (n + 1)) / n)
        mx   = max(self.arr) or 1
        for i, val in enumerate(self.arr):
            x0 = gap + i * (bw + gap)
            bh = int((val / mx) * (h - 30))
            y0 = h - bh
            x1 = x0 + bw
            y1 = h
            self.canvas.create_rectangle(x0, y0, x1, y1,
                                         fill=self.colors[i],
                                         outline="")
            if bw > 18 and n <= 60:
                self.canvas.create_text(
                    (x0 + x1) / 2, y0 - 6,
                    text=str(val), fill=TXT,
                    font=("Courier New", max(7, int(bw * 0.5))))

    # ── stats / code highlight ───────────────────────────────────────────────
    def _update_stats(self, elapsed: float):
        self.lbl_n.config(   text=f"Elements     : {self.n}")
        self.lbl_cmp.config( text=f"Comparisons  : {self.comparisons}")
        self.lbl_swp.config( text=f"Swaps        : {self.swaps}")
        self.lbl_time.config(text=f"Time         : {elapsed:.3f}s")

    def _set_status(self, text: str, color: str):
        self.lbl_status.config(text=f"● {text}", fg=color)

    def _highlight_code(self, line_idx: int):
        for i, lbl in enumerate(self.code_labels):
            if i == line_idx:
                lbl.config(bg="#1a2a3a", fg="#ffff88")
            else:
                raw = CODE_LINES[i]
                lbl.config(bg=BG, fg="#666" if raw == "" else TXT)

    # ── sorting thread ───────────────────────────────────────────────────────
    def _start(self):
        if self.running:
            return
        self.running = True
        self._stop   = False
        self.comparisons = 0
        self.swaps       = 0
        self.colors  = [BAR_DEF] * self.n
        self.btn_start.config(state="disabled")
        self.btn_stop.config( state="normal")
        self.btn_reset.config(state="disabled")
        self._set_status("RUNNING", BAR_CMP)
        self._thread = threading.Thread(target=self._sort_thread, daemon=True)
        self._thread.start()

    def _stop_sort(self):
        self._stop = True

    def _sort_thread(self):
        t0 = time.time()
        n  = len(self.arr)          # snapshot length — safe against slider race
        self._hl(LINE["fn_qs"])
        self._quicksort(0, n - 1)
        elapsed = time.time() - t0
        if not self._stop:
            # mark all done
            for i in range(self.n):
                self.colors[i] = BAR_DONE
            self._refresh(elapsed)
            self._hl(-1)
            self.root.after(0, lambda: self._set_status("DONE ✓", BAR_DONE))
        else:
            self.root.after(0, lambda: self._set_status("STOPPED", "#ff4444"))
        self.root.after(0, self._reset_buttons)

    def _quicksort(self, lo: int, hi: int):
        if self._stop:
            return
        self._hl(LINE["if_lo_hi"])
        self._sleep()
        if lo < hi:
            self._hl(LINE["p_partition"])
            self._sleep()
            p = self._partition(lo, hi)
            if self._stop:
                return
            self._hl(LINE["rec_left"])
            self._sleep()
            self._quicksort(lo, p - 1)
            self._hl(LINE["rec_right"])
            self._sleep()
            self._quicksort(p + 1, hi)

    def _partition(self, lo: int, hi: int) -> int:
        self._hl(LINE["pivot"])
        pivot = self.arr[hi]
        self.colors[hi] = BAR_PIV
        self._refresh()
        self._sleep()

        self._hl(LINE["i_init"])
        i = lo - 1
        self._sleep()

        self._hl(LINE["for_j"])
        for j in range(lo, hi):
            if self._stop:
                return lo
            self._hl(LINE["if_cmp"])
            self.comparisons += 1
            # compare colour
            prev_j = self.colors[j]
            self.colors[j] = BAR_CMP
            self._refresh()
            self._sleep()

            if self.arr[j] <= pivot:
                self._hl(LINE["i_inc"])
                i += 1
                self._hl(LINE["swap_ij"])
                self.swaps += 1
                self.colors[i] = BAR_SWAP
                self.colors[j] = BAR_SWAP
                self._refresh()
                self._sleep()
                self.arr[i], self.arr[j] = self.arr[j], self.arr[i]
                self.colors[i] = BAR_DEF
                self.colors[j] = BAR_DEF
            else:
                self.colors[j] = BAR_DEF
            self.colors[hi] = BAR_PIV
            self._refresh()

        self._hl(LINE["swap_pivot"])
        self.swaps += 1
        self.colors[i + 1] = BAR_SWAP
        self.colors[hi]     = BAR_SWAP
        self._refresh()
        self._sleep()
        self.arr[i + 1], self.arr[hi] = self.arr[hi], self.arr[i + 1]
        self.colors[i + 1] = BAR_DONE
        self.colors[hi]     = BAR_DEF
        self._refresh()

        self._hl(LINE["return"])
        self._sleep()
        return i + 1

    # ── threading helpers ────────────────────────────────────────────────────
    def _hl(self, line: int):
        self.root.after(0, lambda l=line: self._highlight_code(l))

    def _sleep(self):
        time.sleep(self.speed)

    def _refresh(self, elapsed: float = None):
        if elapsed is None:
            elapsed = 0.0
        self.root.after(0, lambda e=elapsed: (self._draw(),
                                               self._update_stats(e)))

    def _reset_buttons(self):
        self.running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config( state="disabled")
        self.btn_reset.config(state="normal")

    # ── slider callbacks ─────────────────────────────────────────────────────
    def _on_size(self, val):
        if self.running:
            return
        self.n = int(val)
        self._new_array()

    def _on_speed(self, val):
        # 1 → slowest (0.5s), 100 → fastest (0.001s)
        self.speed = 0.5 - (int(val) - 1) * (0.499 / 99)


def main():
    root = tk.Tk()
    root.geometry("1100x680")
    root.minsize(800, 500)
    app = QuickSortVisualizer(root)
    root.bind("<Configure>", lambda e: app._draw())
    root.mainloop()


if __name__ == "__main__":
    main()