---
kg: 0.2
---

# Kiểu node

@concept: Khái niệm
- meta: kind=type, allow="role, important"

@group: Nhóm
- meta: kind=type, allow="important"

@module: Module
- meta: kind=type

@dien-tich
- meta: kind=type

# Khóa meta

@role: Vai trò
- meta: kind=key, values="Nạp | Xuất | Cầu | Phụ", required=true

@important: Quan trọng
- meta: kind=key, value=bool

# Loại link

@export: Xuất ra node chứa
- meta: kind=link

@needs: Cần biết trước
- meta: kind=link, dag=true

@part-of: Là phần của
- meta: kind=link, dag=true, to=group
