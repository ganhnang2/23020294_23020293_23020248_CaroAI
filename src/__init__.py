# Import các thành phần cốt lõi từ các file module nội bộ
from .board import Board, EMPTY, HUMAN, AI, WIN_LENGTH, BOARD_SIZE
from .evaluate import evaluate
from .ai import minimax, get_best_move_minimax, alpha_beta, get_best_move_alphabeta
from .benchmark import run_benchmark

# Định nghĩa các thành phần được phép export ra ngoài khi dùng: from core import *
__all__ = [
    "Board", "EMPTY", "HUMAN", "AI", "WIN_LENGTH", "BOARD_SIZE",                        # module board.py
    "evaluate",                                                                         # module evaluate.py
    "minimax", "get_best_move_minimax", "alpha_beta", "get_best_move_alphabeta",        # module ai.py
    "run_benchmark"                                                                     # module benchmark.py
]