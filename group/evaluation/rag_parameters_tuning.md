# Hướng Dẫn Tinh Chỉnh Tham Số RAG Pipeline (Drug Law Chatbot)

Tài liệu này mô tả chi tiết ý nghĩa, phạm vi giá trị và cách tinh chỉnh các tham số trong hệ thống Hybrid RAG nhằm đạt được hiệu năng tối ưu (đo lường qua các chỉ số DeepEval).

---

## 1. Tham Số Phân Đoạn Văn Bản (Chunking Parameters)

### `CHUNK_SIZE`
* **Tệp cấu hình:** `task4_chunking_indexing.py`
* **Ý nghĩa:** Kích thước tối đa của mỗi đoạn văn bản được chia nhỏ (tính bằng số ký tự đối với `RecursiveCharacterTextSplitter`).
* **Phạm vi giá trị:**
  * **Tối thiểu (Min):** `100` ký tự (nhỏ hơn mức này sẽ làm câu văn bị vụn vỡ, mất ngữ cảnh hoàn toàn).
  * **Tối đa (Max):** Giới hạn tối đa của cửa sổ ngữ cảnh đầu vào mô hình Embedding (với `all-MiniLM-L6-v2` là 256 tokens ~ 500 ký tự, với `bge-m3` là 8192 tokens ~ 30,000 ký tự).
  * **Khoảng thông dụng (Typical):** `300` - `1000` ký tự.
* **Cơ sở lựa chọn giá trị mặc định (500):** Cân bằng giữa khả năng chứa trọn vẹn một ý hoàn chỉnh (3-5 câu văn liên tiếp) và giới hạn xử lý (context window) của các mô hình embedding nhỏ, tránh việc dữ liệu bị cắt cụt do vượt giới hạn mô hình.
* **Hướng dẫn tinh chỉnh:**
  * **Tăng lên (ví dụ: 800 - 1000):** Khi tài liệu chứa các phân đoạn lập luận dài, phức tạp.
  * **Giảm xuống (ví dụ: 300 - 400):** Khi tài liệu ngắn gọn, có cấu trúc độc lập cao để giảm nhiễu ngữ cảnh.

### `CHUNK_OVERLAP`
* **Tệp cấu hình:** `task4_chunking_indexing.py`
* **Ý nghĩa:** Độ dài của phần văn bản trùng lặp giữa hai đoạn kề nhau.
* **Phạm vi giá trị:**
  * **Tối thiểu (Min):** `0` (không trùng lặp).
  * **Tối đa (Max):** Nên nhỏ hơn `50%` của `CHUNK_SIZE` (tránh trùng lặp quá mức gây tốn token và tăng dung lượng lưu trữ thừa).
  * **Khoảng thông dụng (Typical):** `10%` - `20%` của `CHUNK_SIZE`.
* **Cơ sở lựa chọn giá trị mặc định (50):** Chiều dài trung bình của một cụm từ ghép hoặc nửa câu phức (~7-10 từ), đảm bảo các danh từ riêng hay số hiệu điều luật ở vùng biên giới cắt không bị chia cắt làm đôi.
* **Hướng dẫn tinh chỉnh:** Luôn điều chỉnh tỉ lệ thuận với `CHUNK_SIZE` (khoảng 10-15% kích thước chunk).

---

## 2. Tham Số Tìm Kiếm Từ Khóa BM25 (Lexical Search Parameters)

### `k1` (Tốc độ bão hòa tần suất từ khóa)
* **Tệp cấu hình:** `task6_lexical_search.py` (Tham số mặc định của `BM25Okapi`)
* **Ý nghĩa:** Điều chỉnh độ nhạy điểm số khi từ khóa xuất hiện lặp lại nhiều lần trong một đoạn văn.
  * Nếu `k1` lớn: Điểm số tăng mạnh và tuyến tính hơn khi từ khóa lặp lại nhiều lần.
  * Nếu `k1` nhỏ: Điểm số bão hòa rất nhanh, hầu như không phân biệt từ xuất hiện 2 lần hay 10 lần.
