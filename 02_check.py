import pandas as pd

# ① 全部の列を文字として読む（ステップ1と同じ）
df = pd.read_csv("input/orders_202610.csv", encoding="cp932", dtype=str)

print("【チェック結果】")
print(f"全体の行数：{len(df)}行")
print()


# 共通の表示係：条件に当てはまる行を表示する
def show(title, mask, cols):
    hits = df[mask]
    print(f"■ {title}：{len(hits)}件")
    if len(hits) > 0:
        print(hits[cols].to_string())
    print()


# ② 日付：「2026/10/01」の形になっていない行
standard = df["注文日"].str.fullmatch(r"\d{4}/\d{2}/\d{2}")
show("日付の形がそろっていない", ~standard, ["注文番号", "注文日"])

# ③ 日付：10月以外の注文（標準の形の行だけで判定）
not_oct = standard & ~df["注文日"].str.startswith("2026/10")
show("10月以外の注文", not_oct, ["注文番号", "注文日"])

# ④ ステータスの内訳
print("■ ステータスの内訳")
print(df["ステータス"].value_counts().to_string())
print()

# ⑤ 完全に同じ行（重複）
show("完全に同じ行（重複）", df.duplicated(keep=False), ["注文番号", "商品名", "数量"])

# ⑥ 商品コードが5桁でない
show("商品コードが5桁でない", df["商品コード"].str.len() != 5, ["注文番号", "商品コード", "商品名"])

# ⑦ 空欄がある（単価・カテゴリ）
show("単価が空欄", df["単価"].isna(), ["注文番号", "商品名", "単価"])
show("カテゴリが空欄", df["カテゴリ"].isna(), ["注文番号", "商品名", "カテゴリ"])

# ⑧ 数量が半角数字でない（全角など）
qty_ok = df["数量"].str.fullmatch(r"-?[0-9]+")
show("数量が半角数字でない", ~qty_ok, ["注文番号", "商品名", "数量"])

# ⑨ 金額にカンマが入っている
comma = df["小計"].str.contains(",") | df["合計金額"].str.contains(",")
print(f"■ 金額にカンマが入っている：{comma.sum()}件（多いので件数だけ表示）")
print()

# ⑩ 商品名の一覧（表記ゆれを目で確認する）
print("■ 商品名の一覧（同じ商品が別の名前になっていないか）")
print(df["商品名"].value_counts().to_string())