# Plan v2a: KING Markdown 0.3 (bản gọn)

Bản chi tiết: [plan-v2.md](plan-v2.md). Syntax mẫu: [plan-v2b.md](plan-v2b.md).

## 1. Mục tiêu và chức năng chính

**Mục tiêu:** viết tri thức bằng văn bản thuần (`.kg.md`), đọc được như Markdown, và sinh ra được đồ thị tri thức (graph JSON), sách (HTML) và Typst.

**Chức năng chính:**
- **Node và link đều là kiểu.** Kiểu gốc là `node` và `link`. Kiểu mới kế thừa từ kiểu có sẵn.
- **Node có thuộc tính, nội dung và node con** (`has`).
- **Link** viết rời (`@link: from A to B`) hoặc gắn trong node (`- link: needs(B)`). Link giữa các nhóm node dùng `each`.
- **Schema và style** viết ở file riêng (`use:`) hoặc ngay trong file dữ liệu. Có bản mặc định của hệ thống (`king/…`).
- **Parser viết bằng Python**, không có macro hay parser tự định nghĩa bằng `.kg.md`.
- **Editor:** các view Graph, Tree, Book, Module và Inspector. Mọi chỉnh sửa trên editor được ghi ngược về file `.kg.md`.

## 2. Syntax cơ bản

### 2.1 Block

| Block | Bắt đầu | Kết thúc |
|---|---|---|
| Section | dòng `#`, `##`, … `######` | trước heading cùng cấp hoặc cấp cao hơn, hoặc hết file |
| Node / link | `@` ở **đầu dòng** | trước `@` đầu dòng tiếp theo, trước heading, hoặc hết file |
| Thuộc tính | các dòng `- ` liền ngay dưới dòng `@` hoặc heading (sau này đổi thành `> `) | ở dòng đầu tiên không bắt đầu bằng `- ` |
| Nội dung | sau dãy thuộc tính, cách **một dòng trắng** | hết block. Mặc định là Markdown hay Typst tùy schema |

```markdown
@node-type node-name: Nhãn
- key: value
- has: sub1, sub2

Nội dung của node (Markdown hoặc Typst).
```

### 2.2 Dòng

| Ký hiệu | Nghĩa |
|---|---|
| `:` | tạo / gán: `@kiểu id: nhãn`, `- key: value` |
| `=` | khai báo: `@node hinh = Hình` (kiểu mới); `- key: Kiểu = mặc-định` |
| `//` | comment tới cuối dòng (trừ khi nằm trong chuỗi hoặc code) |
| `( ) [ ]` | List / Dict, Content |
| `"…"` | chuỗi |
| `` `…` `` | code (giữ nguyên văn) |
| phép toán | `+ - * / %`, so sánh `== != < <= > >=`, logic `and or not` (danh sách cần chốt) |

### 2.3 Kiểu dữ liệu

| Kiểu | Ví dụ |
|---|---|
| Num | `3`, `0.5` |
| Str | `Nạp`, `"có, dấu phẩy"` |
| Bool | `true`, `false` |
| None | `none` |
| List | `(a, b, c)` |
| Dict | `(a=1, b=3)` |
| Content | `[ … ]`, viết Typst, LaTeX, Markdown hoặc Python bên trong; loại nào là do schema quy định |

### 2.4 Kiểu, node, link, node con

```markdown
@node hinh = Hình                  // khai báo kiểu
@hinh vuong: Hình vuông            // tạo node
- has: canh, goc                   // node con
@link needs = Cần                  // khai báo kiểu link
@needs: from dao-ham to tich-phan  // tạo link
```

**Chưa có:** cú pháp khai báo kiểu cho từng node con trong `has`. Phương án ở [plan-v2b.md](plan-v2b.md) mục 5.
