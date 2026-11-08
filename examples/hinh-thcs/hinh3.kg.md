---
kg: 0.2
---

Cùng knowledge graph với hinh1, hinh2; chỉ khác style. Ở đây: schema và style viết ngay trong file (# Schema, # Style), không cần use:.

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

# Schema

@concept: Khái niệm
- meta: kind=type, allow="role, important"

@group: Nhóm
- meta: kind=type, allow="important"

@role: Vai trò
- meta: kind=key, values="Nạp | Xuất", required=true

@important: Quan trọng
- meta: kind=key, value=bool

@part-of: Là phần của
- meta: kind=link, dag=true, to=group

@needs: Cần biết trước
- meta: kind=link, dag=true

# Style

Tông tím: section chữ nhật tím nhạt, concept hình thoi, group chữ nhật bo góc lớn, link tím.

@s-section: Section
- meta: select="kind=section", html.shape=box, html.radius=0, html.color=lavender, html.border-color=purple

@s-concept: Khái niệm
- meta: select="type=concept", html.shape=diamond, html.size=28, html.color=plum, html.border-color=purple

@s-group: Nhóm
- meta: select="type=group", html.shape=box, html.radius=18, html.color=thistle, html.border-color=purple, html.border=2

@s-quan-trong: Quan trọng
- meta: select="important=true", html.color=orchid, html.border=3

@l-all: Mọi link
- meta: select="link", html.color=purple, html.width=2

@l-part-of: Là phần của
- meta: select="link=part-of", html.dash=true, html.arrows=none
