---
kg: 0.2
---

Style riêng của hinh3.kg.md (định dạng style giữ cú pháp v0.2 ở KING 0.3).

# Style

Tông tím: section chữ nhật tím nhạt, concept hình thoi, group chữ nhật bo góc lớn, link tím.

@s-section: Section
- meta: select="kind=section", html.shape=box, html.radius=0, html.color=lavender, html.border-color=purple

@s-concept: Khái niệm
- meta: select="type=Concept", html.shape=diamond, html.size=28, html.color=plum, html.border-color=purple

@s-group: Nhóm
- meta: select="type=Group", html.shape=box, html.radius=18, html.color=thistle, html.border-color=purple, html.border=2

@s-quan-trong: Quan trọng
- meta: select="important=true", html.color=orchid, html.border=3

@l-all: Mọi link
- meta: select="link", html.color=purple, html.width=2

@l-part-of: Là phần của
- meta: select="link=part-of", html.dash=true, html.arrows=none
