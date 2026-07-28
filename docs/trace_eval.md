# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

**Đề tài nhóm**: 5. Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả
**Ngày thực hiện**: 2026-07-28

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

> **Mục tiêu**: Chứng minh bài toán "Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả" CẦN dùng ReAct Agent chứ không chỉ Chatbot thuần.

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Agent cần suy luận qua nhiều bước: (1) Xác định mã đơn hàng từ câu hỏi người dùng → (2) Tra cứu trạng thái đơn hàng trong database → (3) Kiểm tra chính sách đổi trả (thời hạn, điều kiện sản phẩm) → (4) Quyết định chấp nhận/từ chối đổi trả và tạo yêu cầu. Mỗi bước phụ thuộc vào kết quả bước trước. |
| 🛠️ **Tool Interaction** | `5/5` | Cần gọi nhiều tool thực tế: `lookup_order` (tra cứu đơn hàng theo mã), `check_return_policy` (kiểm tra chính sách đổi trả theo loại sản phẩm), `create_return_request` (tạo yêu cầu đổi trả). Chatbot thuần KHÔNG THỂ truy cập database đơn hàng thời gian thực — sẽ bịa thông tin đơn hàng (hallucination). |
| 🔀 **Dynamic Decision** | `5/5` | Quyết định ở mỗi bước thay đổi hoàn toàn tùy theo dữ liệu: Nếu đơn hàng không tồn tại → thông báo lỗi. Nếu đơn hàng đã giao quá 30 ngày → từ chối đổi trả. Nếu sản phẩm thuộc danh mục không được đổi → fallback lịch sự. Nếu hợp lệ → tạo yêu cầu đổi trả. Mỗi nhánh logic phụ thuộc vào Observation thực tế từ tool. |
| ⏳ **Long Horizon** | `4/5` | Quy trình đổi trả gồm 3-4 bước xử lý tuần tự (tra cứu → kiểm tra chính sách → xử lý yêu cầu → xác nhận). Không quá dài như planning phức tạp, nhưng đủ để Chatbot thuần không thể xử lý đúng vì thiếu khả năng gọi tool tuần tự và phản hồi dựa trên dữ liệu thực. |
| **TỔNG ĐIỂM FIT** | **19/20** | **KẾT LUẬN: BÀI TOÁN RẤT PHÙ HỢP VỚI REACT AGENT!** |

---

### 📝 Phân tích chi tiết: Tại sao Chatbot KHÔNG đủ cho bài toán này?

| Thành phần | Chatbot có trả lời? | Có evidence thật từ Tool? | Có thực hiện Action? |
| :--- | :---: | :---: | :---: |
| **Tra cứu trạng thái đơn hàng (mã ĐH, ngày mua, sản phẩm)** | ❌ (Bịa thông tin đơn hàng) | ❌ | ❌ |
| **Kiểm tra chính sách đổi trả (thời hạn, điều kiện)** | ⚠️ (Trả lời chung chung, không chính xác theo từng sản phẩm) | ❌ | ❌ |
| **Tạo yêu cầu đổi trả cho khách** | ❌ (Không có side-effect, chỉ nói suông) | ❌ | ❌ |
| **Tư vấn quy trình đổi trả chung** | ✅ (Kiến thức tĩnh) | ❌ | ❌ |

**→ Kết luận**: Chỉ có câu hỏi lý thuyết chung (VD: "Quy trình đổi trả gồm mấy bước?") là Chatbot thuần có thể trả lời. Mọi tác vụ cần dữ liệu thực tế (đơn hàng cụ thể, chính sách theo sản phẩm, tạo yêu cầu) đều **BẮT BUỘC** phải dùng ReAct Agent với Tool.

---

### 🔧 Danh sách Tool gợi ý cho đề tài (Phối hợp với Role 2)

| Tool Name | Mục đích | Input | Output | Side Effect |
| :--- | :--- | :--- | :--- | :--- |
| `lookup_order` | Tra cứu thông tin đơn hàng | `order_id: str` | Thông tin đơn hàng (sản phẩm, ngày mua, trạng thái, giá) | Read-only |
| `check_return_policy` | Kiểm tra chính sách đổi trả | `product_category: str` | Điều kiện đổi trả (thời hạn, yêu cầu) | Read-only |
| `create_return_request` | Tạo yêu cầu đổi trả | `order_id: str, reason: str` | Mã yêu cầu đổi trả + hướng dẫn tiếp theo | **Write** (tạo request mới) |

