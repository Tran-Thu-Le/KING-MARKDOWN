# Plan v2: KING Markdown 0.3

Kiểu thống nhất (node, link), khai báo bằng `@`, cú pháp rút gọn cho link, dữ liệu có kiểu (đồng bộ Typst), nhóm và cạnh giữa các nhóm.

Trạng thái: **bản thiết kế, chưa sửa code.** Ngôn ngữ hiện tại là v0.2 (tag `v0.2`). Mọi cú pháp dưới đây là đề xuất cho v0.3. Các chỗ còn phải chốt nằm ở mục 6.

---

## 0. Tóm tắt

| # | Yêu cầu | Đề xuất chuẩn |
|---|---|---|
| 1 | node và link trở thành kiểu | Hai kiểu gốc `node`, `link`. Mọi kiểu khác kế thừa từ một trong hai: `@node exercise = Bài tập`, `@exercise mcq = Trắc nghiệm`, `@link friend = Quan hệ bạn bè` |
| 2 | `@node tên`, `@link tên`, kèm `- label:`, `- meta:` | Dòng `@<kiểu> <id>` tạo một **thể hiện** (node hoặc link) của kiểu đó; các dòng `- tên: giá trị` là thuộc tính |
| 3 | Cú pháp rút gọn cho link | `@link tên: from A to B`, hoặc theo kiểu `@friend: from an to binh` (tên không bắt buộc) |
| 4 | Dữ liệu sau `:` đến cuối dòng; nhiều dòng dùng `[]`; Str, Num, Bool | Mọi vị trí giá trị đều đọc theo cùng một quy tắc, gồm 7 kiểu đồng bộ Typst: Str, Num, Bool, None, List `( )`, Dict `(k: v)`, Content `[ ]` |
| 5 | Gom node, sinh cạnh giữa các nhóm | Kiểu có sẵn `group` với `- members: (...)`. Link có đầu mút là nhóm, cùng từ khóa `each` để sinh cạnh tới từng thành viên |

Quy tắc phân biệt quan trọng nhất của v0.3: **`=` khai báo kiểu, `:` tạo thể hiện.**

```markdown
@node exercise = Bài tập          ← khai báo KIỂU exercise (con của node), nhãn "Bài tập"
@exercise bai-1: Giải phương trình ← tạo NODE bai-1 thuộc kiểu exercise, nhãn sau dấu :
@friend: from an to binh           ← tạo LINK kiểu friend, không cần tên
```

---

## 1. Phân tích từng yêu cầu

### 1.1 node và link trở thành kiểu

**v0.2:** Kiểu node là một khóa meta (`- meta: type=concept`), được khai báo trong schema bằng `@concept` + `- meta: kind=type`. Loại link khai báo bằng `kind=link`. Node và link là hai thế giới tách biệt: link không có ID, không có thuộc tính, và chỉ tồn tại như một token `needs(B)` trong dòng `- link:`.

**Vấn đề:**
- Phải viết `type=` trên mọi node, dài và dễ quên.
- Không có kế thừa: `mcq` là một loại `exercise`, nhưng schema không diễn tả được.
- Link không mang được dữ liệu: không có trọng số, nhãn hay ghi chú trên cạnh.
- Có ba cơ chế khai báo khác nhau (`kind=type`, `kind=key`, `kind=link`).

**Đề xuất:**
- Có hai kiểu gốc dựng sẵn là `node` và `link`. Một kiểu là cây con của một trong hai gốc này.
- Khai báo kiểu: `@<kiểu-cha> <tên-kiểu> = <Nhãn>`. Kiểu cha có thể là `node`, `link`, hoặc một kiểu đã khai báo (ở trong file, trong file `use:` hay trong hệ thống).
- Kế thừa: kiểu con nhận mọi thuộc tính và tùy chọn của kiểu cha. Một node `mcq` là `exercise` và cũng là `node`. Style và kiểm lỗi viết cho `exercise` sẽ áp cả cho `mcq`.
- Tùy chọn của kiểu (các khóa như `kind=link`, `dag=true` của v0.2) đặt trong `- meta:` của dòng khai báo kiểu:

```markdown
@link friend = Quan hệ bạn bè
- meta: symmetric=true

@link needs = Cần biết trước
- meta: dag=true, from=concept, to=concept
```

**Về đoạn mẫu của bạn:**

```markdown
@node exercise = Bài tập
  @exercise mcq = Trắc nghiệm
  @link friend = Quan hệ bạn bè
  - meta: symmetric=true
```

Đoạn này đúng ý, nhưng thụt lề gây hiểu nhầm. `@link friend` thụt vào dưới `exercise` trông như con của `exercise`, trong khi cha thật của nó là `link`. Chuẩn hóa: **thụt lề không diễn tả quan hệ cha–con.** Cha của một kiểu chỉ là từ viết ngay sau `@`. Hơn nữa, theo luật block (mục 2.4), `@` phải ở cột đầu tiên mới mở block, nên `  @exercise mcq` có thụt lề sẽ chỉ là một dòng nối tiếp của `exercise`. Phải viết không thụt lề:

```markdown
@node exercise = Bài tập

@exercise mcq = Trắc nghiệm

@link friend = Quan hệ bạn bè
- meta: symmetric=true
```

### 1.2 `@node tên`, `@link tên`, kèm `- label:`, `- meta:`

**v0.2:** `@id: Tiêu đề` mở node; có đúng 5 trường cố định (`meta`, `content`, `ask`, `link`, `show`); dữ liệu riêng phải nhét vào `- meta: a=1, b=2`.

