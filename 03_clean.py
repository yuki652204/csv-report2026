import re
import unicodedata

import pandas as pd

SRC = "input/orders_202610.csv"

# ファイル名から「年」と「月」を取り出す（orders_202610 → 2026年10月）
m = re.search(r"(\d{4})(\d{2})", SRC)
YEAR, MONTH = int(m.group(1)), int(m.group(2))

df = pd.read_csv(SRC, encoding="cp932", dtype=str)


# ① 文字のゆれをそろえる（半角カナ→全角、全角数字→半角、前後の空白を消す）
def normalize(s):
    if pd.isna(s):
        return s
    return unicodedata.normalize("NFKC", s).strip()


df = df.map(normalize)

# かっこだけは全角に戻す（森さんの表記に合わせる）
df["商品名"] = df["商品名"].str.replace("(", "（").str.replace(")", "）")


# ② 日付を「2026/10/01」の形にそろえる
def fix_date(s):
    s = s.replace("-", "/")  # 2026-10-15 → 2026/10/15
    s = s.split(" ")[0]  # 2026/10/17 16:13 → 2026/10/17
    jp = re.fullmatch(r"(\d{1,2})月(\d{1,2})日", s)
    if jp:  # 10月6日 → 2026/10/06（年はファイル名から）
        return f"{YEAR}/{int(jp.group(1)):02d}/{int(jp.group(2)):02d}"
    return s


df["注文日"] = pd.to_datetime(df["注文日"].map(fix_date), format="%Y/%m/%d")

# ③ 商品コードを5桁にそろえる（124 → 00124）
df["商品コード"] = df["商品コード"].str.zfill(5)

# ④ 金額・数量を数値にする（カンマを消してから）
for col in ["単価", "数量", "小計", "送料", "合計金額"]:
    df[col] = pd.to_numeric(df[col].str.replace(",", "")).astype("Int64")

# ---- 結果の確認 ----
print("■ 型")
print(df.dtypes.to_string())
print()
print("■ 商品名の一覧")
print(df["商品名"].value_counts().to_string())
print()
print("■ 日付の範囲：", df["注文日"].min().date(), "〜", df["注文日"].max().date())
print("■ 商品コードの桁数：", df["商品コード"].str.len().unique().tolist())
print("■ 空欄の数：", df.isna().sum()[df.isna().sum() > 0].to_dict())