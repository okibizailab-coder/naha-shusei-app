import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- PDF作成クラス（全16ページ・マルチページ完全対応） ---
class NahaMasterPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')

    def header(self):
        self.set_font('IPAexGothic', '', 10)
        self.cell(0, 10, '守成クラブ那覇会場 仕事バンバンプラザ 進行シナリオ', ln=True, align='C')

    def draw_full_scenario(self, df):
        self.set_font('IPAexGothic', '', 9)
        w = [15, 15, 35, 125] 
        lh = 5.5 
        for _, row in df.iterrows():
            content = str(row['進行内容'])
            prep = str(row['準備・動き'])
            
            # 内容に合わせて高さを計算
            lines = self.multi_cell(w[3], lh, content, split_only=True)
            prep_lines = self.multi_cell(w[2], lh, prep, split_only=True)
            h = max(lh, len(lines) * lh, len(prep_lines) * lh)
            
            # 改ページ判定
            if self.get_y() + h > 275: self.add_page()
            
            curr_y = self.y
            self.cell(w[0], h, str(row['時間']), border=1, align='C')
            self.cell(w[1], h, str(row['担当']), border=1, align='C')
            # 準備・動きのマルチセル
            curr_x = self.x
            self.multi_cell(w[2], lh, prep, border=1)
            self.set_xy(curr_x + w[2], curr_y)
            # 進行内容のマルチセル
            self.multi_cell(w[3], lh, content, border=1)
            self.set_y(curr_y + h)

# --- 16ページ分の全セリフデータ生成 ---
def get_master_script(mcs, tms, guests, rep, secrecy, mapper, departure):
    tm_list = "、".join(tms[:12]) if tms else "（名簿から抽出）"
    
    script = [
        {"時間": "13:45", "担当": "司会", "準備・動き": "壇上照明OFF / 受付状況確認", 
         "進行内容": "まもなく開会10分前です。携帯電話は音が出ないようにお願いします。チラシ配布の方は55分までにお席へ。お車の方は守衛所で駐車券に印鑑を。懇親会は定員に達したため受付終了しました。リストバンド着用をお願いします。"},
        {"時間": "13:50", "担当": "司会", "準備・動き": "石川さん合図", 
         "進行内容": "それでは例会前の体操をします。本日の指導者は「整体ここからの石川一久」さんです。"},
        {"時間": "14:00", "担当": "司会", "準備・動き": "壇上照明OFF", 
         "進行内容": "第1部スタート。オープニング動画、それでは皆様スクリーンに注目をお願いします。"},
        {"時間": "14:03", "担当": "司会", "準備・動き": "壇上照明ON", 
         "進行内容": f"ただいまより第56回仕事バンバンプラザ那覇を開会いたします。本日の司会は {mcs} です。"},
        {"時間": "14:05", "担当": "司会", "準備・動き": "全員起立確認", 
         "進行内容": f"本日のタイムキーパーは普天間忍さん。テーブルマスターは {tm_list} さんです。ご起立ください。ウェルカムドリンクは綿谷さんのBENI、お菓子は知花さんの蜂蜜飴です。"},
        {"時間": "14:05", "担当": "司会", "準備・動き": "照明ON", 
         "進行内容": "開会宣言「宝の山」。Sea Whisperの西川結音子さんに朗読して頂きます。本日は07番です。"},
        {"時間": "14:08", "担当": "司会", "準備・動き": "センターマイク", 
         "進行内容": f"代表挨拶。株式会社Office IJU {rep} さん、ご挨拶をお願いします。"},
        {"時間": "14:12", "担当": "司会", "準備・動き": "アナウンス", 
         "進行内容": "広報かわら版のお知らせです。伊敷ゆきさんお願いします。"},
        {"時間": "14:15", "担当": "司会", "準備・動き": "センターマイク使用", 
         "進行内容": f"本日お越しの {len(guests)} 名のゲストをご紹介します。お名前を呼ばれた方はその場でご起立ください。"},
    ]
    # ゲストリスト追加
    for i, (_, g) in enumerate(guests.iterrows(), 1):
        script.append({"時間": "", "担当": "", "準備・動き": "", "進行内容": f"{i})紹介者:{g.get('紹介者','-')}さん / ゲスト:{g.get('会社名','-')} {g.get('氏名','-')}様"})
    
    script.extend([
        {"時間": "14:16", "担当": "事務局", "準備・動き": "外間さん", "進行内容": "事務局からのお知らせです。一般会員ログインの案内、5周年記念商品券の利用店舗募集について。"},
        {"時間": "14:19", "担当": "司会", "準備・動き": "開催案内見せる", "進行内容": "他会場紹介。本日は県内外10会場からご参加です。いばらき南、品川、池袋、ひるの銀座、横浜みなとみらい、堺、沖縄、ヒルノ沖縄、沖縄北部、沖縄中部の皆様です。"},
        {"時間": "14:22", "担当": "司会", "準備・動き": "授与式準備", "進行内容": "授与式です。緑バッチ、赤バッチ、がんばれ楯、鬼瓦、ゴールドバッチ。義元大蔵さんより授与頂きます。"},
        {"時間": "14:27", "担当": "司会", "準備・動き": "タイマー表示", "進行内容": "TM説明。マッチングPOPの記入、名札位置、車座の流れを説明してください。"},
        {"時間": "14:31", "担当": "司会", "準備・動き": "照明OFF / カウントダウン", "進行内容": "1回目車座商談会スタート。お一人様2分です。"},
        {"時間": "14:52", "担当": "司会", "準備・動き": "席替え誘導", "進行内容": "2回目車座商談会スタート。荷物をまとめて移動してください。"},
        {"時間": "15:10", "担当": "比嘉", "準備・動き": "ブースPR担当", "進行内容": "ブースPRタイムです。お一人30秒。特別枠、綿谷、中島、仲本、伊敷、小林、山崎、知花、セントローレント、天野、座安、會澤、生藤、若林、谷水の順です。"},
        {"時間": "15:19", "担当": "司会", "準備・動き": "第1部終了", "進行内容": "休憩に入ります。ゲストの皆様はオリエンテーションへ。駐車券、マッチングPOPの提出、懇親会費のお支払いをお願いします。"},
        {"時間": "15:39", "担当": "司会", "準備・動き": "守成マップ動画", "進行内容": f"第2部スタート。守成マップ動画を流します。担当は {mapper} さんです。"},
        {"時間": "15:40", "担当": "司会", "準備・動き": "義元さん登壇", "進行内容": "挨拶。全国連絡協議会 常務理事 義元大蔵様よりご挨拶頂きます。"},
        {"時間": "15:47", "担当": "司会", "準備・動き": "商談報告3組", "進行内容": "商談報告です。①伊敷さん・加藤さん、②外間さん・ステーキ協会、③小林さん・神田橋さんの3組です。"},
        {"時間": "15:49", "担当": "司会", "準備・動き": "名刺交換音楽", "進行内容": "大名刺交換会。名刺を交換したら半歩右へ。入会されない方は名刺の返却を。"},
        {"時間": "16:04", "担当": "司会", "準備・動き": "紹介者・ゲスト登壇", "進行内容": "入会予定者紹介。皆様、せーの！！めんそ〜れ〜！"},
        {"時間": "16:15", "担当": "世話人", "準備・動き": "伊敷さん・南風見さん", "進行内容": "世話人からのお知らせ。自主運営への協力、がんばれ冊子、ランチ会、夜会の案内。次回2/17はコレクティブ開催です。"},
        {"時間": "16:18", "担当": "司会", "準備・動き": "全員起立", "進行内容": f"出発進行。本日は {departure} さんです。"},
        {"時間": "16:21", "担当": "司会", "準備・動き": "終了", "進行内容": "閉会のご案内。新規入会オリエンテーション、名札の返却、ゴミの持ち帰りをお願いします。本日はありがとうございました！"}
    ])
    return script

