# Fixtures (ALL SYNTHETIC)

Tiny hand-written CSV files used by the importer tests. None of them comes from
real customers or from `data/uploads/`.

| File | Purpose |
|------|---------|
| `customers_clean.csv` | English headers, all rows valid |
| `orders_french_headers.csv` | French headers (alias fallback), status synonyms, 3 date formats |
| `orders_half_bad.csv` | 3 of 6 rows lack the required `customer_id` (50 % rejected) |
| `orders_mostly_bad.csv` | 4 of 5 rows invalid -> import must abort |
| `customers_no_id_column.csv` | no column maps to `customer_id` -> mapping error |
| `empty.csv` | zero bytes -> "CSV has no header row" |
| `header_only.csv` | header, no rows |
