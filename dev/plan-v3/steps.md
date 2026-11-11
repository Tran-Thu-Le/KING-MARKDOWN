# Các bước triển khai KING 0.3 (đã xong 0–6)

## Step 0: chuẩn bị

### Việc

- [ ] Tạo nhánh `v0.3` từ `main`. Commit `dev/plan-v2/` trước khi bắt đầu.
- [ ] Đóng băng UI:
  - Inspector ẩn mặc định và chỉ đọc.
  - Graph tắt chế độ tạo node / nối link / kéo vào section.
  - Tắt các phím tắt gửi op: Ctrl+C/V/X trên view, Ctrl+/ trên view. Trong khung văn bản thì giữ.
- [ ] Chốt các điểm của plan-v2c cần cho parser (ghi kết quả vào plan-v2c mục 7):

| # | Điểm | Đề xuất |
|---|---|---|
| 3 | Escape | Không có comment trong code fence, trong `` `…` `` hay trong `"…"`. `//` chỉ là comment khi đứng đầu dòng hoặc sau khoảng trắng, nên `https://` không bị cắt. `@` chỉ mở block khi ở cột 1 và theo sau là `node` / `link`. `\@`, `\#` ở đầu dòng để viết chữ thường. |
| 5 | Import `inverse` | Import `author` thì `works` có theo. |
| 6 | Hoa / thường | Tên kiểu, tên link và tên node luôn viết thường (`[a-z0-9-]`). Viết `Concept` thì báo lỗi, kèm gợi ý `concept`. |
| 7 | Ngoặc kép | Không bắt buộc. Chỉ cần khi chuỗi có `,` ở đầu hay cuối, có ` //`, hoặc trông giống số / bool (`"3"`, `"true"`). |
| 8 | Ranh giới thuộc tính / nội dung | Dãy thuộc tính là mọi dòng `- ` liền nhau ngay sau dòng mở. Dòng `- ` sai cú pháp (không có `key:`) thì báo lỗi. Nội dung bắt đầu sau dòng trắng đầu tiên. |
| mới | Schema 0.3 | Trong file schema: mỗi `@node X` là một node type, mỗi `@link X` là một link type. Dòng `- from … to …` trong file schema là lỗi. |
| mới | `@link` trong file dữ liệu | Vừa khai báo link type cục bộ, vừa chứa các dòng `- from A to (B, C)`. Link type khai báo trong file thì không cần import. |
| **đã chốt** | Tên và nhãn | `@node tên`: tên như biến, phạm vi trong file, không có ID riêng. `- label:` chỉ là diễn nghĩa, có thể bỏ (khi đó view hiện tên). |
| **đã chốt** | Văn bản dưới heading (trước block `@` đầu tiên) | Là nội dung của section (`content` của node section), không sinh node riêng. |

### Xong khi

- Bảng trên được chốt (đồng ý hoặc sửa).
- UI không còn đường nào ghi file ngoài khung văn bản.

## Step 1: đọc giá trị và dòng

Module mới `src/king_markdown/values.py`, thuần hàm, không phụ thuộc parser.

### Việc

- [ ] `strip_comment(line)`: bỏ `// …`, trừ khi `//` nằm trong `"…"`, trong `` `…` ``, hoặc ngay sau `:` (URL). Bỏ `%% %%` (cú pháp v0.2) và báo cảnh báo khi gặp.
- [ ] `split_top(s, sep=",")`: tách theo dấu phẩy ở mức ngoài cùng, tôn trọng `( )`, `[ ]`, `"…"`, `` `…` ``.
- [ ] `parse_value(s)` trả về một cặp (kiểu, giá trị):

| Đầu vào | Kiểu | Giá trị Python |
|---|---|---|
| `3`, `-2`, `0.5` | Num | int / float |
| `true`, `false` | Bool | bool |
| `none` | None | None |
| `"có, phẩy"`, `chữ tự do` | Str | str |
| `` `f'(x)` `` | Code (Str nguyên văn) | `{"code": "f'(x)"}` |
| `(a, b)`, `(a,)`, `()` | List | list |
| `(a=1, b=(x, y))` | Dict | dict (theo thứ tự) |
| `[ … ]` một hay nhiều dòng | Content | `{"content": "…"}` (nguyên văn) |

- [ ] List và Dict lồng nhau. Phân biệt bằng phần tử đầu ở mức ngoài: có `=` thì là Dict, không có thì List. Trộn hai loại là lỗi.
- [ ] `(x)` là List một phần tử, vì đây là cách viết `- link needs: (x)`.
- [ ] Lỗi có vị trí (cột): thiếu ngoặc đóng, chuỗi chưa đóng, Dict trùng khóa.
- [ ] `format_value(v)`: ghi ngược ra văn bản, đúng 8 dạng trên. Dùng cho test round-trip và cho các op ghi văn bản sau này.