# --- メインアプリ ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：全16ページ・フルシナリオ完全版")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # 列名の自動判別
    def find_col(keys):
        for c in df.columns:
            if any(k in str(c) for k in keys): return c
        return None

    col_name = find_col(['氏名', '名前'])
    col_shusei = find_col(['守成', '役'])
    col_comp = find_col(['会社'])
    col_intro = find_col(['紹介'])

    # 各担当者の抽出
    tms = df[df[col_shusei].str.contains('★', na=False)][col_name].tolist() if col_shusei else []
    guests = df[df[col_shusei].str.contains('ゲスト', na=False)] if col_shusei else pd.DataFrame()
    rep = df[df[col_shusei].str.contains('代表', na=False)][col_name].iloc[0] if col_shusei and not df[df[col_shusei].str.contains('代表', na=False)].empty else "伊集 比佐乃"
    dep = df[df[col_shusei].str.contains('旗手', na=False)][col_name].iloc[0] if col_shusei and not df[df[col_shusei].str.contains('旗手', na=False)].empty else "安里 正直"

    # サイドバーでの設定
    mc_input = st.sidebar.text_input("司会担当名", "桜井 有里、神田橋 あずさ")
    map_input = st.sidebar.text_input("守成マップ担当", "比嘉 太一")

    st.header("🖊️ 全16ページ・シナリオの編集")
    st.caption("※以下の表をダブルクリックして、実際のPDFのセリフを一言一句自由に書き換えられます。")
    
    # データの生成とエディタ
    full_script = get_master_script(mc_input, tms, guests, rep, "伊敷ゆき", map_input, dep)
    edited_df = st.data_editor(pd.DataFrame(full_script), num_rows="dynamic", use_container_width=True)

    # PDFダウンロード
    if st.button("🖨️ フルシナリオ(PDF)をダウンロード"):
        pdf = NahaMasterPDF()
        pdf.add_page()
        pdf.draw_full_scenario(edited_df)
        st.download_button("📥 PDF保存", data=bytes(pdf.output()), file_name="naha_perfect_scenario.pdf")
