import pandas as pd


def create_sample_dataframe() -> pd.DataFrame:
    """Create a sample DataFrame with 3 columns and 6 rows.

    Returns:
        pd.DataFrame: A DataFrame with columns 'name' (str), 'age' (int),
            and 'score' (float), containing 6 sample records.
    """
    data = {
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "age": [25, 30, 35, 28, 22, 45],
        "score": [88.5, 92.0, 76.3, 95.1, 83.7, 61.4],
    }
    return pd.DataFrame(data)


if __name__ == "__main__":
    df = create_sample_dataframe()
    print(df)
