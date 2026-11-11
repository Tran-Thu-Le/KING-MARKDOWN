# Plan v2b: syntax mẫu

Đi kèm [plan-v2a.md](plan-v2a.md).

## 1. Khai báo kiểu

```markdown
@node hinh = Hình
- level: Num = 1                   // thuộc tính có kiểu và giá trị mặc định
- tags: List = ()

@hinh tu-giac = Tứ giác            // kiểu con, kế thừa từ hinh
- canh: Num = 4

@link needs = Cần
@link friend = Quan hệ bạn bè
- meta: (symmetric=true)
```

## 2. Node

```markdown
@tu-giac hinh-vuong: Hình vuông
- level: 2
- tags: (dac-biet, lop-8)
- size: (w=3, h=2)
- link: is-a(hinh-chu-nhat), is-a(hinh-thoi)
- ask: Thêm hình minh họa.

Hình vuông là tứ giác có bốn cạnh bằng nhau và bốn góc vuông.
Diện tích: $S = a^2$.
```

## 3. Link

```markdown
@needs: from dao-ham to tich-phan             // link không tên
@needs n1: from gioi-han to dao-ham           // link có ID
- label: Cần trước
- weight: 2

@friend: from an to binh                      // symmetric: sinh cả hai chiều
@needs: from each (a, b) to each (c, d)       // 4 link: a→c, a→d, b→c, b→d
```

## 4. Section và nội dung

```markdown
# Đạo hàm @dao-ham-chuong
- level: 1

Phần mở đầu của chương (Markdown).
Sinh ra một node kiểu `content` thuộc section này.

## Định nghĩa

@concept dao-ham: Đạo hàm
- link: needs(gioi-han)

Đạo hàm của $f$ tại $x_0$ …
```

## 5. Node con (`has`): các phương án khai báo kiểu

Hiện tại `- has: sub1, sub2` chưa nói được node con thuộc kiểu gì. Có ba phương án:

```markdown
// A. Dict trong khai báo kiểu: tên vai trò = kiểu
@node tam-giac = Tam giác
- has: (dinh=diem, canh=doan-thang)

// B. Kiểu ngay trong instance, dạng "kiểu id"
@tam-giac abc: Tam giác ABC
- has: (diem A, diem B, diem C)

// C. Node con là block @ thường, chỉ khai báo cha
@diem A: Điểm A
- in: abc
```

Đề xuất: **A cho kiểu, B cho instance.** Node con chưa tồn tại thì parser tự tạo nó theo kiểu khai báo; nếu đã có thì chỉ nối cạnh `has`. Cần chốt.

## 6. Giá trị và Content

```markdown
@exercise b1: Bài 1
- diem: 2.5                         // Num
- done: false                       // Bool
- parent: none                      // None
- ask: "Sửa đề, thêm hình"          // Str có dấu phẩy
- hint: `f'(x) = 2x`                // code, giữ nguyên văn
- de: [                             // Content nhiều dòng (Typst)
  Cho $f(x) = x^2$. Tính $f'(1)$.
  ]
- check: diem >= 2 and done == false  // biểu thức (nếu chốt hỗ trợ phép toán)
```
