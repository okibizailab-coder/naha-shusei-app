import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- PDF作成クラス：那覇会場公式フォーマット再現 ---
class NahaOfficialPDF(FPDF):
    def __init__(self, m_info, font_path='ipaexg.ttf'):
        super().__init__()
        try:
            self.add_font('IPAexGothic', '', font_path)
            self.font_ready = True
        except:
            self.font_ready = False
        self.m_info = m_info

    def header(self):
        if not self.font_ready: return
        self.set_font('IPAexGothic', '', 12)
        # 左上ヘッダー
        self.cell(40, 8, self.m_info['no'], ln=0)
        self.cell(40, 8, '守成クラブ', ln=0)
        self.cell(40, 8, '那覇会場', ln=1)
        # 右上日付
        self.set_y(10)
        self.cell(0, 8, self.m_info['date'], ln=True, align='R')
        self.ln(5)
        # 列ヘッダー
        self.set_fill_color(240, 240, 240)
        self.set_font('IPAexGothic', '', 9)
        w = [15, 15, 35, 125]
        h = ["時間", "担当", "準備・動き", "進行内容"]
        for i in range(4):
            self.cell(w[i], 8, h[i], border=1, align='C', fill=True)
        self.ln()

    def draw_rows(self, df):
        if not self.font_ready: return
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

# --- 文字コード対策付きCSV読み込み ---
def load_naha_csv(path):
    if not os.path.exists(path): return None
    for enc in ['utf-8', 'shift_jis', 'cp932']:
        try:
            with open(path, 'r', encoding=enc) as f:
                lines = [line.strip().strip('"') for line in f]
            return pd.read_csv(io.StringIO("\n".join(lines)))
        except: continue
    return None

# --- アプリメイン ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("守成クラブ那覇会場：運営DXシステム（完全版）")

# 1. システム診断（サイドバー）
st.sidebar.header("🔍 システム診断")
files = {"台本ひな形": "master_script.csv", "日本語フォント": "ipaexg.ttf"}
status = True
for label, filename in files.items():
    if os.path.exists(filename): st.sidebar.success(f"✅ {label}: OK")
    else:
        st.sidebar.error(f"❌ {label}: 未検出")
        status = False

# 2. 名簿読み込み
uploaded_file = st.sidebar.file_uploader("今回の名簿（Excel/CSV）を選択", type=['xlsx', 'csv'])

if uploaded_file and status:
    df_m = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    cols = df_m.columns.tolist()
    
    st.sidebar.subheader("基本情報・列設定")
    m_no = st.sidebar.text_input("例会回数", "第56回")
    m_date = st.sidebar.text_input("開催日", "2026年1月20日 火曜日")
    
    def gc(ks): return next((c for c in cols if any(k in str(c) for k in ks)), cols[0])
    c_s, c_n, c_i, c_c, c_p = gc(['守成']), gc(['氏名']), gc(['紹介']), gc(['会社']), gc(['二次会'])
    
    tms = df_m[df_m[c_s].str.contains('★', na=False)][c_n].tolist()
    guests = df_m[df_m[c_s].str.contains('ゲスト', na=False)]
    party = df_m[df_m[c_p].str.contains('参加予定', na=False)] if c_p else pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["🖋️ シナリオ編集・PDF", "📜 タイムテーブル", "🍶 二次会名簿"])

    with tab1:
        st.header("進行シナリオ編集")
        m_df = load_naha_csv("master_script.csv")
        if m_df is not None:
            rows = []
            for _, r in m_df.iterrows():
                if "[GUESTS]" in str(r['時間']):
                    for i, (_, g) in enumerate(guests.iterrows(), 1):
                        rows.append(["", "", "", f"{i}) 紹介者:{g[c_i]}さん / ゲスト:{g[c_c]} {g[c_n]}様"])
                else:
                    txt = str(r['進行内容']).replace("{mcs}", "桜井有里、神田橋あずさ").replace("{tk}", "普天間 忍").replace("{tms}", "、".join(tms[:12])).replace("{rep}", "伊集比佐乃").replace("{dep}", "安里正直").replace("{mapper}", "比嘉太一").replace("{len_guests}", str(len(guests)))
                    rows.append([r['時間'], r['担当'], r['準備・動き'], txt])
            
            # 編集・プレビュー
            ed_sc = st.data_editor(pd.DataFrame(rows, columns=["時間", "担当", "準備・動き", "進行内容"]), use_container_width=True)
            st.subheader("👀 全文プレビュー")
            st.table(ed_sc)

            # ダウンロード
            col_d1, col_d2 = st.columns(2)
            fmt = col_d1.selectbox("形式を選択", ["PDF", "Excel"])
            if fmt == "PDF":
                pdf = NahaOfficialPDF({'no': m_no, 'date': m_date})
                pdf.add_page(); pdf.draw_rows(ed_sc)
                col_d2.download_button("📥 PDF保存", data=bytes(pdf.output()), file_name=f"scenario_{m_no}.pdf")
            else:
                out = io.BytesIO()
                ed_sc.to_excel(out, index=False)
                col_d2.download_button("📥 Excel保存", data=out.getvalue(), file_name=f"scenario_{m_no}.xlsx")

    with tab2:
        st.header("本日の次第（タイムテーブル）")
        tt_data = [["13:45", "14:00", "開会前アナウンス", "司会"], ["14:00", "14:03", "オープニング動画", "司会"], ["14:03", "14:08", "代表挨拶", "伊集"], ["14:15", "14:16", "ゲスト紹介", "司会"], ["16:18", "16:21", "出発進行", "安里"]]
        ed_tt = st.data_editor(pd.DataFrame(tt_data, columns=["開始", "終了", "内容", "担当"]), use_container_width=True)
        
        col_t1, col_t2 = st.columns(2)
        tt_fmt = col_t1.selectbox("次第の形式", ["Excel", "PDF"], key="ttfmt")
        if tt_fmt == "Excel":
            out_tt = io.BytesIO()
            ed_tt.to_excel(out_tt, index=False)
            col_t2.download_button("📥 次第Excel保存", data=out_tt.getvalue(), file_name="timetable.xlsx")
        else: st.info("次第のPDF出力は準備中です。Excelをご利用ください。")

    with tab3:
        st.header(f"二次会参加者リスト ({len(party)}名)")
        if not party.empty:
            st.table(party[[c_n, c_c, c_p]])
            out_p = io.BytesIO()
            party[[c_n, c_c, c_p]].to_excel(out_p, index=False)
            st.download_button("📥 名簿Excel保存", data=out_p.getvalue(), file_name="party_list.xlsx")
