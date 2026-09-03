# ALGORITHM

## 1. Join Pattern Generator (join_patterns.py)

Mọi cấu kiện = đúng 2 đoạn `a + b = L`, nối bằng 1 tăng đơ giữa. Không có case
1 đoạn hay 3 đoạn. Rule "đoạn tối thiểu" được đọc từ `config.py`:

- `MIN_SEGMENT_MODE = "ratio"` → đoạn ngắn nhất phải `≥ L * MIN_SEGMENT_RATIO`
  (mặc định `MIN_SEGMENT_RATIO = 1/3`).
- `MIN_SEGMENT_MODE = "fixed"` → đoạn ngắn nhất phải `≥ MIN_SEGMENT_FIXED_MM`
  (vd 2000mm).

**Điều kiện hợp lệ của `a` (b = L - a suy ra tương tự)** — gọi `min_len` là
độ dài đoạn tối thiểu theo config:

```
a_min = max(min_len, L - stock_length)   # đủ chịu lực, và b = L-a phải ≤ stock_length
a_max = min(L - min_len, stock_length)   # đủ chịu lực (b ≥ min_len), và a phải ≤ stock_length
```

Nếu `a_min > a_max` → **không có lời giải hợp lệ với stock_length này**
(cần cảnh báo, không tự động bỏ qua cấu kiện).

**Hàm chính:**

```python
def generate_2seg_patterns(L: float, stock_length: float, step: float = 50.0) -> list[tuple[float, float]]:
    """
    Trả về danh sách (a, b) hợp lệ, a <= b, cách nhau `step` mm để giới hạn
    số lượng phương án (tránh bùng nổ tổ hợp với số thực).
    """
```

- `step` dùng để rời rạc hoá (vd 50mm hoặc 100mm theo dung sai cắt thực tế).
- Ưu tiên sắp kết quả theo tiêu chí "dễ tái sử dụng phần dư" (xem mục 2).
- Nếu có nhiều loại stock_length khác nhau, gọi hàm này cho từng loại, hợp nhất
  danh sách pattern (đánh dấu pattern đó khả thi với loại stock nào).

**Test case bắt buộc:** L=7500, stock=6000 → phải cho ra (5000,2500), (4500,3000)
... và loại bỏ (6000,1500).

## 2. Cutting Engine (cutting_engine.py)

**Chiến lược: First Fit Decreasing + Remnant Pool**

1. Với mỗi Component × quantity, chọn 1 join pattern (a,b) — ban đầu chọn pattern
   đầu tiên hợp lệ (heuristic đơn giản); để lại danh sách "job đoạn" gồm tất cả
   a, b của mọi cấu kiện, sort giảm dần theo chiều dài.
2. Duy trì **remnant_pool**: list các đoạn dư còn dùng được (từ cây đã cắt trước
   đó), sort giảm dần.
3. Với mỗi job đoạn (duyệt từ dài → ngắn):
   - Thử tìm trong `remnant_pool` một đoạn dư ≥ độ dài cần, chọn đoạn dư **nhỏ
     nhất thoả mãn** (best-fit trong remnant) → cắt từ đó, phần dư mới quay lại
     pool.
   - Nếu không có remnant phù hợp → mở 1 cây stock mới (chọn loại stock nhỏ
     nhất mà vẫn ≥ độ dài cần, nếu có nhiều loại), cắt, phần dư cho vào
     remnant_pool.
4. Ghi nhận: mỗi lần cắt → CutPlan (cây nào, đoạn nào, dư bao nhiêu).
5. Ghi nhận: mỗi Component → ComponentAssembly (đoạn a từ đâu, đoạn b từ đâu).

**Điểm cần lưu ý khi code:**

- Remnant quá ngắn (không dùng được cho bất kỳ job nào còn lại) → tính vào phế
  liệu cuối cùng, không giữ mãi trong pool.
- Nên có ngưỡng `min_usable_remnant` (vd 200mm) — dưới ngưỡng này coi như phế
  liệu luôn, không đưa vào pool (tránh pool phình to vô ích).
- Nếu nhiều loại stock_length, ưu tiên dùng remnant trước, sau đó chọn stock
  mới theo nguyên tắc "vừa khít nhất" để giảm phế liệu.

## 3. Optimizer (optimizer.py) — đã triển khai

**Chiến lược: Greedy ngẫu nhiên + Restart**

Vì kết quả greedy đơn giản (mục 2) chưa đủ tốt, đã triển khai optimizer:

1. **Shuffle thứ tự xử lý**: mỗi lần chạy, các instance (cấu kiện × số lượng)
   được xáo trộn thứ tự ngẫu nhiên bằng `random.Random(seed)`.
2. **Chọn join pattern theo phế ước lượng**: với mỗi instance, thay vì lấy
   pattern đầu tiên, tính "tổng phế ước lượng" cho từng pattern (a,b):
   - `eval_waste(seg)`: nếu có remnant đủ chứa → phế = remnant - seg; ngược lại
     phế = stock_length - seg (mở cây mới).
   - Chọn pattern có `eval_waste(a) + eval_waste(b)` nhỏ nhất.
3. **Đặt đoạn**: vẫn dùng best-fit remnant (nhỏ nhất đủ chứa), không có thì mở
   cây mới; phần dư ≥ `min_remnant` (200mm) quay lại pool.
4. **Restart nhiều lần**: chạy `max_restarts` lần (mặc định 60) với seed khác
   nhau, giữ lời giải tốt nhất theo tiêu chí so sánh:

   ```
   key = (số cây dùng, tổng phế liệu)   # ít hơn là tốt hơn
   ```

5. **Giới hạn vòng lặp**: `--restarts` (CLI) để tránh treo (model free, tránh
   thuật toán quá nặng).

**Kết quả trên bộ dữ liệu thực tế** (fc344, fc83, fc65, fc61, fc79, fc66, fc93;
stock 6000mm):

- Greedy cũ (mục 2): **31 cây, 37,436 mm phế**
- Optimizer: **29 cây, 24,793 mm phế** (giảm 2 cây, ~34% phế liệu)

## 4. Đầu ra cần validate trước khi xuất báo cáo

- Tổng chiều dài đoạn cắt từ 1 cây + remnant = đúng stock_length (sanity check).
- Mỗi cấu kiện có đúng 2 đoạn, tổng = L, cả 2 đều ≥ L/3.
- Không có đoạn nào bị dùng 2 lần.