### Test (`tests/test_values.py`)

- Mỗi kiểu một ca, cùng các ca lồng nhau và các ca lỗi.
- Round-trip: `parse_value(format_value(v)) == v`.
- Comment: `https://x.org // ghi chú`, `"a // b"`, `` `a // b` ``.

### Xong khi

Test qua hết. Chưa đụng tới `parser.py`.

## Step 2: cắt block

Thay `Parser.parse_body` (v0.2) bằng bộ cắt block mới. Bước này chỉ ra **cây block**, chưa có ngữ nghĩa.

### Cấu trúc

```python
Block(kind,      # "section" | "node" | "link"
      name,      # tên node / tên link / tên section (như tên biến, phạm vi file)
      level,     # cấp heading (section)
      attrs,     # [(key, sub, raw_value, line)]  sub = tên link khi key == "link"
      froms,     # [(src_raw, dst_raw, line)]     chỉ có ở @link
      body,      # văn bản nội dung, giữ dòng trống ở giữa
      line, end_line, parent)
```

### Việc

- [ ] **Frontmatter:**
  - `kg: 0.3`.
  - `use:` dạng danh sách YAML: `- king/schema.node: a, b`, `- king/schema.link: x`, `- king/style`.
  - Vẫn nhận dạng một dòng `use: a, b`.
  - `kg: 0.2` thì báo lỗi "file v0.2, chạy `king migrate`", trừ file style.
- [ ] **Section:** `#`… `######`. Kết thúc trước heading cùng cấp hoặc cấp cao hơn. Giữ `@tên` tùy chọn ở cuối heading (không có thì tự sinh từ tiêu đề) và cảnh báo nhảy cấp (code cũ).
- [ ] **Block `@`:**
  - Chỉ mở khi ở cột 1 và có dạng `@node <tên>` hoặc `@link <tên>`, không có gì thêm.
  - `@node tên: …` (có nhãn) là lỗi, kèm gợi ý `- label:`.
  - `@id: …` (dạng v0.2) cũng là lỗi, kèm gợi ý migrate.
- [ ] **Dãy thuộc tính:**
  - Các dòng `- ` liền nhau ngay sau dòng mở hoặc heading.
  - Dạng `- key: value`, `- link tên: value`, hoặc (trong `@link`) `- from A to B`.
  - Giá trị `[` chưa đóng thì nối các dòng sau cho tới `]`.
- [ ] **Nội dung:**
  - Từ sau dòng trắng đầu tiên cho tới hết block.
  - Giữ nguyên Markdown, kể cả các dòng `- ` của danh sách.
  - Code fence: bên trong không cắt block, không bỏ comment.
- [ ] Văn bản dưới heading, trước block `@` đầu tiên, là `body` của block section.
- [ ] Mọi phần tử đều mang `line`, để báo lỗi đúng dòng.

### Test (`tests/test_blocks.py`)

- **Ranh giới:**
  - `@` ở cột 1 và `@` thụt lề;
  - `@node` nằm trong code fence;
  - heading ngay sau block;
  - hai block liền nhau không có dòng trắng.
- **Thuộc tính và nội dung:**
  - thuộc tính sai cú pháp;
  - nội dung bắt đầu bằng `- ý danh sách`;
  - dòng trắng ở giữa nội dung.
- **Frontmatter:** cả hai dạng `use:`.

### Xong khi

Cây block của mọi ví dụ trong plan-v2c đúng như mong đợi, có in ra bằng `king tree file.kg.md` để xem.

## Step 3: ngữ nghĩa (cây block → graph JSON)

### JSON 0.3

Giữ dạng networkx node-link, để các view đổi ít nhất có thể.

```json
{ "kg": "0.3",
  "nodes": [{"id" (= tên), "kind": "section|node|external", "type", "label", "title", "attrs": {},
             "content", "parent", "level", "line"}],
  "links": [{"source", "target", "type", "line", "tree": true?}],
  "types": {"node": {"concept": {"label"}}, "link": {"author": {"label", "inverse", "dag"}}},
  "errors": [], "warnings": [] }
```

- `id` trong JSON chính là **tên** node, giữ tên trường `id` vì networkx và các view cần. Đây không phải một khái niệm ID riêng trong cú pháp.
- `label` là diễn nghĩa. Không có thì JSON để trống, view hiện tên.
- `title` là bí danh của `label` (dự phòng là tên), để view cũ chạy được.
- Section có `content` là văn bản dưới heading.
- `meta` cũ thay bằng `attrs`. Trong giai đoạn chuyển tiếp, JSON xuất cả `meta = attrs` cho view.

### Việc

- [ ] **Import:**
  - nạp schema theo `use:` và chỉ lấy đúng các tên được liệt kê;
  - tên không có trong file schema thì báo lỗi;
  - link type viết bằng `@link` trong chính file thì cũng tính là đã import.