---

### 🔀 Failure Modes dự kiến (Phối hợp với Role 3)

| Dạng lỗi (Failure Mode) | Biểu hiện thực tế | Cách Agent V2 nên xử lý |
| :--- | :--- | :--- |
| **Mã đơn hàng không tồn tại** | User nhập `ĐH-999999` không có trong database | Tool trả về lỗi → Agent thông báo lịch sự: "Không tìm thấy đơn hàng, vui lòng kiểm tra lại mã." |
| **Đơn hàng quá hạn đổi trả** | Đơn hàng đã giao 45 ngày trước (quá hạn 30 ngày) | Tool trả về thông tin ngày → Agent suy luận quá hạn → Từ chối lịch sự kèm giải thích. |
| **Sản phẩm không được đổi trả** | Sản phẩm thuộc danh mục "Đồ lót / Thực phẩm" không được đổi | `check_return_policy` trả về "Không hỗ trợ đổi trả" → Agent fallback lịch sự. |
| **User không cung cấp mã đơn hàng** | Hỏi "Tôi muốn đổi trả" mà không kèm mã ĐH | Agent dùng Thought để nhận ra thiếu thông tin → Hỏi lại user thay vì bịa mã. |

---

## 🔍 2. SO SÁNH PHẢN HỒI (CHATBOT VS AGENT)

> *(Phần này sẽ được điền ở Mốc 2 & Mốc 3 sau khi chạy test cases thực tế)*

### Test Case #1 — 🟢 Đơn giản (Lý thuyết)
**Câu hỏi**: *(Chờ Role 1 soạn test case)*

#### 🤖 Chatbot Baseline:
* **Phản hồi**: *(Chờ kết quả chạy thực tế)*
* **Nhận xét**: *(Chờ đánh giá)*

#### 🧠 ReAct Agent:
* **Trace Log**: *(Chờ kết quả chạy thực tế)*
* **Nhận xét**: *(Chờ đánh giá)*

---

### Test Case #3 — 🟡 Multi-step (Cần Tool)
**Câu hỏi**: *(Chờ Role 1 soạn test case)*

#### 🤖 Chatbot Baseline:
* **Phản hồi**: *(Chờ kết quả chạy thực tế)*
* **Nhận xét**: *(Chờ đánh giá)*

#### 🧠 ReAct Agent:
* **Trace Log**: *(Chờ kết quả chạy thực tế)*
* **Nhận xét**: *(Chờ đánh giá)*

---

### Test Case #5 — 🔴 Edge Case (Bẫy Guardrail)
**Câu hỏi**: *(Chờ Role 1 soạn test case)*

#### 🤖 Chatbot Baseline:
* **Phản hồi**: *(Chờ kết quả chạy thực tế)*
* **Nhận xét**: *(Chờ đánh giá)*

#### 🧠 ReAct Agent:
* **Trace Log**: *(Chờ kết quả chạy thực tế)*
* **Nhận xét**: *(Chờ đánh giá)*

---

## 📈 3. BẢNG ĐÁNH GIÁ TỔNG HỢP (SCORING RUBRIC)

> *(Phần này sẽ được điền ở Mốc 3 & Mốc 4 sau khi chạy toàn bộ 5 test cases)*

| # | Câu hỏi | Factual (0-2) | Grounding (0-2) | Tool Selection (0-2) | Termination (0-2) | Tổng (0-8) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | *(Chờ test case)* | — | — | — | — | — |
| 2 | *(Chờ test case)* | — | — | — | — | — |
| 3 | *(Chờ test case)* | — | — | — | — | — |
| 4 | *(Chờ test case)* | — | — | — | — | — |
| 5 | *(Chờ test case)* | — | — | — | — | — |

---

## 🔄 4. FAILED TRACE & ROOT CAUSE ANALYSIS (RCA)

> *(Phần này sẽ được điền ở Mốc 3 sau khi phát hiện Failed Trace)*

### Failed Trace #1
* **Câu hỏi gây lỗi**: *(Chờ kết quả)*
* **Biểu hiện lỗi**: *(Mô tả hành vi sai)*
* **Root Cause**: *(Nguyên nhân gốc)*
* **Cách khắc phục (V2)**: *(Giải pháp)*
* **Kết quả sau khi sửa**: *(So sánh Before/After)*
