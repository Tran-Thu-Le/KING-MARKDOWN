# KING Markdown

**KING Markdown** (Knowledge In Nodes & Graphs) là Markdown mở rộng để viết **đồ thị tri thức** (node, cây gom nhóm, link có kiểu) bằng văn bản thường. Đuôi file `.kg.md`. Dữ liệu, schema và style đều viết bằng cùng một cú pháp.

*Knowledge is KING.*

```markdown
---
kg: 0.3
use:
- king/schema.node: Concept, Group
- king/schema.link: part-of, needs
- king/style
---

# Toán @toan

@node tich-phan
- label: Tích phân
- type: Concept
- role: Xuất
- link part-of: (giai-tich)
- link needs: (dao-ham)

Diện tích dưới đường cong, nối với @dao-ham.
```

## Cài đặt

Cần Python 3.9 trở lên, không phụ thuộc thư viện ngoài. Trình duyệt tải `vis-network` từ CDN.

```bash
pip install -e .
```

## Dùng

```bash
king serve examples/python-course                      # mở editor trên trình duyệt; đóng trang thì server dừng (--keep để giữ)
king parse examples/python-course/vidu.kg.md -o graph.json
king parse bai.kg.md -o graph.json --strict            # thoát mã 1 nếu có lỗi (CI)
king html  bai.kg.md bai.html                          # HTML tĩnh, chỉ xem
```

Chưa cài thì chạy bằng `python -m king_markdown ...` với `PYTHONPATH=src`.

## Editor

- Hai vùng, mỗi vùng có tab; nút **+** thêm view: **Text**, **Graph**, **Tree**, **Book**, **Module**. Mọi view đi theo văn bản.
- **Graph** mặc định xếp dạng cây từ trái sang phải trên lưới. Chọn bố cục ở ô sổ xuống (hoặc **L**): Thụt lề (mặc định) → Cây cân → Tỏa tròn → Lực; **Shift+L** xếp lại, **G** bật/tắt lưới. Vị trí kéo tay được lưu và giữ khi sửa file.
- **Ctrl+S** lưu. **Ctrl+H** tạm hiện node bị ẩn bằng `- hide: all` hoặc `- hide: graph, module`.
- Tô màu `.kg.md` trong VS Code: cài extension *Highlight*; cấu hình có sẵn trong [.vscode/settings.json](.vscode/settings.json).

## Thư mục

| Đường dẫn | Vai trò |
|---|---|
| [docs/documentation.kg.md](docs/documentation.kg.md) | Tài liệu chính (tiếng Anh, viết bằng KING Markdown): mục tiêu và tác giả, cú pháp cơ bản, cú pháp nâng cao, kế hoạch cải tiến. Xem bằng `king serve docs` hoặc `docs/documentation.html` |
| [docs/architecture.md](docs/architecture.md) | Kiến trúc parser, server, editor (cho người phát triển) |
| [src/king_markdown/parser.py](src/king_markdown/parser.py) | Parser 0.3: `.kg.md` → JSON (networkx); `values.py` đọc giá trị; `legacy.py` là parser v0.2 (file style, ops) |
| [src/king_markdown/ops.py](src/king_markdown/ops.py) | Lớp `Doc` và các phép sửa văn bản `op_*` |
| [src/king_markdown/server.py](src/king_markdown/server.py) | Server HTTP cục bộ cho editor |
| [src/king_markdown/cli.py](src/king_markdown/cli.py) | Lệnh `king serve \| parse \| html` |
| [src/king_markdown/web/](src/king_markdown/web/) | Giao diện editor: `index.html`, `app.css`, `js/` |
| [templates/](templates/) | `schema.kg.md`, `style.kg.md` mẫu; editor chép sang thư mục chưa có |
| [examples/python-course/](examples/python-course/) | Ví dụ `vidu.kg.md` kèm schema, style và bản HTML tĩnh |
| [examples/hinh-thcs/](examples/hinh-thcs/) | Mini project hình học: `tu-giac.kg.md` và `solid.kg.md` (cây `specialize`, dùng schema/style của thư mục), `tam-giac.kg.md` (schema trong file, style riêng `tam-giac-style.kg.md`); `hinh1/2/3.kg.md` cùng một bài Hình tròn, chỉ khác cách gắn schema/style: của hệ thống (`use: king/...`), của thư mục, file style riêng |
| [examples/tri-thuc/](examples/tri-thuc/) | Tri thức chung: `dong-vat.kg.md` (phân loại động vật, `part-of`) và `quan-he.kg.md` (quan hệ bạn bè, giải Nobel, quê hương giữa các nhà khoa học) |
| [tests/](tests/) | `python -m unittest discover -s tests` |
| [dev/](dev/) | Kế hoạch phát triển: `plan-v1`, `plan-v2` (cú pháp 0.3), `plan-v3` (triển khai 0.3 và việc tiếp theo); `tools/` công cụ chuyển 0.2 → 0.3 |
