""" ai.py - Thuật toán Minimax và Alpha-Beta Pruning (đã tối ưu)

Các cải tiến so với phiên bản gốc:
  1. Move Ordering  – sắp xếp nước đi theo điểm nhanh trước khi đệ quy,
                      giúp Alpha-Beta cắt được nhiều nhánh hơn đáng kể.
  2. Transposition Table – lưu cache (board_hash → value) để tránh tính
                      lại các trạng thái đã gặp.
  3. Giới hạn số nước đi – chỉ xét tối đa MAX_MOVES nước ứng viên
                      tốt nhất thay vì toàn bộ.
"""

import time
from .board import Board, HUMAN, AI
from .evaluate import evaluate

INF       = float('inf')
MAX_MOVES = 15   # Chỉ xét tối đa 15 nước đi ứng viên mỗi tầng -> Để càng cao thì càng chính xác nma tốc độ sẽ chậm

# ─── Hàm hỗ trợ ──────────────────────────────────────────────────────────────
"""
    Chấm điểm nhanh cho ô (r,c) mà không gọi evaluate() đầy đủ.
    Dùng để sắp xếp nước đi trước khi đệ quy (move ordering).
    Ý tưởng: thử đặt quân AI rồi người, lấy điểm cao hơn.
"""
def _quick_score(board: Board, r: int, c: int) -> int:
    board.place(r, c, AI)
    s_ai = evaluate(board)
    board.undo(r, c)

    board.place(r, c, HUMAN)
    s_human = evaluate(board)       # Trả về một số < 0
    board.undo(r, c)

    # Ưu tiên ô vừa tấn công vừa chặn tốt
    # Trả về: Ô cờ mang lại điểm tấn công cao cho máy hoặc những ô chặn nước đi nguy hiểm của người chơi
    return max(s_ai, -s_human)

""" Moving order
    Lấy danh sách nước đi ứng viên, sắp xếp theo điểm nhanh giảm dần,
    và chỉ giữ lại tối đa MAX_MOVES nước tốt nhất.
"""
def _ordered_moves(board: Board) -> list[tuple[int, int]]:
    # Gọi board.get_candidate_moves() để lấy các ô xung quanh vùng giao tranh.
    # candidates: Tập hợp các ô trống xung quanh ô đang được đánh
    # -> Ô nào có khoảng cách nhỏ hơn thì được xếp lên trước 
    candidates = board.get_candidate_moves()
    scored = sorted(candidates,
                    key=lambda p: _quick_score(board, p[0], p[1]),          # Số điểm tính toán lớn nhất thì được xếp lên trước
                    reverse=True)
    # Nó chỉ trả về [:MAX_MOVES] (tối đa 15 nước đi tốt nhất). Điều này làm giảm đáng kể 
    # chiều rộng của cây tìm kiếm (Branching Factor), đánh đổi một chút sự chính xác tuyệt
    # đối để lấy tốc độ vượt trội.
    return scored[:MAX_MOVES]

"""
    Chuyển trạng thái bàn cờ thành key bất biến để dùng làm khóa cache.
    Dùng tuple lồng nhau – đủ nhanh với bàn 15x15.
    Lý do: Python Dictionary (được dùng làm bộ nhớ đệm Transposition Table) yêu cầu khóa (key) 
    phải là kiểu dữ liệu bất biến. 
    -> Biến đổi List lồng List thành Tuple lồng Tuple giúp tạo ra một mã KEY duy nhất cho 
    mỗi trạng thái bàn cờ.
"""
def _board_key(board: Board) -> tuple:
    return tuple(tuple(row) for row in board.grid)


