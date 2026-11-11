# Plan: parser nội tại của KING (`@parser`, macro đổi văn bản)

> **ĐÃ BỎ (2026-11-09):** KING chỉ parse bằng Python, không có `@parser` hay macro tự định nghĩa bằng `.kg.md`. File này chỉ giữ lại để tham khảo. Xem [plan-v2a.md](plan-v2a.md).
>
> Trạng thái cũ: **kế hoạch, chưa sửa code.** Bổ sung cho [plan-v2.md](plan-v2.md), trả lời mục Todo 7 ("meta programming"): chọn **mức 3 (macro)** nhưng làm theo kiểu **văn bản → văn bản**, không cho macro đụng vào cây hay đồ thị.

## 0. Tóm tắt

- `@parser tên:` khai báo một **macro**. Mọi dòng `@tên …` ở đầu dòng được giao cho macro đó.
- Macro **cắt** dòng (hoặc block) thành các mảnh theo luật khai báo (`wrap`, `split`), rồi **ghép** các mảnh thành một đoạn KING mới, bằng mẫu (`emit`) hoặc bằng Python (`run`).
- Đoạn mới được parse lại bằng các luật thường. Nếu nó còn chứa macro thì tiếp tục mở rộng, tới khi chỉ còn **KING lõi**.
- Python (nếu có) chỉ biến **chuỗi thành chuỗi**. Nó không biết AST, Model hay đồ thị.
- Mã Python viết dạng **code** trong dấu backtick: `` `…` `` một dòng, hoặc khối ```` ```py … ``` ```` nhiều dòng (giống kiểu `raw` của Typst). Không dùng `[ ]`, vì `[ ]` là Content Typst.

````markdown
@parser function:
- take: line
- wrap: (, )
- split: ,
- emit: ```king
@node {name}
- type: function
- input: {args}
```

@function sum(x, y)
````

mở rộng thành

```markdown
@node sum
- type: function
- input: x, y
```

---

## 1. Pipeline bốn bước

```
① .kg.md           văn bản tác giả viết, có cú pháp viết tắt
   │  rewrite: áp các @parser, lặp tới khi hết macro          rewrite.py
   ▼
② .kg.md lõi       chỉ còn heading, @kiểu id: …, - khóa: giá trị, nội dung
   │  parse lõi: cắt block theo @ đầu dòng và heading           core.py
   ▼
③ cây block        Block(kind, type, id, label, attrs, body, children, span)
   │  build: resolve ID, is-a, thừa hưởng, link, each, nhóm, kiểm lỗi   build.py
   ▼
④ graph JSON       king-json/1: nodes, links, errors (mỗi mục có span)
```

| Bước | Biết gì | Không biết gì | Lệnh xem kết quả |
|---|---|---|---|
| ① → ② rewrite | văn bản, các `@parser` | kiểu, ID, đồ thị | `king expand file.kg.md` |
| ② → ③ parse lõi | đúng các mẫu cú pháp lõi (mục 2) | macro, nghĩa của các trường | `king tree file.kg.md` |
| ③ → ④ build | cây block, schema, style | văn bản gốc trông thế nào | `king json file.kg.md` |

Ba điều giữ cho thiết kế bền:

1. **Bước ② là ranh giới cứng.** Đổi hay thêm cú pháp chỉ đụng ①→②. Thêm luật kiểm lỗi chỉ đụng ③→④.
2. **Hai loại Python, không lẫn nhau.** Script `run` trong `@parser` chạy ở ①→② (chuỗi → chuỗi). Python ở ③→④ là chính công cụ KING (cây → đồ thị).
3. **Mọi bước giữ `span`** (file, dòng, cột trong file gốc, kèm chuỗi macro đã đi qua). Lỗi ở ④ vẫn trỏ đúng dòng tác giả viết ở ①; editor biết sửa chỗ nào.

---

## 2. KING lõi (đầu ra của bước ②)

Chỉ còn bốn mẫu, parser lõi không bao giờ phải đổi khi thêm cú pháp mới:

```
#{1..6} Tiêu đề [@id]                 heading (block tới heading cùng cấp hoặc cao hơn)
@kiểu id[: nhãn]                      thể hiện;  @kiểu id = Nhãn  là khai báo kiểu
- khóa: giá trị                       thuộc tính (dãy liền sau dòng mở)
văn bản thường                        nội dung (Markdown)
```

cộng với một khai báo đặc biệt:

```
@parser tên:                          khai báo macro (mục 3)
```

