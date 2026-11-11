# Plan v3: triển khai KING Markdown 0.3 theo plan-v2c

Nguồn cú pháp: [../plan-v2/plan-v2c.md](../plan-v2/plan-v2c.md). Code hiện tại: **v0.2** (tag `v0.2`).

**Ưu tiên số 1:** cú pháp chắc (parser và test).
**Ưu tiên số 2:** bốn view Graph, Tree, Book, Module hiển thị ổn.
Việc nào không phục vụ hai ưu tiên này thì đóng băng.

## Tiến độ (2026-11-09, nhánh `v0.3`)

| Step | Trạng thái |
|---|---|
| 0 | xong: nhánh `v0.3`; Inspector ẩn mặc định và chỉ đọc; `op()` không gửi gì (`FROZEN`); công cụ sửa trên Graph bị ẩn |
| 1 | xong: `values.py` + `tests/test_values.py` |
| 2–3 | xong: `parser.py` mới (cắt block + ngữ nghĩa) + `tests/test_parser.py`; parser cũ thành `legacy.py` |
| 4 | xong: `templates/schema.kg.md` viết bằng 0.3; `style.kg.md` giữ v0.2, đổi sang bảng màu mới |
| 5 | xong: examples, docs và README sang 0.3 (`dev/tools/migrate_02_03.py`); style viết trong file (hinh3, tam-giac) tách ra `*-style.kg.md` |
| 6 | xong: tô màu khung sửa theo 0.3; Graph có nhãn kiểu tím; Tree / Book theo bảng màu mới |
| 6+ | xong (2026-11-10): hai vùng có tab và nút +, Ctrl+S, `hide`, lưới Graph, giữ vị trí node, Tree hiện type/role output, chuẩn 5 màu node, kiểu Example/Warning, dọn examples |
| 7 | còn: merge vào `main`, tag `v0.3` (chờ anh duyệt) |
| tiếp | [plan-v3b.md](plan-v3b.md): A (bố cục cây trái → phải cho Graph) xong 2026-11-11; B diagnostics chuẩn LSP rồi `king lsp` |

## 1. So khớp hiện trạng (v0.2) với plan-v2c

| Chủ đề | v0.2 (code hiện tại) | plan-v2c | Mức đổi |
|---|---|---|---|
| Mở node | `@id: Tiêu đề` (`RE_NODE`) | `@node tên` (tên như biến, phạm vi file; không có ID riêng), diễn nghĩa ở `- label:` | lớn |
| Kiểu node | `- meta: type=concept` | `- type: concept` | vừa |
| Thuộc tính | 5 trường cố định (`FIELDS`), dữ liệu khác nhét vào `- meta: k=v` | `- key: value` tự do | lớn |
| Nội dung | `- content: …` hoặc `[ … ]` | văn bản sau dãy thuộc tính, cách một dòng trắng | lớn |
| Link trong node | `- link: part-of(x), needs(y)` | `- link part-of: (x)` | vừa |
| Khai báo link | node trong schema với `meta: kind=link` | `@link tên`, `- label:`, `- inverse:` | lớn |
| Link viết riêng | không có | `- from A to (B, C)` trong `@link` | mới |
| Chiều ngược, gộp link trùng | không có | `inverse`, gộp cạnh trùng | mới |
| Import | `use: king/schema, king/style` (một dòng) | danh sách YAML, `king/schema.node: a, b` | vừa |
| Kiểm tra kiểu | schema `kind=type/key/link`, `allow=`, `values=` | node type và link type phải được import; attribute tự do; cảnh báo attribute chỉ dùng một lần | vừa |
| Giá trị | `parse_value`: Bool, số, chuỗi | Num, Str, Bool, None, List `( )`, Dict `(a=1)`, Content `[ ]`, code `` ` ` `` | vừa |
| Comment | `//` có khoảng trắng phía trước, `%% %%` | `//` | nhỏ (cần luật escape) |
| Section | `#` + `@id` tùy chọn, tự sinh `contains`; văn bản dưới heading bị bỏ hoặc dồn vào node | `# Tiêu đề @tên` tùy chọn; văn bản dưới heading là nội dung của section (đã chốt) | nhỏ |
| `@tên` trong nội dung | sinh cạnh `mention` | không nhắc tới, đề xuất giữ | không đổi |
| Style | `style.kg.md` viết bằng cú pháp v0.2 (`select=`, `html.*`) | chưa đặc tả | **đóng băng**: giữ định dạng cũ |
| Bảng màu | xanh, vàng, cam, hồng, nâu | nền `#1E1E1E`, vàng / tím / xanh nhạt / xanh ngọc | vừa |

