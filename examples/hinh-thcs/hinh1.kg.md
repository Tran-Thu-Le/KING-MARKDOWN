---
kg: 0.2
use: king/schema, king/style
---

Cùng knowledge graph với hinh2, hinh3; chỉ khác style. Ở đây: schema và style của hệ thống (use: king/schema, king/style).

# Hình tròn @hinh-tron-bai

@hinh-hoc-phang: Hình học phẳng
- meta: type=group

@duong-tron: Đường tròn
- meta: type=concept, role=Nạp
- content: Tập hợp các điểm cách điểm O cố định một khoảng R không đổi.
- link: part-of(hinh-hoc-phang)

@hinh-tron: Hình tròn
- meta: type=concept, role=Xuất, important=true
- content: Đường tròn cùng các điểm nằm bên trong nó. Diện tích S = πR².
- link: part-of(hinh-hoc-phang), needs(duong-tron)
