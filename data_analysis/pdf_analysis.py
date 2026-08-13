
"""
さいたま市 有料老人ホーム一覧表（PDF）→ CSV
 
出典: さいたま市「令和7年7月1日現在の有料老人ホーム経営状況等報告」
      R7yuuryouroujinnho-muitir.pdf
      https://www.city.saitama.lg.jp/005/001/008/p096840.html
 
PDFの構成（実データで確認済み 2026-08-12）:
    表① 住所地特例対象      No.1〜179  (179件)
    表② 住所地特例対象外    No.1       (1件, ミモザ浦和)
    合計 180件 / 定員合計 9,942人
 
    PDF末尾の「計180施設」は表②を含んだ数字。
    No は表①と表②で重複するため主キーに使えない。
    provider_no も住宅型では空になるため、facility_id を振り直す。
 
使い方:
    python parse_facilities.py
出力:
    saitama_facilities.csv

学習につかったもの:
[pdfplumberについての記事]https://qiita.com/dakikd/items/2d7a44abfb24d026204b
[is演算子について]https://qiita.com/i13602/items/6d8914e019c13e858c72
[enumerate関数]https://www.kikagaku.co.jp/personal/blog/python-enumerate
[replace]https://note.nkmk.me/python-str-replace-translate-re-sub/#google_vignette
[unicodedataについて]https://docs.python.org/ja/3/library/unicodedata.html
[re.sub]https://docs.python.org/ja/3/library/re.html
        https://note.nkmk.me/python-str-replace-translate-re-sub/#resub-resubn



rows = [] # すべての行データを格納するリスト

# PDFファイルを開く
with pdfplumber.open("R7yuuryouroujinnho-muitir.pdf") as pdf:
    # pdf.pages で全ページを取得してループ
    for i, page in enumerate(pdf.pages):
        # ページ内の表を抽出
        for t in page.extract_tables():
            # 各表のサイズ（行数と、1行目の要素数＝列数）を出力
            print(f"page {i + 1}: {len(t)}行 x {len(t[0])}列")
            
            # 抽出した表の行データを rows リストに追加していく
            rows.extend(t)

# すべてのページから抽出した行数の合計を出力
print("合計行数:", len(rows))

print("======")

def norm(s):
    if s is None:
        return None # セルが空(None)の場合はそのまま返す
    s = s.replace("\n", "") # セル内の改行を削除
    s = unicodedata.normalize("NFKC", s) # 全角英数字を半角にするなど、文字の企画を統一する
    s = re.sub(r"\s+", "", s) # スペースやタブなどの空白文字を削除
    return s or None # 綺麗にした結果何も残らなかったらnoneを返す

rows = []
with pdfplumber.open("R7yuuryouroujinnho-muitir.pdf") as pdf:
    for page in pdf.pages:
        for t in page.extract_tables():
            rows.extend(t) # 抽出した表の行データを追加

# r:rows から取り出した1行分のデータ
# r[0]:その行の1列目のデータ
# norm(r[0]):1列目のデータを先ほどの関数で綺麗にする
# .isdigit(): その文字列が数字だけで構成されているかを判定
data = [r for r in rows if norm(r[0]) and norm(r[0]).isdigit()]

print("データ行数:", len(data))
"""

import pdfplumber, re, unicodedata, sys
import pandas as pd

PDF_PATH = "R7yuuryouroujinnho-muitir.pdf"
OUT_PATH = "saitama_facilities.csv"

SOURCE_NAME = "さいたま市 有料老人ホーム一覧表"
SOURCE_DATE = "2025-07-01"

EXPECTED_TOTAL = 180
EXPECTED_CAPACITY = 9942

COLS = [
    "no", "name", "facility_type", "tenure_type", "entry_requirement",
    "insurance_designation", "provider_no", "address", "phone", "capacity",
    "room_type", "opened_on", "tokurei_from", "access", "corporate_name",
    "corp_zip", "corp_address", "notified_on", "changed_on", "remarks",
]

# 空白を完全に潰してよい列（自由文でないもの） 「値が固定的か、文章か」
# 施設名、類型、電話番号などの「PDFの体裁調整で入ったノイズ」を全除去
STRICT_COLS = {
    "no", "name", "facility_type", "tenure_type", "entry_requirement",
    "insurance_designation", "provider_no", "phone", "capacity",
    "room_type", "opened_on", "tokurei_from", "corporate_name",
    "corp_zip", "notified_on", "changed_on",
}
 
# 「値なし」の意味で使われている記号
NULL_TOKENS = {"-", "‐", "―", "－", "ー", ""}

