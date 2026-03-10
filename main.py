import tkinter as tk
import random
import time
import threading

#colour palette ───────────────────────────────────────────────────────────
BG        = "#0d0d0d"
BAR_DEF   = "#1e90ff" #default
BAR_ROOT  = "#ff4d4d" #current root
BAR_CMP   = "#ffd700" #comparing children
BAR_SWAP  = "#ff8c00" #swapping
BAR_HEAP  = "#c740f5" #inside the heap
BAR_DONE  = "#00e676" #sorted
TXT       = "#e0e0e0"
ACC       = "#1e90ff"

FONT_TITLE = ("Courier New", 20, "bold")
FONT_CODE  = ("Courier New", 11)
FONT_STAT  = ("Courier New", 12, "bold")

#heapsort source ──────────────────────────────────────────────────────────
CODE_LINES = [
    "def heapsort(arr):",
    "    n = len(arr)",
    "    # Build max-heap",
    "    for i in range(n//2 - 1, -1, -1):",
    "        sift_down(arr, i, n)",
    "",
    "    # Extract elements one by one",
    "    for i in range(n - 1, 0, -1):",
    "        arr[0], arr[i] = arr[i], arr[0]",
    "        sift_down(arr, 0, i)",
    "",
    "def sift_down(arr, root, end):",
    "    while True:",
    "        largest = root",
    "        left    = 2 * root + 1",
    "        right   = 2 * root + 2",
    "        if left < end and arr[left] > arr[largest]:",
    "            largest = left",
    "        if right < end and arr[right] > arr[largest]:",
    "            largest = right",
    "        if largest == root:",
    "            break",
    "        arr[root], arr[largest] = arr[largest], arr[root]",
    "        root = largest",
]

LINE = {
    "fn_hs"        : 0,
    "n_len"        : 1,
    "comment_build": 2,
    "for_build"    : 3,
    "sift_build"   : 4,
    "comment_ext"  : 6,
    "for_extract"  : 7,
    "swap_root"    : 8,
    "sift_extract" : 9,
    "fn_sd"        : 11,
    "while"        : 12,
    "largest"      : 13,
    "left"         : 14,
    "right"        : 15,
    "if_left"      : 16,
    "upd_left"     : 17,
    "if_right"     : 18,
    "upd_right"    : 19,
    "if_done"      : 20,
    "break"        : 21,
    "swap_sd"      : 22,
    "root_upd"     : 23,
}