# ═══════════════════════════════════════════════════════════════════════════════
# LEVEL 1 – MINIMAX  (có move ordering)
# ═══════════════════════════════════════════════════════════════════════════════
"""
    Minimax với move ordering.
    Move ordering giúp xét nước tốt trước → cải thiện thứ tự đánh giá.
"""
def minimax(board: Board,
            depth: int,
            is_maximizing: bool,
            counter: list) -> int:
    counter[0] += 1

    # BASE CASE: Dừng đệ quy nếu một bên thắng, hòa hoặc chạm đến độ sâu tối đa
    if board.check_win(AI):
        return  500_000 + depth
    if board.check_win(HUMAN):
        return -500_000 - depth
    if board.is_draw():
        return 0
    if depth == 0:    
        return evaluate(board)

    # Duyệt 15 nhánh ở mỗi độ sâu
    moves = _ordered_moves(board)

    # Lượt của MAX (AI)
    if is_maximizing:
        best = -INF
        for r, c in moves:
            board.place(r, c, AI)
            val = minimax(board, depth - 1, False, counter)     # Trả về giá trị ước lượng   
            board.undo(r, c)
            best = max(best, val)   # So sánh để tối đa hóa giá trị 
        return best
    # Lượt của MIN (Người)
    else:
        best = INF
        for r, c in moves:
            board.place(r, c, HUMAN)
            val = minimax(board, depth - 1, True, counter)      # Trả về giá trị ước lượng
            board.undo(r, c)
            best = min(best, val)   # So sánh để tối thiểu hóa giá trị
        return best

