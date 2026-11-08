---
kg: 0.2
---

# Plan v1: KING Markdown @plan-v1

Chuẩn hóa từ `plan-v1.md` (ghi chú hội thoại) sang cú pháp `.kg.md` v0.2.

## Tên gọi @ten-goi

@king-markdown: KING Markdown
- meta: type=decision, status=chot, full="Knowledge In Nodes & Graphs"
- content: Tên ngôn ngữ. Đặt theo cách gọi các phương ngữ (dialect) của Markdown, nên người đọc hiểu ngay đây là "một dạng Markdown mở rộng" và tên ngắn KING không còn mơ hồ.
- link: part-of(), follows(phuong-ngu)

@phuong-ngu: Tiền lệ phương ngữ Markdown
- meta: type=reference
- content: GitHub Flavored Markdown; R Markdown (`.Rmd`); MyST Markdown (tài liệu khoa học); MDX.
- link: part-of()

### Quy ước dùng tên @quy-uoc

@duoi-file: Đuôi file
- meta: type=convention, value=".kg.md"
- content: Tự giải thích: KING, và là Markdown.
- link: part-of(), names!(king-markdown)

@ten-repo: Tên repo
- meta: type=convention, value=king-markdown
- link: part-of(), names!(king-markdown)

@goi-python: Gói Python và lệnh
- meta: type=convention, package=king-markdown, import=king_markdown, command=king
- content: Cài bằng `pip install king-markdown`, gọi lệnh `king`.
- link: part-of(), names!(king-markdown)

@slogan: Slogan
- meta: type=convention, value="Knowledge is KING."
- link: part-of(), names!(king-markdown)

@ten-truong: Tên trường dùng động từ nguyên mẫu
- meta: type=convention, value="ask, show, link, contain"
- content: Tên trường và khóa meta dùng động từ tiếng Anh nguyên mẫu, chữ thường: `contain`, không viết `contains`. Ngoại lệ giữ để tương thích: `content`, `meta`, `type`, `needs`, `part-of`.
- link: part-of()

### Ưu điểm @uu-diem

@de-tim: Dễ tìm kiếm
- meta: type=reason
- content: Tìm "KING Markdown" ra đúng project, không lẫn với các thứ khác tên King.
- link: part-of(), supports(king-markdown)

@tach-ten-app: Tách tên app khỏi tên ngôn ngữ
- meta: type=reason
- content: Sau này nếu có app editor riêng, có thể đặt tên khác cho app mà ngôn ngữ vẫn là KING Markdown.
- link: part-of(), supports(king-markdown)

## Cấu trúc repo @cau-truc-repo

@cay-thu-muc: Cây thư mục đề xuất
- meta: type=layout
- content: Bố cục cho repo `king-markdown`. Bản gốc ghi `knotebook`; đã đổi theo quy ước tên ở trên.
```text
king-markdown/
├── README.md            giới thiệu, ảnh chụp màn hình, cách cài
├── LICENSE
├── pyproject.toml       cài bằng: pip install -e .
├── .gitignore
├── docs/
│   ├── spec.md          đặc tả ngôn ngữ .kg.md
│   ├── architecture.md
│   └── plan.md
├── src/king_markdown/
│   ├── __init__.py
│   ├── parser.py        ← kgmd.py
│   ├── server.py        ← kgserve.py (phần HTTP)
│   ├── ops.py           ← lớp Doc và các op_* tách ra
│   ├── cli.py           lệnh: king serve | parse | html
│   └── web/
│       ├── index.html
│       ├── app.css
│       └── js/          explorer.js, editor.js, graph.js, book.js
├── templates/           schema.kg.md, style.kg.md mẫu
├── examples/
│   └── python-course/   vidu.kg.md và các file liên quan
├── tests/
│   ├── fixtures/        các file .kg.md đúng và sai
│   ├── test_parser.py
│   └── test_ops.py
└── .github/workflows/ci.yml   chạy test và king parse --strict trên examples
```
- link: part-of(), needs(ten-repo, goi-python)

### Tài liệu @r-docs

@spec: docs/spec.md
- meta: type=file, from="README.md"
- content: Đặc tả ngôn ngữ `.kg.md`.
- link: part-of()

@architecture: docs/architecture.md
- meta: type=file, from="ARCHITECTURE-v1.md"
- link: part-of()

@doc-plan: docs/plan.md
- meta: type=file, from="plan.md"
- link: part-of()

### Mã nguồn @r-src

@parser: src/king_markdown/parser.py
- meta: type=file, from="kgmd.py"
- content: Parser duy nhất: `.kg.md` → JSON, kiểm lỗi theo schema, tính style.
- link: part-of()

@ops: src/king_markdown/ops.py
- meta: type=file, from="kgserve.py"
- content: Lớp `Doc` và các hàm `op_*` tách khỏi server.
- link: part-of(), needs(parser)

@server: src/king_markdown/server.py
- meta: type=file, from="kgserve.py"
- content: Phần HTTP của server cục bộ.
- link: part-of(), needs(parser, ops)

@cli: src/king_markdown/cli.py
- meta: type=file, command="king serve | parse | html"
- link: part-of(), needs(parser, server)

@web: src/king_markdown/web/
- meta: type=folder, from="editor.html"
- content: `index.html`, `app.css`, `js/` gồm explorer.js, editor.js, graph.js, book.js.
- link: part-of(), needs(server)

### Mẫu, ví dụ, kiểm thử @r-extra

@templates: templates/
- meta: type=folder, from="schema.kg.md, style.kg.md"
- content: Bản mẫu schema và style, editor chép sang khi thư mục chưa có.
- link: part-of()

@examples: examples/python-course/
- meta: type=folder, from="vidu.kg.md"
- link: part-of(), needs(templates)

@tests: tests/
- meta: type=folder
- content: `fixtures/` (file `.kg.md` đúng và sai), `test_parser.py`, `test_ops.py`.
- link: part-of(), needs(parser, ops)

@ci: .github/workflows/ci.yml
- meta: type=file
- content: Chạy test và `king parse --strict` trên examples.
- link: part-of(), needs(tests, examples, cli)

## Yêu cầu đối với html

@yeu-cau-html
- meta: contain=menu-html

@menu-html 
- ask: it should contain: File (open folder), View (graph- first focus, tree, book), Format (node, link, font, size, color, border) 

## todo list 

@code 
- ask: [giao diện app như vscode, cần có nền đen, style md, nhưng bổ sung các trường của meta, hay link type phải khác màu]


## Việc cần làm @viec

@kiem-tra-ten: Kiểm tra tên trên GitHub và PyPI
- meta: type=task, status=todo
- ask: Tra xem `king-markdown` đã có trên GitHub và PyPI chưa, trước khi tạo repo.
- link: part-of(), needs(king-markdown)

@tao-repo: Tạo repo theo cây thư mục
- meta: type=task, status=todo
- link: part-of(), needs(kiem-tra-ten, cay-thu-muc)
