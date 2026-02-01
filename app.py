import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- PDF作成クラス：本物のフォーマットを完全再現 ---
class NahaOfficialPDF(FPDF):
    def __init__(self, m_info, font_path='ipaexg.ttf'):
        super().__init__()
        self.add_font('IPAexGothic', '', font_path)
        self.m_info = m_info
    def header(self):
        self.set_font('IPAexGothic', '', 12)
        self.cell(40, 8, self.m_info['no'], ln=0)
        self.cell(40, 8, '守成クラブ', ln=0)
        self.cell(40, 8, '那覇会場', ln=1)
        self.set_y(10)
        self.cell(0, 8, self.m_info['date'], ln=True, align='R')
        self.ln(5)
        self.set_fill_color(240, 240, 240)
        w = [15, 15, 35, 125]
        h = ["時間", "担当", "準備・動き", "進行内容"]
        for i in range(4): self.cell(w[i], 8, h[i], border=1, align='C', fill=True)
        self.ln()
    def draw_rows(self, df):
        self.set_font('IPAexGothic', '', 9)
        w, lh = [15, 15, 35, 125], 5.0
        for _, row in df.iterrows():
            c, p = str(row['進行内容']), str(row['準備・動き'])
            lines = self.multi_cell(w[3], lh, c, split_only=True)
            h = max(lh, len(lines) * lh) + 4
            if self.get_y() + h > 275: self.add_page()
            curr_y = self.get_y()
            for i in range(4): self.rect(self.get_x() + sum(w[:i]), curr_y, w[i], h)
            self.cell(w[0], h, str(row['時間']), align='C')
            self.cell(w[1], h, str(row['担当']), align='C')
            self.set_xy(self.get_x(), curr_y+2); self.multi_cell(w[2], lh, p)
            self.set_xy(self.get_x()+w[2], curr_y+2); self.multi_cell(w[3], lh, c)
            self.set_y(curr_y + h)

# --- CSV読み込み補助 ---
def load_naha_csv(path):
    if not os.path.exists(path): return None
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.strip().strip('"') for line in f]
    return pd.read_csv(io.StringIO("\n".join(lines)))

# --- アプリメイン ---
st.set_page_config(page_title="守成那覇 運営アシスタント", layout="wide")
st.title("那覇会場：全資料一括作成システム")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df_m = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    cols = df_m.columns.tolist()
    
    st.sidebar.subheader("基本情報")
    m_no = st.sidebar.text_input("例会回数", "第56回")
    m_date = st.sidebar.text_input("開催日", "2026年1月20日 火曜日")
    
    st.sidebar.subheader("列の設定（エラー防止用）")
    c_s = st.sidebar.selectbox("守成役の列", cols, index=0)
    c_n = st.sidebar.selectbox("氏名の列", cols, index=0)
    c_i = st.sidebar.selectbox("紹介者の列", cols, index=0)
    c_c = st.sidebar.selectbox("会社名の列", cols, index=0)
    c_p = st.sidebar.selectbox("二次会の列", cols, index=0)

    # データ抽出
    tms = df_m[df_m[c_s].str.contains('★', na=False)][c_n].tolist()
    guests = df_m[df_m[c_s].str.contains('ゲスト', na=False)]
    party = df_m[df_m[c_p].str.contains('参加予定', na=False)] if c_p else pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["🖋️ シナリオ編集・PDF", "📜 タイムテーブル", "🍶 二次会名簿"])

    with tab1:
        st.header("進行シナリオ（全16ページ）")
        master_df = load_naha_csv("master_script.csv")
        if master_df is not None:
            rows = []
            for _, r in master_df.iterrows():
                if "[GUESTS]" in str(r['時間']):
                    for i, (_, g) in enumerate(guests.iterrows(), 1):
                        rows.append(["", "", "", f"{i}) 紹介者:{g[c_i]} / ゲスト:{g[c_c]} {g[c_n]}様"])
                else:
                    txt = str(r['進行内容']).replace("{mcs}", "桜井有里、神田橋あずさ").replace("{tk}", "普天間 忍").replace("{tms}", "、".join(tms[:12])).replace("{rep}", "伊集比佐乃").replace("{dep}", "安里正直")
                    rows.append([r['時間'], r['担当'], r['準備・動き'], txt])
            
            # エディタとプレビュー
            ed_sc = st.data_editor(pd.DataFrame(rows, columns=["時間", "担当", "準備・動き", "進行内容"]), use_container_width=True, key="sc_ed")
            st.table(ed_sc)

            st.write("---")
            col_d1, col_d2 = st.columns(2)
            fmt = col_d1.selectbox("ダウンロード形式", ["PDF", "Excel"], key="fmt_sc")
            if fmt == "PDF":
                pdf = NahaOfficialPDF({'no': m_no, 'date': m_date})
                pdf.add_page(); pdf.draw_rows(ed_sc)
                col_d2.download_button("📥 PDFを保存", data=bytes(pdf.output()), file_name="scenario.pdf")
            else:
                out = io.BytesIO()
                ed_sc.to_excel(out, index=False)
                col_d2.download_button("📥 Excelを保存", data=out.getvalue(), file_name="scenario.xlsx")

    with tab2:
        st.header("タイムテーブル（見本）")
        tt_data = [["13:45", "14:00", "アナウンス", "司会"], ["14:00", "14:03", "動画", "司会"], ["14:03", "14:05", "役割紹介", "司会"]]
        ed_tt = st.data_editor(pd.DataFrame(tt_data, columns=["開始", "終了", "イベント", "担当"]), use_container_width=True, key="tt_ed")
        st.table(ed_tt)
        
        out_tt = io.BytesIO()
        ed_tt.to_excel(out_tt, index=False)
        st.download_button("📥 タイムテーブル(Excel)を保存", data=out_tt.getvalue(), file_name="timetable.xlsx")

    with tab3:
        st.header(f"二次会名簿 ({len(party)}名)")
        st.table(party[[c_n, c_c, c_p]])
