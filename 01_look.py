import pandas as pd

# CSVを読み込む
df = pd.read_csv("input/orders_202610.csv", encoding="cp932", dtype=str)
# 最初の5行を表示する
print(df.head())

# 列ごとの型を表示する
print(df.dtypes)