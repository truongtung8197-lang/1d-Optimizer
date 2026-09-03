# DATA SCHEMA

## Input

### Cách nhập liệu chính: `data/input.xlsx` (2 sheet)

File Excel chứa **cả stock và required trong cùng 1 file**, mỗi loại 1 sheet,
có định dạng sẵn (header màu, banded rows, freeze, filter).

#### Sheet `Stock`

| column | type | note |
| --- | --- | --- |
| stock_type_id | str | vd "S6000" |
| length_mm | float | vd 6000 |
| quantity | int | số cây có sẵn loại này |

#### Sheet `Required`

| column | type | note |
| --- | --- | --- |
| component_id | str | vd "fc83" |
| length_mm | float | chiều dài cấu kiện |
| quantity | int | số lượng cần |

> Tạo lại file `input.xlsx` từ dữ liệu mẫu bằng lệnh: `python create_input_excel.py`.
> Khi đã có file, chỉ cần chỉnh sửa dữ liệu vào 2 sheet, chạy `main.py` là xong.

### Cách nhập liệu cũ (tương thích ngược, tùy chọn)

Hai file CSV riêng:

#### `data/stock.csv`

| column | type | note |
| --- | --- | --- |
| stock_type_id | str | vd "S6000" |
| length_mm | float | vd 6000 |
| quantity | int | số cây có sẵn loại này |

#### `data/required.csv`

| column | type | note |
| --- | --- | --- |
| component_id | str | vd "C-001" |
| length_mm | float | chiều dài cấu kiện |
| quantity | int | số lượng cần |

## Output

### `output/cutting_plan.json`

```json
{
  "summary": {
    "total_stock_used": 27,
    "total_scrap_mm": 17474,
    "scrap_by_stock_type": {"S6000": 17474},
    "used_mm": 144432,
    "stock_mm_used": 162000,
    "used_percent": 89.16
  },
  "warnings": [],
  "cuts": [
    {
      "stock_instance_id": "S6000-#001",
      "stock_type_id": "S6000",
      "segments": [
        {"segment_id": "SEG-0001", "length_mm": 2000, "source": "stock", "used_by_component": "fc61"},
        {"segment_id": "SEG-0002", "length_mm": 3080, "source": "stock", "used_by_component": "fc83"}
      ],
      "remnant_mm": 920,
      "remnant_reused_as": null
    }
  ],
  "assemblies": [
    {
      "component_id": "fc61",
      "instance_no": 2,
      "target_length_mm": 7302,
      "segment_a": {"segment_id": "SEG-0001", "length_mm": 2000, "from": "S6000-#001"},
      "segment_b": {"segment_id": "SEG-0003", "length_mm": 5302, "from": "S6000-#002"},
      "joint": "tăng đơ"
    }
  ]
}
```

**Các trường summary:**

- `total_stock_used`: số cây thép đã dùng.
- `stock_mm_used`: tổng chiều dài stock đã dùng (= số cây × chiều dài cây).
- `used_mm`: tổng chiều dài đoạn đã dùng cho cấu kiện.
- `used_percent`: **% sử dụng** = `used_mm ÷ stock_mm_used × 100`.
- `total_scrap_mm` + `scrap_by_stock_type`: phế liệu (phần dư không tái dùng).

### `output/cutting_plan.xlsx` — các sheet (đã format màu)

1. **Summary**: tổng cây dùng, tổng stock dùng (mm), tổng sử dụng (mm), **% SỬ DỤNG**,
   phế liệu theo loại stock.
2. **Cutting Detail**: mỗi dòng = 1 đoạn cắt từ cây stock, cột `type` phân loại
   "dùng"/"phế" (dòng phế tô hồng), dòng "(dư)" = phần dư cây.
3. **Assembly Detail**: mỗi dòng = 1 cấu kiện, đoạn a (nguồn), đoạn b (nguồn),
   ghi rõ tăng đơ nối giữa.
4. **Warnings** (nếu có): cảnh báo màu đỏ (cấu kiện vô nghiệm, thiếu stock...).

## Ghi chú

- Trường `warnings` (cấp cao nhất trong JSON) liệt kê các cảnh báo: cấu kiện
  vô nghiệm (không có pattern hợp lệ), thiếu stock để cắt, hoặc cấu kiện thiếu
  đoạn a/b. Nếu không có cảnh báo, mảng rỗng.
- `segment.source` trong `cuts[].segments` ghi nguồn gốc đoạn: `"stock"` (cắt từ
  cây mới) hoặc `"remnant"` (cắt từ phần dư tái sử dụng).
- `remnant_reused_as` ghi mã cấu kiện đã tái dùng phần dư của cây đó (nếu có).
