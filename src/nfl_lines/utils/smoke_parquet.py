# smoke_parquet.py
from parquet_utils import load_all_parquet, load_season

def main():
    print("== Full cache ==")
    df = load_all_parquet()
    print(df.groupby(["season", "week"]).size().head(10))

    print("\n== One season ==")
    df2023 = load_season(2023)
    print(df2023.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
