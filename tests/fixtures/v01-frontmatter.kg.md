---
kg: 0.1
node: content, meta, link, show, ask
link: export, part-of, needs
import: [thpt, toan, tin]
from: { lop11: [tiep-tuyen] }
---

# Bài 1 Python cơ bản @bai-1

## Python

## Colab

@giao-dien: Giao diện Colab
- meta: type=concept, important=true
- ask: Tách thành các node con: thanh dọc, thanh ngang, file, AI.
- link: export()            // xuất ra bai-1

## Toán

@giai-tich: Giải tích
- meta: type=group
- show: none

@dao-ham: Đạo hàm
- content: Đạo hàm có liên hệ với @tiep-tuyen.
- link: part-of(giai-tich)


@tich-phan
- content: Ai giúp giải thích 
- link: part-of(giai-tich), needs(dao-ham), generates!(dao-ham), needs*(dai-so) // đã ở trong code thì ref variable chỉ cần gọn thẳng tên. needs*= không cần đại số! còn needs!= đại số cần tích phân. 