* **Phạm vi giá trị:**
  * **Tối thiểu (Min):** `0` (tần suất từ khóa không còn ý nghĩa, chỉ quan tâm từ đó có xuất hiện hay không).
  * **Tối đa (Max):** Vô cùng ($\infty$). Khoảng thực tế thường dùng là từ `1.2` đến `2.0`.
* **Cơ sở lựa chọn giá trị mặc định (1.5):** Là giá trị chuẩn tối ưu qua thực nghiệm trên các tập dữ liệu lớn của ngành (TREC), giúp cân bằng giữa việc thưởng điểm cho tài liệu tập trung sâu và loại bỏ các tài liệu cố tình nhồi nhét từ khóa.
* **Hướng dẫn tinh chỉnh:** Tăng lên `1.8 - 2.0` nếu tài liệu có tính chuyên môn sâu và việc lặp lại từ khóa chính xác là biểu hiện của độ liên quan cao.

### `b` (Mức độ phạt độ dài tài liệu)
* **Tệp cấu hình:** `task6_lexical_search.py` (Tham số mặc định của `BM25Okapi`)
* **Ý nghĩa:** Điều chỉnh mức độ phạt điểm đối với các tài liệu dài dòng chứa từ khóa.
  * Nếu `b = 1`: Phạt tối đa, điểm số tỉ lệ nghịch hoàn toàn với độ dài tài liệu.
  * Nếu `b = 0`: Không phạt độ dài, tài liệu dài hay ngắn chứa cùng từ khóa đều bằng điểm.
* **Phạm vi giá trị:**
  * **Tối thiểu (Min):** `0` (không phạt độ dài tài liệu).
  * **Tối đa (Max):** `1` (phạt tối đa).
* **Cơ sở lựa chọn giá trị mặc định (0.75):** Ưu tiên các đoạn văn ngắn gọn, súc tích chứa từ khóa nhưng vẫn cho phép tài liệu dài đứng hạng cao nếu mật độ từ khóa đủ lớn.
* **Hướng dẫn tinh chỉnh:** Giảm xuống `0.5 - 0.6` đối với dữ liệu **văn bản pháp luật** (do các điều luật thường được viết chi tiết, dài dòng theo mẫu chuẩn, việc phạt độ dài quá nặng sẽ làm mất ưu thế của văn bản luật chính xác).

---

## 3. Tham Số Gộp Xếp Hạng RRF (Reciprocal Rank Fusion)

### `k` (Hằng số làm mịn thứ hạng)
* **Tệp cấu hình:** `task7_reranking.py`
* **Ý nghĩa:** Xác định độ dốc của điểm số phân phối theo thứ hạng trong công thức RRF: $\text{RRF Score}(d) = \sum \frac{1}{k + rank}$.
* **Phạm vi giá trị:**
  * **Tối thiểu (Min):** `1` (thứ hạng cao sẽ lấn át hoàn toàn).
  * **Tối đa (Max):** Thường tối đa có ý nghĩa là `200` (giá trị quá lớn sẽ triệt tiêu khoảng cách thứ hạng).
  * **Khoảng thông dụng (Typical):** `50` - `100`.
* **Cơ sở lựa chọn giá trị mặc định (60):** Điểm ngọt thực nghiệm được đề xuất bởi Microsoft Research, giúp dung hòa và tạo sự công bằng giữa các bộ tìm kiếm khác nhau.
* **Hướng dẫn tinh chỉnh:** Giữ nguyên mức `60` vì đây là giá trị cân bằng nhất đã được kiểm chứng khoa học.

---

## 4. Tham Số Lọc Cuối Cùng & Kích Hoạt Fallback

