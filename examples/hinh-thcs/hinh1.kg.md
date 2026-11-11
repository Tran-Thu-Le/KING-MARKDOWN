---
kg: 0.3
use:
- king/schema.node: Concept, Group
- king/schema.link: part-of, needs
- king/style:
---

Cùng knowledge graph với hinh2, hinh3; chỉ khác style. Ở đây: schema và style của hệ thống (import từ king/schema, style king/style).

# Hình tròn @hinh-tron-bai



@link truong-hop-dac-biet 
- label: Trường hợp đặc biệt của 
- type: directed 
- sublinks: abc, def, ghk


@node hinh-hoc-phang
- label: Hình học phẳng
- type: Group

@node duong-tron
- label: Đường tròn
- type: Concept
- role: Nạp
- link part-of: (hinh-hoc-phang)
- content: [Đây mới chính xác là nội dung của của node duong-tron]

Còn bên dưới đây là nội dung của file. Tức khu vực này là một node có `type: Content`. 

@node hinh-tron
- label: Hình tròn
- type: Concept
- role: Xuất
- important: true
- link part-of: (hinh-hoc-phang)
- link needs: (duong-tron)

Đường tròn cùng các điểm nằm bên trong nó. Diện tích $S = \pi R^2$.
