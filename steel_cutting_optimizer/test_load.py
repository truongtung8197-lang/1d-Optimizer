"""Test tạm thời cho Phase 0: load và in ra danh sách object."""

from pathlib import Path

from input_loader import load_required, load_stock

BASE = Path(__file__).parent / "data"

if __name__ == "__main__":
    stocks = load_stock(BASE / "stock.csv")
    components = load_required(BASE / "required.csv")

    print("=== STOCKS ===")
    for s in stocks:
        print(s)

    print("\n=== COMPONENTS ===")
    for c in components:
        print(c)

    print(f"\nTổng stock: {len(stocks)} loại")
    print(f"Tổng component: {len(components)} loại")
