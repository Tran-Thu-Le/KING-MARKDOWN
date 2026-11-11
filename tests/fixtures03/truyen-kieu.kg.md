---
kg: 0.3
---

# Văn học

Các tác phẩm và tác giả.

@link author
- label: Tác giả
- inverse: works

@node truyen-kieu
- label: Truyện Kiều
- year: 1820
- link author: (nguyen-du)

Truyện thơ lục bát, 3254 câu.

@node nguyen-du
- label: Nguyễn Du
- link works: (truyen-kieu)

@node ho-xuan-huong
- label: Hồ Xuân Hương

@node thi-sinh
- label: Thơ Nôm

@link wrote
- label: Viết
- from (nguyen-du, ho-xuan-huong) to thi-sinh