- [ ] **Kiểu node:**
  - `- type: X` thì X phải là node type đã import;
  - không có `- type:` thì kiểu là `node`.
- [ ] **Link trong node:**
  - `- link tên: (B, C)`: tên phải là link type đã import, hoặc là `inverse` của một link type đã import;
  - với `inverse`, sinh cạnh theo chiều gốc (từ B tới node hiện tại) và đặt `type` là tên gốc.
- [ ] **Link viết riêng:** `- from A to (B, C)` trong `@link tên`. A và B có thể là một tên hoặc một List tên.
- [ ] **Gộp link trùng** theo (source, target, type). Giữ `line` của lần khai báo đầu và ghi thêm `lines` cho các lần sau.
- [ ] **Giữ từ v0.2:**
  - section `contains` (cạnh `tree`);
  - `mention` từ `@tên` trong nội dung (dùng lại `prose`);
  - kiểm `dag` / chu trình (`check_cycles`);
  - node import qua module (nếu còn chạy).
- [ ] **Kiểm lỗi:**
  - tên trùng (khai báo hai lần trong file);
  - đầu mút link không tồn tại;
  - link type hoặc node type chưa import;
  - `- type:` lặp lại;
  - attribute dùng `link` sai dạng.
- [ ] **Cảnh báo:**
  - attribute chỉ xuất hiện đúng một lần trong file (có thể là gõ nhầm);
  - `has`, `<:`, `::` chưa hỗ trợ.
- [ ] **Giá trị attribute:** đọc bằng `values.parse_value`. `label` luôn là Str.

### Test (`tests/test_parser.py`, viết lại)

- Hai ví dụ trong plan-v2c (Hình tròn, Truyện Kiều), so với JSON mong đợi.
- `author` / `works` khai ở cả hai node thì chỉ cho ra **một** cạnh.
- Các lỗi: tên chưa import, link tới tên chưa khai báo, chu trình `needs`.

### Xong khi

- `king json` của mọi ví dụ không có lỗi ngoài những lỗi được cố ý tạo ra.
- Test của bước 1–3 qua hết.

## Step 4: schema và style hệ thống

### Schema (`templates/schema.kg.md`, viết lại bằng 0.3)

```markdown
---
kg: 0.3
---

## Node types

@node concept
- label: Khái niệm

@node group-node
- label: Nhóm node

## Link types

@link part-of
- label: Là phần của
- dag: true

@link needs
- label: Cần biết trước
- dag: true
```

- [ ] Cập nhật bộ đọc schema: `@node` là node type, `@link` là link type; đọc `label`, `inverse`, `dag`.
- [ ] Bỏ `kind=key`, `allow=`, `values=`, `required=`, vì attribute giờ tự do. Các luật này để sau.
- [ ] Cú pháp import: `king/schema.node: concept` lấy node type, `king/schema.link: needs` lấy link type.

### Style (đóng băng định dạng)

- [ ] `templates/style.kg.md` vẫn dùng `kg: 0.2`, `select=`, `html.*`. Bộ đọc style tách khỏi parser cũ, thành `style.py`.
- [ ] Selector đọc dữ liệu từ JSON 0.3: `type=` đọc từ `node.type`, `kind=` giữ như cũ.
- [ ] Đổi màu mặc định theo bảng màu plan-v2c:
  - node nền `#E8D48A`, chữ `#1E1E1E`;
  - link `#A5ABB6`, độ mờ 70%;
  - section và group giữ hình dạng như hiện tại, chỉnh màu cho hợp nền tối.

### Xong khi

`use: - king/schema.node: …` và `- king/style` chạy được trên các ví dụ của plan-v2c.

## Step 5: chuyển examples và docs sang 0.3

### Việc

- [ ] Script dùng một lần `dev/tools/migrate_02_03.py`, chưa đưa vào CLI. Chuyển đổi như sau:

| v0.2 | 0.3 |
|---|---|
| `@id: Tiêu đề` | `@node id` + `- label: Tiêu đề` (id cũ thành tên) |
| `- meta: type=X, a=1` | `- type: X` + `- a: 1` |
| `- link: needs(a, b), part-of(c)` | `- link needs: (a, b)` + `- link part-of: (c)` |
| `- content: …` / `[ … ]` | dòng trắng + văn bản nội dung |
| `- ask:` / `- show:` | giữ nguyên, là attribute thường |
| `use: king/schema, king/style` | danh sách YAML, liệt kê các type đã dùng |
| node `kind=link` trong schema | `@link tên` |

