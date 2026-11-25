---
kg: 0.3
use:
- schema
- style
import: math, tin-hoc, lop11.tiep-tuyen
---

# Bài 1 Python cơ bản @bai-1

## Python

chưa có nội dung here.

## Colab

@node giao-dien
- label: Giao diện Colab
- type: Concept
- role: Nạp
- important: true
- ask: Tách thành các node con: thanh dọc, thanh ngang, file, AI.
- link export: (bai-1)

## Toán

@node duoi-vi-phan
- label: Đạo hàm riêng
- type: Concept
- link part-of: (giai-tich)

@node giai-tich
- label: Giải tích
- type: Group
- ask: cần bao nhiêu khái niệm con
- show: none

@node dao-ham
- label: Đạo hàm
- type: Concept
- role: Nạp
- link part-of: (giai-tich)

Đạo hàm có liên hệ với @tiep-tuyen. Xem thêm https://vi.wikipedia.org

@node tich-phan
- label: Tích phân hàm 1 biến
- type: Concept
- role: Xuất
- ask: Giải thích trực quan, nối với @dao-ham.
- link part-of: (giai-tich)
- link needs: (dao-ham, math.gioi-han)

@node to-hop
- label: Tổ hợp
- type: Concept
