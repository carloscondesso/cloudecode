"""
Builds KPIs and visualizations from the latest Parquet data in
.claude/skills/migrate/data/, saving PNG charts to
.claude/skills/visualize/visualizations/<datetime-folder>/.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


sns.set_theme(style="whitegrid")


def get_latest_folder(base_path: str) -> tuple[str, Path]:
    """Return (folder_name, full_path) for the latest datetime folder."""
    base = Path(base_path)
    folders = [d for d in base.iterdir() if d.is_dir()]
    if not folders:
        raise FileNotFoundError(f"No folders found in {base_path}")
    latest = max(folders, key=lambda x: x.name)
    return latest.name, latest


def load_data(data_folder: Path) -> dict[str, pd.DataFrame]:
    """Load all parquet files from the given folder into a dict."""
    return {f.stem: pd.read_parquet(f) for f in sorted(data_folder.glob("*.parquet"))}


def build_kpis(tables: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Compute summary KPIs from the fact tables."""
    sales = tables["fact_sales"]
    returns = tables["fact_returns"]

    total_sales = sales["net_amount"].sum()
    total_returns = returns["refund_amount"].sum()

    kpis = {
        "Total Sales": total_sales,
        "Total Returns": total_returns,
        "Net Sales": total_sales - total_returns,
        "Avg Sales per Store": total_sales / sales["store_sk"].nunique(),
        "Avg Sales per Product": total_sales / sales["product_sk"].nunique(),
        "Avg Sales per Customer": total_sales / sales["customer_sk"].nunique(),
    }
    return kpis


def save_fig(fig: plt.Figure, output_dir: Path, filename: str) -> None:
    """Save figure to output directory and close it."""
    fig.savefig(output_dir / filename, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  Saved: {filename}")


def build_visualizations(tables: dict[str, pd.DataFrame], output_dir: Path) -> None:
    """Generate and save all 8 charts."""
    sales = tables["fact_sales"]
    returns = tables["fact_returns"]
    dim_date = tables["dim_date"]
    dim_store = tables["dim_store"]
    dim_product = tables["dim_product"]
    dim_customer = tables["dim_customer"]

    # --- Sales Trend Over Time ---
    sales_by_date = (
        sales.merge(dim_date[["date_sk", "date"]], on="date_sk")
        .groupby("date")["net_amount"].sum()
        .reset_index()
        .sort_values("date")
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(sales_by_date["date"], sales_by_date["net_amount"], linewidth=1.5)
    ax.set_title("Sales Trend Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Net Amount")
    plt.xticks(rotation=45)
    save_fig(fig, output_dir, "01_sales_trend_over_time.png")

    # --- Sales by Store ---
    sales_by_store = (
        sales.merge(dim_store[["store_sk", "store_name"]], on="store_sk")
        .groupby("store_name")["net_amount"].sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=sales_by_store, x="store_name", y="net_amount", ax=ax)
    ax.set_title("Sales by Store")
    ax.set_xlabel("Store")
    ax.set_ylabel("Net Amount")
    plt.xticks(rotation=30, ha="right")
    save_fig(fig, output_dir, "02_sales_by_store.png")

    # --- Sales by Product ---
    sales_by_product = (
        sales.merge(dim_product[["product_sk", "product_name"]], on="product_sk")
        .groupby("product_name")["net_amount"].sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(data=sales_by_product, x="product_name", y="net_amount", ax=ax)
    ax.set_title("Sales by Product")
    ax.set_xlabel("Product")
    ax.set_ylabel("Net Amount")
    plt.xticks(rotation=30, ha="right")
    save_fig(fig, output_dir, "03_sales_by_product.png")

    # --- Sales by Customer (top 20) ---
    dim_customer["full_name"] = (
        dim_customer["first_name"] + " " + dim_customer["last_name"]
    )
    sales_by_customer = (
        sales.merge(dim_customer[["customer_sk", "full_name"]], on="customer_sk")
        .groupby("full_name")["net_amount"].sum()
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(14, 5))
    sns.barplot(data=sales_by_customer, x="full_name", y="net_amount", ax=ax)
    ax.set_title("Sales by Customer (Top 20)")
    ax.set_xlabel("Customer")
    ax.set_ylabel("Net Amount")
    plt.xticks(rotation=45, ha="right")
    save_fig(fig, output_dir, "04_sales_by_customer.png")

    # --- Returns Trend Over Time ---
    returns_by_date = (
        returns.merge(dim_date[["date_sk", "date"]], on="date_sk")
        .groupby("date")["refund_amount"].sum()
        .reset_index()
        .sort_values("date")
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(
        returns_by_date["date"],
        returns_by_date["refund_amount"],
        color="tomato",
        linewidth=1.5,
    )
    ax.set_title("Returns Trend Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Refund Amount")
    plt.xticks(rotation=45)
    save_fig(fig, output_dir, "05_returns_trend_over_time.png")

    # --- Returns by Store ---
    returns_by_store = (
        returns.merge(dim_store[["store_sk", "store_name"]], on="store_sk")
        .groupby("store_name")["refund_amount"].sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=returns_by_store, x="store_name", y="refund_amount", ax=ax, color="tomato")
    ax.set_title("Returns by Store")
    ax.set_xlabel("Store")
    ax.set_ylabel("Refund Amount")
    plt.xticks(rotation=30, ha="right")
    save_fig(fig, output_dir, "06_returns_by_store.png")

    # --- Returns by Product ---
    returns_by_product = (
        returns.merge(dim_product[["product_sk", "product_name"]], on="product_sk")
        .groupby("product_name")["refund_amount"].sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(data=returns_by_product, x="product_name", y="refund_amount", ax=ax, color="tomato")
    ax.set_title("Returns by Product")
    ax.set_xlabel("Product")
    ax.set_ylabel("Refund Amount")
    plt.xticks(rotation=30, ha="right")
    save_fig(fig, output_dir, "07_returns_by_product.png")

    # --- Returns by Customer (via fact_sales join) ---
    returns_with_customer = (
        returns.merge(sales[["sales_id", "customer_sk"]], on="sales_id", how="left")
        .merge(dim_customer[["customer_sk", "full_name"]], on="customer_sk", how="left")
        .groupby("full_name")["refund_amount"].sum()
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(14, 5))
    sns.barplot(data=returns_with_customer, x="full_name", y="refund_amount", ax=ax, color="tomato")
    ax.set_title("Returns by Customer (Top 20)")
    ax.set_xlabel("Customer")
    ax.set_ylabel("Refund Amount")
    plt.xticks(rotation=45, ha="right")
    save_fig(fig, output_dir, "08_returns_by_customer.png")


def main() -> None:
    """Orchestrate KPI computation and chart generation."""
    # Derive paths from this file's location so the script works from any CWD.
    # File is at <project_root>/.claude/skills/visualize/Scripts/build_visualizations.py
    project_root = Path(__file__).resolve().parents[4]
    data_base = project_root / ".claude" / "skills" / "migrate" / "data"
    viz_base = project_root / ".claude" / "skills" / "visualize" / "visualizations"

    folder_name, data_folder = get_latest_folder(data_base)
    output_dir = Path(viz_base) / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Source folder : {data_folder}")
    print(f"Output folder : {output_dir}\n")

    tables = load_data(data_folder)

    print("=== KPIs ===")
    kpis = build_kpis(tables)
    for name, value in kpis.items():
        print(f"  {name}: {value:,.2f}")

    print("\n=== Visualizations ===")
    build_visualizations(tables, output_dir)

    print("\nDone.")


if __name__ == "__main__":
    main()
