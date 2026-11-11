# Plan v3b: bố cục cây cho Graph và diagnostics

Ngày 2026-11-10, nhánh `v0.3`. Viết sau khi đã dọn `plan-v3` và `examples`.

Plan có hai phần độc lập:
- **A.** Bố cục cây trái → phải trên lưới, dùng làm mặc định cho Graph.
- **B.** Diagnostics theo cấu trúc LSP: trước hết dùng cho editor web, sau này làm `king lsp`.

Làm A trước vì A chỉ đụng tới `graph.js`. **A đã xong (2026-11-11)**: nút ⊢ Cây / ✺ Lực, phím L và Shift+L. Mục 5 (khi bật Ctrl+H, chèn node ẩn vào cây) chưa làm: node ẩn hiện lại ở vị trí ngẫu nhiên, Shift+L để xếp lại.

---

## A. Graph: bố cục cây trên lưới, mặc định

### Mục tiêu

Lecture có cấu trúc chương → section → group → khái niệm. Graph mặc định nên xếp theo cấu trúc này:
- gốc ở bên trái, mỗi cấp con lùi sang phải một cột;
- anh em xếp dọc;
- mọi node nằm đúng điểm lưới (`GRID = 40`).

Bố cục "lực" (physics) hiện tại vẫn giữ, nhưng chỉ chạy khi người dùng chọn.

### Hiện trạng

- `graph.js` có lưới, có snap khi kéo, và lưu vị trí trong `kgpos:root|name`.
- Lần đầu mở một file, graph chạy physics `forceAtlas2Based` rồi tắt.
- Node đã có vị trí lưu thì được ghim, chỉ node mới được xếp.

### Thiết kế

1. **Cây dùng để xếp:** mỗi node chọn đúng một cha, theo thứ tự ưu tiên:
   1. `part-of` (node nằm trong group);
   2. `contains` (section chứa node, chứa sub-section);
   3. `parent`.

   Các link khác (`needs`, `mention`, …) không ảnh hưởng vị trí, chỉ vẽ đè lên. Node không có cha nào làm gốc, xếp theo thứ tự dòng trong file.

2. **Thuật toán:** tự viết, khoảng 60 dòng, không dùng `layout.hierarchical` của vis.
   - Duyệt cây theo thứ tự dòng trong file (giống thứ tự đọc của lecture).
   - Mỗi lá chiếm một hàng: `y = hàng × 2·GRID`.
   - Cha nằm ở hàng của con đầu tiên, căn trên, cho dễ đọc như mục lục.
   - Cột: `x = độ sâu × 6·GRID` (khoảng 240 px; chỉnh được bằng hằng số `COL`).
   - Kết quả là toạ độ nguyên theo bội số của `GRID`, nên khớp sẵn với lưới.

   Không dùng `layout.hierarchical` vì nó khoá trục, không tương thích với kéo tự do và lưu vị trí, và không cho chọn cha theo thứ tự ưu tiên ở trên.

3. **Chế độ:** thêm nút `#bLayout` (phím **L**) xoay vòng giữa hai chế độ:
   - `Cây` (mặc định): xếp theo cây ở trên.
   - `Lực`: physics như cũ.

   Chế độ lưu riêng cho từng file trong localStorage, khoá `kglayout:root|name`.

4. **Quan hệ với vị trí đã lưu:**
   - Node đã kéo tay (có trong `kgpos`) **giữ nguyên vị trí**, giống hiện tại.
   - Node mới: ở chế độ Cây, xếp theo cây rồi đẩy xuống hàng trống gần nhất nếu đè lên node đã ghim. Ở chế độ Lực, xếp như hiện tại.
   - Lệnh **Xếp lại** (Shift+L) xoá `kgpos` của file và xếp lại toàn bộ theo chế độ hiện tại. Lệnh này hỏi xác nhận trước.

5. **Node ẩn** (`hide`) không chiếm hàng; khi bật Ctrl+H thì chèn vào và xếp lại phần bị ảnh hưởng.

### Các bước

| # | Việc | Kiểm tra |
|---|---|---|
| A1 | Hàm `treeParent(g)` trả về bảng con → cha theo thứ tự ưu tiên ở mục 1, có chặn vòng | test bằng `node` trên JSON của `python-lecture.kg.md`: mỗi node ≤ 1 cha, không vòng |
| A2 | Hàm `treeLayout(g, visible)` trả về `{name: {x, y}}`, toạ độ là bội số của `GRID` | trên 3 file mẫu: không có hai node trùng ô; cha nằm bên trái con |
| A3 | Nối vào `render`: lần đầu mở file dùng `treeLayout`; physics chỉ chạy ở chế độ Lực | headless Edge: mở `python-lecture`, chụp ảnh; mở lại sau khi thêm 1 node, các node cũ không đổi vị trí |
| A4 | Nút `#bLayout`, phím L, lưu `kglayout`; Shift+L để xếp lại | đổi chế độ rồi tải lại trang, chế độ vẫn giữ |
| A5 | Cập nhật `docs/documentation.kg.md` (node `views`) và tạo lại các HTML | `unittest` OK; 0 lỗi trên mọi file mẫu |

