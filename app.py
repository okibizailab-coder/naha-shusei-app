import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- 1. PDF作成クラス：本物のシナリオ再現 ---
class NahaScenarioPDF(FPDF):
    def __init__(self, m_info):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')
        self.m_info = m_info
    def header(self):
        self.set_font('IPAexGothic', '', 12)
        self.cell(30, 8, self.m_info['no'], ln=0)
        self.cell(30, 8, '守成クラブ', ln=0)
        self.cell(30, 8, '那覇会場', ln=1)
        self.set_y(10)
        self.cell(0, 8, self.m_info['date'], ln=True, align='R')
        self.ln(5)
        self.set_font('IPAexGothic', '', 9)
        self.set_fill_color(240, 240, 240)
        w = [15, 15, 35, 125]
        h = ["時間", "担当", "準備・動き", "進行内容"]
        for i in range(4):
            self.cell(w[i], 8, h[i], border=1, align='C', fill=True)
        self.ln()
    def draw_rows(self, df):
        self.set_font('IPAexGothic', '', 9)
        w = [15, 15, 35, 125]; lh = 5.0
        for _, row in df.iterrows():
            c, p = str(row['進行内容']), str(row['準備・動き'])
            lines_c = self.multi_cell(w[3], lh, c, split_only=True)
            h = max(lh, len(lines_c) * lh) + 4
            if self.get_y() + h > 275: self.add_page()
            curr_x, curr_y = self.get_x(), self.get_y()
            for i in range(4): self.rect(curr_x + sum(w[:i]), curr_y, w[i], h)
            self.cell(w[0], h, str(row['時間']), align='C')
            self.cell(w[1], h, str(row['担当']), align='C')
            self.set_xy(curr_x + w[0] + w[1], curr_y + 2); self.multi_cell(w[2], lh, p)
            self.set_xy(curr_x + w[0] + w[1] + w[2], curr_y + 2); self.multi_cell(w[3], lh, c)
            self.set_y(curr_y + h)

# --- 2. CSV読み込み補助 ---
def load_naha_csv(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip().strip('"') for line in f]
        return pd.read_csv(io.StringIO("\n".join(lines)))
    return None

# --- アプリメイン ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：運営資料作成システム")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）を読み込む", type=['xlsx', 'csv'])

if uploaded_file:
    df_m = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    cols = df_m.columns.tolist()
    
    st.sidebar.subheader("基本情報")
    m_no = st.sidebar.text_input("例会回数", "第56回")
    m_date = st.sidebar.text_input("開催日", "2026年1月20日 火曜日")
    
    def get_c(ks): return next((c for c in cols if any(k in str(c) for k in ks)), cols[0])
    c_s, c_n, c_i, c_c, c_p = get_c(['守成']), get_c(['氏名']), get_c(['紹介']), get_c(['会社']), get_c(['二次会'])
    
    tms = df_m[df_m[c_s].str.contains('★', na=False)][c_n].tolist()
    guests = df_m[df_m[c_s].str.contains('ゲスト', na=False)]
    party = df_m[df_m[c_p].str.contains('参加予定', na=False)] if c_p else pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["🖋️ シナリオ編集", "📜 タイムテーブル", "🍶 二次会名簿"])

    # --- タブ1: シナリオ ---
    with tab1:
        st.header("進行シナリオ（全16ページ）")
        m_df = load_naha_csv("master_script.csv")
        if m_df is not None:
            rows = []
            for _, r in m_df.iterrows():
                if "[GUESTS]" in str(r['時間']):
                    for i, (_, g) in enumerate(guests.iterrows(), 1):
                        rows.append(["", "", "", f"{i}) 紹介者:{g[c_i]} / ゲスト:{g[c_c]} {g[c_n]}様"])
                else:
                    txt = str(r['進行内容']).replace("{mcs}", "桜井有里、神田橋あずさ").replace("{tk}", "普天間 忍").replace("{tms}", "、".join(tms[:12])).replace("{rep}", "伊集比佐乃").replace("{dep}", "安里正直")
                    rows.append([r['時間'], r['担当'], r['準備・動き'], txt])
            
            ed_sc = st.data_editor(pd.DataFrame(rows, columns=["時間", "担当", "準備・動き", "進行内容"]), use_container_width=True, key="sc_editor")
            
            # ダウンロード機能（修正版：ボタンを入れ子にしない）
            st.write("---")
            c1, c2 = st.columns(2)
            fmt = c1.selectbox("ダウンロード形式", ["PDF", "Excel"], key="sc_fmt")
            
            if fmt == "PDF":
                pdf = NahaScenarioPDF({'no': m_no, 'date': m_date})
                pdf.add_page()
                pdf.draw_rows(ed_sc)
                c2.download_button("📥 シナリオPDFを保存", data=bytes(pdf.output()), file_name="naha_scenario.pdf", mime="application/pdf")
            else:
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                    ed_sc.to_excel(writer, index=False)
                c2.download_button("📥 シナリオExcelを保存", data=out.getvalue(), file_name="naha_scenario.xlsx")
            
            st.subheader("👀 全文表示（印刷イメージ）")
            st.table(ed_sc)

    # --- タブ2: タイムテーブル ---
    with tab2:
        st.header("タイムテーブル（次第）")
        # 1月タイムテーブル見本から主要項目を抽出
        tt_data = [["13:45", "14:00", "アナウンス", "司会"], ["14:00", "14:03", "動画", "司会"], ["14:03", "14:05", "役割紹介", "司会"], ["14:05", "14:08", "宝の山", "西川"], ["14:08", "14:12", "代表挨拶", "伊集"], ["14:15", "14:16", "ゲスト紹介", "司会"]]
        ed_tt = st.data_editor(pd.DataFrame(tt_data, columns=["開始", "終了", "イベント", "担当"]), use_container_width=True, key="tt_editor")
        
        tt_out = io.BytesIO()
        with pd.ExcelWriter(tt_out, engine='xlsxwriter') as writer:
            ed_tt.to_excel(writer, index=False)
        st.download_button("📥 タイムテーブル(Excel)を保存", data=tt_out.getvalue(), file_name="timetable.xlsx")

    # --- タブ3: 二次会 ---
    with tab3:
        st.header(f"二次会名簿 ({len(party)}名)")
        st.table(party[[c_n, c_c, c_p]])
