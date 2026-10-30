import re

import sys
from pathlib import Path
import unicodedata

import pandas as pd

# 対象のCSVを決める：指定があればそれ、なければ input の中でいちばん新しい月
if len(sys.argv) > 1:
    SRC = sys.argv[1]
else:
    files = sorted(Path("input").glob("orders_*.csv"))
    if not files:
        sys.exit("input フォルダに orders_YYYYMM.csv が見つかりません")
    SRC = str(files[-1])
print(f"対象ファイル：{SRC}")

# ファイル名から「年」と「月」を取り出す（orders_202610 → 2026年10月）
m = re.search(r"orders_(\d{4})(\d{2})", SRC)
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

# ============ ここから 3-B ============
log = []  # 修正ログ：[注文番号, 内容]

# ⑤ 単価の空欄を「小計 ÷ 数量」で補う
for i in df[df["単価"].isna()].index:
    price = df.at[i, "小計"] // df.at[i, "数量"]
    df.at[i, "単価"] = price
    log.append([df.at[i, "注文番号"], f"単価が空欄 → 小計÷数量で {price}円 を補完"])

# ⑥ カテゴリの空欄を、同じ商品コードのほかの行から補う
cat_of = df.dropna(subset=["カテゴリ"]).groupby("商品コード")["カテゴリ"].first()
for i in df[df["カテゴリ"].isna()].index:
    code = df.at[i, "商品コード"]
    df.at[i, "カテゴリ"] = cat_of[code]
    log.append([df.at[i, "注文番号"], f"カテゴリが空欄 → 商品コード{code}から「{cat_of[code]}」を補完"])


    # ⑥-2 森さんに確認して決まった修正を、修正リストから当てる
checked = set()  # 修正リストで確認済みの行（検算の対象から外す）
fix_file = Path(f"input/corrections_{YEAR}{MONTH:02d}.csv")
if fix_file.exists():
    fixes = pd.read_csv(fix_file, encoding="utf-8-sig", dtype=str)
    for _, f in fixes.iterrows():
        hit = (df["注文番号"] == f["注文番号"]) & (df["商品コード"] == f["商品コード"])
        for i in df[hit].index:
            old = df.at[i, f["列"]]
            df.at[i, f["列"]] = int(f["正しい値"])
            checked.add(i)
            log.append([f["注文番号"], f"{f['列']} {old} → {f['正しい値']}：{f['理由']}"])


# ⑦ 検算：小計 ＝ 単価 × 数量 になっているか（直さずに報告だけ）
mismatch = df["小計"] != df["単価"] * df["数量"]
for i in df[mismatch].index.difference(list(checked)):
    calc = df.at[i, "単価"] * df.at[i, "数量"]
    log.append([df.at[i, "注文番号"], f"【要確認】小計{df.at[i, '小計']}円 ≠ 単価×数量{calc}円"])

# ⑧ 重複を1行にまとめる
dup = df.duplicated()
for i in df[dup].index:
    log.append([df.at[i, "注文番号"], "重複行を削除（CSVの出力不具合として1行にまとめるルール：2026年10月 ○○さんと合意）"])
df = df[~dup]

# ⑨ 対象月以外を除く
other = (df["注文日"].dt.year != YEAR) | (df["注文日"].dt.month != MONTH)
for i in df[other].index:
    log.append([df.at[i, "注文番号"], f"{df.at[i, '注文日'].date()} の注文のため除外（{MONTH}月分ではない）"])
df = df[~other]

# ⑩ キャンセルを除き、返品を分ける
cancel = df[df["ステータス"] == "キャンセル"]
returns = df[df["ステータス"] == "返品"]
sales = df[df["ステータス"] == "発送済み"]

# ⑪ ファイルに保存する（Excelで文字化けしないよう utf-8-sig）
Path("output").mkdir(exist_ok=True)
ym = f"{YEAR}{MONTH:02d}"
sales.to_csv(f"output/sales_{ym}.csv", index=False, encoding="utf-8-sig")
returns.to_csv(f"output/returns_{ym}.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(log, columns=["注文番号", "内容"]).to_csv(
    f"output/log_{ym}.csv", index=False, encoding="utf-8-sig"
)

# ---- 結果の確認 ----
print(f"■ 売上の対象：{len(sales)}行")
print(f"■ キャンセル（除外）：{len(cancel)}行")
print(f"■ 返品（別表）：{len(returns)}行")
print()
print("■ 修正ログ")
for order_no, note in log:
    print(f"  {order_no}：{note}")
print()
print("■ 残っている空欄：", int(sales.isna().sum().sum()), "件")