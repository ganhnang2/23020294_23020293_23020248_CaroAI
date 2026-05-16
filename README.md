# Cờ Caro AI – Minimax & Alpha-Beta Pruning

## Cấu trúc thư mục

```
caro_AI/
├── main.py             # Giao diện tkinter + điểm khởi động
└── src/
    ├── __init__.py
    ├── ai.py           # Thuật toán Minimax & Alpha-Beta
    ├── benchmark.py    # So sánh hai thuật toán (Level 3)
    ├── board.py        # Biểu diễn bàn cờ, luật chơi, sinh nước đi
    └── evaluate.py     # Hàm đánh giá trạng thái
```

## Cài đặt

```bash
# Không cần cài thêm thư viện ngoài (tkinter có sẵn trong Python)
python --version   # Cần Python >= 3.10
```

## Chạy chương trình

```bash
# Chơi game với giao diện đồ họa
python main.py

# Chạy benchmark so sánh hai thuật toán
python -m src.benchmark
```

## Cách chơi

| Hành động | Mô tả |
|-----------|-------|
| Click ô bàn cờ | Đặt quân X |
| Người (X) / Máy (O) | Lựa chọn phía đi đầu tiên |
| Nút `🔄 Chơi lại` | Bắt đầu ván mới |
| `Minimax / Alpha-Beta` | Chọn thuật toán AI |
| `−` / `+` | Giảm/tăng độ sâu tìm kiếm |

## Thông số mặc định

- Bàn cờ: 15 × 15
- Luật thắng: 4 quân liên tiếp (ngang / dọc / chéo)
- Độ sâu mặc định: 3
- Thuật toán mặc định: Alpha-Beta
