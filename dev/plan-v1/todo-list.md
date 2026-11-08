# Todo list

## Đồng bộ kiểu dữ liệu với Typst

Mục tiêu: giá trị trong `.kg.md` (nhất là `meta`) dùng đúng các kiểu dữ liệu của Typst, để khi chuyển `.kg.md` sang Typst thì mỗi giá trị đổi thẳng sang một giá trị Typst, không phải đoán.

### Kiểu giá trị

| Loại | Kiểu | Viết trong `.kg.md` | Sang Typst |
|---|---|---|---|
| Đơn | Num | `level=3`, `ratio=0.5` | `3`, `0.5` (int / float) |
| Đơn | Bool | `important=true` | `true` |
| Đơn | Str | `role=Nạp`, `title="Đạo hàm, tích phân"` | `"Nạp"` |
| Đơn | None | `parent=none` | `none` |
| Phức | List | `tags=(dao-ham, tich-phan)` | `("dao-ham", "tich-phan")` |
| Phức | Dict | `size=(w: 3, h: 2)` | `(w: 3, h: 2)` |
| Phức | Content | `note=[Đây là *nội dung* có $x^2$]` | `[Đây là *nội dung* có $x^2$]` |

Ví dụ một node:

```markdown
@tich-phan: Tích phân
- meta: type=concept, level=2, important=true, parent=none, tags=(giai-tich, lop-12), size=(w: 3, h: 2)
- content: [Diện tích dưới đường cong $y = f(x)$ trên đoạn $[a, b]$:
  $ integral_a^b f(x) dif x $]
```

### Content `[]` là môi trường Typst

- Khi chuyển `.kg.md` sang Typst, phần trong `[ ... ]` (của `content`, `ask`, hay một giá trị meta dạng Content) phải được **đọc như môi trường Typst**: giữ nguyên markup Typst (`*đậm*`, `_nghiêng_`, `$công thức$`, `#hàm(...)`), không coi là Markdown hay chuỗi thường.
- Ví dụ khi xuất node trên sang Typst:

  ```typst
  #node(
    id: "tich-phan",
    title: "Tích phân",
    meta: (type: "concept", level: 2, important: true, parent: none,
           tags: ("giai-tich", "lop-12"), size: (w: 3, h: 2)),
  )[Diện tích dưới đường cong $y = f(x)$ trên đoạn $[a, b]$:
    $ integral_a^b f(x) dif x $]
  ```

### Hiện trạng cần sửa (parser v0.2)

- `parse_value()` chỉ nhận `true` / `false`, số nguyên, số thực và chuỗi; chưa có `none`, List, Dict, Content.
- `split_top()` tách meta theo dấu phẩy và chỉ bỏ qua dấu phẩy trong `"..."`; cần bỏ qua cả dấu phẩy nằm trong `( )` và `[ ]`, để `tags=(a, b)` không bị cắt đôi.
- Nội dung `[ ... ]` của `content` / `ask` hiện bị bỏ ngoặc khi lưu, không còn dấu hiệu nó là Content Typst. Cần giữ thông tin này trong JSON (ví dụ `"content": {"typst": "..."}` hoặc một cờ riêng) để bước xuất Typst biết đường đọc nguyên văn.
- Bên trong `[ ... ]` có `$...$`, `#...`, `//` của Typst: parser không được cắt comment, cũng không được coi `@` trong đó là tham chiếu khi đã ở chế độ Typst (cần quyết định).

### Việc cần làm

- [ ] Chốt cú pháp 7 kiểu trong `docs/documentation.kg.md` (mục Fields / Built-in meta).
- [ ] `parse_value()`: thêm `none`, List `( )`, Dict `(:)`, Content `[ ]`; đọc lồng nhau (List trong Dict…).
- [ ] `split_top()` / `parse_meta()`: tôn trọng ngoặc `( )`, `[ ]` và chuỗi `"..."`.
- [ ] JSON đầu ra: giữ kiểu của từng giá trị (Content khác Str).
- [ ] Schema: `value=num|bool|str|none|list|dict|content` thay cho `bool|int|number|text` hiện tại (giữ tên cũ làm bí danh).
- [ ] `format_meta()` (editor ghi ngược meta): viết lại đúng 7 kiểu.
- [ ] Xuất Typst: `king typst file.kg.md` → `.typ`, Content `[ ]` chép nguyên văn như markup Typst; kết hợp `typst.*` trong style.
- [ ] Tô màu khung sửa: phân biệt Content `[ ]` (môi trường Typst) với chuỗi thường.
- [ ] Test: mỗi kiểu một fixture, cùng các trường hợp lồng nhau và lỗi cú pháp (thiếu ngoặc đóng).