**Rủi ro: thấp.** Toàn bộ thay đổi nằm trong `graph.js` và một nút trong `index.html`; parser không đổi. Rủi ro chính là vị trí đã lưu của người dùng, nhưng mục 4 giữ nguyên chúng.

---

## B. Diagnostics (chuẩn LSP), rồi `king lsp`

### Đánh giá trước khi làm

**Dễ làm không? Dễ, với bước 1.**
- Parser đã gom mọi lỗi vào hai danh sách `errors` và `warnings`, mỗi mục là `{line, msg, file?}`.
- Có khoảng 35 chỗ tạo lỗi, tất cả đi qua `self.err`, `self.warn` hoặc `errors.append` trong `cut_blocks`.
- Chuyển sang dạng LSP chỉ cần **một hàm chuyển đổi**, không phải sửa từng chỗ.

**Có dễ làm hỏng code hiện tại không? Không, nếu chỉ thêm và không đổi.**
- Giữ nguyên `graph.errors` và `graph.warnings`, vì Problems, `S.bad`, CLI và test đang dùng chúng.
- `diagnostics` là trường **thêm vào** kết quả `build()`, được sinh từ hai danh sách trên. Code cũ không thấy khác biệt.
- Điều duy nhất có thể vỡ: test nào so sánh **toàn bộ** dict kết quả. Bước B0 sẽ kiểm tra việc này.

**Chỗ còn thiếu:**
- **Lỗi chưa có cột.** LSP cần `range` (dòng, cột bắt đầu → dòng, cột kết thúc). Bước đầu gạch cả dòng (bỏ khoảng trắng đầu dòng). Thêm cột chính xác sau, từng loại lỗi một; đây là phần tốn công nhất nhưng không bắt buộc.
- **Chưa có mã lỗi.** Thông báo đang là câu tiếng Việt. Nên thêm `code` (ví dụ `KG101`) để editor lọc được và để có quick-fix sau này. Việc này cũng làm dần.
- **Lỗi từ file import** (có `file`): LSP gắn diagnostics theo từng file (URI). Bước đầu gắn vào dòng `use:` / `import:` của file đang mở, kèm `relatedInformation` trỏ sang file gốc.

**Phần khó nhất nằm ở bước 2, không phải bước 1:** VS Code cần một extension nhỏ viết bằng TypeScript để khởi chạy `king lsp`. Cách làm cụ thể ở mục B9.

### Định dạng

`king parse` và `/api/parse` (hoặc `/api/check`) trả về:

```json
{
  "graph": { "...": "như hiện tại, giữ errors / warnings" },
  "nodes": [], "links": [],
  "diagnostics": [
    {
      "range": {"start": {"line": 40, "character": 0}, "end": {"line": 40, "character": 18}},
      "severity": 1,
      "code": "KG201",
      "source": "king",
      "message": "không tìm thấy node: lambda",
      "relatedInformation": []
    }
  ]
}
```

- `line` và `character` **đếm từ 0**, theo LSP. Parser hiện đếm dòng từ 1, nên hàm chuyển đổi trừ 1.
- `severity`: 1 là lỗi, 2 là cảnh báo, 3 là thông tin, 4 là gợi ý.
- `character` tính theo **UTF-16**, mặc định của LSP. Tiếng Việt có dấu nằm trong BMP nên 1 ký tự Python = 1 đơn vị UTF-16; emoji thì không. Hàm chuyển đổi cần tính đúng điều này.

### Các bước triển khai

**Giai đoạn 1: diagnostics trong editor web (chưa cần LSP)**