**Đề xuất:**
- `@<kiểu> <id>` mở một thể hiện của kiểu đó. Kiểu gốc là `node` thì tạo node; gốc là `link` thì tạo link.
- `@<id>: <nhãn>` (cú pháp v0.2) vẫn hợp lệ và tương đương `@node <id>: <nhãn>`.
- `- label:` thay cho "tiêu đề" (JSON v0.2 dùng `title`; v0.3 dùng `label` và vẫn xuất `title` làm bí danh một thời gian).
- Bỏ giới hạn 5 trường. Mỗi dòng `- tên: giá trị` là **một thuộc tính**, được kiểu khai báo và kiểm tra. `- meta: a=1, b=2` vẫn giữ, là dạng viết gộp nhiều thuộc tính trên một dòng: `- meta: level=2, done=true` tương đương hai dòng `- level: 2` và `- done: true`.
- Thuộc tính dựng sẵn:

| Thuộc kiểu | Thuộc tính | Ý nghĩa |
|---|---|---|
| `node` | `label` | nhãn (mặc định là ID); thường viết ngay sau `:` trên dòng `@` |
| `node` | `ask` | lời dặn cho AI / đồng tác giả; luôn là **thuộc tính cuối cùng**, ngay trên nội dung |
| `node` | `show` | `none` thì không hiện trong sách |
| `node` | `link` | dạng rút gọn tạo link từ node này (mục 1.3) |
| `link` | `from`, `to` | hai đầu mút (ID, List ID, hoặc nhóm) |
| `link` | `label` | nhãn của cạnh |
| mọi kiểu | `meta` | dạng gộp `k=v, k=v` |

**Không còn thuộc tính `content`** (chốt Q13). Nội dung của node là **văn bản thường** viết sau dòng `@` và sau dãy thuộc tính `- tên:`; xem mục 2.6.

- Trong **khai báo kiểu**, dòng `- tên: Kiểu` khai báo một thuộc tính, còn `- tên: Kiểu = mặc-định` khai báo kèm giá trị mặc định:

```markdown
@node exercise = Bài tập
- level: Num = 1
- answer: Content
- done: Bool = false

@exercise mcq = Trắc nghiệm
- choices: List
- correct: Num
```

Trong **thể hiện**, cùng dòng đó mang giá trị:

```markdown
@mcq cau-1: Đạo hàm của x² là?
- choices: (x, 2x, x², 2)
- correct: 1
- level: 2
```

Cách này thay cho `kind=key`, `values=`, `value=`, `required=` của v0.2:
- `values="a | b"` → `- role: Str in (Nạp, Xuất)`;
- `required=true` → bỏ `= mặc-định` và đánh dấu `!`: `- role!: Str`. Ký hiệu cụ thể chốt ở mục 6.

### 1.3 Cú pháp rút gọn cho link

**v0.2:** `- link: needs(B), part-of(C)` nằm trong node nguồn; không có link độc lập.

**Đề xuất:** link có hai dạng, cùng sinh ra một cạnh như nhau.

```markdown
@friend f1: from an to binh          ← link có tên (tham chiếu được, gắn thuộc tính được)
- since: 2020
- label: Bạn từ lớp 6

@friend: from an to chi              ← link không tên (dạng thường gặp nhất)

@needs: from tich-phan to (dao-ham, gioi-han)   ← nhiều đích: 2 cạnh

@dao-ham: Đạo hàm
- link: needs(gioi-han), part-of(giai-tich)     ← dạng v0.2, vẫn giữ: nguồn là node đang viết
```

Quy tắc:
- Giá trị của dòng `@<kiểu-link> [id]: ...` có dạng `from <đầu> to <đầu>`. Mỗi đầu là một ID, một List ID `(a, b)`, hoặc một nhóm (mục 1.5).
- Viết tắt (tùy chọn, chốt ở mục 6): `A -> B` tương đương `from A to B`, còn `A -- B` dùng cho kiểu `symmetric`.
- Kiểu có `symmetric=true` (như `friend`): thứ tự hai đầu không quan trọng; trùng lặp được kiểm theo cặp không thứ tự; vẽ không có mũi tên.
- `- link: loại(B)` trong node vẫn là dạng viết gọn của `@loại: from <node-này> to B`. `loại!(B)` vẫn là chiều ngược.
- `from`, `to`, `each` là từ khóa trên dòng link, nên không dùng làm ID.

### 1.4 Dữ liệu sau `:` và kiểu giá trị

**v0.2:** Giá trị meta được đoán kiểu (`true`/`false`, số, chuỗi). Chuỗi có dấu phẩy phải đặt trong ngoặc kép. Nhiều dòng chỉ có ở `content`/`ask` (dòng nối tiếp, hoặc `[ ]`). Tiêu đề node là chuỗi tự do.

**Đề xuất:** một quy tắc giá trị duy nhất cho **mọi vị trí** (sau `:` trên dòng `@`, sau `- tên:`, và vế phải của `k=` trong `meta`):
- Giá trị kéo dài **từ sau dấu `:` đến cuối dòng** (trừ comment).
- Giá trị nhiều dòng: mở bằng `[`, kết thúc ở dòng có `]` cuối dòng. Bên trong là Content, đọc như môi trường Typst (xem `dev/plan-v1/todo-list.md`).
- Bảy kiểu, đồng bộ Typst:

| Kiểu | Viết | Ghi chú |
|---|---|---|
| Num | `3`, `-2`, `0.5` | int / float |
| Bool | `true`, `false` | |
| None | `none` | |
| Str | `Đạo hàm`, `"3"` | chữ trần là Str; trông như số hay `true` mà muốn là Str thì đặt trong `"..."` |
| List | `(a, b, c)` | phần tử theo cùng quy tắc |
| Dict | `(w: 3, h: 2)` | |
| Content | `[Diện tích $S = pi r^2$]` | một dòng hoặc nhiều dòng |

- Mỗi thuộc tính một dòng, nên **hết vấn đề dấu phẩy** trong chuỗi. Dạng gộp `- meta: a=1, b=2` thì vẫn phải tách theo dấu phẩy ở cấp ngoài cùng, bỏ qua `( )`, `[ ]` và `"..."`.
- Kiểu khai báo trong schema (`- level: Num`) dùng để kiểm lỗi: ghi `level: hai` là lỗi "cần Num".

