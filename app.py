import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- PDF作成クラス ---
class NahaMasterPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')
    def header(self):
        self.set_font('IPAexGothic', '', 10)
        self.cell(0, 10, '守成クラブ那覇会場 仕事バンバンプラザ 運営資料', ln=True, align='C')
    def draw_table(self, df):
        self.set_font('IPAexGothic', '', 8.5)
        w = [12, 12, 35, 131] 
        lh = 5.0
        for _, row in df.iterrows():
            c, p = str(row['進行内容']), str(row['準備・動き'])
            lines_c = self.multi_cell(w[3], lh, c, split_only=True)
            h = max(lh, len(lines_c) * lh) + 4
            if self.get_y() + h > 275: self.add_page()
            curr_y = self.get_y()
            # 枠線
            for i in range(4): self.rect(self.get_x() + sum(w[:i]), curr_y, w[i], h)
            self.cell(w[0], h, str(row['時間']), align='C')
            self.cell(w[1], h, str(row['担当']), align='C')
            self.set_xy(self.get_x(), curr_y+2); self.multi_cell(w[2], lh, p)
            self.set_xy(self.get_x()+w[2], curr_y+2); self.multi_cell(w[3], lh, c)
            self.set_y(curr_y + h)

# --- メイン画面 ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：運営DXシステム（完全版）")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）を読み込む", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    cols = df.columns.tolist()
    
    # 列名の自動・手動設定
    def find_idx(ks):
        for i, c in enumerate(cols):
            if any(k in str(c) for k in ks): return i
        return 0

    st.sidebar.subheader("列の設定確認")
    c_s = st.sidebar.selectbox("守成役の列", cols, index=find_idx(['守成役', '役']))
    c_n = st.sidebar.selectbox("氏名の列", cols, index=find_idx(['氏名', '名前']))
    c_i = st.sidebar.selectbox("紹介者の列", cols, index=find_idx(['紹介']))
    c_c = st.sidebar.selectbox("会社名の列", cols, index=find_idx(['会社']))
    c_p = st.sidebar.selectbox("二次会の列", cols, index=find_idx(['二次会']))

    # データ抽出
    tms = df[df[c_s].str.contains('★', na=False)][c_n].tolist()
    guests = df[df[c_s].str.contains('ゲスト', na=False)]
    party = df[df[c_p].str.contains('参加予定', na=False)]
    
    # タブ作成
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ 基本設定", "📜 タイムテーブル", "🖋️ 台本編集・PDF出力", "🍶 二次会名簿"])

    with tab1:
        st.header("1. 役割の最終確認")
        mcs = st.text_input("司会担当", "桜井 有里、神田橋 あずさ")
        tk = st.text_input("タイムキーパー", "普天間 忍")
        map_p = st.text_input("マップ担当", "比嘉 太一")
        dep = st.text_input("出発進行担当", "安里 正直")
        rep = st.text_input("代表挨拶", "伊集 比佐乃")

    with tab2:
        st.header("2. 2026年1月例会 タイムテーブル")
        # 1月タイムテーブルPDFから転記
        shiki_data = [["13:45", "第1部 アナウンス開始"], ["14:00", "オープニング動画"], ["14:03", "開会・役割紹介"], ["14:08", "代表世話人挨拶"], ["14:15", "ゲスト紹介"], ["14:31", "車座商談会①"], ["15:10", "ブースPR"], ["15:39", "第2部 守成マップ動画"], ["16:18", "出発進行"]]
        st.table(pd.DataFrame(shiki_data, columns=["予定時間", "項目"]))

    with tab3:
        st.header("3. シナリオの編集と全文プレビュー")
        st.info("💡 表を編集すると、下の『全文表示プレビュー』に即座に反映されます。")
        
        # master_script.csv の読み込み
        try:
            m_df = pd.read_csv("master_script.csv")
            final_data = []
            for _, r in m_df.iterrows():
                if "[GUESTS]" in str(r['時間']):
                    for i, (_, g) in enumerate(guests.iterrows(), 1):
                        final_data.append(["", "", "", f"{i}) 紹介者:{g[c_i]}さん / ゲスト:{g[c_c]} {g[c_n]}様"])
                else:
                    text = str(r['進行内容']).replace("{mcs}", mcs).replace("{tk}", tk).replace("{tms}", "、".join(tms[:12])).replace("{len_guests}", str(len(guests))).replace("{rep}", rep).replace("{dep}", dep).replace("{mapper}", map_p)
                    final_data.append([r['時間'], r['担当'], r['準備・動き'], text])
            
            # 編集エディタ
            ed_df = st.data_editor(pd.DataFrame(final_data, columns=["時間", "担当", "準備・動き", "進行内容"]), num_rows="dynamic", use_container_width=True)
            
            st.subheader("👀 全文表示プレビュー（印刷イメージ）")
            # st.tableで全文を改行表示
            st.table(ed_df)

            if st.button("🖨️ 全ての資料をPDFで保存"):
                pdf = NahaMasterPDF()
                pdf.add_page(); pdf.draw_table(ed_df)
                if not party.empty:
                    pdf.add_page(); pdf.set_font('IPAexGothic', '', 14); pdf.cell(0, 10, '二次会参加者リスト', ln=True); pdf.ln(5)
                    # 簡易二次会リスト
                st.download_button("📥 PDFダウンロード", data=bytes(pdf.output()), file_name="naha_script_202601.pdf")
        except:
            st.error("GitHubに master_script.csv をアップロードしてください。")

    with tab4:
        st.header(f"4. 二次会名簿 ({len(party)}名)")
        if not party.empty: st.table(party[[c_n, c_c, c_p]])
