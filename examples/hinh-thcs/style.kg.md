---
kg: 0.2
---

Màu viết bằng tên có sẵn: red, orange, yellow, green, teal, blue, purple, pink, brown, gray, black, white, lightblue, lightgreen, lightyellow, lightpink, lightgray (hoặc mã #rrggbb).

# Node

@hinh: Mọi hình
- meta: select="type=Hinh", html.shape=box, html.color=lightblue, html.border-color=blue

@goc: Tứ giác (gốc)
- meta: select="#tu-giac", html.color=lightgray, html.border-color=gray

@s-hinh-thang: Hình thang
- meta: select="#hinh-thang", html.color=lightblue, html.border-color=blue, html.border=2

@s-hinh-binh-hanh: Hình bình hành
- meta: select="#hinh-binh-hanh", html.color="#f1a2a2"

@vuong: Hình vuông
- meta: select="#hinh-vuong", html.shape=square, html.color="#f5f06b", html.border-color=orange, html.border=3, html.font-color=blue

# Bài Hình tròn (hinh2.kg.md): xanh lá, section khung đứt, concept elip, group chữ nhật vàng

@sec: Section
- meta: select="kind=section", html.shape=box, html.radius=0, html.color=white, html.border-color=green, html.dash=true

@concept: Khái niệm
- meta: select="type=Concept", html.shape=ellipse, html.color=lightgreen, html.border-color=green

@group: Nhóm
- meta: select="type=Group", html.shape=box, html.radius=4, html.color=lightyellow, html.border-color=orange

@quan-trong: Quan trọng
- meta: select="important=true", html.border=3, html.font-size=16

# Link

@l-specialize: Là trường hợp riêng của
- meta: select="link=specialize", html.color=green, html.width=2

@l-needs: Cần biết trước
- meta: select="link=needs", html.color=green, html.width=2

@l-part-of: Là phần của
- meta: select="link=part-of", html.color=orange, html.dash=true

# Node cụ thể

@s-hinh-thang-can
- meta: select="#hinh-thang-can", html.color="#51f565"