### 1.5 Gom node và sinh cạnh giữa các nhóm

**v0.2:** Có ba cách gom nhưng không thống nhất:
- section (heading), sinh cạnh `contains`;
- `part-of` (link do người dùng khai báo);
- `meta: contain=a, b`, sinh cạnh `contain`.

Không có cách nối hai nhóm với nhau.

**Đề xuất:**

**(a) Kiểu dựng sẵn `group`** (con của `node`), có thuộc tính `members: List`:

```markdown
@group hinh-phang: Hình phẳng
- members: (tam-giac, tu-giac, duong-tron)

@group hinh-khoi: Hình khối
- members: (lang-tru, hinh-chop)
```

- Một node thuộc được nhiều nhóm. Nhóm lồng được nhóm.
- Section (heading) là một nhóm ngầm, chứa mọi node viết dưới nó.
- `meta: contain=...` của v0.2 là cách viết cũ của `members`.
- Parser sinh cạnh `member` (đổi tên từ `contains`/`contain`, xem mục 6) từ nhóm tới từng thành viên. View Module vẽ nhóm thành hộp bo góc chứa thành viên.

**(b) Cạnh giữa các nhóm.** Đầu mút của link có thể là một nhóm. Từ khóa `each` quyết định có tách thành cạnh tới từng thành viên hay không:

| Viết | Sinh ra |
|---|---|
| `@needs: from hinh-khoi to hinh-phang` | **1 cạnh nhóm → nhóm** (giữ nguyên, Module vẽ giữa hai hộp) |
| `@needs: from each hinh-khoi to hinh-phang` | mỗi thành viên của `hinh-khoi` → nhóm `hinh-phang` |
| `@needs: from hinh-khoi to each hinh-phang` | nhóm `hinh-khoi` → mỗi thành viên của `hinh-phang` |
| `@needs: from each hinh-khoi to each hinh-phang` | tích Descartes: mọi cặp (2 × 3 = 6 cạnh) |
| `@needs: from (lang-tru, hinh-chop) to tam-giac` | List cũng được: 2 cạnh |

- Mỗi cạnh sinh ra mang `via` (ID hoặc dòng của link nhóm gốc), để editor biết sửa/xóa ở đâu. Inspector hiện chúng là "tự sinh từ dòng N".
- Ràng buộc `from=` / `to=` của kiểu link được kiểm **sau khi tách** cạnh.
- `dag=true` được kiểm trên đồ thị đã tách, nên vòng lặp qua nhóm cũng bị phát hiện.

---

## 2. Đặc tả nháp v0.3

### 2.1 Các dòng `@`

| Dạng | Nghĩa |
|---|---|
| `@<cha> <tên> = <Nhãn>` | khai báo kiểu `<tên>` con của `<cha>` |
| `@<kiểu> <id>: <nhãn>` | node `<id>` thuộc `<kiểu>` (gốc `node`) |
| `@<id>: <nhãn>` | node `<id>` kiểu `node` (tương thích v0.2) |
| `@<kiểu-link> [<id>]: from <đầu> to <đầu>` | link thuộc `<kiểu-link>` (gốc `link`); `<id>` không bắt buộc |
| `@<kiểu-link> [<id>]` + `- from:` / `- to:` | dạng dài của link |

Quy tắc đọc một dòng `@` (theo thứ tự):
1. Có ` = ` → khai báo kiểu.
2. Có `@A B` (hai từ trước `:`) → A phải là kiểu đã biết (ở bất kỳ đâu trong file, trong `use:` hay hệ thống), B là ID. Gốc của A quyết định đây là node hay link.
3. Chỉ có `@A:` hoặc `@A` → nếu A là kiểu link thì đây là link không tên; nếu không thì là node `A` kiểu `node` (v0.2).

Hệ quả: cần đọc hai lượt (thu thập kiểu trước, rồi đọc thể hiện), để kiểu khai báo ở cuối file vẫn dùng được ở đầu file.

### 2.2 Ngữ pháp (EBNF, rút gọn)

```ebnf
section     = "#"{1..6} " " title [ " @" id ] NL { attr-line } [ body ] ;
type-decl   = "@" type " " name " = " label NL { attr-decl | meta-line } [ body ] ;
node-inst   = "@" [ type " " ] id [ ":" value ] NL { attr-line | meta-line } [ body ] ;
link-inst   = "@" link-type [ " " id ] ":" ends NL { attr-line | meta-line } [ body ] ;
body        = { markdown-line } ;        (* nội dung: từ dòng đầu tiên không phải "- tên:" tới hết block *)
ends        = "from " end " to " end | end ( "->" | "--" ) end ;
end         = [ "each " ] ( id | list ) ;
attr-decl   = "- " name [ "!" ] ": " vtype [ " in " list ] [ " = " value ] NL ;
attr-line   = "- " name ": " value NL ;
meta-line   = "- meta: " name "=" value { ", " name "=" value } NL ;
value       = num | bool | "none" | str | list | dict | content ;
list        = "(" [ value { "," value } ] ")" ;
dict        = "(" name ":" value { "," name ":" value } ")" ;
content     = "[" … "]" ;                (* nhiều dòng tới "]" cuối dòng *)
vtype       = "Num" | "Bool" | "None" | "Str" | "List" | "Dict" | "Content" | type ;
```

Kiểu của thuộc tính có thể là một kiểu node (ví dụ `- teacher: person`): giá trị khi đó là ID, và parser sinh một cạnh kiểu thuộc tính (`teacher`) từ node tới ID đó. Đây là cách "thuộc tính tham chiếu" trở thành cạnh.

### 2.3 Ví dụ đầy đủ

