import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- 那覇会場専用：次第・シナリオ完全再現クラス ---
class NahaPerfectScenarioPDF(FPDF):
    def __init__(self, meeting_info):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')
        self.meeting_info = meeting_info # 例会回数や日付

    def header(self):
        # PDFの冒頭：回数、会場名、日付の再現
        self.set_font('IPAexGothic', '', 12)
        self.cell(40, 10, self.meeting_info['no'], ln=0)
        self.cell(40, 10, '守成クラブ', ln=0)
        self.cell(40, 10, '那覇会場', ln=1)
        self.set_font('IPAexGothic', '', 10)
        self.cell(0, 10, self.meeting_info['date'], ln=True, align='R')
        self.ln(2)
        
        # 列ヘッダーの再現 
        self.set_fill_color(240, 240, 240) # 薄いグレー
        self.set_font('IPAexGothic', '', 9)
        w = [15, 15, 35, 125]
        headers = ["時間", "担当", "準備・動き", "進行内容"]
        for i in range(4):
            self.cell(w[i], 8, headers[i], border=1, align='C', fill=True)
        self.ln()

    def footer(self):
        # ページ番号の再現 
        self.set_y(-15)
        self.set_font('IPAexGothic', '', 8)
        self.cell(0, 10, f'{self.page_no()}', 0, 0, 'C')

    def draw_rows(self, df):
        self.set_font('IPAexGothic', '', 9)
        w = [15, 15, 35, 125] 
        lh = 5.0
        for _, row in df.iterrows():
            content = str(row['進行内容'])
            prep = str(row['準備・動き'])
            
            # 高さを計算（進行内容の長さに合わせる）
            lines_c = self.multi_cell(w[3], lh, content, split_only=True)
            lines_p = self.multi_cell(w[2], lh, prep, split_only=True)
            row_h = max(lh, len(lines_c) * lh, len(lines_p) * lh) + 4
            
            # 改ページ処理
            if self.get_y() + row_h > 275:
                self.add_page()
            
            x, y = self.get_x(), self.get_y()
            
            # セル枠の描画
            self.rect(x, y, w[0], row_h); self.rect(x + w[0], y, w[1], row_h)
            self.rect(x + w[0] + w[1], y, w[2], row_h); self.rect(x + w[0] + w[1] + w[2], y, w[3], row_h)
            
            # テキスト流し込み
            self.cell(w[0], row_h, str(row['時間']), align='C')
            self.cell(w[1], row_h, str(row['担当']), align='C')
            
            # 準備・動き（自動改行対応）
            self.set_xy(x + w[0] + w[1], y + 2)
            self.multi_cell(w[2], lh, prep, align='L')
            
            # 進行内容（自動改行対応） 
            self.set_xy(x + w[0] + w[1] + w[2], y + 2)
            self.multi_cell(w[3], lh, content, align='L')
            
            self.set_y(y + row_h)

# --- CSV読み込み ---
def load_script():
    if os.path.exists("master_script.csv"):
        with open("master_script.csv", 'r', encoding='utf-8') as f:
            lines = [line.strip().strip('"') for line in f]
        return pd.read_csv(io.StringIO("\n".join(lines)))
    return None

# --- Streamlit アプリ ---
st.set_page_config(page_title="守成那覇 シナリオ再現システム", layout="wide")
st.title("那覇会場：公式シナリオ再現システム")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df_meibo = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    cols = df_meibo.columns.tolist()
    
    # サイドバー設定
    st.sidebar.subheader("PDFヘッダー情報 ")
    m_no = st.sidebar.text_input("例会回数", "第56回")
    m_date = st.sidebar.text_input("開催日", "2026年1月20日 火曜日")
    
    st.sidebar.subheader("列の紐付け")
    c_n = st.sidebar.selectbox("氏名", cols, index=0)
    c_s = st.sidebar.selectbox("守成役", cols, index=0)
    c_i = st.sidebar.selectbox("紹介者", cols, index=0)
    c_c = st.sidebar.selectbox("会社名", cols, index=0)

    # データ抽出
    tms = df_meibo[df_meibo[c_s].str.contains('★', na=False)][c_n].tolist()
    guests = df_meibo[df_meibo[c_s].str.contains('ゲスト', na=False)]

    # タブ
    tab1, tab2 = st.tabs(["🖋️ シナリオ編集", "📜 二次会名簿"])

    with tab1:
        st.header("進行シナリオのプレビュー")
        master_df = load_script()
        if master_df is not None:
            # 変数置換
            final_rows = []
            for _, r in master_df.iterrows():
                if "[GUESTS]" in str(r['時間']):
                    for i, (_, g) in enumerate(guests.iterrows(), 1):
                        final_rows.append(["", "", "", f"{i}) 紹介者:{g[c_i]}さん / ゲスト:{g[c_c]} {g[c_n]}様"])
                else:
                    txt = str(r['進行内容']).replace("{mcs}", "桜井有里、神田橋あずさ").replace("{tms}", "、".join(tms[:12])).replace("{tk}", "普天間 忍")
                    final_rows.append([r['時間'], r['担当'], r['準備・動き'], txt])
            
            ed_df = st.data_editor(pd.DataFrame(final_rows, columns=["時間", "担当", "準備・動き", "進行内容"]), num_rows="dynamic", use_container_width=True)
            
            if st.button("🖨️ 公式フォーマットでPDFを作成"):
                pdf = NahaPerfectScenarioPDF({'no': m_no, 'date': m_date})
                pdf.add_page()
                pdf.draw_rows(ed_df)
                st.download_button("📥 PDFを保存する", data=bytes(pdf.output()), file_name=f"naha_scenario_{m_no}.pdf")
            
            st.subheader("👀 全文表示（印刷イメージ）")
            st.table(ed_df)
