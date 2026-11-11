---
kg: 0.3
use:
- king/style
---

# Các nhà khoa học và quan hệ @nha-khoa-hoc

Đồ thị quan hệ (relation): bạn bè, vợ chồng, thầy trò, quê hương, giải thưởng. Mỗi `@link` là một loại quan hệ; có thể viết từ phía node nào cũng được nhờ `inverse`.

## Kiểu và quan hệ @kieu

@node Nguoi
- label: Người

@node Noi-chon
- label: Địa danh

@node Giai
- label: Giải thưởng

@link que-huong
- label: Quê hương
- inverse: nguoi-con

@link giai-thuong
- label: Đạt giải
- inverse: nguoi-dat-giai

@link ban-be
- label: Bạn bè
- from albert-einstein to (marie-curie, niels-bohr, max-planck)

Quan hệ hai chiều: chỉ cần viết một lần. Ở đây viết ngay trong khai báo, bằng `- from … to …`.

@link vo-chong
- label: Vợ / chồng

@link thay
- label: Thầy hướng dẫn
- inverse: hoc-tro
- dag: true

## Con người @con-nguoi

@node albert-einstein
- label: Albert Einstein
- type: Nguoi
- nam-sinh: 1879
- nobel: (vat-ly=1921)
- link que-huong: (ulm)
- link giai-thuong: (nobel-vat-ly)

Nobel 1921 cho hiệu ứng quang điện.

@node marie-curie
- label: Marie Curie
- type: Nguoi
- nam-sinh: 1867
- nobel: (vat-ly=1903, hoa-hoc=1911)
- link que-huong: (warszawa)
- link giai-thuong: (nobel-vat-ly, nobel-hoa-hoc)
- link vo-chong: (pierre-curie)

Người đầu tiên đạt hai giải Nobel, ở hai lĩnh vực khác nhau.

@node pierre-curie
- label: Pierre Curie
- type: Nguoi
- nam-sinh: 1859
- nobel: (vat-ly=1903)
- link que-huong: (paris)
- link giai-thuong: (nobel-vat-ly)

@node niels-bohr
- label: Niels Bohr
- type: Nguoi
- nam-sinh: 1885
- nobel: (vat-ly=1922)
- link que-huong: (copenhagen)
- link giai-thuong: (nobel-vat-ly)
- link thay: (ernest-rutherford)

Tranh luận nhiều năm với @albert-einstein về cơ học lượng tử, nhưng vẫn là bạn.

@node ernest-rutherford
- label: Ernest Rutherford
- type: Nguoi
- nam-sinh: 1871
- nobel: (hoa-hoc=1908)
- link que-huong: (new-zealand)
- link giai-thuong: (nobel-hoa-hoc)

@node max-planck
- label: Max Planck
- type: Nguoi
- nam-sinh: 1858
- nobel: (vat-ly=1918)
- link que-huong: (kiel)
- link giai-thuong: (nobel-vat-ly)

@node ngo-bao-chau
- label: Ngô Bảo Châu
- type: Nguoi
- nam-sinh: 1972
- link que-huong: (ha-noi)
- link giai-thuong: (fields)

Toán học không có giải Nobel; giải tương đương là Huy chương Fields (2010).

## Giải thưởng @giai

@node nobel-vat-ly
- label: Nobel Vật lý
- type: Giai

@node nobel-hoa-hoc
- label: Nobel Hóa học
- type: Giai

@node fields
- label: Huy chương Fields
- type: Giai

## Quê hương @noi-chon

@node ulm
- label: Ulm (Đức)
- type: Noi-chon

@node kiel
- label: Kiel (Đức)
- type: Noi-chon

@node warszawa
- label: Warszawa (Ba Lan)
- type: Noi-chon

@node paris
- label: Paris (Pháp)
- type: Noi-chon

@node copenhagen
- label: Copenhagen (Đan Mạch)
- type: Noi-chon

@node new-zealand
- label: New Zealand
- type: Noi-chon

@node ha-noi
- label: Hà Nội
- type: Noi-chon
- link nguoi-con: (ngo-bao-chau)