```markdown
---
kg: 0.3
use: king/schema, king/style
---

# Kiểu

@node hinh = Hình
- level: Num = 1
Mọi hình hình học trong chương này.      ← nội dung của khai báo kiểu: mô tả kiểu

@hinh khoi = Hình khối

@link specialize = Là trường hợp riêng của
- meta: dag=true, from=hinh, to=hinh

@link friend = Liên quan
- meta: symmetric=true

# Hình khối @solid

@khoi hinh-khoi: Hình khối
@khoi lang-tru: Lăng trụ
@khoi lang-tru-dung: Lăng trụ đứng
- level: 2
Lăng trụ có cạnh bên vuông góc với đáy.  ← nội dung: văn bản thường, nhiều dòng tự nhiên
Thể tích $V = S h$.
@khoi chop: Hình chóp

@specialize: from lang-tru to hinh-khoi
@specialize: from lang-tru-dung to lang-tru
@specialize: from chop to hinh-khoi

@group da-dien: Đa diện
- members: (lang-tru, lang-tru-dung, chop)

@friend: from each da-dien to hinh-khoi
```

Đây chính là `examples/hinh-thcs/solid.kg.md` viết lại. Bản v0.2 phải lặp `- meta: type=hinh` ở mọi node.

### 2.4 Xác định block khi parse

Parser chia file thành các **block** lồng nhau. Điểm bắt đầu và điểm kết thúc của mỗi block chỉ dựa vào ký hiệu ở **cột đầu tiên** của dòng (`---`, `#`, `@`, `- `, `[`/`]`, rào code). Thụt lề không tạo cấp lồng nào.

**Section (heading).** Section cấp *n* bắt đầu ở dòng có *n* dấu `#` (`#`, `##`, `###`, `####`, `#####`, `######`). Nó kéo dài **cho tới dòng heading kế tiếp có cùng cấp hoặc cấp cao hơn** (ít `#` hơn hoặc bằng), hoặc tới **hết file**.

```markdown
# A            ← A: từ đây …
## A1          ←   A1: từ đây …
### A1a        ←     A1a: từ đây …
## A2          ←   … A1 và A1a kết thúc ở đây (gặp ## cùng cấp với A1); A2 bắt đầu
# B            ← … A và A2 kết thúc ở đây (gặp # cùng cấp với A); B bắt đầu
               ← B kéo dài tới hết file
```

- Heading cấp thấp hơn (nhiều `#` hơn) **không** kết thúc section hiện tại mà mở một section con bên trong nó.
- Gặp heading cấp cao hơn (ít `#` hơn) thì đóng mọi section từ cấp đó trở xuống. Ví dụ ở trên, `# B` đóng cả `A2` lẫn `A`.
- Cha của một section là section đang mở gần nhất có cấp nhỏ hơn. Nhảy cấp (`#` rồi `###`) vẫn hợp lệ nhưng bị cảnh báo; `###` khi đó là con trực tiếp của `#`.
- Section là một nhóm ngầm (mục 1.5): mọi node, link, khai báo kiểu nằm trong block của nó đều là thành viên của nó.
- v0.2 đã làm đúng như vậy (ngăn xếp heading, bỏ ra mọi mục có cấp ≥ cấp mới). v0.3 ghi thành luật chính thức.

Về cách viết `#4`, `#5`: nếu ý là "cấp 4, cấp 5" thì cú pháp chuẩn vẫn là `####`, `#####`. Nếu muốn **viết tắt** `#4 Tiêu đề` thay cho `#### Tiêu đề` thì xem Q11 (mục 6): cách này không còn là Markdown hợp lệ.

**Block `@` (khai báo kiểu, node, link).** Một block `@` bắt đầu ở dòng có **ký tự `@` ở đầu dòng** (cột 1, không có khoảng trắng phía trước). Nó **kết thúc ở dòng cuối cùng trước dòng kế tiếp có `@` ở đầu dòng** (hoặc hết file).

```markdown
@concept dao-ham: Đạo hàm        ← block dao-ham bắt đầu
- meta: role=Nạp                 ← thuộc tính
Tốc độ thay đổi của hàm.         ← nội dung (văn bản thường, mục 2.6)
Dòng nối tiếp vẫn thuộc dao-ham.
  @gioi-han ở giữa dòng hay sau thụt lề: chỉ là tham chiếu, không mở block
                                 ← dòng trống cuối block bị bỏ
@concept tich-phan: Tích phân     ← block dao-ham kết thúc ở dòng ngay trên; tich-phan bắt đầu
```

- "Đầu dòng" nghĩa là cột đầu tiên. Dòng `  @x` (có thụt lề) **không** mở block. Nó là dòng nối tiếp của block đang mở, và `@x` trong đó là tham chiếu. v0.2 bỏ khoảng trắng đầu dòng trước khi nhận `@`, nên đây là điểm **khác v0.2** (xem Q1, Q12).
- Các dòng trống ở cuối block không thuộc block (khi sửa ngược, editor chèn vào trước các dòng trống này).
- Mọi thứ trong block (thuộc tính `- tên:`, nội dung, `[ ]`, khối code) thuộc về block đó. Bên trong block chỉ có hai phần, theo thứ tự: **dãy thuộc tính** rồi **nội dung** (mục 2.6).
- **Gặp heading thì sao?** Theo đúng luật trên, một heading nằm giữa hai dòng `@` sẽ rơi vào block `@` phía trên. Điều đó sai với ý viết: node cuối của một section không chứa heading của section sau. Vì vậy block `@` **cũng kết thúc trước dòng heading kế tiếp**: section là block cha, block `@` lồng trong nó và không vượt qua ranh giới section. Xem Q12.

**Bảng tổng hợp** (điểm bắt đầu và kết thúc chỉ dựa vào ký hiệu ở cột đầu tiên):