**Kết luận:** phần lõi `parse_body` và `FIELDS` phải viết lại. Các tiện ích (`slug`, `strip_comment`, `split_top`, xử lý fence, `prose` / mention, `check_cycles`, frontmatter) dùng lại được.

## 2. Đóng băng (không sửa trong 0.3, trừ khi hỏng tới mức chặn việc khác)

| Phần | Cách xử lý trong 0.3 |
|---|---|
| **Thanh bên phải (Inspector)** | Ẩn mặc định. Nếu mở thì chỉ đọc, không gửi op. Không thêm tính năng. |
| **Sửa trên view** (kéo thả, tạo node / link trên Graph, đổi tên, paste, comment node; `ops.py` trừ op ghi văn bản) | Tắt. Chỉ sửa qua khung văn bản. Các op cũ giữ trong code nhưng không gọi. |
| Sửa style / schema bằng giao diện (`op_set_style`, `op_schema_add`) | Tắt. |
| Định dạng file style | Giữ cú pháp v0.2. Parser 0.3 đọc file có `kg: 0.2` bằng đường cũ, chỉ dành cho style. |
| Typst export, kiểu `Content` chạy như Typst | Chỉ parse và giữ nguyên văn; chưa xuất. |
| Macro / `@parser` | Đã bỏ. |
| `has` (node con), khai báo kiểu `<:` / `::`, toán tử | Chưa chốt nên chưa làm. Parser báo "chưa hỗ trợ" nếu gặp. |
| `import:` / `from` module giữa nhiều file | Giữ nếu chạy được sau khi viết lại; không sửa thêm. |
| Export SVG, menu Format phụ | Giữ nguyên, không mở rộng. |

## 3. Các bước

| # | File | Nội dung | Kết quả |
|---|---|---|---|
| 0 | [steps.md](steps.md) | nhánh, đóng băng UI, chốt 5 điểm còn mở | quyết định ghi vào plan-v2c |
| 1 | [steps.md](steps.md) | đọc giá trị và dòng: 7 kiểu, code, comment, escape | `values.py` + test |
| 2 | [steps.md](steps.md) | cắt block: frontmatter, section, `@node`, `@link`, thuộc tính, nội dung | cây block + test |
| 3 | [steps.md](steps.md) | import, kiểu, link (trong node, `from … to`, `inverse`, gộp), mention, cảnh báo | graph JSON 0.3 + test |
| 4 | [steps.md](steps.md) | `king/schema` viết lại bằng 0.3; style giữ v0.2, chỉ đổi selector | template mới |
| 5 | [steps.md](steps.md) | chuyển examples và docs sang 0.3 | mọi file `.kg.md` 0 lỗi |
| 6 | [steps.md](steps.md) | khung sửa (tô màu), Graph, Tree, Book, Module theo JSON và bảng màu mới | 4 view hiển thị đúng |
| 7 | [steps.md](steps.md) | test toàn bộ, kiểm tra trên trình duyệt, cập nhật docs, tag `v0.3` | phát hành |

Thứ tự bắt buộc: 0 → 1 → 2 → 3 → (4, 5) → 6 → 7. Bước 1–3 là phần "cú pháp chắc", và mỗi bước chỉ xong khi test của nó qua hết.
