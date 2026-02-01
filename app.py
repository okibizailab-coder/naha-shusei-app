import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from datetime import datetime, timedelta

# --- PDF作成クラス（那覇会場専用：4列レイアウト & 二次会ページ対応） ---
class NahaDX_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')

    def header(self):
        self.set_font('IPAexGothic', '', 12)
        self.cell(0, 10, '守成クラブ那覇会場 仕事バンバンプラザ 資料', ln=True, align='C')

    def draw_scenario_table(self, df_scenario):
        self.set_font('IPAexGothic', '', 9)
        w = [15, 15, 35, 125] 
        lh = 7
        for _, row in df_scenario.iterrows():
            lines = self.multi_cell(w[3], lh, str(row['進行内容']), split_only=True)
            h = max(lh, len(lines) * lh)
            if self.get_y() + h > 270: self.add_page()
            curr_x, curr_y = self.x, self.y
            self.cell(w[0], h, str(row['時間']), border=1, align='C')
            self.cell(w[1], h, str(row['担当']), border=1, align='C')
            self.cell(w[2], h, str(row['準備・動き']), border=1)
            self.multi_cell(w[3], lh, str(row['進行内容']), border=1)
            self.set_y(curr_y + h)

    def draw_party_list(self, df_party):
        self.add_page()
        self.set_font('IPAexGothic', '', 14)
        self.cell(0, 10, '二次会（懇親会）参加者リスト', ln=True, align='L')
        self.ln(5)
        self.set_font('IPAexGothic', '', 10)
        # 表のヘッダー
        cols = ["No", "氏名", "会社名", "紹介者"]
        widths = [10, 40, 70, 40]
        for i, col in enumerate(cols):
            self.cell(widths[i], 10, col, border=1, align='C')
        self.ln()
        # 参加者データ
        for i, (_, row) in enumerate(df_party.iterrows(), 1):
            self.cell(widths[0], 8, str(i), border=1)
            self.cell(widths[1], 8, str(row['氏名']), border=1)
            self.cell(widths[2], 8, str(row['会社名']), border=1)
            self.cell(widths[3], 8, str(row.get('紹介者', '-')), border=1)
            self.ln()

# --- アプリ画面制御 ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：全自動シナリオ＆二次会リスト作成")

# 名簿アップロード
uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # データ抽出
    tms = df[df['守成役'].str.contains('★', na=False)]['氏名'].tolist()
    guests = df[df['守成役'].str.contains('ゲスト', na=False)]
    party_members = df[df['二次会'].str.contains('参加予定', na=False)]

    tab1, tab2, tab3 = st.tabs(["📋 役割配置", "台本編集・プレビュー", "🍶 二次会リスト"])

    with tab1:
        st.header("1. 役割の最終確認")
        mc_names = st.text_input("司会担当", "桜井 有里、神田橋 あずさ")
        guest_time = len(guests) * 10 # 1人10秒
        st.write(f"ゲスト数: {len(guests)}名 (想定時間: {guest_time}秒)")

    with tab2:
        st.header("2. シナリオの編集・手直し")
        st.caption("※表の中を直接ダブルクリックして自由に書き換えられます。")
        
        # 初期データの自動生成
        initial_data = [
            {"時間": "14:00", "担当": "司会", "準備・動き": "照明OFF", "進行内容": "オープニング動画開始。"},
            {"時間": "14:03", "担当": "司会", "準備・動き": "照明ON", "進行内容": f"第56回 例会を開会します。本日の司会は {mc_names} です。"},
            {"時間": "14:05", "担当": "司会", "準備・動き": "全員起立", "進行内容": f"本日のTMは {', '.join(tms[:12])} さんです。"},
        ]
        # ゲスト紹介の追加
        for i, (_, g) in enumerate(guests.iterrows(), 1):
            initial_data.append({"時間": "", "担当": "", "準備・動き": "", "進行内容": f"{i}) 紹介者:{g['紹介者']}さん / ゲスト:{g['会社名']} {g['氏名']}様"})

        # 【重要】データエディタ機能（ここで手直し可能）
        edited_df = st.data_editor(pd.DataFrame(initial_data), num_rows="dynamic", use_container_width=True)

        # PDFダウンロード
        if st.button("🖨️ シナリオPDFをダウンロード"):
            pdf = NahaDX_PDF()
            pdf.add_page()
            pdf.draw_scenario_table(edited_df)
            st.download_button("📥 ダウンロード開始", data=bytes(pdf.output()), file_name="scenario.pdf")

    with tab3:
        st.header(f"3. 二次会参加予定者 ({len(party_members)}名)")
        st.dataframe(party_members[['氏名', '会社名', '二次会']], use_container_width=True)
        
        if st.button("🍶 二次会リストをPDFで保存"):
            pdf = NahaDX_PDF()
            pdf.draw_party_list(party_members)
            st.download_button("📥 二次会PDF保存", data=bytes(pdf.output()), file_name="party_list.pdf")
