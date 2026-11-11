---
kg: 0.3
use:
- schema
- style
---

Cùng knowledge graph với hinh1, hinh3; chỉ khác style. Ở đây: schema.kg.md và style.kg.md của thư mục hiện tại (use: schema, style).

# Hình tròn @hinh-tron-bai

@node hinh-hoc-phang
- label: Hình học phẳng
- type: Group

@node duong-tron
- label: Đường tròn
- type: Concept
- role: Nạp
- link part-of: (hinh-hoc-phang)

Tập hợp các điểm cách điểm O cố định một khoảng R không đổi.

@node hinh-tron
- label: Hình tròn
- type: Concept
- role: Xuất
- important: true
- link part-of: (hinh-hoc-phang)
- link needs: (duong-tron)

Đường tròn cùng các điểm nằm bên trong nó. Diện tích S = πR².
