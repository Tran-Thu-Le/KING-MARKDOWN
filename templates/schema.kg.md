---
kg: 0.3
---

Schema hệ thống. Import: use: - king/schema.node: Concept, Group  /  - king/schema.link: needs, part-of
Node type viết hoa chữ đầu; link type viết thường, gạch nối.

# Node types

@node Concept
- label: Khái niệm

Một khái niệm, định nghĩa hay định lý.

@node Group
- label: Nhóm node

Gom các node cùng chủ đề; vẽ thành hình chữ nhật bo góc.

@node Module
- label: Module

@node Example
- label: Ví dụ

Ví dụ minh họa, bài mẫu, đoạn code chạy thử.

@node Warning
- label: Lưu ý

Lỗi hay gặp, điều cần tránh.

# Link types

@link needs
- label: Cần biết trước
- inverse: needed-by
- dag: true

@link part-of
- label: Là phần của
- inverse: parts
- dag: true

@link export
- label: Xuất ra node chứa
