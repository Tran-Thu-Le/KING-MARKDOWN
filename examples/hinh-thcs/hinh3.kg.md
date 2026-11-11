---
kg: 0.3
use:
- hinh3-style
---

Cùng knowledge graph với hinh1, hinh2; chỉ khác style. Ở đây: schema viết ngay trong file (# Schema); style riêng ở hinh3-style.kg.md (định dạng style đóng băng ở 0.3).

# Hình tròn @hinh-tron-bai

@node hinh-hoc-phang
- label: Hình học phẳng
- type: Group

@node duong-tron
- label: Đường tròn
- type: Concept
- role: Nạp
- link part-of: (hinh-hoc-phang)

Tập hợp các điểm cách điểm O cố định một khoảng R không đổi.

@node hinh-tron
- label: Hình tròn
- type: Concept
- role: Xuất
- important: true
- link part-of: (hinh-hoc-phang)
- link needs: (duong-tron)

Đường tròn cùng các điểm nằm bên trong nó. Diện tích S = πR².

# Schema

@node Concept
- label: Khái niệm

@node Group
- label: Nhóm

@link part-of
- label: Là phần của
- dag: true

@link needs
- label: Cần biết trước
- dag: true