Các cú pháp v0.3 khác trong plan-v2 (`@id: nhãn` kiểu v0.2, `@link: from A to B`, `- link: needs(x)`, `each`, `- meta: a=1, b=2`) **về lâu dài** có thể viết lại thành macro trong file hệ thống `king/syntax.kg.md`. Giai đoạn đầu vẫn để trong lõi (xem lộ trình, mục 9).

---

## 3. Đặc tả `@parser`

`parser` là một kiểu dựng sẵn, nên `@parser function:` đúng mẫu `@kiểu id:` của v0.3. Tên các trường theo quy ước động từ tiếng Anh nguyên mẫu:

| Trường | Giá trị | Ý nghĩa | Tên trong bản nháp |
|---|---|---|---|
| `take` | `line` (mặc định) \| `block` | macro nhận một dòng, hay cả block `@` (dòng mở + thuộc tính + nội dung) | `scope` |
| `wrap` | List 2 chuỗi, ví dụ `(, )` | cặp mở / đóng bao phần đối số; tìm cặp đầu tiên, tôn trọng lồng nhau và chuỗi `"…"` | `start-end` |
| `split` | Str, ví dụ `,` | ký tự tách đối số bên trong `wrap`; bỏ qua dấu tách nằm trong ngoặc / chuỗi lồng | `split` |
| `emit` | code `` `…` `` hoặc khối ```` ```king ```` | mẫu văn bản đầu ra, có chỗ trống `{…}` | `to` |
| `run` | code `` `…` `` hoặc khối ```` ```py ```` | thân hàm Python, trả về chuỗi KING | `py` |
| `ask` | Str | (tùy chọn) lời dặn / mô tả macro, như mọi node | |

Có đúng một trong `emit` và `run`. Nội dung (văn bản thường sau dãy thuộc tính) là **tài liệu của macro**, hiện ở Inspector khi trỏ vào dòng dùng macro.

### 3.1 Cắt mảnh

Với `take: line`, dòng `@function sum(x, y) rest` được cắt:

```
@function␠ sum ( x, y ) ␠rest
          └name┘ └inner┘  └tail┘
                 args = split(inner) = ["x", "y"]
```

Các chỗ trống dùng được trong `emit` (và có trong đối tượng `p` của `run`):

| Chỗ trống | Giá trị | Ví dụ |
|---|---|---|
| `{name}` | phần trước `wrap` (đã bỏ khoảng trắng) | `sum` |
| `{inner}` | nguyên văn giữa `wrap` | `x, y` |
| `{args}` | các đối số, nối lại bằng `, ` | `x, y` |
| `{1}`, `{2}`, … | đối số thứ i (thiếu thì rỗng) | `x`, `y` |
| `{tail}` | phần sau dấu đóng | `rest` |
| `{rest}` | toàn bộ dòng sau `@function ` (khi không có `wrap`) | `sum(x, y) rest` |
| `{attrs}` | (chỉ `take: block`) dãy thuộc tính gốc, nguyên văn | `- level: 2` |
| `{body}` | (chỉ `take: block`) nội dung gốc, nguyên văn | |

Không có `wrap` thì `{name}` là từ đầu tiên của `{rest}`, còn `split` (nếu có) áp lên phần còn lại của `{rest}` để ra `{1}…{n}`. Ví dụ `@chain a -> b -> c` với `split: ->`: `name = a`, `args = [b, c]`, `rest = a -> b -> c`.

### 3.2 Mẫu `emit`

````markdown
@parser theorem:
- take: block
- emit: ```king
@node {name}
- type: theorem
{attrs}

{body}
```
````

- Mặc định mọi `{x}` đều được **thoát** (mục 5, luật 4). `{x!raw}` chèn nguyên văn. `{attrs}` và `{body}` mặc định là raw, vì chúng vốn là KING của tác giả.
- Muốn viết dấu `{` thật thì dùng `{{`.

### 3.3 Script `run`

````markdown
@parser function:
- wrap: (, )
- split: ,
- run: ```py
lines = [f"@node {q(p.name)}", "- type: function"]
if p.args:
    lines.append("- input: " + ", ".join(q(a) for a in p.args))
return "\n".join(lines)
```
````

Một dòng thì viết `` - run: `return f"@node {q(p.name)}"` ``.

- Thân script được bọc thành `def macro(p): …`. Biến có sẵn:
  - `p.name`, `p.inner`, `p.args`, `p.tail`, `p.rest`, `p.attrs`, `p.body`;
  - `p.line` (số dòng gốc), `p.file`.
