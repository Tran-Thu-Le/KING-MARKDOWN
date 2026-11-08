# KING Markdown

**KING Markdown** (Knowledge In Nodes & Graphs) là Markdown mở rộng để viết **đồ thị tri thức** (node, cây gom nhóm, link có kiểu) bằng văn bản thường. Đuôi file `.kg.md`. Dữ liệu, schema và style đều viết bằng cùng một cú pháp.

*Knowledge is KING.*

```markdown
---
kg: 0.2
use: schema, style
---

# Toán @toan

@tich-phan: Tích phân
- meta: type=concept, role=Xuất
- content: Diện tích dưới đường cong, nối với @dao-ham.
- link: part-of(giai-tich), needs(dao-ham)
```

## Cài đặt

Cần Python 3.8 trở lên, không phụ thuộc thư viện ngoài. Trình duyệt tải `vis-network` từ CDN.

```bash
pip install -e .
```

## Dùng

```bash
king serve examples/python-course                      # editor: trái là văn bản, phải là đồ thị; đóng trang thì server dừng
king parse examples/python-course/vidu.kg.md -o graph.json
king parse bai.kg.md -o graph.json --strict            # thoát mã 1 nếu có lỗi (CI)
king html  bai.kg.md bai.html                          # HTML tĩnh, chỉ xem
```

Chưa cài thì chạy bằng `python -m king_markdown ...` với `PYTHONPATH=src`.

## Thư mục

| Đường dẫn | Vai trò |
|---|---|
| [docs/documentation.kg.md](docs/documentation.kg.md) | Tài liệu chính (tiếng Anh, viết bằng KING Markdown): mục tiêu và tác giả, cú pháp cơ bản, cú pháp nâng cao, kế hoạch cải tiến. Xem bằng `king serve docs` hoặc `docs/documentation.html` |
| [docs/architecture.md](docs/architecture.md) | Kiến trúc parser, server, editor (cho người phát triển) |
| [src/king_markdown/parser.py](src/king_markdown/parser.py) | Parser: `.kg.md` → JSON (networkx), kiểm lỗi theo schema, tính style |
| [src/king_markdown/ops.py](src/king_markdown/ops.py) | Lớp `Doc` và các phép sửa văn bản `op_*` |
| [src/king_markdown/server.py](src/king_markdown/server.py) | Server HTTP cục bộ cho editor |
| [src/king_markdown/cli.py](src/king_markdown/cli.py) | Lệnh `king serve \| parse \| html` |
| [src/king_markdown/web/](src/king_markdown/web/) | Giao diện editor: `index.html`, `app.css`, `js/` |
| [templates/](templates/) | `schema.kg.md`, `style.kg.md` mẫu; editor chép sang thư mục chưa có |
| [examples/python-course/](examples/python-course/) | Ví dụ `vidu.kg.md` kèm schema, style và bản HTML tĩnh |
| [examples/hinh-thcs/](examples/hinh-thcs/) | Mini project hình học: `tu-giac.kg.md` (cây `specialize` từ tứ giác tới hình vuông, dùng schema/style riêng) và `tam-giac.kg.md` (schema + style viết chung trong một file); `hinh1/2/3.kg.md` cùng một knowledge graph (bài Hình tròn), chỉ khác cách gắn schema/style: của hệ thống (`use: king/...`), của thư mục, ngay trong file |
| [tests/](tests/) | `python -m unittest discover -s tests` |
| [dev/](dev/) | Ghi chú kế hoạch (plan-v1) |
