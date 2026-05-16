"""
main.py - Điểm khởi động: Chạy game Caro với giao diện tkinter

Cách chạy:
    python main.py

Phím tắt trong game:
    r       : Restart
    m / a   : Chuyển chế độ AI (Minimax / Alpha-Beta)
    +/-     : Tăng/giảm độ sâu

Tóm tắt quy trình gồm 3 giai đoạn trên 2 Thread khác nhau:
    - Giai đoạn 1 — Main Thread: _on_click()
    - Giai đoạn 2 — Background Thread: _ai_worker()
    - Giai đoạn 3 — Main Thread trở lại: _ai_done(result)
"""

import tkinter as tk
from tkinter import messagebox
import threading
from src import *

# ─── Cài đặt giao diện ───────────────────────────────────────────────────────
BOARD_SIZE   = 15
CELL_SIZE    = 38
MARGIN       = 25
CANVAS_SIZE  = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)

COLOR_BG     = "#F5DEB3"   # Màu bàn cờ (wheat)
COLOR_LINE   = "#8B4513"
COLOR_HUMAN  = "#1a1a2e"   # X (đen xanh)
COLOR_AI     = "#c0392b"   # O (đỏ)
COLOR_LAST   = "#27ae60"   # Viền nước đi cuối

DEFAULT_DEPTH    = 3
DEFAULT_ALGO     = "alpha_beta"   # "minimax" hoặc "alpha_beta"
DEFAULT_FIRST    = "human"        # "human" hoặc "ai"

class CaroGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Cờ Caro AI – Minimax / Alpha-Beta")
        self.board = Board(BOARD_SIZE)
        self.current_player = HUMAN   # Người đi trước
        self.game_over = False
        self.ai_thinking = False      # Đang chờ AI → khoá click của người
        self.depth = DEFAULT_DEPTH
        self.algo  = DEFAULT_ALGO
        self.first_player = DEFAULT_FIRST  # Ai đi trước: "human" hoặc "ai"

        self._build_ui()
        self._draw_board()
        # Nếu cài đặt ban đầu là AI đi trước, kích hoạt AI ngay
        self._maybe_ai_first()

    # ─── Xây dựng giao diện ──────────────────────────────────────────────────

    def _build_ui(self):
        # Canvas bàn cờ
        self.canvas = tk.Canvas(self.root,
                                width=CANVAS_SIZE, height=CANVAS_SIZE,
                                bg=COLOR_BG)
        self.canvas.grid(row=0, column=0, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._on_click)

        # Panel bên phải
        panel = tk.Frame(self.root)
        panel.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        tk.Label(panel, text="⚙ Cài đặt", font=("Arial", 13, "bold")).pack(pady=5)

        # Chọn thuật toán
        tk.Label(panel, text="Thuật toán AI:").pack(anchor="w")
        self.algo_var = tk.StringVar(value=self.algo)
        tk.Radiobutton(panel, text="Minimax",    variable=self.algo_var,
                       value="minimax",     command=self._on_algo).pack(anchor="w")
        tk.Radiobutton(panel, text="Alpha-Beta", variable=self.algo_var,
                       value="alpha_beta",  command=self._on_algo).pack(anchor="w")

        # ── Chọn phe đi trước ────────────────────────────────────────────────
        tk.Label(panel, text="\nPhe đi trước:").pack(anchor="w")       
        # Kiểu dữ liệu stringVar thuộc thư viện tkinter -> Nó có khả năng tự động đồng bộ với widget đang dùng nó
        # — khi giá trị thay đổi, widget cập nhật ngay lập tức và ngược lại.
        # Ví dụ: Khi ta chọn Radiobutton "Người (X)" thì self.first_var = "human". Khi này, ta thực hiện hàm 
        # self._on_first() và hàm này giúp gán self.first_player = giá trị nút Radiobutton 
        self.first_var = tk.StringVar(value=self.first_player)
        tk.Radiobutton(panel, text="Người (X)",
                       variable=self.first_var, value="human",
                       command=self._on_first).pack(anchor="w")
        tk.Radiobutton(panel, text="Máy (O)",
                       variable=self.first_var, value="ai",
                       command=self._on_first).pack(anchor="w")

        # Độ sâu
        tk.Label(panel, text="\nĐộ sâu tìm kiếm:").pack(anchor="w")
        depth_frame = tk.Frame(panel)
        depth_frame.pack()
        tk.Button(depth_frame, text="−", width=3,
                  command=lambda: self._change_depth(-1)).pack(side="left")
        self.depth_label = tk.Label(depth_frame, text=str(self.depth), width=3)
        self.depth_label.pack(side="left")
        tk.Button(depth_frame, text="+", width=3,
                  command=lambda: self._change_depth(+1)).pack(side="left")

        # Nút restart
        tk.Button(panel, text="🔄  Chơi lại (R)", font=("Arial", 11),
                  command=self._restart, bg="#2980b9", fg="white",
                  padx=8, pady=4).pack(pady=15, fill="x")

        # Thống kê
        tk.Label(panel, text="📊 Thống kê nước đi cuối:",
                 font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 0))
        self.stat_text = tk.Text(panel, width=28, height=10,
                                 state="disabled", font=("Courier", 9))
        self.stat_text.pack()

        # Trạng thái game
        self.status_var = tk.StringVar(value="Lượt của bạn (X)")
        tk.Label(panel, textvariable=self.status_var,
                 font=("Arial", 12, "bold"), fg="#2c3e50").pack(pady=8)
        
        # Xử lý các sự kiện từ bàn phím và nút bấm
        self.root.bind("<r>", lambda e: self._restart())
        self.root.bind("<m>", lambda e: self._set_algo("minimax"))
        self.root.bind("<a>", lambda e: self._set_algo("alpha_beta"))
        self.root.bind("<plus>",  lambda e: self._change_depth(+1))
        self.root.bind("<minus>", lambda e: self._change_depth(-1))

    # ─── Vẽ bàn cờ ───────────────────────────────────────────────────────────

    def _draw_board(self):
        self.canvas.delete("all")
        # Vẽ lưới
        for i in range(BOARD_SIZE):
            x = MARGIN + i * CELL_SIZE
            y = MARGIN + i * CELL_SIZE
            self.canvas.create_line(MARGIN, y, CANVAS_SIZE - MARGIN, y,
                                    fill=COLOR_LINE, width=1)
            self.canvas.create_line(x, MARGIN, x, CANVAS_SIZE - MARGIN,
                                    fill=COLOR_LINE, width=1)

        # Vẽ quân
        r_quart = CELL_SIZE // 2 - 3
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cell = self.board.grid[r][c]
                if cell == EMPTY:
                    continue
                cx = MARGIN + c * CELL_SIZE
                cy = MARGIN + r * CELL_SIZE
                is_last = (self.board.last_move == (r, c))
                outline = COLOR_LAST if is_last else "#555"
                color   = COLOR_HUMAN if cell == HUMAN else COLOR_AI
                self.canvas.create_oval(cx - r_quart, cy - r_quart,
                                        cx + r_quart, cy + r_quart,
                                        fill=color, outline=outline,
                                        width=3 if is_last else 1)
                symbol = "X" if cell == HUMAN else "O"
                self.canvas.create_text(cx, cy, text=symbol,
                                        fill="white", font=("Arial", 12, "bold"))

    # ─── Xử lý sự kiện ───────────────────────────────────────────────────────
    '''

    '''
    def _on_click(self, event):
        # B1: Chặn thao tác không hợp lệ, lập tức dừng lại nếu trò chơi đã kết thúc, đang là lượt của máy hoặc
        # máy trong quá trình tính toán
        if self.game_over or self.current_player != HUMAN or self.ai_thinking:
            return
        
        # B2: Quy đổi tọa độ
        c = round((event.x - MARGIN) / CELL_SIZE)
        r = round((event.y - MARGIN) / CELL_SIZE)
        # Kiểm tra tính hợp lý của vị trí được đặt
        if not self.board.is_valid(r, c):
            return
        # B3: Đặt quân cờ X của người chơi và vẽ lại bàn cờ
        self.board.place(r, c, HUMAN)
        self._draw_board()
        # B4: Gọi _check_end() để xem đã kết thúc lượt chơi chưa
        # Nếu chưa, chuyển lượt cho AI, khóa giao diện click
        if self._check_end():
            return
        # Cập nhật trạng thái người chơi hiện tại và đặt cờ ai_thinking
        self.current_player = AI
        self.ai_thinking = True
        self.status_var.set("Máy đang suy nghĩ…")
        # B5: Chạy AI trên thread riêng để UI không bị đơ
        threading.Thread(target=self._ai_worker, daemon=True).start()

    """Chạy thuật toán AI trên background thread."""
    def _ai_worker(self):
        # Sử dụng thuật toán minimax hay alpha-beta
        fn = (get_best_move_minimax if self.algo == "minimax"
              else get_best_move_alphabeta)
        # Gọi hàm tương ứng với thuật toán được lựa chọn
        result = fn(self.board, self.depth)     
        # Trả kết quả về main thread qua after()
        self.root.after(0, self._ai_done, result)
    
    """Tiến hành đặt quân O xuống bàn cờ, vẽ lại UI, in thông số ra bảng thống kê"""
    def _ai_done(self, result):
        """Callback trên main thread sau khi AI tính xong."""
        self.ai_thinking = False
        # Đặt quân O tại vị trí (r,c)
        if result["move"]:
            r, c = result["move"]
            self.board.place(r, c, AI)
        self._draw_board()
        self._update_stats(result)
        # Kiểm tra xem AI có thắng không, nếu không thì mở khóa giao diện trả lại lượt cho Người chơi.
        if not self._check_end():
            self.current_player = HUMAN
            self.status_var.set("Lượt của bạn (X)")

    """Kiểm tra xem trò chơi đã kết thúc hay chưa"""
    def _check_end(self) -> bool:
        if self.board.check_win(HUMAN):
            self._end("🎉 Bạn thắng!")
            return True
        if self.board.check_win(AI):
            self._end("🤖 Máy thắng!")
            return True
        if self.board.is_draw():
            self._end("🤝 Hòa!")
            return True
        return False

    """Hiển thị dòng thông báo khi kết thúc trò chơi"""
    def _end(self, msg: str):
        self.game_over = True
        self.status_var.set(msg)
        messagebox.showinfo("Kết thúc ván", msg)

    """Reset toàn bộ bàn cờ"""
    def _restart(self):
        self.board = Board(BOARD_SIZE)
        self.game_over = False
        self.ai_thinking = False
        self._draw_board()
        self._update_stats(None)
        # Xác định ai đi trước dựa theo lựa chọn của người dùng
        if self.first_player == "ai":
            self.current_player = AI
            self._maybe_ai_first()
        else:
            self.current_player = HUMAN
            self.status_var.set("Lượt của bạn (X)")

    """Cập nhật các thông tin về nước cờ mà AI đi được"""
    def _update_stats(self, result):
        self.stat_text.config(state="normal")
        self.stat_text.delete("1.0", "end")
        if result:
            txt = (f"Thuật toán : {result['algorithm']}\n"
                   f"Độ sâu     : {result['depth']}\n"
                   f"Nước đi    : {result['move']}\n"
                   f"Giá trị    : {result['value']:,}\n"
                   f"Trạng thái : {result['states_visited']:,}\n"
                   f"Thời gian  : {result['time_ms']} ms")
            self.stat_text.insert("end", txt)
        self.stat_text.config(state="disabled")

    """Trả về thuật toán đang được sử dụng"""
    def _on_algo(self):
        self.algo = self.algo_var.get()

    """Thiết lập thuật toán sử dụng (minimax hoặc alpha-beta)"""
    def _set_algo(self, algo: str):
        self.algo = algo
        self.algo_var.set(algo)

    """Thay đổi độ sâu"""
    def _change_depth(self, delta: int):
        self.depth = max(1, min(6, self.depth + delta))
        self.depth_label.config(text=str(self.depth))

    """Lưu lựa chọn phe đi trước khi người dùng thay đổi radio button"""
    def _on_first(self):
        self.first_player = self.first_var.get()        

    """Kích hoạt AI đi ngay nếu cài đặt là máy đi trước.
    Dùng after(100) để đảm bảo UI đã render xong trước khi spawn thread."""
    def _maybe_ai_first(self):
        if self.first_player == "ai" and not self.game_over:
            self.current_player = AI
            self.ai_thinking = True
            self.status_var.set("Máy đang suy nghĩ…")
            # Delay nhỏ để tkinter kịp vẽ bàn cờ trước khi AI bắt đầu tính
            self.root.after(100, lambda: threading.Thread(
                target=self._ai_worker, daemon=True).start())


# ─── Chạy chương trình ───────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = CaroGUI(root)
    root.mainloop()