### `SCORE_THRESHOLD`
* **Tệp cấu hình:** `task9_retrieval_pipeline.py`
* **Ý nghĩa:** Ngưỡng điểm tối thiểu của tài liệu khớp nhất sau khi Reranker đánh giá lại.
* **Phạm vi giá trị:**
  * **Tối thiểu (Min):** `0.0` (không bao giờ kích hoạt fallback).
  * **Tối đa (Max):** `1.0` (luôn luôn fallback).
  * **Khoảng thông dụng (Typical):** `0.2` - `0.4`.
* **Cơ sở lựa chọn giá trị mặc định (0.3):** Điểm tương đồng ngữ nghĩa dưới `0.3` thường chỉ chứa các từ khóa ngẫu nhiên, không liên quan đến ý nghĩa câu hỏi. Ngưỡng `0.3` giúp ngăn chặn LLM đọc ngữ cảnh rác gây ảo giác (hallucination).
* **Hướng dẫn tinh chỉnh:**
  * **Tăng lên `0.35 - 0.4`:** Nếu muốn giảm thiểu ảo giác của LLM tới mức tối đa (ưu tiên fallback sang PageIndex tìm kiếm rộng).
  * **Giảm xuống `0.2 - 0.25`:** Nếu hệ thống fallback bên ngoài phản hồi chậm hoặc tốn kém, chấp nhận các đoạn văn có độ liên quan thấp hơn ở local.

### `top_k` (Số lượng ngữ cảnh đưa vào LLM)
* **Tệp cấu hình:** `task9_retrieval_pipeline.py` & `app.py`
* **Ý nghĩa:** Số lượng ngữ cảnh (chunks) tốt nhất cung cấp cho LLM tổng hợp câu trả lời.
* **Phạm vi giá trị:**
  * **Tối thiểu (Min):** `1`
  * **Tối đa (Max):** Giới hạn context window của LLM.
  * **Khoảng thông dụng (Typical):** `3` - `7`.
* **Cơ sở lựa chọn giá trị mặc định (5):** Đảm bảo đủ thông tin để trả lời các câu hỏi phức tạp cần tổng hợp từ nhiều nguồn, đồng thời giữ số lượng token ở mức hợp lý để LLM tập trung trích xuất tốt nhất, tránh hiện tượng *Lost-in-the-middle*.
* **Hướng dẫn tinh chỉnh:** Tăng lên `6 - 7` khi các câu hỏi yêu cầu tổng hợp so sánh diện rộng; giảm xuống `3` khi chỉ cần trả lời thông tin cụ thể, ngắn gọn để tiết kiệm chi phí và tăng tốc độ xử lý.

---

## 5. Tổng Hợp Hướng Dẫn Nâng Cấp Hệ Thống Qua Tinh Chỉnh Tham Số

Để tăng điểm số đánh giá hệ thống, bạn có thể thực hiện tinh chỉnh đồng bộ các tham số như sau:

| Mục tiêu cải thiện | Tham số cần chỉnh | Giá trị đề xuất | Lý do kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Tăng Context Recall** <br>*(Retriever lấy đủ chứng cứ)* | 1. `EMBEDDING_MODEL` <br>2. Ứng viên Rerank | 1. `"BAAI/bge-m3"` <br>2. Tăng từ `top_k*2` lên `top_k*5` | - BGE-M3 hiểu tiếng Việt vượt trội so với MiniLM.<br>- Reranker có phổ ứng viên rộng hơn để chọn lọc. |
| **Tăng Faithfulness** <br>*(LLM trả lời chính xác, không bịa đặt)* | 1. `CHUNKING_METHOD` <br>2. `SCORE_THRESHOLD` | 1. `"markdown_header"` <br>2. Tăng lên `0.35` | - Markdown Header giúp giữ trọn vẹn ngữ cảnh điều luật.<br>- Ngưỡng cao giúp loại bỏ triệt để ngữ cảnh nhiễu. |
| **Tối ưu tra cứu văn bản Luật** | Tham số BM25 | `k1 = 2.0`, `b = 0.6` | Giảm hình phạt độ dài cho văn bản luật và tăng trọng số cho các từ khóa xuất hiện tập trung. |
