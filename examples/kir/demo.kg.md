---
kg: v0.4
title: Ví dụ KING IR
---

# Ví dụ KING IR v0.4

Dòng này là văn xuôi, không phải lệnh. Liên hệ: alice@gmail.com (`@` giữa dòng là văn bản).
\@add dòng này bắt đầu bằng \@ nên là chữ thường, không phải lệnh.

## Kiểu và người
@add Person is-a Type          // Type viết hoa chỉ là quy ước
@add alice is-a person
@add Bob is-a Person           // không phân biệt hoa thường: bob = Bob
@add carol is-a person
@add alice friend-of bob
@add carol friend-of BOB
@add f1 = alice knows carol    // phát biểu có tên

## Giá trị
@add alice email "alice@gmail.com"
@add alice age 30
@add alice score 3.14
@add alice active true
@add bob nickname none
@add alice quote "nói \"xin chào\" // không phải comment"
@add contact = alice.email is-a value   // a.b: thuộc tính email của alice
@add alice = alice.email                // `=` ở vị trí link: cạnh key `=`

## Node ẩn danh và node suy ra
@add _ likes alice
@add _ likes alice
@add parents = ?x friend-of bob         // chỉ lưu, chưa tính

## Ngôn ngữ mới và block
@add rust is-a language

@block hello
```python
@decorator
def hi():  // giữ nguyên, không phải comment KING
    return "hi"
```

@block snippet
```rust
fn main() {} // comment của rust
```

@ask ?x friend-of bob
@ask ?x is-a person, ?x friend-of ?y