- Hàm có sẵn: `q(s)` (thoát), `split(s, sep)` (tách có tôn trọng ngoặc), `slug(s)` (đổi chuỗi thành ID hợp lệ).
- Giá trị trả về phải là `str`. Trả `None` nghĩa là "không khớp, để lõi xử lý".
- Không có `import`, không có `open`, không có `__builtins__` đầy đủ (mục 5, luật 5).

---

## 4. Thuật toán rewrite (bước ①→②)

```
rewrite(text, file, depth=0):
  if depth > 16: lỗi "macro lồng quá sâu"
  macros = các @parser lấy từ những file trong use: (mục 5, luật 5)
  for block ở cột 1 trong text:              # cắt block như plan-v2 mục 2.4
    X = từ đầu tiên sau "@"
    if X không phải tên macro: giữ nguyên, ghi span
    else:
      p   = cut(block hoặc dòng đầu, macros[X])
      out = emit(p) | run(p)
      kiểm tra out (UTF-8, ≤ 64 KB, thời gian ≤ 1 s)
      thay block bằng rewrite(out, file, depth+1), mọi dòng mới mang span của dòng gốc + chuỗi [X]
  return text lõi + bảng span
```

- **Macro không áp vào chính khai báo `@parser`**, và không áp bên trong khối code hay giá trị `[ ]`.
- **Trùng tên:** tên macro trùng tên kiểu là lỗi. Hai file `use:` cùng định nghĩa một macro thì file đứng sau thắng, kèm cảnh báo.
- **`take: line`** chỉ thay dòng mở. Các dòng thuộc tính và nội dung phía sau vẫn ở lại block, nối tiếp đầu ra của macro. Ví dụ `@function sum(x, y)` rồi `- ask: …` thì `- ask` gắn vào `@node sum`.

---

## 5. Năm luật

1. **Đoạn mở rộng không được ghi vào file.** File chỉ lưu dòng gốc `@function sum(x, y)`. Editor sửa dòng gốc; các node, trường sinh từ macro hiện **chỉ đọc**, có nhãn "từ macro `function`".
2. **Lỗi trỏ về dòng gốc**, kèm chuỗi macro:
   `dòng 12 (@function sum) → macro function → - input: sai kiểu (cần List)`.
3. **Giới hạn độ sâu** 16 lớp, cộng giới hạn thời gian và kích thước đầu ra, để macro gọi lại chính nó không làm parser chạy mãi.
4. **Chặn chèn mã.** Nếu một mảnh chứa xuống dòng, hoặc bắt đầu bằng `@`, `#`, `- `, nó có thể sinh khai báo ngoài ý muốn. `q(s)` thay xuống dòng bằng khoảng trắng và thoát ký tự đầu dòng. Trong `emit`, mọi `{x}` mặc định qua `q`; chỉ `{x!raw}` mới chèn nguyên văn.
5. **Script thuần, chỉ nằm trong file được `use:`.**
   - `@parser` viết ngay trong file dữ liệu: chỉ cho `emit` (mẫu, không chạy code). `run` ở đó bị bỏ qua, có cảnh báo.
   - `run` trong file `use:` chạy với builtins tối thiểu, không có `import`, `open`, `eval`, `exec`, thuộc tính `__…__`.
   - Python không có sandbox thật, nên đây là lớp **giảm rủi ro**, chưa phải lớp bảo mật. Vì vậy:
     - `king` chỉ chạy `run` của file hệ thống `king/…` và của các file trong cùng thư mục dự án;
     - file `use:` từ nơi khác phải được cho phép rõ bằng `--trust <đường dẫn>`.

---

## 6. Chiều ngược: từ đồ thị về văn bản

Editor cần sửa file mà không làm mất các viết tắt tác giả đã dùng.

- **Mỗi node sinh từ macro mang `origin`:** `{line, macro, parts}`, trong đó `parts` là các mảnh đã cắt (`name`, `args`, `tail`…).
- **Inspector sửa mảnh, không sửa đầu ra.** Trỏ vào `sum` thì Inspector hiện form theo mảnh: `name = sum`, `args = x, y`. Sửa xong, editor **dựng lại dòng gốc** từ các mảnh:
  `"@" + macro + " " + name + wrap[0] + join(args, split + " ") + wrap[1] + tail`.
  Vì luật cắt là khai báo (`wrap`, `split`), dựng lại luôn làm được, kể cả khi macro dùng `run`. Đây là `unparse` tự có, không cần tác giả viết.
- **Trường không thuộc mảnh nào** (ví dụ `- type: function` do mẫu sinh): chỉ đọc. Muốn đổi thì có nút "**tách khỏi macro**": thay dòng gốc bằng đầu ra của `king expand` cho riêng block đó, từ đó sửa như node thường.
- **Thuộc tính và nội dung tác giả viết thêm** dưới dòng macro (luật `take: line`, mục 4) sửa bình thường, vì chúng có span thật trong file.