- [ ] Chạy script trên `examples/`: `python-course`, `hinh-thcs/*` kể cả `solid.kg.md`. Đọc lại từng file và sửa tay chỗ script làm chưa đẹp.
- [ ] `hinh1/2/3`: giữ ý "cùng một graph, ba cách gắn style". Riêng `hinh3` (schema và style viết trong file) cần xem lại: schema viết bằng `@node` / `@link` trong file, còn style trong file thì **đóng băng**, chuyển sang file style riêng nếu không viết được.
- [ ] `docs/documentation.kg.md`: chuyển cú pháp, rồi viết lại các mục Basic / Advanced syntax theo plan-v2c.
- [ ] Sinh lại các file `.html` tĩnh.

### Xong khi

Mọi `.kg.md` trong repo (trừ `dev/plan-v1`) parse ra 0 lỗi.

## Step 6: khung sửa và bốn view

Chỉ sửa phần **hiển thị**. Inspector và các thao tác sửa trên view vẫn đóng băng (README mục 2).

### Bảng màu chung (`app.css`: biến `--k-*`; `editor.js`: `PAL`)

| Biến | Màu | Dùng cho |
|---|---|---|
| `--k-bg` | `#1E1E1E` | nền |
| `--k-node` | `#E8D48A` | tên node, kể cả khi được tham chiếu |
| `--k-link` | `#A5ABB6` | tên link, `inverse` |
| `--k-kw` | `#C586C0` | `@node`, `@link`, `link`, `from`, `to`, nhãn kiểu node |
| `--k-key` | `#9CDCFE` | attribute key |
| `--k-type` | `#4EC9B0` | Num, Str, Bool, None, List, Dict, Content |
| `--k-val` | `#D4D4D4` | giá trị, ngoặc |
| `--k-str` | `#CE9178` | Str |
| `--k-com` | `#6A9955` (nghiêng) | comment |
| `--k-punct` | `#808080` | `-`, `:`, `,` |

### Việc

- [ ] **Khung sửa (`editor.js`):**
  - viết lại bộ tô màu theo cú pháp 0.3 (dòng mở, dãy thuộc tính, `- link tên:`, `- from A to B`, giá trị theo kiểu, comment);
  - nội dung tô kiểu Markdown đơn giản;
  - giữ phím tắt và Alt+Z.
- [ ] **Graph (`graph.js`):**
  - node nền `#E8D48A`, chữ `#1E1E1E`, nhãn nằm dưới hình (giữ cách vẽ hiện tại);
  - link `#A5ABB6`, độ mờ 70%, nhãn nhỏ;
  - kiểu node hiện thành nhãn nhỏ màu tím;
  - đọc `label` (dự phòng `title`).
- [ ] **Tree (`explorer.js`):** tên node vàng, kiểu node tím, link xám.
- [ ] **Book (`book.js`):**
  - tiêu đề vàng;
  - attribute ẩn, hoặc hiện màu xám `#808080`;
  - khung `ask` nằm trên nội dung (đã chốt trước đó);
  - nội dung render Markdown như hiện tại;
  - chip link xám.
- [ ] **Module (`module.js`):** màu theo bảng; group (`type=group-node`) là hình chữ nhật bo góc, section là hình chữ nhật vuông góc.
- [ ] **Nhãn kiểu:** view nào cũng lấy `node.type` từ JSON 0.3.
- [ ] Banner nhỏ ở thanh trạng thái: "Inspector tạm khóa (0.3)".

### Xong khi

Mở bằng `king serve` hai ví dụ plan-v2c, `hinh1/2/3` và `documentation.kg.md`:
- cả bốn view hiển thị đủ node, link và nhãn;
- màu đúng bảng;
- không có lỗi trong console.

## Step 7: nghiệm thu và phát hành 0.3

### Việc

- [ ] **`pytest`:**
  - `test_values`, `test_blocks` và `test_parser` qua hết;
  - `test_ops`: chỉ giữ các op ghi văn bản còn dùng, các op đóng băng đánh dấu skip.
- [ ] **Kiểm tra trên trình duyệt** (headless Edge qua CDP, như các lần trước):
  - với mỗi ví dụ, mở bốn view;
  - đếm số node và link vẽ ra, so với JSON;
  - chụp ảnh màn hình.
- [ ] **Sửa trong khung văn bản** thì các view cập nhật, và file trên đĩa đúng nội dung vừa sửa.
- [ ] **Cập nhật tài liệu:**
  - `docs/documentation.kg.md` và `docs/architecture.md` (pipeline: giá trị → block → ngữ nghĩa → JSON);
  - ghi danh sách phần đóng băng.
- [ ] **Phát hành:** merge `v0.3` vào `main`, rồi tag `v0.3`.

### Sau 0.3 (mở băng theo thứ tự đề xuất)

1. Inspector: chỉnh sửa lại, ghi ngược bằng op mới dựa trên cây block.
2. Thao tác trên Graph: tạo node, nối link.
3. Định dạng style 0.3.
4. `has` (node con), khai báo kiểu `<:`.
5. Toán tử (0.4), xuất Typst.