| # | Việc | Đụng tới | Kiểm tra |
|---|---|---|---|
| B0 | Rà test: có test nào so sánh nguyên dict của `build()` không; ghi lại số test hiện tại (66, skipped=2) | `tests/` | chưa sửa gì |
| B1 | Module mới `diagnostics.py`: `to_lsp(errors, warnings, lines) → list`. Gạch cả dòng (bỏ khoảng trắng đầu dòng); tính UTF-16 | file mới | `tests/test_diagnostics.py`: dòng 1 → 0; dòng trống; dòng có emoji; lỗi từ file import |
| B2 | `Parser.build()` thêm `g["diagnostics"] = to_lsp(...)` | `parser.py`, 1 dòng | toàn bộ test cũ vẫn OK |
| B3 | `king parse --diagnostics` chỉ in diagnostics. Mã thoát khác 0 nếu có lỗi, dùng được cho CI hoặc pre-commit | `cli.py` | chạy trên `examples/` và `python-lecture.kg.md` |
| B4 | `/api/check` (nhẹ: chỉ trả diagnostics), hoặc dùng luôn `/api/parse` | `server.py` | gọi bằng curl |
| B5 | Editor web vẽ **gạch sóng** đỏ/vàng trong lớp tô màu `#hlIn` theo `range`; rê chuột hiện message; Problems đọc từ `diagnostics` | `editor.js`, `app.css`, `graph.js` (Problems) | headless Edge: gõ link sai → có gạch sóng đúng dòng; con trỏ vẫn khớp chữ (đừng để vỡ lại lỗi lệch con trỏ đã sửa) |
| B6 | Thêm `code` cho từng loại lỗi (bảng mã trong `diagnostics.py`), làm theo nhóm: cú pháp KG1xx, tên/kiểu KG2xx, link KG3xx, cảnh báo KG9xx | `parser.py` (các lời gọi `err` / `warn` thêm tham số `code`, mặc định None) | test cũ OK; test mới kiểm tra mã |
| B7 | Thêm cột chính xác cho các lỗi hay gặp: link tới node không có (gạch đúng tên), tên viết sai, kiểu chưa import | `parser.py` (thêm `col` / `end` tùy chọn khi gọi `err`) | test cho từng loại lỗi |

Sau B2 là có thể dừng an toàn: mọi bước sau là thêm, không đổi gì cũ.

**Giai đoạn 2: `king lsp`**

| # | Việc | Ghi chú |
|---|---|---|
| B8 | `king lsp`: vòng lặp đọc stdin theo khung `Content-Length` của JSON-RPC. Xử lý `initialize`, `initialized`, `textDocument/didOpen`, `didChange` (gửi cả file), `didClose`, `shutdown`, `exit`. Mỗi lần đổi: gọi đúng `Parser(...).build()` rồi gửi `textDocument/publishDiagnostics` | chỉ dùng thư viện chuẩn, khoảng 150 dòng. Có thể dùng `pygls`, nhưng sẽ thêm một phụ thuộc. Đợi khoảng 300 ms sau lần gõ cuối mới parse. |
| B9 | Client cho VS Code: chọn một trong hai cách | (a) Extension tối thiểu bằng TypeScript với `vscode-languageclient`, khoảng 40 dòng, đóng gói `.vsix`, đăng ký ngôn ngữ `kgmd` cho `*.kg.md`. (b) Dùng tạm extension "generic LSP client" có sẵn, chỉ cấu hình lệnh `king lsp`. Nên làm (b) để thử, rồi chuyển sang (a). |
| B10 | Thêm dần: `hover` (label, type của node), `definition` (nhảy tới `@node`), `completion` (tên node sau `(`, tên kiểu sau `type:`) | parser đã có `line` của node nên làm được |
| B11 | Tô màu chuẩn: TextMate grammar trong extension ở (a), thay cho cấu hình Highlight bằng regex | lúc đó bỏ `highlight.regexes` trong `.vscode/settings.json` |

**Rủi ro của giai đoạn 2:**
- Parser được gọi rất thường xuyên. Với `python-lecture` (khoảng 1 000 dòng) cần đo thời gian; nếu trên 100 ms thì đợi lâu hơn trước khi parse.
- Parser không được đọc file khác theo đường dẫn tương đối với thư mục hiện tại; phải dùng đường dẫn lấy từ URI của file.
- Parser không bao giờ được ghi gì ra stdout, vì stdout là kênh JSON-RPC. Mọi `print` gỡ lỗi phải chuyển sang stderr.

### Kết luận

| Phần | Độ khó | Nguy cơ làm hỏng code hiện tại |
|---|---|---|
| A. Bố cục cây | vừa | thấp (chỉ `graph.js`) |
| B1–B5. Diagnostics trên web | dễ | rất thấp (chỉ thêm) |
| B6–B7. Mã lỗi, cột chính xác | vừa, nhiều việc vặt | thấp (tham số tùy chọn) |
| B8. `king lsp` | vừa | không có (lệnh mới) |
| B9–B11. Extension VS Code | vừa, cần Node/TypeScript | không có (repo hoặc folder riêng) |

Thứ tự đề xuất: **A1→A5**, rồi **B0→B5** (một đợt), rồi B6–B7 làm dần, cuối cùng B8–B9.
