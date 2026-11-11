---
kg: 0.3
use:
- king/schema.node: Group, Concept
- king/schema.link: part-of, needs
- king/style
---

# Hình tròn

@node hinh-hoc-phang
- label: "Hình học phẳng"
- type: Group          // node type

@node duong-tron
- label: "Đường tròn"
- type: Concept        // type chuẩn
- role: "Nạp"
- link part-of: (hinh-hoc-phang)

Tập hợp các điểm cách điểm O cố định một khoảng R không đổi.

@node hinh-tron
- label: "Hình tròn"
- type: Concept
- role: "Xuất"
- important: true
- link part-of: (hinh-hoc-phang)
- link needs: (duong-tron)

Đường tròn cùng các điểm nằm bên trong nó. Diện tích S = πR².
Xem @duong-tron.