"""改行・空白を全除去し NFKC 正規化する。

NFKC で全角英数が半角に寄るため、'ＡＬＳＯＫ' と 'ALSOK' の
表記ゆれもここで吸収される。
"""
def norm_strict(s):
    """改行・空白を全除去し NFKC 正規化する。
    
    NFKC で全角英数が半角に寄るため、'ＡＬＳＯＫ' と 'ALSOK' の
    表記ゆれもここで吸収される。
    """
    if s is None:
        return None
    s = unicodedata.normalize("NFKC", s.replace("\n", ""))
    s = re.sub(r"\s+", "", s)
    return None if s in NULL_TOKENS else s # 三項演算子で書かれている [条件を満たした時の結果] if [条件] else [条件を満たさなかった時の結果]
# [pythonの三項演算子]https://qiita.com/howmuch515/items/bf6d21f603d9736fb4a5
# 上記の1行は、この4行と全く同じ処理をしています
# if s in NULL_TOKENS:
#     return None
# else:
#     return s

# [strip()メソッドについて]https://www.sejuku.net/blog/50412#index_id0
def norm_loose(s):
    """住所・交通案内など、単語間の空白に意味がある列用。改行のみ除去。"""
    if s is None:
        return None
    s = unicodedata.normalize("NFKC", s.replace("\n", ""))
    s = re.sub(r"\s+", " ", s).strip()
    return None if s in NULL_TOKENS else s

# [extend()メソッド]https://qiita.com/michi1750/items/c499f9ae8c6a1982caa4
def extract_rows(pdf_path):
    """全ページから行を取り出す。"""
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages: #PDFの全ページを1ページずつ順番に処理
            for table in page.extract_tables(): # ページ内にある「すべての表」を自動検出して抽出
                rows.extend(table) # 抽出した表の「行データ」を rows リストにまとめて追加
    return rows

# [isdigitメソッド]https://qiita.com/yuzuki_luck7/items/5418b035571ac23e0c16
def is_data_row(row):
    """番号列が数字ならデータ行。ヘッダー・タイトル行を除外する。"""
    head = norm_strict(row[0])
    return bool(head and head.isdigit()) # boolで囲むことで、True Falseを返している。 
    # head and と書くことで左から実行される、headの中身がない時点で処理が終わるので、isdigitが動かない　エラーがでない

# [zip関数について]https://docs.python.org/ja/3/library/functions.html#zip
# [appendメソッドについて]https://www.sejuku.net/blog/40530
# [pandas DataFrame]https://qiita.com/Tomato_otamoT/items/0cadec5c7ebec86aed37
#                   https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
def to_dataframe(rows):
    records = []
    for row in rows:
        if not is_data_row(row):# ① データ行でなければスキップ（見出しやタイトルを除外）
            continue
        rec = {}
        # ② 列名（COLS）と セルデータ（row）をペアにして整形
        for col, cell in zip(COLS, row):
            rec[col] = norm_strict(cell) if col in STRICT_COLS else norm_loose(cell)# 重要な列なら厳格な正規化(norm_strict)、それ以外はゆるい正規化(norm_loose)
        records.append(rec)
    return pd.DataFrame(records, columns=COLS)

# [pandas fillnaについて]https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.fillna.html
#                       https://note.nkmk.me/python-pandas-nan-fillna/#google_vignette
# [str.contains]https://note.nkmk.me/python-pandas-str-contains-match/#strcontains
# [str.extract]https://note.nkmk.me/python-pandas-str-extract-extractall/
# [to_numeric]https://pythondatalab.com/pandas-to-numeric/
# [.insert]https://pythondatalab.com/pandas-to-numeric/
#           https://note.nkmk.me/python-pandas-assign-append/#insert

def add_derived_columns(df):
    # 住所特例の対象外=地域密着型
    # ページ位置ではなくしていないようで判定する(ページ構成が変わっても壊れないため)。
    designation = df["insurance_designation"].fillna("")
    df["is_jusho_chi_tokurei"] = ~designation.str.contains("地域密着型")

    # 所在地「桜区 神田715」を区　と　町名以下に分割
    df["ward"] = df["address"].str.extract(r"^(.+?区)")[0]
    df["address_detail"] = df["address"].str.replace(r"^.+?区\s*", "", regex=True)

    df["capacity_num"] = pd.to_numeric(df["capacity"], errors = "coerce")

    # No は表①と表②で重複するため、通し番号を主キーとして振り直す
    df.insert(0, "facility_id", range(1, len(df) + 1))

    # 出所の記録
    df["source"] = SOURCE_NAME
    df["source_date"] = SOURCE_DATE
    return df


