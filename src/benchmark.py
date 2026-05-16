"""
benchmark.py - Level 3: So sánh Minimax vs Alpha-Beta trên nhiều trạng thái

Cách chạy:
    python -m src.benchmark

Kết quả được in ra console và lưu vào benchmark_results.txt
"""

from .board import Board, HUMAN, AI, EMPTY
from .ai import get_best_move_minimax, get_best_move_alphabeta


# ─── Định nghĩa 6 trạng thái kiểm thử ───────────────────────────────────────

def build_state_empty() -> Board:
    """Trạng thái 1: Bàn cờ gần trống (2 quân)"""
    b = Board(15)
    b.place(7, 7, HUMAN)
    b.place(7, 8, AI)
    return b


def build_state_midgame() -> Board:
    """Trạng thái 2: Giữa ván, nhiều quân hai bên"""
    b = Board(15)
    moves = [
        (7, 7, HUMAN), (7, 8, AI),
        (6, 7, HUMAN), (8, 8, AI),
        (6, 8, HUMAN), (6, 9, AI),
        (5, 8, HUMAN), (5, 9, AI),
        (8, 7, HUMAN), (9, 9, AI),
    ]
    for r, c, p in moves:
        b.place(r, c, p)
    return b


def build_state_ai_can_win() -> Board:
    """Trạng thái 3: AI có thể thắng ngay (3 quân liên tiếp, còn 1 ô)"""
    b = Board(15)
    b.place(5, 5, HUMAN); b.place(7, 7, AI)
    b.place(5, 6, HUMAN); b.place(7, 8, AI)
    b.place(5, 9, HUMAN); b.place(7, 9, AI)
    # AI có 3 quân: (7,7),(7,8),(7,9) → đánh (7,10) là thắng
    return b


def build_state_block_human() -> Board:
    """Trạng thái 4: Người sắp thắng, AI phải chặn"""
    b = Board(15)
    b.place(7, 5, HUMAN); b.place(3, 3, AI)
    b.place(7, 6, HUMAN); b.place(3, 4, AI)
    b.place(7, 7, HUMAN); b.place(3, 5, AI)
    # Người có 3 quân: (7,5),(7,6),(7,7) → AI phải đánh (7,4) hoặc (7,8)
    return b


def build_state_mutual_attack() -> Board:
    """Trạng thái 5: Hai bên đều có cơ hội tấn công"""
    b = Board(15)
    moves = [
        (7, 7, HUMAN), (8, 8, AI),
        (7, 8, HUMAN), (8, 7, AI),
        (7, 9, HUMAN), (8, 6, AI),
        (6, 6, HUMAN), (9, 9, AI),
    ]
    for r, c, p in moves:
        b.place(r, c, p)
    return b


def build_state_crowded() -> Board:
    """Trạng thái 6: Bàn cờ đông quân, nhiều nước đi hợp lệ"""
    b = Board(15)
    import itertools, random
    random.seed(42)
    positions = [(r, c) for r in range(4, 12) for c in range(4, 12)]
    random.shuffle(positions)
    for i, (r, c) in enumerate(positions[:20]):
        player = HUMAN if i % 2 == 0 else AI
        b.place(r, c, player)
        if b.check_win(HUMAN) or b.check_win(AI):
            b.undo(r, c)   # Bỏ qua nước tạo ra thắng để tiếp tục
    return b


STATES = [
    ("1. Bàn cờ gần trống",             build_state_empty),
    ("2. Giữa ván",                      build_state_midgame),
    ("3. AI có thể thắng ngay",          build_state_ai_can_win),
    ("4. Người sắp thắng, AI phải chặn", build_state_block_human),
    ("5. Hai bên đều tấn công",          build_state_mutual_attack),
    ("6. Bàn cờ đông quân",              build_state_crowded),
]

DEPTHS = [1, 2, 3]


# ─── Chạy benchmark ──────────────────────────────────────────────────────────

def run_benchmark():
    lines = []

    def log(text=""):
        print(text)
        lines.append(text)

    log("=" * 80)
    log("BENCHMARK: Minimax vs Alpha-Beta Pruning")
    log("=" * 80)

    header = (f"{'Trạng thái':<35} {'Depth':>5} "
              f"{'MM States':>10} {'MM ms':>8} "
              f"{'AB States':>10} {'AB ms':>8} "
              f"{'Giảm %':>8} {'Same?':>6}")
    log(header)
    log("-" * 80)

    for state_name, builder in STATES:
        for depth in DEPTHS:
            board_mm = builder()   # Bàn cờ cho Minimax
            board_ab = builder()   # Bàn cờ riêng cho Alpha-Beta

            mm = get_best_move_minimax(board_mm, depth)
            ab = get_best_move_alphabeta(board_ab, depth)

            same_move = "✓" if mm["move"] == ab["move"] else "✗"
            reduction = 0
            if mm["states_visited"] > 0:
                reduction = (1 - ab["states_visited"] / mm["states_visited"]) * 100

            row = (f"{state_name:<35} {depth:>5} "
                   f"{mm['states_visited']:>10,} {mm['time_ms']:>8.1f} "
                   f"{ab['states_visited']:>10,} {ab['time_ms']:>8.1f} "
                   f"{reduction:>7.1f}% {same_move:>6}")
            log(row)

        log()

    log("=" * 80)
    log("Ghi chú:")
    log("  MM States / AB States: số trạng thái đã xét")
    log("  Giảm %   : % trạng thái Alpha-Beta giảm so với Minimax")
    log("  Same?    : Alpha-Beta và Minimax chọn cùng nước đi không")

    with open("benchmark_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\nKết quả đã lưu vào benchmark_results.txt")


if __name__ == "__main__":
    run_benchmark()