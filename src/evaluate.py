"""
evaluate.py - Hàm đánh giá trạng thái bàn cờ Caro

Ý tưởng chính:
  Quét toàn bộ bàn cờ theo 4 hướng (ngang, dọc, chéo /, chéo \).
  Với mỗi "chuỗi" gồm quân cùng loại, tính điểm dựa trên:
    - Độ dài chuỗi (2, 3, 4 quân)
    - Số đầu mở (0, 1 hoặc 2 đầu không bị chặn)

Giải thích:
Bởi vì bàn cờ là dạng lưới, một chuỗi quân liên tiếp (ngang, dọc hoặc chéo) luôn có 2 đầu. 
Tùy thuộc vào việc 2 đầu này là ô trống hay bị chặn (bởi quân của đối phương hoặc mép bàn cờ), ta có 3 trường hợp:
1. Có 2 đầu mở (Không bị chặn đầu nào)
2. Có 1 đầu mở (Bị chặn 1 đầu)
3. Có 0 đầu mở (Bị chặn cả 2 đầu)
-> Chuỗi quân càng dài và càng nhiều đầu mở thì AI sẽ chấm điểm càng cao, từ đó ưu tiên đánh vào những vị trí tạo ra 
thế cờ đó (để tấn công) hoặc đánh chặn chúng (để phòng thủ).
"""

from .board import EMPTY, HUMAN, AI, WIN_LENGTH

# ─── Bảng điểm ───────────────────────────────────────────────────────────────
# Chỉ số [length][open_ends] → điểm tương đối
# Hai dictionary lồng nhau
# Dictionary ngoài có: KEY = độ dài chuỗi đếm, VALUE = dictionary lưu trữ số điểm trả về ứng với open_ends
# Dictionary trong có: KEY = số lượng open_ends, VALUE = số điểm đạt được
SCORE_TABLE = {
    #5: {0:  500_000, 1: 50_000, 2:  200_000},     # thắng
    4: {0:   5_000,  1: 50_000, 2:  200_000},     # 4 quân -> thắng
    3: {0:        0, 1:  1_000, 2:   10_000},     # 3 quân
    2: {0:        0, 1:     50, 2:      200},     # 2 quân
    1: {0:        0, 1:      5, 2:       10},     # 1 quân
}

"""Tra bảng điểm và đảo dấu nếu là quân người."""
def _score_sequence(length: int, open_ends: int, is_ai: bool) -> int:
    # Nếu độ dài chuỗi đếm được lớn hơn hoặc bằng độ dài chiến thắng (ở đây là 4 hoặc 5 tùy luật), 
    # thì ép nó về đúng WIN_LENGTH
    if length >= WIN_LENGTH:
        length = WIN_LENGTH
    # SCORE_TABLE.get(length, {}): Tìm key length trong bảng điểm. Nếu không tìm thấy (ví dụ độ dài là 0, hoặc lớn hơn mà chưa bị chặn), 
    # nó sẽ trả về một dictionary rỗng {} thay vì báo lỗi.
    # .get(open_ends, 0): Tiếp tục tìm key open_ends bên trong kết quả vừa lấy được ở bước trên. Nếu không tìm thấy 
    # (hoặc nếu kết quả bước trước là {} rỗng), nó sẽ trả về giá trị mặc định là 0.
    score = SCORE_TABLE.get(length, {}).get(open_ends, 0)

    # Nếu chuỗi này là của AI thì hàm trả về điểm âm. Nếu chuỗi này là của người chơi
    # hàm trả về điểm âm (AI sẽ hiểu đây là rủi ro và tìm cách ngăn chặn)
    return score if is_ai else -score

""" Hàm ước lượng
    Trả về điểm tổng của bàn cờ theo góc nhìn của AI:
      > 0 : AI đang có lợi
      < 0 : Người đang có lợi
        0 : Cân bằng
"""
def evaluate(board) -> int:
    total = 0
    size = board.size
    grid = board.grid

    # 4 hướng quét: (dr, dc)
    # Quét về 4 phía
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for dr, dc in directions:
        # Duyệt tọa độ từng hàng, từng cột trên bàn cờ
        for r in range(size):
            for c in range(size):
                cell = grid[r][c]
                if cell == EMPTY:       # Nếu mà ô kiểm tra là EMPTY thì bỏ qua để tiết kiệm thời gian
                    continue

                # Chỉ xét điểm bắt đầu (tránh tính lại chuỗi từ giữa)
                # Thuật toán chỉ đếm khi tọa độ (r, c) là điểm bắt đầu 
                # Mục đích: Tránh việc tính điểm trùng lặp cho cùng một chuỗi khi ta duyệt nhiều cell khác nhau.
                # Cách thực hiện: Nó lùi lại 1 bước theo hướng đang quét (pr, pc = r - dr, c - dc). Nếu ô
                # lùi lại này nằm trong bàn cờ và có cùng màu cờ với ô hiện tại, điều đó có nghĩa là ô (r, c)
                # đang nằm ở giữa hoặc cuối của một chuỗi đã được đếm trước đó rồi.
                pr, pc = r - dr, c - dc
                if (0 <= pr < size and 0 <= pc < size and
                        grid[pr][pc] == cell):
                    continue   # Ô trước cùng màu → không phải điểm bắt đầu 

                # Đếm độ dài chuỗi
                length = 0
                nr, nc = r, c       
                # Dùng vòng lặp while để tiến theo hướng (dr, dc)
                # Vòng lặp dừng lại khi đụng mép bàn cờ hoặc gặp ô trống / quân đối phương.
                while (0 <= nr < size and 0 <= nc < size and
                       grid[nr][nc] == cell):
                    length += 1
                    nr += dr
                    nc += dc        # Khi này, (nr, nc) là vị trí của ô ngay sau điểm kết thúc của chuỗi
        
                # Kiểm tra đầu mở
                # Đầu trước (br, bc): Là ô nằm ngay trước điểm bắt đầu (r, c). Nếu là ô trống, cộng 1 đầu mở.
                # Đầu sau (nr, nc): Là ô nằm ngay sau điểm kết thúc chuỗi (chính là tọa độ còn lưu lại từ vòng lặp đếm ở Bước 4). 
                # Nếu là ô trống, cộng 1 đầu mở.
                open_ends = 0
                # Đầu trước
                br, bc = r - dr, c - dc
                if (0 <= br < size and 0 <= bc < size and
                        grid[br][bc] == EMPTY):
                    open_ends += 1
                # Đầu sau
                if (0 <= nr < size and 0 <= nc < size and
                        grid[nr][nc] == EMPTY):
                    open_ends += 1

                # Tính toán tổng điểm cho ước lượng này
                total += _score_sequence(length, open_ends, cell == AI)

    return total