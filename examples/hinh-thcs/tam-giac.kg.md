---
kg: 0.2
---

Schema và style viết ngay trong file này (mục # Schema, # Style), không cần use:.

@hinh-chung: Hình chung 
- meta: type=hinh


@tam-giac: Tam giác
- meta: type=hinh
- content: Hình gồm ba đoạn thẳng nối ba điểm không thẳng hàng. Tổng ba góc bằng 180°.
- link: specialize(hinh-chung)

@tam-giac-deu: Tam giác đều
- meta: type=hinh
- content: Tam giác có ba cạnh bằng nhau; mỗi góc bằng 60°.
- link: specialize(tam-giac)

@tam-giac-vuong: Tam giác vuông
- meta: type=hinh
- content: Tam giác có một góc vuông. Bình phương cạnh huyền bằng tổng bình phương hai cạnh góc vuông.
- link: specialize(tam-giac)
- show: none

@hinh-vuong: hinh-vuong

# Schema

@hinh: Hình
- meta: kind=type

@specialize: Là trường hợp riêng của
- meta: kind=link, dag=true, from=hinh, to=hinh

# Style

@s-hinh: Mọi hình
- meta: select="type=hinh", html.shape=triangle, html.size=30, html.color=lightgray, html.border-color=gray

@s-deu: Tam giác đều
- meta: select="#tam-giac-deu", html.color=lightgreen, html.border-color=green

@s-vuong: Tam giác vuông
- meta: select="#tam-giac-vuong", html.color=lightblue, html.border-color=blue

@l-specialize: Là trường hợp riêng của
- meta: select="link=specialize", html.color=gray, html.width=2


