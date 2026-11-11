# Plan v2c: KING Markdown 0.3 (cú pháp đã chốt)

Thay thế phần cú pháp của [plan-v2a.md](plan-v2a.md) và [plan-v2b.md](plan-v2b.md) ở những chỗ khác nhau. Parser chỉ viết bằng Python.

## 1. Block

| Block | Cú pháp |
|---|---|
| Section | `#` … `######` (Markdown) |
| Node | `@node tên` |
| Link | `@link tên` |

- Dòng mở block **không có `:` và không có nhãn**. Nhãn viết ở `- label:`, kiểu node viết ở `- type:`.
- **Tên, không phải ID.** Giống ngôn ngữ lập trình, `@node duong-tron` khai báo một **tên** (như tên biến), có phạm vi trong file đó. Không có khái niệm ID riêng. Tham chiếu tới node là dùng tên của nó (`- link needs: (duong-tron)`, `@duong-tron` trong nội dung). Từ file khác thì viết `module.tên`.
- **`- label:` chỉ là diễn nghĩa** (chữ hiển thị cho người đọc), không dùng để tham chiếu. Có thể bỏ; khi đó view hiện tên.
- **Văn bản dưới heading** (trước block `@` đầu tiên) là nội dung của chính section. Không sinh node riêng (đã chốt; thay cho plan-v2 mục 2.5).
- Section kết thúc trước heading cùng cấp hoặc cấp cao hơn, hoặc khi hết file.
- Block `@` kết thúc trước dòng `@` đầu dòng tiếp theo, trước heading, hoặc khi hết file.

## 2. Dòng trong block

| Dòng | Cú pháp |
|---|---|
| Thuộc tính | `- key: value` |
| Nhãn | `- label: …` |
| Kiểu node | `- type: concept` |
| Link trong node | `- link tên: (B, C)` |
| Chiều ngược (trong `@link`) | `- inverse: tên` |
| Link viết riêng (trong `@link`) | `- from A to (B, C)` |
| Nội dung | sau các dòng thuộc tính, cách một dòng trắng |

**Ký hiệu trong dòng:**
- `//` mở comment;
- `( )` cho List / Dict;
- `[ ]` cho Content;
- `"…"` cho chuỗi;
- `` `…` `` cho code.

**Kiểu dữ liệu:** Num, Str, Bool, None, List, Dict, Content.

## 3. Quy ước link

- Tên link là **danh từ**, đọc là "**tên** của A là B". Ví dụ `- link author: (nguyen-du)` đọc là "tác giả của truyện Kiều là Nguyễn Du".
- `- link <inverse>: X` nghĩa là link đi từ X tới node hiện tại. Graph chỉ lưu chiều gốc.
- Link trùng nhau được gộp lại. Ví dụ `author` khai ở một node và `works` khai ở node kia vẫn chỉ cho ra một cạnh.

## 4. Import

```markdown
---
kg: 0.3
use:
- king/schema.node: group-node, concept
- king/schema.link: part-of, needs
- king/style
---
```

- **Node type và link type phải được import rõ.** Dùng tên chưa import, ở `- type:` hay ở `- link tên:`, thì parser báo lỗi.
- **Attribute thì tự do**, viết `- key: value` nào cũng được.
- Để bắt lỗi gõ nhầm (ví dụ `- rol: "Nạp"`), parser **cảnh báo** khi một attribute chỉ xuất hiện đúng một lần trong file.

## 5. Ví dụ

```markdown
---
kg: 0.3
use:
- king/schema.node: group-node, concept
- king/schema.link: part-of, needs, author
- king/style
---

# Hình tròn

@node hinh-hoc-phang
- label: "Hình học phẳng"
- type: group-node          // node type

@node duong-tron
- label: "Đường tròn"
- type: concept             // type chuẩn
- role: "Nạp"
- link part-of: (hinh-hoc-phang)

Tập hợp các điểm cách điểm O cố định một khoảng R không đổi.

@node hinh-tron
- label: "Hình tròn"
- type: concept
- role: "Xuất"
- important: true
- link part-of: (hinh-hoc-phang)
- link needs: (duong-tron)

Đường tròn cùng các điểm nằm bên trong nó. Diện tích S = πR².

@link author
- label: Tác giả
- inverse: works

@node truyen-kieu
- label: Truyện Kiều
- year: 1820
- link author: (nguyen-du)

Truyện thơ lục bát, 3254 câu.

@node nguyen-du
- label: Nguyễn Du
- link works: (truyen-kieu)
```