class HeapSortVisualizer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("HeapSort Visualizer — Pure Python")
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

        tk.Label(self.root, text="◈  HEAPSORT VISUALIZER",
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
        self.lbl_phase  = tk.Label(sf, text="Phase       : —",
                                   font=FONT_STAT, fg=BAR_HEAP, bg=BG, anchor="w")
        self.lbl_status = tk.Label(sf, text="● IDLE",
                                   font=FONT_STAT, fg="#888",   bg=BG, anchor="w")
        for w in (self.lbl_n, self.lbl_cmp, self.lbl_swp,
                  self.lbl_time, self.lbl_phase, self.lbl_status):
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
                           fg="#666" if line == "" else
                              ("#555" if line.startswith("    #") else TXT),
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
            (BAR_ROOT, "Root/Sifting"),
            (BAR_CMP,  "Comparing"),
            (BAR_SWAP, "Swapping"),
            (BAR_HEAP, "Heap range"),
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
        self._update_stats(0.0)
        self._set_status("IDLE", "#888")
        self._set_phase("—")
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

    #stats ────────────────────────────────────────────────────
    def _update_stats(self, elapsed: float):
        self.lbl_n.config(  text=f"Elements    : {self.n}")
        self.lbl_cmp.config(text=f"Comparisons : {self.comparisons}")
        self.lbl_swp.config(text=f"Swaps       : {self.swaps}")
        self.lbl_time.config(text=f"Time        : {elapsed:.3f}s")

    def _set_status(self, text: str, color: str):
        self.lbl_status.config(text=f"● {text}", fg=color)

    def _set_phase(self, text: str):
        self.lbl_phase.config(text=f"Phase       : {text}")

    def _highlight_code(self, idx: int):
        for i, lbl in enumerate(self.code_labels):
            if i == idx:
                lbl.config(bg="#1a2a3a", fg="#ffff88")
            else:
                raw = CODE_LINES[i]
                if raw == "":
                    fg = "#666"
                elif raw.strip().startswith("#"):
                    fg = "#555"
                else:
                    fg = TXT
                lbl.config(bg=BG, fg=fg)

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

        self._hl(LINE["fn_hs"]); self._sleep()
        self._hl(LINE["n_len"]); self._sleep()

        #ph 1 build max-heap ──────────────────────────────────────────
        self.root.after(0, lambda: self._set_phase("Build Max-Heap"))
        self._hl(LINE["comment_build"]); self._sleep()
        self._hl(LINE["for_build"]); self._sleep()

        for i in range(n // 2 - 1, -1, -1):
            if self._stop:
                break
            #tint the heap range
            for k in range(n):
                if self.colors[k] not in (BAR_DONE,):
                    self.colors[k] = BAR_HEAP
            self._hl(LINE["sift_build"]); self._sleep()
            self._sift_down(i, n)

        if not self._stop:
            #reset colours after build
            for k in range(n):
                if self.colors[k] != BAR_DONE:
                    self.colors[k] = BAR_DEF
            self._refresh()

            #ph 2 extract ─────────────────────────────────────────────
            self.root.after(0, lambda: self._set_phase("Extract Max"))
            self._hl(LINE["comment_ext"]); self._sleep()
            self._hl(LINE["for_extract"]); self._sleep()

            for i in range(n - 1, 0, -1):
                if self._stop:
                    break

                #swap root with last unsorted element
                self._hl(LINE["swap_root"])
                self.colors[0] = BAR_ROOT
                self.colors[i] = BAR_SWAP
                self._refresh(); self._sleep()
                self.arr[0], self.arr[i] = self.arr[i], self.arr[0]
                self.swaps += 1
                self.colors[i] = BAR_DONE
                self.colors[0] = BAR_DEF
                self._refresh(); self._sleep()

                self._hl(LINE["sift_extract"]); self._sleep()
                self._sift_down(0, i)

        elapsed = time.time() - t0
        if not self._stop:
            self.colors[0] = BAR_DONE
            self._refresh(elapsed)
            self._hl(-1)
            self.root.after(0, lambda: self._set_status("DONE ✓", BAR_DONE))
            self.root.after(0, lambda: self._set_phase("Complete"))
        else:
            self.root.after(0, lambda: self._set_status("STOPPED", "#ff4444"))
        self.root.after(0, self._reset_buttons)

    def _sift_down(self, root: int, end: int):
        self._hl(LINE["fn_sd"]); self._sleep()
        self._hl(LINE["while"])

        while True:
            if self._stop:
                return

            self._hl(LINE["largest"])
            largest = root
            self._hl(LINE["left"])
            left  = 2 * root + 1
            self._hl(LINE["right"])
            right = 2 * root + 2
            self._sleep()

            #highlight root
            self.colors[root] = BAR_ROOT
            self._refresh(); self._sleep()

            #compare with left child
            self._hl(LINE["if_left"])
            self.comparisons += 1
            if left < end:
                self.colors[left] = BAR_CMP
                self._refresh(); self._sleep()
                if self.arr[left] > self.arr[largest]:
                    self._hl(LINE["upd_left"])
                    largest = left
                    self._sleep()
                self.colors[left] = BAR_DEF if left != root else BAR_ROOT

            #compare with right child
            self._hl(LINE["if_right"])
            self.comparisons += 1
            if right < end:
                self.colors[right] = BAR_CMP
                self._refresh(); self._sleep()
                if self.arr[right] > self.arr[largest]:
                    self._hl(LINE["upd_right"])
                    largest = right
                    self._sleep()
                self.colors[right] = BAR_DEF if right != root else BAR_ROOT

            #check if done sifting
            self._hl(LINE["if_done"]); self._sleep()
            if largest == root:
                self._hl(LINE["break"]); self._sleep()
                self.colors[root] = BAR_DEF
                self._refresh()
                break

            #swap
            self._hl(LINE["swap_sd"])
            self.colors[root]    = BAR_SWAP
            self.colors[largest] = BAR_SWAP
            self._refresh(); self._sleep()
            self.arr[root], self.arr[largest] = self.arr[largest], self.arr[root]
            self.swaps += 1
            self.colors[root]    = BAR_DEF
            self.colors[largest] = BAR_DEF
            self._refresh()

            self._hl(LINE["root_upd"])
            root = largest
            self._sleep()

    #helpers ──────────────────────────────────────────────────────────────
    def _hl(self, line: int):
        self.root.after(0, lambda l=line: self._highlight_code(l))

    def _sleep(self):
        time.sleep(self.speed)

    def _refresh(self, elapsed: float = 0.0):
        self.root.after(0, lambda e=elapsed: (self._draw(),
                                               self._update_stats(e)))

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
    app = HeapSortVisualizer(root)
    root.bind("<Configure>", lambda e: app._draw())
    root.mainloop()


if __name__ == "__main__":
    main()