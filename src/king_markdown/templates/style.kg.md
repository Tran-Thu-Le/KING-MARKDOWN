---
kg: 0.2
---

Style hệ thống (use: king/style). Định dạng style giữ cú pháp v0.2 (đóng băng ở 0.3).
Bảng màu 0.3, nền trang #1E1E1E: node vàng nhạt #E8D48A, link xám #A5ABB6 mờ 70%.
Trên Graph mọi nhãn nằm dưới hình; node thường là hình elip.

Hình thức chuẩn của một node: mỗi loại node ghi đủ năm màu.

| Khóa | Vai trò |
|---|---|
| html.color | nền |
| html.border-color | viền |
| html.font-color | chữ chính nằm trên nền node (vd. trong hình tròn của Module) |
| html.label-color | nhãn nằm ngoài hình, trên nền trang (Graph, tên nhóm trong Module) |
| html.sub-color | chữ phụ: kiểu node, "+n con" |

Thiếu font-color thì chữ tự đổi trắng / đen theo độ sáng của nền.

# Theo loại

@sec: Section
- meta: select="kind=section", html.shape=box, html.radius=0, html.color=#3A3D41, html.border-color=#A5ABB6, html.font-color=#FFFFFF, html.label-color=#FFFFFF, html.sub-color=#A5ABB6

@nod: Node
- meta: select="kind=node", html.shape=ellipse, html.color=#E8D48A, html.border-color=#C9B66E, html.font-color=#1E1E1E, html.label-color=#E8D48A, html.sub-color=#C586C0

@nhom: Nhóm node
- meta: select="type=Group", html.shape=box, html.radius=10, html.color=#2D2D30, html.border-color=#E8D48A, html.border=2, html.font-color=#FFFFFF, html.label-color=#FFFFFF, html.sub-color=#C586C0

@ext: Node import
- meta: select="kind=external", html.shape=ellipse, html.color=#E8D48A, html.border-color=#C9B66E, html.font-color=#1E1E1E, html.label-color=#E8D48A, html.sub-color=#C586C0, html.dash=true

# Theo trạng thái

@cho-ai: Chờ AI viết
- meta: select="ask", html.dash=true

@an: Ẩn khỏi sách
- meta: select="show=none", typst.hide=true, html.opacity=0.5

@quan-trong: Quan trọng
- meta: select="important=true", html.border=3

# Link

@l-all: Mọi link
- meta: select="link", html.color=#A5ABB6, html.opacity=0.7, html.width=1.5

@l-contains: Cạnh chứa (section → node)
- meta: select="link=contains", html.color=#A5ABB6, html.dash=true, html.opacity=0.35, html.width=1

@l-mention: Tham chiếu @
- meta: select="link=mention", html.color=#A5ABB6, html.dash=true, html.opacity=0.6, html.width=1