| Block | Bắt đầu | Kết thúc (trước dòng nào gặp trước) |
|---|---|---|
| Frontmatter | dòng `---` đầu file | dòng `---` kế tiếp |
| Section | `#`…`######` ở đầu dòng | heading cùng cấp hoặc cao hơn; hết file |
| Khai báo kiểu, node, link | `@` ở đầu dòng | `@` ở đầu dòng kế tiếp; heading kế tiếp; hết file. Bỏ dòng trống ở cuối |
| Dãy thuộc tính (của section hoặc của block `@`) | các dòng `- tên:` **liền ngay sau** dòng heading / dòng `@` | dòng đầu tiên không phải `- tên:` (kể cả dòng trống). Giá trị `[ … ]` nhiều dòng thuộc về thuộc tính của nó |
| Giá trị `[ ]` nhiều dòng | `[` ngay sau `:` mà dòng đó chưa có `]` | dòng kết thúc bằng `]`. Bên trong **không** có heading, `@` hay `- tên:` |
| Nội dung của block `@` (mục 2.6) | dòng đầu tiên sau dãy thuộc tính | hết block `@` |
| Nội dung của section (node `content`, mục 2.5) | dòng đầu tiên sau dãy thuộc tính của section | `@` ở đầu dòng kế tiếp; heading kế tiếp; hết file |
| Khối code | ```` ``` ```` / `~~~` | dấu rào cùng loại kế tiếp. Bên trong không có cấu trúc |

Thứ tự ưu tiên khi đọc một dòng: giá trị `[ ]` đang mở → khối code đang mở → heading → `@` ở cột 1 → `- tên:` (chỉ khi còn trong dãy thuộc tính) → văn bản nội dung. Nhờ đó, một dòng `# …` hay `@…` nằm trong `[ ]` hoặc trong khối code không bao giờ mở block, và một dòng `- tên:` nằm giữa nội dung chỉ là chữ.

Cách cắt block này cho parser một bước đầu rất đơn giản: **quét cột đầu của từng dòng để chia file thành các block, rồi mới đọc chi tiết từng block.** Editor cũng nhờ đó mà biết chính xác dòng đầu, dòng cuối của mỗi node khi cắt, dán hay sửa.

### 2.5 Văn bản thường dưới heading: node kiểu `content`

**v0.2:** văn bản nằm dưới heading mà không thuộc node nào là "ghi chú tự do". Parser bỏ qua nó: không có trong JSON, không hiện trong Book, không sửa được từ editor.

**Luật v0.3:** phần thân của một section (từ sau dòng heading tới dòng `@` đầu tiên, heading kế tiếp hoặc hết file) được chia làm hai phần, theo thứ tự:

1. **Thuộc tính của section:** các dòng `- tên: giá trị` đứng liền ngay sau heading. Chúng gán thuộc tính cho chính section, theo cùng quy tắc giá trị (mục 1.4).
2. **Văn bản của section:** mọi dòng còn lại, kể từ dòng đầu tiên không phải `- tên:`. Phần này là **Markdown thường** (đoạn văn, danh sách `- ý`, bảng, khối code, công thức…). Parser đặt nó vào **một node tự sinh có kiểu `content`**, là con của section.

```markdown
# Đạo hàm @dao-ham-chuong          ← section
- level: 2                         ← thuộc tính của section (liền sau heading)
- meta: important=true

Chương này giới thiệu **đạo hàm**  ← từ đây: văn bản → node kiểu content
và cách tính.

- Ý thứ nhất                       ← danh sách Markdown, KHÔNG phải thuộc tính
- Ý thứ hai                          (đã qua phần thuộc tính; và "Ý thứ nhất" không có dạng "tên:")

@concept dao-ham: Đạo hàm           ← block @ đầu tiên: văn bản của section dừng ở dòng trên
```

Node sinh ra:

| Trường | Giá trị |
|---|---|
| `id` | `<id-section>-content`. Ví dụ `dao-ham-chuong-content`. Section không có `@id` thì lấy ID tự sinh của section (đổi theo tiêu đề, nên đừng link tới) |
| `type` | `content` (kiểu dựng sẵn, con của `node`) |
| `label` | tiêu đề section (hoặc để trống, xem Q14) |
| `content` | nguyên văn Markdown, bỏ dòng trống ở đầu và cuối |
| `parent` | section; có cạnh `contain` từ section tới node này, và node này đứng **đầu tiên** trong các con của section |
| `line` | dòng đầu tiên của đoạn văn bản, để editor sửa đúng chỗ |

Hệ quả:
- **Mỗi section có tối đa một node `content`.** Sau dòng `@` đầu tiên, mọi văn bản đều thuộc block `@` đang mở (mục 2.4), nên không còn văn bản tự do nào khác. Muốn chen đoạn văn giữa các node thì viết thành một node (hoặc một node `@content … :` tường minh, xem Q15).
- Section không có văn bản thì không sinh node `content`.
- `@id` trong văn bản này vẫn sinh cạnh tham chiếu (`mention`), với nguồn là node `content`.
- Văn bản trước heading đầu tiên (ngay sau frontmatter) là văn bản của **cả file**. Nó sinh node `content` có ID `<tên-file>-content` (xem Q16).
- **Book:** node `content` hiện thành đoạn văn ngay dưới tiêu đề section, không có khung thẻ. Đây chính là cách đọc tự nhiên của một chương sách.
- **Graph và Module:** mặc định **ẩn** (giống node định nghĩa schema/style) để đồ thị không rối; có ô bật ở menu Format. **Tree:** hiện, có biểu tượng riêng.
- **Inspector / sửa ngược:** sửa trường `content` của node này thì ghi lại đúng các dòng văn bản dưới heading. Không thêm dòng `@` nào.
- **Typst:** văn bản này là Markdown, chưa phải Content Typst. Khi xuất Typst cần một bước đổi Markdown sang markup Typst (đậm, nghiêng, danh sách, bảng), khác với `[ ]` vốn được chép nguyên văn.

