"""
board.py - Biểu diễn bàn cờ và logic trò chơi Caro

- Chức năng: Chịu trách nhiệm lưu trữ và quản lý trạng thái của bàn cờ (mảng 2 chiều 15x15).
- Nhiệm vụ chính: Cung cấp các phương thức để thao tác với bàn cờ như đặt quân (place), rút quân (undo - rất quan trọng cho thuật toán đệ quy), 
kiểm tra tính hợp lệ của nước đi (is_valid). Nó cũng chứa logic cốt lõi để xác định thắng/thua/hòa (check_win, is_draw).
- Tối ưu hóa: Hàm get_candidate_moves được thiết kế thông minh để khoanh vùng các ô trống xung quanh các quân cờ đã đánh 
(thay vì quét toàn bộ bàn cờ), giúp thu hẹp đáng kể không gian tìm kiếm cho AI.
"""
EMPTY = 0
HUMAN = 1   # X
AI    = 2   # O

WIN_LENGTH = 4   # 4 quân liên tiếp là thắng
BOARD_SIZE = 15  # Bàn cờ 15x15

class Board:
    """
    Bàn cờ Caro được biểu diễn bằng mảng 2 chiều (list of lists).
    Mỗi ô có giá trị: 0=trống, 1=người (X), 2=máy (O)
    """
    def __init__(self, size: int = BOARD_SIZE):
        self.size = size
        # Khởi tạo bàn cờ toàn ô trống
        self.grid = [[EMPTY] * size for _ in range(size)]
        self.move_count = 0          # Tổng số nước đã đánh
        self.last_move: tuple | None = None  # Nước đi cuối cùng

    # ─── Đặt / bỏ quân ───────────────────────────────────────────────────────

    """ Đặt quân tại (row, col) – dùng trong quá trình Minimax.
        Tham số:
            - row: Hàng
            - col: Cột
        Trả về:
            - bool: Kiểm tra việc đặt quân của player tại (row, col) thành công không
    """
    def place(self, row: int, col: int, player: int) -> bool:
        if not self.is_valid(row, col):
            return False
        self.grid[row][col] = player
        self.move_count += 1
        self.last_move = (row, col)
        return True

    """Gỡ quân tại (row, col) – dùng trong quá trình Minimax."""
    def undo(self, row: int, col: int):
        self.grid[row][col] = EMPTY
        self.move_count -= 1

    """Ô hợp lệ: nằm trong bàn cờ và còn trống."""
    def is_valid(self, row: int, col: int) -> bool:
        
        return (0 <= row < self.size and
                0 <= col < self.size and
                self.grid[row][col] == EMPTY)

    # ─── Kiểm tra thắng / hòa ────────────────────────────────────────────────

    """Trả về True nếu player có WIN_LENGTH quân liên tiếp.
    Tham số:
        - player: Người chơi được truyền vào (AI hoặc người)

    Trả về:
        - bool: Kiểm tra player đã chiến thắng hay chưa
    """
    def check_win(self, player: int) -> bool:
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] != player:
                    continue

                # Xét từng tọa độ xung quanh của ô (r,c)
                for dr, dc in directions:
                    count = 1
                    nr, nc = r + dr, c + dc
                    # Dếm số lượng chuỗi liên tiếp
                    while (0 <= nr < self.size and
                           0 <= nc < self.size and
                           self.grid[nr][nc] == player):
                        count += 1
                        nr += dr
                        nc += dc
                    # Player chiến thắng!
                    if count >= WIN_LENGTH:
                        return True
        return False

    """Hòa khi bàn cờ đầy và không ai thắng."""
    def is_draw(self) -> bool:
        # Tổng số nước đã đánh = kích thước của ô cờ thì kết luận HÒA
        return self.move_count == self.size * self.size

    # Nếu hàm trả về True, AI sẽ dừng thuật toán đệ quy tại nút đó
    def is_terminal(self) -> bool:
        return (self.check_win(HUMAN) or
                self.check_win(AI)   or
                self.is_draw())

    # ─── Sinh nước đi hợp lệ ─────────────────────────────────────────────────
    """ Hàm tối ưu
        Chỉ sinh các ô trống nằm trong khoảng 'radius' ô
        tính từ các quân đã đánh. Giúp cắt không gian tìm kiếm đáng kể.
        Nếu bàn cờ trống, trả về ô trung tâm.
    """
    def get_candidate_moves(self, radius: int = 2) -> list[tuple[int, int]]:
        # Bàn cờ trống thì trả về ô trung tâm
        if self.move_count == 0:
            mid = self.size // 2
            return [(mid, mid)]

        # Tạo ra một tập hợp (set) để tự động loại bỏ các phần tử trùng lặp
        candidates = set()
        for r in range(self.size):
            for c in range(self.size):
                # Thuật toán chỉ dừng lại tại ô đã có quân cờ (người chơi hoặc AI)
                if self.grid[r][c] == EMPTY:
                    continue

                # Với mỗi quân đã đánh, đưa các ô lân cận vào tập ứng viên
                for dr in range(-radius, radius + 1):
                    for dc in range(-radius, radius + 1):
                        nr, nc = r + dr, c + dc
                        # Nếu thỏa mãn, ô trống này lập tức được thêm vào tập 
                        # candidates để AI xét đến sau này.
                        if (0 <= nr < self.size and
                                0 <= nc < self.size and
                                self.grid[nr][nc] == EMPTY):
                            candidates.add((nr, nc))

        # Sắp xếp ưu tiên ô gần trung tâm (giúp Alpha-Beta cắt nhiều hơn)
        # Dùng công thức tính khoảng cách Manhattan từ điểm p đến điểm tâm mid của bàn cờ
        # Ô nào có khoảng cách nhỏ hơn thì được sắp xếp lên trước
        mid = self.size // 2
        return sorted(candidates,
                      key=lambda p: abs(p[0] - mid) + abs(p[1] - mid))

    # ─── Hiển thị console ────────────────────────────────────────────────────
    def display(self):
        symbols = {EMPTY: '.', HUMAN: 'X', AI: 'O'}
        header = "   " + " ".join(f"{c:2}" for c in range(self.size))
        print(header)
        for r in range(self.size):
            row_str = f"{r:2} " + "  ".join(symbols[self.grid[r][c]]
                                             for c in range(self.size))
            print(row_str)
        print()

    # Trả về một bản sao độc lập (deep copy) của bàn cờ hiện tại.
    def clone(self) -> "Board":
        """Tạo bản sao sâu của bàn cờ – dùng khi cần lưu trạng thái."""
        b = Board(self.size)
        b.grid = [row[:] for row in self.grid]
        b.move_count = self.move_count
        b.last_move = self.last_move
        return b