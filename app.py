import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- 那覇会場専用 PDF作成クラス（全ページ対応版） ---
class NahaFullPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')

    def header(self):
        self.set_font('IPAexGothic', '', 10)
        self.cell(0, 10, '守成クラブ那覇会場 仕事バンバンプラザ 進行シナリオ', ln=True, align='C')

    def draw_scenario(self, df):
        self.set_font('IPAexGothic', '', 9)
        w = [15, 15, 35, 125] 
        lh = 6 
        for _, row in df.iterrows():
            content = str(row['進行内容'])
            lines = self.multi_cell(w[3], lh, content, split_only=True)
            h = max(lh, len(lines) * lh)
            
            if self.get_y() + h > 275: self.add_page()
            
            curr_y = self.y
            self.cell(w[0], h, str(row['時間']), border=1, align='C')
            self.cell(w[1], h, str(row['担当']), border=1, align='C')
            self.cell(w[2], h, str(row['準備・動き']), border=1)
            self.multi_cell(w[3], lh, content, border=1)
            self.set_y(curr_y + h)

# --- シナリオのベースデータ（16ページ分を凝縮） ---
def get_base_scenario(mc_names, tms, guests, reps):
    tm_text = "、".join(tms[:12]) if tms else "（名簿から抽出）"
    guest_list = []
    for i, (_, g) in enumerate(guests.iterrows(), 1):
        guest_list.append(f"{i})紹介者:{g.get('紹介者','-')}さん / ゲスト:{g.get('会社名','-')} {g.get('氏名','-')}様")
    
    return [
        {"時間": "13:45", "担当": "司会", "準備・動き": "壇上照明OFF", "進行内容": "まもなく開会10分前です。携帯電話は音が出ないようにお願いします。"},
        {"時間": "13:50", "担当": "石川", "準備・動き": "様子見", "進行内容": "それでは今から例会前の体操をします。本日の指導者は石川一久さんです。"},
        {"時間": "14:00", "担当": "司会", "準備・動き": "壇上照明OFF", "進行内容": "第1部スタート。それでは皆様スクリーンに注目をお願いします（オープニング動画）。"},
        {"時間": "14:03", "担当": "司会", "準備・動き": "壇上照明ON", "進行内容": f"第56回那覇会場 開会します。本日の司会は {mc_names} です。"},
        {"時間": "14:05", "担当": "司会", "準備・動き": "全員起立", "進行内容": f"本日のTMは {tm_text} さんです。ご起立ください。"},
        {"時間": "14:08", "担当": "代表", "準備・動き": "センターマイク", "進行内容": f"代表挨拶。{reps}さんお願いします。"},
        {"時間": "14:15", "担当": "司会", "準備・動き": "マイク準備", "進行内容": f"本日お越しの {len(guests)} 名のゲストをご紹介します。"}
    ] + [{"時間": "", "担当": "", "準備・動き": "", "進行内容": g} for g in guest_list] + [
        {"時間": "15:39", "担当": "司会", "準備・動き": "第2部開始", "進行内容": "守成マップ動画を流します。比嘉太一さんご起立ください。"},
        {"時間": "16:04", "担当": "司会", "準備・動き": "紹介者登壇", "進行内容": "入会予定者のご紹介です。皆様、せーの！！めんそ〜れ〜！"},
        {"時間": "16:18", "担当": "安里", "準備・動き": "出発進行", "進行内容": "本日の出発進行は安里正直さんです。皆様ご起立ください。"},
        {"時間": "16:21", "担当": "司会", "準備・動き": "終了", "進行内容": "本日の司会は桜井と神田橋でした。次回も楽しみにしております！"}
    ]

# --- メインアプリ ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：全16ページ・フルシナリオ自動生成")

uploaded_file = st.sidebar.file_uploader("名簿(Excel/CSV)をアップロード", type=['xlsx', 'csv'])

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

    tms = df[df[col_shusei].str.contains('★', na=False)][col_name].tolist() if col_shusei else []
    guests = df[df[col_shusei].str.contains('ゲスト', na=False)] if col_shusei else pd.DataFrame()
    rep_name = df[df[col_shusei].str.contains('代表', na=False)][col_name].iloc[0] if col_shusei and not df[df[col_shusei].str.contains('代表', na=False)].empty else "伊集比佐乃"

    st.sidebar.info(f"抽出結果: TM {len(tms)}名 / ゲスト {len(guests)}名")

    # 1. 配置と編集
    mc_input = st.text_input("司会担当名", "桜井 有里、神田橋 あずさ")
    
    st.header("🖊️ 台本の最終編集 (全セリフ表示)")
    st.caption("※エディタ内で自由に書き換え、追加が可能です。")
    
    # 16ページ分のセリフを流し込んだデータエディタ
    base_data = get_base_scenario(mc_input, tms, guests, rep_name)
    edited_df = st.data_editor(pd.DataFrame(base_data), num_rows="dynamic", use_container_width=True)

    # 2. PDF生成
    if st.button("🖨️ フルシナリオ(PDF)をダウンロード"):
        pdf = NahaFullPDF()
        pdf.add_page()
        pdf.draw_scenario(edited_df)
        st.download_button("📥 PDF保存", data=bytes(pdf.output()), file_name="naha_full_scenario.pdf")