### 2.6 Nội dung là văn bản thường (bỏ thuộc tính `content`)

Chốt Q13: **không còn `- content:`.** Mọi block (section `#` và block `@`) có cùng một khuôn:

```markdown
<dòng mở>                 # Tiêu đề @id      hoặc      @kiểu id: Nhãn
- tên: giá trị            ← dãy thuộc tính: các dòng "- tên:" liền ngay sau dòng mở
- tên: giá trị
                          ← (dòng trống: tùy chọn, kết thúc dãy thuộc tính)
Văn bản thường …          ← nội dung: từ dòng đầu tiên không phải "- tên:" tới hết block
- một ý của danh sách     ← vẫn là nội dung (đã qua dãy thuộc tính)
```

Luật:
- **Dãy thuộc tính** gồm các dòng `- tên: giá trị` đứng liền ngay sau dòng mở. Nó dừng ở dòng đầu tiên không có dạng `- tên:`, hoặc ở dòng trống đầu tiên.
- **Nội dung** là mọi dòng còn lại của block, viết như Markdown thường: đoạn văn, danh sách, bảng, khối code, công thức. Không cần `[ ]` để viết nhiều dòng.
  - Một dòng `- tên: …` nằm **trong** nội dung chỉ là chữ, không phải thuộc tính.
  - Muốn nội dung bắt đầu bằng một dòng trông như thuộc tính (ví dụ `- note: …` là một ý của danh sách), hãy chèn **một dòng trống** sau dãy thuộc tính.
- **`- ask:` đứng cuối dãy thuộc tính**, ngay trên nội dung: lời dặn nằm sát phần văn bản nó nhắm tới, đọc file là thấy ngay việc cần làm. Parser không báo lỗi nếu `ask` nằm giữa dãy (chỉ cảnh báo nhẹ); editor và `king fmt` luôn đưa nó xuống cuối.
- Dòng trống ở đầu và cuối nội dung bị bỏ. Dòng trống ở giữa được giữ, để tách đoạn văn.
- `@id` trong nội dung (ở đầu chuỗi hoặc sau khoảng trắng, không nằm trong code) là tham chiếu, sinh cạnh `mention`.
- **Nơi lưu:**
  - Nội dung của block `@` thuộc chính node / link / kiểu đó. Trong JSON vẫn là trường `content` của node (đây là tên trường dữ liệu, không phải cú pháp).
  - Nội dung của block khai báo kiểu là phần mô tả kiểu (hiện trong tài liệu và Inspector).
  - Nội dung của section là node tự sinh kiểu `content` (mục 2.5).
- **Còn dùng `[ ]` ở đâu?** Chỉ cho **giá trị thuộc tính** nhiều dòng, hoặc giá trị kiểu Content (môi trường Typst), ví dụ `- ask: [ … ]`, `- note: [ … ]`, hay nhãn dài sau `:` trên dòng `@`.
- **Nội dung là Markdown, còn `[ ]` là Typst.** Khi xuất Typst, nội dung cần một bước đổi Markdown sang Typst; giá trị `[ ]` thì chép nguyên văn.

Ví dụ:

```markdown
@concept tich-phan: Tích phân
- role: Xuất
- link: part-of(giai-tich), needs(dao-ham)
- ask: Thêm hình minh họa diện tích.

Tích phân xác định của $f$ trên $[a, b]$ là diện tích có dấu dưới đồ thị.

- Liên hệ với @dao-ham qua định lý cơ bản.
- Ứng dụng: diện tích, thể tích, quãng đường.
```

Trong v0.2 cùng node đó phải viết `- content: Tích phân xác định …` rồi các dòng nối tiếp, và danh sách `- Liên hệ …` dễ bị đọc nhầm thành trường.

**Sửa ngược (editor):** Inspector sửa nội dung thì thay đúng phần nội dung của block (các dòng sau dãy thuộc tính), giữ nguyên dãy thuộc tính. Thêm thuộc tính thì chèn vào cuối dãy thuộc tính nhưng **trên `- ask:`** (nếu có), để `ask` luôn là dòng cuối của dãy, ngay trên nội dung. **Book** cũng hiện theo thứ tự đó: thuộc tính → khung `ask` → nội dung.

---

## 3. Ánh xạ v0.2 → v0.3

| v0.2 | v0.3 |
|---|---|
| `@id: Tiêu đề` | giữ nguyên (= `@node id: Tiêu đề`) |
| `@id` + `- meta: type=concept` | `@concept id: Tiêu đề` |
| schema `@concept` + `- meta: kind=type, allow="role, important"` | `@node concept = Khái niệm` + `- role: Str` + `- important: Bool = false` |
| schema `@role` + `kind=key, values="Nạp \| Xuất", required=true` | trong kiểu: `- role!: Str in (Nạp, Xuất)` |
| schema `@needs` + `kind=link, dag=true, to=group` | `@link needs = Cần biết trước` + `- meta: dag=true, to=group` |
| `- link: needs(B)` | giữ nguyên, hoặc `@needs: from id to B` |
| `- meta: contain="a, b"` | `- members: (a, b)` (nên khai báo kiểu `group`) |
| cạnh tự sinh `contains` (section), `contain` | `member` (chốt ở mục 6) |
| `title` trong JSON | `label` (giữ `title` làm bí danh) |
| style `select="type=concept"` | giữ; khớp cả kiểu con. Thêm `select="is=exercise"` nếu cần phân biệt (mục 6) |
| `- content: …` (và các dòng nối tiếp, hoặc `[ … ]`) | **bỏ**: viết thành văn bản thường sau dãy thuộc tính (mục 2.6). `king migrate` chuyển tự động |
| văn bản tự do dưới heading (bị bỏ qua) | node tự sinh kiểu `content`, con của section (mục 2.5) |
| dòng `- tên:` ngay dưới heading (v0.2 bỏ qua) | thuộc tính của section |

