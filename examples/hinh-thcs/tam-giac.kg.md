---
kg: 0.3
use:
- tam-giac-style
---

Schema viết ngay trong file này (mục # Schema). Style ở tam-giac-style.kg.md (định dạng style đóng băng ở 0.3).

@node hinh-chung
- label: Hình chung
- type: Hinh

@node tam-giac
- label: Tam giác
- type: Hinh
- link specialize: (hinh-chung)

Hình gồm ba đoạn thẳng nối ba điểm không thẳng hàng. Tổng ba góc bằng 180°.

@node tam-giac-deu
- label: Tam giác đều
- type: Hinh
- link specialize: (tam-giac)

Tam giác có ba cạnh bằng nhau; mỗi góc bằng 60°.

@node tam-giac-vuong
- label: Tam giác vuông
- type: Hinh
- show: none
- link specialize: (tam-giac)

Tam giác có một góc vuông. Bình phương cạnh huyền bằng tổng bình phương hai cạnh góc vuông.

@node hinh-vuong
- label: Hình vuông
- type: Hinh

# Schema

@node Hinh
- label: Hình

@link specialize
- label: Là trường hợp riêng của
- dag: true
