---
kg: 0.2
---

# Theo loại

@sec: Section
- meta: select="kind=section", html.shape=box, html.color="#e8eaf6"

@nod: Node
- meta: select="kind=node", html.shape=ellipse, html.color="#e0f2f1"

@ext: Node import
- meta: select="kind=external", html.color="#f5f5f5", html.dash=true

# Theo meta

@nap: Vai trò Nạp
- meta: select="role=Nạp", typst.frame=khung-nap, html.color="#e8f5e9", html.border-color="#2e7d32"

@xuat: Vai trò Xuất
- meta: select="role=Xuất", typst.frame=khung-xuat, html.color="#ffebee", html.border-color="#c62828"

@nhom: Nhóm
- meta: select="type=group", html.color="#fff8e1"

@cho-ai: Chờ AI viết
- meta: select="ask", html.dash=true

@an: Ẩn khỏi sách
- meta: select="show=none", typst.hide=true, html.opacity=0.5

@quan-trong: Quan trọng
- meta: select="important=true", html.border=3

# Node cụ thể

@s-tich-phan
- meta: select="#tich-phan", html.shape=circle

# Link

@l-all: Mọi link (màu: mỗi loại link một màu riêng, đặt màu bằng select="link=loại")
- meta: select="link", html.width=1

@l-contains: Cạnh chứa
- meta: select="link=contains", html.color="#bbbbbb", html.dash=true

@l-contain: Chứa (meta contain)
- meta: select="link=contain", html.color="#8d6e63", html.width=2

@l-mention: Tham chiếu @
- meta: select="link=mention", html.color="#9e9e9e", html.dash=true

@l-needs: Cần biết trước
- meta: select="link=needs", html.color="#c62828", html.width=2