---

## 7. Ví dụ đề xuất cho `king/syntax.kg.md`

````markdown
@parser exercise:
- wrap: (, )
- split: ,
- emit: ```king
@exercise {name}: {1}
- level: {2}
```
Bài tập viết gọn: `@exercise b1(Tính đạo hàm, 2)`.

@parser chain:
- split: ->
- run: ```py
ids = [slug(a) for a in split(p.rest, "->")]
return "\n".join(f"@needs: from {a} to {b}" for a, b in zip(ids, ids[1:]))
```
Chuỗi phụ thuộc: `@chain gioi-han -> dao-ham -> tich-phan` sinh hai link `needs`.
````

Ví dụ thứ hai cho thấy chỗ cần `run`: số link sinh ra phụ thuộc số đối số.

---

## 8. Tác động lên code (phân tích, chưa làm)

| Phần | Việc |
|---|---|
| `parser.py` | tách thành `rewrite.py` (①→②), `core.py` (②→③), `build.py` (③→④). Hàm hiện có (`parse_value`, `bracket_lines`, `prose`, `check_cycles`…) chia về đúng bước. |
| `span` | thay `line: int` bằng `span: {file, line, col, chain}`; JSON vẫn xuất `line` làm bí danh. |
| `ops.py` | mọi op nhận span. Node có `origin` thì op `set_field` chuyển thành "sửa mảnh" (mục 6) hoặc bị từ chối với thông báo rõ. |
| `cli.py` | thêm `king expand`, `king tree`, `king json`; cờ `--trust`. |
| Editor | tô màu dòng macro (tên macro màu node, mảnh màu giá trị); Inspector có form mảnh và nút "tách khỏi macro"; node sinh từ macro vẽ viền chấm trên Graph. |
| `templates/` | thêm `syntax.kg.md` (macro hệ thống), `use: king/syntax`. |
| Test | mỗi luật một fixture: cắt mảnh (lồng ngoặc, chuỗi), thoát `q`, `{x!raw}`, độ sâu 16, timeout, `run` bị chặn trong file dữ liệu, span của lỗi, dựng lại dòng gốc. |

---

## 9. Lộ trình

1. **Tách pipeline, chưa có macro.** Chia `parser.py` thành ba bước, thêm `span`, thêm `king tree` / `king json`. Test cũ phải qua nguyên vẹn.
2. **`@parser` với `emit`** (không chạy code): cắt mảnh, mẫu, thoát, độ sâu, `king expand`, lỗi trỏ dòng gốc.
3. **Editor:** node chỉ đọc, form mảnh, dựng lại dòng gốc, "tách khỏi macro".
4. **`run`** (Python): builtins tối thiểu, timeout, chỉ trong file `use:`, `--trust`.
5. **Dời cú pháp v0.3 vào `king/syntax.kg.md`** từng phần (ví dụ `- link: needs(x)` trước, rồi `each`), mỗi lần so `king json` trước và sau phải giống nhau.

---

## 10. Quyết định cần chốt

| # | Câu hỏi | Đề xuất |
|---|---|---|
| M1 | Tên trường: `take/wrap/split/emit/run` (động từ, theo quy ước) hay giữ `scope/start-end/split/to/py` của bản nháp? | Dùng động từ; chấp nhận tên cũ làm bí danh một thời gian. |
| M2 | Code viết bằng backtick (`` `…` `` / ```` ```py ````) thay cho `[ ]`? | Có. `[ ]` để dành cho Content Typst. Đây là kiểu giá trị thứ 8, **Code** (tương ứng `raw` của Typst). Cần thêm vào bảng kiểu ở plan-v2 mục 1.4 và `todo-list.md`. |
| M3 | Cho `@parser` viết ngay trong file dữ liệu? | Chỉ với `emit`; `run` chỉ trong file `use:`. |
| M4 | Macro có được sinh ra `@parser` mới không? | Không (tránh macro tự định nghĩa macro). |
| M5 | `take: block` có cần ngay không? | Có, cho các macro kiểu `@theorem`; nhưng làm sau `take: line`. |
| M6 | Dời cú pháp v0.3 thành macro hệ thống? | Có, ở bước 5 lộ trình, sau khi pipeline ổn định; giữ lõi nhỏ nhất có thể. |
| M7 | Cú pháp `run` một tên script dùng lại (`- run: myscript`, với `@script myscript = …`)? | Chưa cần; đợi khi có nhiều macro dùng chung logic. |