## 6. Bảng màu (nền `#1E1E1E`)

| Đối tượng | Màu soạn thảo | Màu trên view (graph, book, tree, module) |
|---|---|---|
| Tên node (kể cả khi được tham chiếu) | `#E8D48A` vàng nhạt | graph: nền node `#E8D48A`, chữ `#1E1E1E`; book/tree/module: tiêu đề `#E8D48A` |
| Tên link (kể cả `inverse`) | `#A5ABB6` xám | graph: đường `#A5ABB6`, độ mờ 70%, nhãn nhỏ; book/tree/module: chữ `#A5ABB6` |
| Keyword (`@node`, `@link`, `link`, `from`, `to`) | `#C586C0` tím | không hiện; kiểu node hiện thành nhãn nhỏ `#C586C0` |
| Attribute key | `#9CDCFE` xanh nhạt | module/inspector: `#9CDCFE`; book: ẩn hoặc `#808080` |
| Type (Num, Str, Bool, None, List, Dict, Content) | `#4EC9B0` xanh ngọc | inspector: nhãn nhỏ `#4EC9B0` |
| Value (mọi giá trị và ngoặc `( ) [ ]`) | `#D4D4D4`; riêng Str `#CE9178` | chữ thường `#D4D4D4` |
| Comment `//` | `#6A9955` nghiêng | không hiện |
| Dấu câu `-` `:` `,` | `#808080` | không hiện |
| Nội dung node | tô theo Markdown/Typst | hiển thị đã render |

Chỉ còn bốn màu nổi: **vàng** cho node, **tím** cho keyword, **xanh nhạt** cho key, **xanh ngọc** cho type. Link và các phần còn lại để màu trung tính.

## 7. Đã chốt (2026-11-09, đã triển khai trên nhánh `v0.3`)

- **Escape:** chưa làm. `//` chỉ là comment khi đứng đầu dòng hoặc sau khoảng trắng, và không nằm trong `"…"` hay `` `…` ``.
- **`inverse`** là một attribute của `@link`, do người dùng viết. Khi xuất JSON, link viết theo tên `inverse` được đổi về chiều gốc.
- **Tên biến** (tên node / tên link) viết thường, nối bằng gạch. **Type** viết hoa chữ đầu (`Concept`, `Group`). `@node Concept` là khai báo node type.
- **Thuộc tính** của section hoặc node / link là các dòng `- ` ngay bên dưới dòng mở. Sau dòng trắng là nội dung.
- **Import:** `- king/schema.node: …` / `.link: …` chỉ lấy đúng các tên được liệt kê. Viết `- schema` (không có `.node` / `.link`) thì lấy mọi kiểu trong file.

## 8. Chưa chốt

1. **Khai báo kiểu.** Kế thừa bằng `<:`, chú thích kiểu bằng `::`. Bỏ `=` thì cần cú pháp mới, ví dụ `@node hinh <: node`.
2. **Node con `has`.** Viết thế nào, có kèm kiểu hay không (các phương án ở [plan-v2b.md](plan-v2b.md) mục 5).
3. **Escape** `@`, `#`, `//` khi nằm trong code fence hoặc trong URL (ví dụ `https://…`).
4. **Danh sách toán tử.** Gợi ý để sang 0.4.
5. **Import `inverse`.** Khi import `author` thì `works` có tự được import theo không? Đề xuất: có, vì nó là một phần của khai báo `author`.
6. **Hoa / thường của tên kiểu.** Bản gốc viết `Concept` nhưng import `concept`. Đề xuất: tên kiểu luôn viết thường, và so khớp có phân biệt hoa thường.
7. **`- label:` có cần ngoặc kép không?** Ví dụ có chỗ viết `"Hình học phẳng"`, có chỗ viết `Truyện Kiều`. Đề xuất: không bắt buộc; chỉ cần ngoặc kép khi chuỗi có `,` hoặc `//`.
8. **Ranh giới thuộc tính / nội dung.** Một dòng `- …` ngay sau dãy thuộc tính mà không có dòng trắng thì sao? Đề xuất: mọi dòng `- ` liền nhau đều là thuộc tính; dòng nào sai cú pháp thì báo lỗi, không tự chuyển thành nội dung.
