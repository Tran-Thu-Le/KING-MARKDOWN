---
kg: 0.2
---

@hinh: Hình
- meta: kind=type

@specialize: Là trường hợp riêng của
- meta: kind=link, dag=true, from=hinh, to=hinh

Cho bài Hình tròn (hinh2.kg.md): cùng từ vựng với schema hệ thống.

@concept: Khái niệm
- meta: kind=type, allow="role, important"

@group: Nhóm
- meta: kind=type, allow="important"

@role: Vai trò
- meta: kind=key, values="Nạp | Xuất", required=true

@important: Quan trọng
- meta: kind=key, value=bool

@part-of: Là phần của
- meta: kind=link, dag=true, to=group

@needs: Cần biết trước
- meta: kind=link, dag=true