'''
Mục đích: Là hàm "mồi" (wrapper) gọi từ giao diện. Nhiệm vụ của nó là duyệt các nước đi ứng viên đầu tiên, 
gọi hàm đệ quy minimax, và trả về tọa độ của nước đi đạt điểm cao nhất, cùng với các thông số thống kê 
(thời gian, số trạng thái đã duyệt).

Tham số:
    - board: Đối tượng board 
    - depth: Độ sâu được xét

Trả về:
    - dict: Thông số thống kê (thời gian, số trạng thái đã duyệt).
'''
def get_best_move_minimax(board: Board, depth: int) -> dict:
    best_move = None
    best_val  = -INF
    counter   = [0]
    t0        = time.perf_counter()

    for r, c in _ordered_moves(board):
        board.place(r, c, AI)
        val = minimax(board, depth - 1, False, counter)
        board.undo(r, c)
        if val > best_val:
            best_val  = val
            best_move = (r, c)

    return {
        "move":           best_move,
        "value":          best_val,
        "states_visited": counter[0],
        "time_ms":        round((time.perf_counter() - t0) * 1000, 2),
        "depth":          depth,
        "algorithm":      "Minimax",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LEVEL 2 – ALPHA-BETA  (move ordering + transposition table)
# ═══════════════════════════════════════════════════════════════════════════════
# Transposition table: { board_key → (depth_stored, flag, value) }
#   flag: 'exact' | 'lower' | 'upper'
#   - exact : giá trị chính xác
#   - lower : giá trị là cận dưới (alpha cutoff) ()
#   - upper : giá trị là cận trên (beta cutoff)
'''
_tt là một bảng băm (Dictionary _tt) dùng để lưu trữ kết quả của các trạng thái bàn cờ đã được duyệt qua.
Đây là bộ nhớ đệm (cache) toàn cục. Key là trạng thái bàn cờ được chuyển thành tuple bất biến 
(vì dict Python chỉ chấp nhận khóa hashable). Value là bộ 3 giá trị:
- depth_stored: Trạng thái này được tính ở độ sâu bao nhiêu. Chỉ dùng lại nếu stored_depth >= depth hiện tại
- flag: Loại kết quả: exact / lower / upper
- value: Điểm số được lưu

𝛼 (Alpha): Là giá trị lớn nhất (tốt nhất cho MAX)"
𝛽 (Beta): Là giá trị nhỏ nhất (tốt nhất cho MIN) 
'''
_tt: dict = {}
TT_MAX_SIZE = 200_000   # Giới hạn số entry trong cache

def _tt_clear():
    _tt.clear()

"""
Alpha-Beta Pruning với:
    - Move ordering       : xét nước tốt nhất trước → cắt nhiều hơn
    - Transposition table : bỏ qua trạng thái đã tính ở độ sâu đủ lớn
"""
def alpha_beta(board: Board,
               depth: int,
               alpha: float,
               beta: float,
               is_maximizing: bool,
               counter: list) -> int:
    counter[0] += 1
    alpha_orig = alpha

    # ── Tra cứu transposition table ──────────────────────────────────────────
    # Kiểm tra xem trạng thái bàn cờ hiện tại đã có trong _tt chưa.
    # Trạng thái bàn cờ: Lưu trữ toàn bộ ô cờ 15x15
    key = _board_key(board)
    if key in _tt:
        # Nếu có, nó kiểm tra điều kiện sống còn: stored_depth >= depth
        # Thực hiện lấy key từ dictionary _tt
        stored_depth, flag, stored_val = _tt[key]
        if stored_depth >= depth:          # Cache đủ sâu → tin dùng được
            if flag == 'exact':
                return stored_val
            elif flag == 'lower':
                alpha = max(alpha, stored_val)
            elif flag == 'upper':
                beta  = min(beta, stored_val)
            # Thực hiện cắt nhánh
            if beta <= alpha:              
                return stored_val          # Cắt nhánh nhờ cache

    # ── Trường hợp cơ sở ────────────────────────────────────────────────────
    # BASE CASE: Giống minimax
    if board.check_win(AI):
        return  500_000 + depth
    if board.check_win(HUMAN):
        return -500_000 - depth
    if board.is_draw():
        return 0
    if depth == 0:
        return evaluate(board)

    # ── Đệ quy với move ordering + cắt nhánh ────────────────────────────────
    # moves: một list gồm nhiều tuple và mỗi tuple có hai phần tử (row, col)
    moves = _ordered_moves(board)
    # Gắn giá trị ban đầu
    best  = -INF if is_maximizing else INF

    # Thực hiện duyệt toàn bộ nhánh
    for r, c in moves:
        player = AI if is_maximizing else HUMAN
        board.place(r, c, player)   # Đặt một quân cờ 
        # Thực hiện alpha-beta
        val = alpha_beta(board, depth - 1, alpha, beta,
                         not is_maximizing, counter)
        board.undo(r, c)            # Trả về trạng thái ban đầu

        # Cập nhật alpha, beta
        if is_maximizing:
            best  = max(best, val)
            alpha = max(alpha, best)
        else:
            best = min(best, val)
            beta = min(beta, best)

        if beta <= alpha:   # Cắt nhánh
            break

    # ── Lưu vào transposition table ──────────────────────────────────────────
    # Sau khi duyệt xong các nhánh con, hàm phải lưu kết quả best vào _tt trước khi trả về. 
    if len(_tt) < TT_MAX_SIZE:
        if best <= alpha_orig:
            flag = 'upper'
        elif best >= beta:
            flag = 'lower'
        else:
            flag = 'exact'
        _tt[key] = (depth, flag, best)

    return best

'''
Đây là hàm bọc (wrapper) được gọi từ giao diện người dùng main.py.

Tham số:
    - board: Đối tượng Board thể hiện trạng thái của bàn cờ
    - depth: Độ sâu hiện tại 

Trả về:
    - dict: Thông số thống kê (thời gian, số trạng thái đã duyệt).
'''
def get_best_move_alphabeta(board: Board, depth: int) -> dict:
    _tt_clear()   # Xóa cache mỗi nước đi (bàn cờ đã thay đổi)

    best_move = None
    best_val  = -INF
    alpha    = -INF        # Khởi tạo alpha ở root
    counter   = [0]
    t0        = time.perf_counter()

    root_moves = _ordered_moves(board)

    for r, c in root_moves:
        board.place(r, c, AI)
        # Truyền alpha hiện tại vào đệ quy
        val = alpha_beta(board, depth - 1, alpha, INF, False, counter)
        board.undo(r, c)
        if val > best_val:
            best_val  = val
            best_move = (r, c)

        # Thực hiện cập nhật lại alpha sau mỗi nước đi để các nhánh sau có thể dùng
        # alpha để pruning 
        alpha = max(alpha, best_val)

    return {
        "move":           best_move,
        "value":          best_val,
        "states_visited": counter[0],
        "time_ms":        round((time.perf_counter() - t0) * 1000, 2),
        "depth":          depth,
        "algorithm":      "Alpha-Beta",
    }