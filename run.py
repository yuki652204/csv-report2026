import os
import subprocess
import sys
from pathlib import Path

# どこから実行されても、このファイルがあるフォルダで動くようにする
os.chdir(Path(__file__).parent)


def step(script):
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print()
        print("【エラー】処理が途中で止まりました。")
        print("この画面を撮影して、担当者に送ってください。")
        sys.exit(1)


print("売上レポートを作成します…")
print()
step("03_clean.py")
print()
step("04_report.py")

# 修正ログに【要確認】があれば、目立つように知らせる
log_file = sorted(Path("output").glob("log_*.csv"))[-1]
if "【要確認】" in log_file.read_text(encoding="utf-8-sig"):
    print()
    print("！！ 確認が必要な注文があります ！！")
    print("レポートの「修正ログ」シートの【要確認】を見て、担当者に連絡してください。")

print()
print("【完了】レポートのフォルダを開きます。")
if sys.platform == "win32":
    os.startfile(Path("report").resolve())