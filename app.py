import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- 1. PDF作成クラス：本物のシナリオ (新)シナリオ2026年1月 を再現 ---
class NahaOfficialScenarioPDF(FPDF):
    def __init__(self, m_info):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')
        self.m_info = m_info

    def header(self):
        self.set_font('IPAexGothic', '', 12)
        # ヘッダー：左側に回数・会場名
        self.cell(30, 8, self.m_info['no'], ln=0)
        self.cell(30, 8, '守成クラブ', ln=0)
        self.cell(30, 8, '那覇会場', ln=1)
        # ヘッダー：右側に日付
        self.set_y(10)
        self.cell(0, 8, self.m_info['date'], ln=True, align='R')
        self.ln(5)
        # テーブル見出し
        self.set_font('IPAexGothic', '', 9)
        self.set_fill_color(240, 240, 240)
        w = [15, 15, 35, 125]
        h = ["時間", "担当", "準備・動き", "進行内容"]
        for i in range(4):
            self.cell(w[i], 8, h[i], border=1, align='C', fill=True)
        self.ln()

    def footer(self):
        self.set_y(-15)
        self.set_font('IPAexGothic', '', 8)
        self.cell(0, 10, f'{self.page_no()}', 0, 0, 'C')

# --- 2. PDF作成クラス：1月タイムテーブル を再現 ---
class NahaTimetablePDF(FPDF):
    def __init__(self, m_info):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')
        self.m_info = m_info

    def header(self):
        self.set_font('IPAexGothic', '', 14)
        self.cell(0, 10, f"{self.m_info['date']}例会 那覇会場 タイムテーブル", ln=True, align='C')
        self.ln(5)

# --- CSV読み込み補助 ---
def load_naha_csv(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip().strip('"') for line in f]
        return pd.read_csv(io.StringIO("\n".join(lines)))
    return None

# --- アプリメイン ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：運営資料作成システム")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df_m = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    cols = df_m.columns.tolist()
    
    # 基本設定
    st.sidebar.subheader("基本情報")
    m_no = st.sidebar.text_input("例会回数", "第56回")
    m_date = st.sidebar.text_input("開催日", "2026年1月20日 火曜日")
    
    # データ抽出
    def get_c(ks): return next((c for c in cols if any(k in str(c) for k in ks)), cols[0])
    c_s, c_n, c_i, c_c, c_p = get_c(['守成']), get_c(['氏名']), get_c(['紹介']), get_c(['会社']), get_c(['二次会'])
    
    tms = df_m[df_m[c_s].str.contains('★', na=False)][c_n].tolist()
    guests = df_m[df_m[c_s].str.contains('ゲスト', na=False)]
    party = df_m[df_m[c_p].str.contains('参加予定', na=False)] if c_p else pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["🖋️ シナリオ編集", "📜 タイムテーブル", "🍶 二次会名簿"])

    # --- タブ1: シナリオ ---
    with tab1:
        st.header("進行シナリオ（16ページ分）")
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
            
            ed_sc = st.data_editor(pd.DataFrame(rows, columns=["時間", "担当", "準備・動き", "進行内容"]), use_container_width=True)
            
            col_d1, col_d2 = st.columns(2)
            format_sc = col_d1.radio("ダウンロード形式を選択（シナリオ）", ["PDF", "Excel"], key="sc_fmt")
            
            if col_d2.button("📥 シナリオをダウンロード"):
                if format_sc == "PDF":
                    pdf = NahaOfficialScenarioPDF({'no': m_no, 'date': m_date})
                    pdf.add_page()
                    # (描画処理は既存クラスの流用)
                    st.download_button("PDFを保存", data=bytes(pdf.output()), file_name="scenario.pdf")
                else:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        ed_sc.to_excel(writer, index=False, sheet_name='Scenario')
                    st.download_button("Excelを保存", data=output.getvalue(), file_name="scenario.xlsx")

    # --- タブ2: タイムテーブル (1月タイムテーブル見本を再現) ---
    with tab2:
        st.header("タイムスケジュール見本")
        # 見本に基づいた固定データ
        tt_data = [
            ["13:45", "14:00", "アナウンス", "司会"],
            ["14:00", "14:03", "オープニング動画", "司会"],
            ["14:03", "14:05", "開会・役割紹介", "司会"],
            ["14:05", "14:08", "開会宣言(宝の山)", "西川"],
            ["14:08", "14:12", "代表世話人挨拶", "伊集"],
            ["14:15", "14:16", "ゲスト紹介", "司会"]
        ]
        ed_tt = st.data_editor(pd.DataFrame(tt_data, columns=["開始", "終了", "イベント", "担当"]), use_container_width=True)
        
        col_t1, col_t2 = st.columns(2)
        format_tt = col_t1.radio("ダウンロード形式を選択（タイムテーブル）", ["PDF", "Excel"], key="tt_fmt")
        
        if col_t2.button("📥 タイムテーブルをダウンロード"):
            if format_tt == "Excel":
                output = io.BytesIO()
                ed_tt.to_excel(output, index=False)
                st.download_button("Excelを保存", data=output.getvalue(), file_name="timetable.xlsx")
            else:
                # PDF出力処理（省略：必要に応じて追加）
                st.info("PDF出力は準備中です。Excelをご利用ください。")

    # --- タブ3: 二次会 ---
    with tab3:
        st.header(f"二次会名簿 ({len(party)}名)")
        st.table(party[[c_n, c_c, c_p]])
