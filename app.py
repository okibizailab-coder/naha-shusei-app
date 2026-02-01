import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- 1. PDF作成：原本(新)シナリオ2026年1月 を忠実に再現 ---
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
        # 左上：第○回 守成クラブ 那覇会場
        self.cell(30, 8, self.m_info['no'], ln=0)
        self.cell(30, 8, '守成クラブ', ln=0)
        self.cell(40, 8, '那覇会場', ln=1)
        # 右上：日付
        self.set_y(10)
        self.cell(0, 8, self.m_info['date'], ln=True, align='R')
        self.ln(5)
        # 表のヘッダー：グレー背景
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
            # 進行内容の長さに合わせて行の高さを計算
            lines_c = self.multi_cell(w[3], lh, c, split_only=True)
            h = max(lh, len(lines_c) * lh) + 4
            # ページ跨ぎ処理
            if self.get_y() + h > 275: self.add_page()
            curr_x, curr_y = self.get_x(), self.get_y()
            # セル枠の描画
            for i in range(4): self.rect(curr_x + sum(w[:i]), curr_y, w[i], h)
            self.cell(w[0], h, str(row['時間']), align='C')
            self.cell(w[1], h, str(row['担当']), align='C')
            self.set_xy(curr_x + w[0] + w[1], curr_y + 2); self.multi_cell(w[2], lh, p)
            self.set_xy(curr_x + w[0] + w[1] + w[2], curr_y + 2); self.multi_cell(w[3], lh, c)
            self.set_y(curr_y + h)

# --- CSV読み込み補助（文字コードエラー対策） ---
def load_naha_csv(path):
    if not os.path.exists(path): return None
    for enc in ['utf-8', 'shift_jis', 'cp932']:
        try:
            with open(path, 'r', encoding=enc) as f:
                lines = [line.strip().strip('"') for line in f]
            return pd.read_csv(io.StringIO("\n".join(lines)))
        except: continue
    return None

# --- アプリ画面設定 ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：運営資料作成システム（完全統合版）")

# サイドバー：システム診断
st.sidebar.header("🔍 システム診断")
status = True
for label, fname in {"台本ひな形": "master_script.csv", "日本語フォント": "ipaexg.ttf"}.items():
    if os.path.exists(fname): st.sidebar.success(f"✅ {label}: OK")
    else: 
        st.sidebar.error(f"❌ {label}: 未検出")
        status = False

uploaded_file = st.sidebar.file_uploader("今回の名簿（Excel/CSV）を選択", type=['xlsx', 'csv'])

if uploaded_file:
    df_m = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    cols = df_m.columns.tolist()
    
    st.sidebar.subheader("基本情報・列設定")
    m_no = st.sidebar.text_input("例会回数", "第56回")
    m_date = st.sidebar.text_input("開催日", "2026年1月20日 火曜日")
    
    def gc(ks): return next((c for c in cols if any(k in str(c) for k in ks)), cols[0])
    c_s, c_n, c_i, c_c, c_p = gc(['守成']), gc(['氏名']), gc(['紹介']), gc(['会社']), gc(['二次会'])
    
    # データ抽出
    tms = df_m[df_m[c_s].str.contains('★', na=False)][c_n].tolist()
    guests = df_m[df_m[c_s].str.contains('ゲスト', na=False)]
    party = df_m[df_m[c_p].str.contains('参加予定', na=False)] if c_p else pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["🖋️ 台本編集・出力", "📜 タイムテーブル", "🍶 二次会名簿"])

    with tab1:
        st.header("進行シナリオ（全16ページ分）")
        m_df = load_naha_csv("master_script.csv")
        if m_df is not None:
            rows = []
            for _, r in m_df.iterrows():
                if "[GUESTS]" in str(r['時間']):
                    for i, (_, g) in enumerate(guests.iterrows(), 1):
                        rows.append(["", "", "", f"{i}) 紹介者:{g[c_i]}さん / ゲスト:{g[c_c]} {g[c_n]}様"])
                else:
                    # 変数置換（原本16ページをすべて自動反映）
                    txt = str(r['進行内容']).replace("{mcs}", "桜井有里、神田橋あずさ").replace("{tk}", "普天間 忍").replace("{tms}", "、".join(tms[:12])).replace("{rep}", "伊集比佐乃").replace("{dep}", "安里正直").replace("{len_guests}", str(len(guests)))
                    rows.append([r['時間'], r['担当'], r['準備・動き'], txt])
            
            # 編集・プレビュー
            ed_sc = st.data_editor(pd.DataFrame(rows, columns=["時間", "担当", "準備・動き", "進行内容"]), use_container_width=True, key="sc_ed")
            st.subheader("👀 全文プレビュー（印刷イメージ）")
            st.table(ed_sc) # クリック不要で全文表示

            # 保存機能（PDF/Excel）
            st.write("---")
            c_d1, c_d2 = st.columns(2)
            fmt = c_d1.selectbox("保存形式を選択", ["PDF", "Excel"])
            if fmt == "PDF":
                if status: # フォントがある場合のみ
                    pdf = NahaOfficialPDF({'no': m_no, 'date': m_date})
                    pdf.add_page(); pdf.draw_rows(ed_sc)
                    c_d2.download_button("📥 シナリオPDFを保存", data=bytes(pdf.output()), file_name=f"scenario_{m_no}.pdf")
                else: c_d2.warning("フォントが見当たらないためPDF作成不可")
            else:
                out = io.BytesIO()
                ed_sc.to_excel(out, index=False)
                c_d2.download_button("📥 シナリオExcelを保存", data=out.getvalue(), file_name=f"scenario_{m_no}.xlsx")
        else:
            st.error("master_script.csv が正しく読み込めません。診断を確認してください。")

    with tab2:
        st.header("タイムスケジュール（次第）")
        # 1月タイムテーブル見本のデータ 
        tt_data = [["13:45", "14:00", "開会前アナウンス", "司会"], ["14:00", "14:03", "オープニング動画", "司会"], ["14:03", "14:08", "代表挨拶", "伊集"], ["14:15", "14:16", "ゲスト紹介", "司会"], ["14:31", "14:49", "車座商談会①", "TM"], ["15:10", "15:19", "ブース出展PR", "比嘉"], ["16:18", "16:21", "出発進行", "安里"]]
        ed_tt = st.data_editor(pd.DataFrame(tt_data, columns=["開始", "終了", "内容", "担当"]), use_container_width=True)
        
        out_tt = io.BytesIO()
        ed_tt.to_excel(out_tt, index=False)
        st.download_button("📥 タイムテーブルExcel保存", data=out_tt.getvalue(), file_name="timetable.xlsx")

    with tab3:
        st.header(f"二次会名簿 ({len(party)}名)")
        if not party.empty:
            st.table(party[[c_n, c_c, c_p]])
            out_p = io.BytesIO()
            party[[c_n, c_c, c_p]].to_excel(out_p, index=False)
            st.download_button("📥 二次会名簿Excel保存", data=out_p.getvalue(), file_name="party_list.xlsx")
