---
kg: 0.3
use:
- schema
- style
---

Các hình tứ giác (Toán 8). Mũi tên specialize đi từ hình riêng tới hình chung.

@node tu-giac
- label: Tứ giác
- type: Hinh

Hình gồm bốn đoạn thẳng nối tiếp, không có hai đoạn nào cùng nằm trên một đường thẳng. Tổng bốn góc bằng 360°.

@node tu-giac-loi
- label: Tứ giác lồi
- type: Hinh
- link specialize: (tu-giac)

Tứ giác luôn nằm về một phía của đường thẳng chứa bất kỳ cạnh nào.

@node hinh-thang
- label: Hình thang
- type: Hinh
- link specialize: (tu-giac-loi)

Tứ giác lồi có hai cạnh đối song song.

@node hinh-thang-can
- label: Hình thang cân
- type: Hinh
- link specialize: (hinh-thang)

Hình thang có hai góc kề một đáy bằng nhau.

@node hinh-binh-hanh
- label: Hình bình hành
- type: Hinh
- link specialize: (hinh-thang)

Tứ giác có các cạnh đối song song.

@node hinh-chu-nhat
- label: Hình chữ nhật
- type: Hinh
- link specialize: (hinh-binh-hanh, hinh-thang-can)

Tứ giác có bốn góc vuông.

@node hinh-thoi
- label: Hình thoi
- type: Hinh
- link specialize: (hinh-binh-hanh)

Tứ giác có bốn cạnh bằng nhau.

@node hinh-vuong
- label: Hình vuông
- type: Hinh
- link specialize: (hinh-chu-nhat, hinh-thoi)

Tứ giác có bốn góc vuông và bốn cạnh bằng nhau.
