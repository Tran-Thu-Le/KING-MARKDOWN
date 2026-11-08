---
kg: 0.2
use: schema, style
---

Các hình tứ giác (Toán 8). Mũi tên specialize đi từ hình riêng tới hình chung.

@tu-giac: Tứ giác
- meta: type=hinh
- content: Hình gồm bốn đoạn thẳng nối tiếp, không có hai đoạn nào cùng nằm trên một đường thẳng. Tổng bốn góc bằng 360°.

@tu-giac-loi: Tứ giác lồi
- meta: type=hinh
- content: Tứ giác luôn nằm về một phía của đường thẳng chứa bất kỳ cạnh nào.
- link: specialize(tu-giac)

@hinh-thang: Hình thang
- meta: type=hinh
- content: Tứ giác lồi có hai cạnh đối song song.
- link: specialize(tu-giac-loi)

@hinh-thang-can: Hình thang cân
- meta: type=hinh
- content: Hình thang có hai góc kề một đáy bằng nhau.
- link: specialize(hinh-thang)

@hinh-binh-hanh: Hình bình hành
- meta: type=hinh
- content: Tứ giác có các cạnh đối song song.
- link: specialize(hinh-thang)

@hinh-chu-nhat: Hình chữ nhật
- meta: type=hinh
- content: Tứ giác có bốn góc vuông.
- link: specialize(hinh-binh-hanh, hinh-thang-can)

@hinh-thoi: Hình thoi
- meta: type=hinh
- content: Tứ giác có bốn cạnh bằng nhau.
- link: specialize(hinh-binh-hanh)

@hinh-vuong: Hình vuông
- meta: type=hinh
- content: Tứ giác có bốn góc vuông và bốn cạnh bằng nhau.
- link: specialize(hinh-chu-nhat, hinh-thoi)