Chiến lược tương thích: file có `kg: 0.2` (hoặc không ghi phiên bản) đọc theo luật v0.2. File `kg: 0.3` đọc theo luật mới. Ngoài ra có lệnh `king migrate file.kg.md` để chuyển tự động, ít nhất cho các mẫu trong bảng trên.

---

## 4. Tác động (phân tích, chưa làm)

| Phần | Thay đổi |
|---|---|
| Parser | đọc hai lượt (kiểu, rồi thể hiện); bộ đọc giá trị 7 kiểu, có lồng nhau; link độc lập; mở rộng `each`; kế thừa thuộc tính và tùy chọn kiểu |
| Kiểm lỗi | thuộc tính chưa khai báo / sai kiểu / thiếu `!`; kiểu cha không tồn tại; vòng kế thừa; đầu mút link sai `from=`/`to=` (sau khi tách); trùng cạnh không thứ tự với `symmetric` |
| JSON | `graph.types` thành cây (`parent`, `root: node\|link`, `attrs`, `meta`); node có `type` và `types` (chuỗi tổ tiên); link có `id?`, `attrs`, `via?`, `symmetric?`; giá trị mang kiểu (Content khác Str) |
| `ops.py` (sửa ngược) | thêm, xóa, sửa link độc lập; sửa thuộc tính theo từng dòng; đổi kiểu node (`@a x` → `@b x`); sửa `members` |
| Editor | Inspector hiện thuộc tính theo kiểu (ô nhập theo Num/Bool/List…); tạo link ở chế độ Nối sinh `@kiểu: from A to B` hay `- link:` (tùy chọn); tô màu dòng khai báo kiểu khác dòng thể hiện |
| Views | Graph: cạnh `symmetric` không mũi tên, cạnh nhóm → nhóm. Module: hộp nhóm từ `members`, cạnh giữa hai hộp. Tree: nhánh theo kiểu. Book: thuộc tính theo kiểu |
| Style | `type=` khớp cả kiểu con; bộ chọn theo thuộc tính (`level=2`); bộ chọn link theo kiểu link con |
| Typst | mỗi node thành `#node(type: …, attrs: (…))[content]`; Content `[ ]` chép nguyên văn |

---

## 5. Lộ trình đề xuất

1. **Giá trị có kiểu:** bộ đọc 7 kiểu, dùng cho `meta` của v0.2 (không phá cú pháp cũ). Test cho từng kiểu.
2. **Kiểu và kế thừa:** `@cha tên = Nhãn`, thuộc tính khai báo, tạo thể hiện `@kiểu id:`. Schema v0.2 vẫn đọc được.
3. **Link độc lập:** `@kiểu [id]: from A to B`, thuộc tính trên link, `symmetric`.
4. **Nhóm:** `group` + `members`, `each`, `via`, đổi tên cạnh tự sinh.
5. **Editor và views:** Inspector theo kiểu, sửa link độc lập, Module vẽ cạnh nhóm.
6. **Migrate và tài liệu:** `king migrate`, cập nhật `docs/documentation.kg.md`, viết lại ví dụ `hinh-thcs` sang v0.3.
7. **Typst:** `king typst`, theo `dev/plan-v1/todo-list.md`.

Mỗi bước kết thúc khi: test xanh, mọi file ví dụ qua `--strict`, và tài liệu đã cập nhật.

---

## 6. Quyết định cần chốt

| # | Câu hỏi | Đề xuất |
|---|---|---|
| Q1 | Thụt lề trước `@` có nghĩa (cây kiểu) không? | Thụt lề **không** diễn tả cây kiểu (cha chỉ là từ sau `@`). Nhưng theo luật block (mục 2.4), `@` phải ở **cột đầu tiên** mới mở block: dòng `  @x` có thụt lề là dòng nối tiếp, và `@x` trong đó là tham chiếu |
| Q2 | Kiểu và ID chung một không gian tên? | Tách riêng, nhưng **cảnh báo** khi trùng tên, để `@exercise mcq` không bao giờ mơ hồ |
| Q3 | Viết tắt `A -> B` / `A -- B` cho link? | Có, bên cạnh dạng chuẩn `from A to B` |
| Q4 | Tên cạnh tự sinh cho quan hệ thuộc nhóm | `member` là danh từ, trái quy ước tên dùng động từ nguyên mẫu. Dùng `contain` cho mọi trường hợp (section, nhóm, `contain` cũ) và bỏ `contains`. **Đề xuất: `contain`** |
| Q5 | Ký hiệu thuộc tính bắt buộc | `- role!: Str`; hoặc `- role: Str required`. **Đề xuất `!`**, ngắn và đã quen từ `loại!()` (dù khác nghĩa, cần ghi rõ trong tài liệu) |
| Q6 | `label` thay `title` trong JSON | Có; xuất cả hai đến v0.4 |
| Q7 | `- meta:` dạng gộp còn cần không khi đã có thuộc tính từng dòng? | Giữ, vì gọn cho nhiều cờ ngắn (`- meta: dag=true, symmetric=true`) |
| Q8 | Trong Content `[ ]`: có nhận `@id` là tham chiếu, có cắt comment `//` không? | Nhận `@id` (giống v0.2); **không** cắt `//` (Typst dùng `//` làm comment riêng của nó) |
| Q9 | Cạnh nhóm → nhóm (không `each`) có được dùng ở Graph không? | Có: vẽ như cạnh giữa hai node nhóm; Module vẽ giữa hai hộp |
| Q10 | Quy ước tên: `members` là danh từ, trái quy ước động từ nguyên mẫu | Dùng `contain` làm tên thuộc tính của `group` (`- contain: (a, b)`), khớp với v0.2 và Q4. **Đề xuất: `contain`** thay `members` |
| Q11 | Cho viết tắt `#4`, `#5` thay `####`, `#####`? | **Không.** `#4 Tiêu đề` không còn là heading Markdown hợp lệ (trình xem Markdown khác sẽ hiện nó như một dòng chữ), trái nguyên tắc "file `.kg.md` là Markdown hợp lệ". Nếu sâu quá 3 cấp thì nên dùng nhóm (`group`) thay cho heading |
| Q12 | Block `@` kết thúc ở đâu: chỉ trước `@` đầu dòng kế tiếp, hay cả trước heading? | **Cả trước heading** (và hết file). Nếu chỉ dừng ở `@`, heading sau node cuối cùng của một section sẽ bị nuốt vào node đó. Section là block cha, block `@` không vượt qua ranh giới section. Ngoài ra `@` phải ở cột 1, khác v0.2 (v0.2 nhận cả `@` sau khoảng trắng): file v0.2 có dòng nối tiếp bắt đầu bằng `@id` thụt lề sẽ đổi nghĩa từ node mới thành tham chiếu. Lệnh `king migrate` cần cảnh báo trường hợp này |
| Q13 | Kiểu `content` trùng tên với thuộc tính `content` của node. Có gây nhầm không? | **Đã chốt: bỏ thuộc tính `content`.** Nội dung viết bằng văn bản thường sau dòng `#` / `@` và sau dãy thuộc tính `- tên:` (mục 2.6). Tên `content` chỉ còn là kiểu node dựng sẵn (mục 2.5) và tên trường dữ liệu trong JSON |
| Q14 | Nhãn của node `content` | Để **trống** trong Graph và Tree (hiện biểu tượng ¶), vì nhãn là tiêu đề section sẽ trùng với chính section |
| Q15 | Có cho viết node `content` tường minh giữa các node không (`@content gioi-thieu:` + văn bản)? | **Có.** Cùng một kiểu `content`: tự sinh khi văn bản nằm ngay dưới heading, viết tay khi cần chen đoạn văn ở chỗ khác. Book hiện cả hai giống nhau |
| Q16 | ID node `content` của văn bản đầu file (trước heading đầu tiên) | `<tên-file>-content` (ví dụ `vidu-content`). Hoặc coi đó là thuộc tính `content` của chính file / đồ thị (`graph.content` trong JSON) và không sinh node. **Đề xuất: sinh node**, để đối xử thống nhất với section |

