---
kg: 0.2
---

Style hệ thống (use: king/style; editor cũng chép file này sang thư mục mới chưa có style).
Cùng bộ màu với khung sửa văn bản: section xanh dương, node và node import vàng nhạt, link cam.
Trên Graph mọi nhãn nằm dưới hình; node thường là hình elip.

# Theo loại

@sec: Section
- meta: select="kind=section", html.shape=box, html.radius=0, html.color=lightblue, html.border-color=dodgerblue

@nod: Node
- meta: select="kind=node", html.shape=ellipse, html.color=lightyellow, html.border-color=goldenrod

@nhom: Nhóm node
- meta: select="type=group", html.shape=box, html.radius=10, html.color=lightyellow, html.border-color=goldenrod, html.border=2

@ext: Node import
- meta: select="kind=external", html.shape=ellipse, html.color=lightyellow, html.border-color=goldenrod, html.dash=true

# Theo trạng thái

@cho-ai: Chờ AI viết
- meta: select="ask", html.dash=true

@an: Ẩn khỏi sách
- meta: select="show=none", typst.hide=true, html.opacity=0.5

@quan-trong: Quan trọng
- meta: select="important=true", html.border=3

# Link

@l-all: Mọi link
- meta: select="link", html.color=orange, html.width=1.5

@l-contains: Cạnh chứa (section → node)
- meta: select="link=contains", html.color=orange, html.dash=true, html.opacity=0.4, html.width=1

@l-mention: Tham chiếu @
- meta: select="link=mention", html.color=orange, html.dash=true, html.opacity=0.7, html.width=1