Nếu chốt Q4 và Q10 theo đề xuất, mục 1.5 đổi `members` thành `contain` và cạnh tự sinh thành `contain`. Nhờ đó v0.2 → v0.3 gần như không phải đổi tên gì.

---

## 7. Todo

- [ ] **Thảo luận: có nên có, hay cho phép, một kiểu "meta programming" để viết gọn hơn không?**

  Nhu cầu: nhiều node giống nhau chỉ khác vài chỗ (cùng kiểu, cùng thuộc tính, cùng link tới một đích) khiến file dài và lặp.

  Các mức có thể có, từ nhẹ đến mạnh:

  | Mức | Ví dụ | Ghi chú |
  |---|---|---|
  | 0. Kế thừa kiểu (đã có trong plan này) | `@node hinh = Hình` + `- level: Num = 1`, rồi `@hinh x:` | giá trị mặc định nằm ở kiểu |
  | 1. Mặc định theo section | dưới `# Hình khối`: `- default: type=khoi, level=2` áp cho mọi node trong block section | thuần khai báo, dễ đọc, dễ sửa ngược |
  | 2. Khai báo hàng loạt | `@khoi (lang-tru, chop, cau): …` tạo nhiều node một lần; `@specialize: from each (lang-tru, chop) to hinh-khoi` (đã có nhờ `each`) | vẫn thuần khai báo |
  | 3. Mẫu (template / macro) | `@template bai-tap(n, de) = …` rồi `@use bai-tap(1, "…")` | bắt đầu khó đọc; editor khó sửa ngược node sinh ra |
  | 4. Vòng lặp, biểu thức | `@for i in range(1, 10): @exercise bai-{i}: …` | gần một ngôn ngữ lập trình; mất tính "văn bản là nguồn duy nhất, dễ đọc" |

  Câu hỏi cần trả lời trước khi chọn:
  - **Sửa ngược:** node do macro hay vòng lặp sinh ra thì Inspector sửa vào đâu? Mỗi node phải có `line` trỏ về văn bản gốc. Với mức 3–4, một dòng sinh nhiều node, nên sửa một node có thể phải tách nó khỏi mẫu.
  - **Đọc được:** người (và AI) đọc file có hiểu ngay không, khi không chạy parser?
  - **Kiểm lỗi:** lỗi báo ở dòng nào: ở dòng mẫu hay ở dòng sử dụng mẫu?
  - **Typst:** Typst đã có hàm và vòng lặp. Phần lập trình có nên để Typst làm, còn `.kg.md` chỉ khai báo?
  - **An toàn:** không cho chạy code tùy ý khi parse (file tải từ nơi khác).

  **Cập nhật 2:** bỏ hướng macro `@parser`; chỉ parse bằng Python (xem [plan-v2a.md](plan-v2a.md)).

  ~~**Cập nhật:** đã chọn mức 3 theo kiểu macro **văn bản → văn bản** (`@parser`), xem [parser-macro.md](parser-macro.md). Macro chỉ sinh KING lõi rồi đi qua parser thường, nên vẫn giữ `line`, kiểm lỗi và sửa ngược được. Mức 4 vẫn không làm trong cú pháp; vòng lặp, nếu cần, nằm trong script `run` của macro.~~

  Đề xuất ban đầu (cần thảo luận): **làm mức 0–2** (thuần khai báo, giữ được `line`, sửa ngược được); **cân nhắc mức 3** sau khi có nhu cầu thật; **không làm mức 4** trong `.kg.md`, mà để phần sinh nội dung lặp cho Typst hoặc cho một script ngoài sinh ra file `.kg.md`.
