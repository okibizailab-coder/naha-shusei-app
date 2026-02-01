import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- PDF作成：那覇会場・完全自動レイアウト版 ---
class NahaDX_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')
    def header(self):
        self.set_font('IPAexGothic', '', 10)
        self.cell(0, 10, '守成クラブ那覇会場 仕事バンバンプラザ 進行資料', ln=True, align='C')
    def draw_table(self, df, col_widths=[12, 12, 35, 131]):
        self.set_font('IPAexGothic', '', 8.5)
        lh = 5.0
        for _, row in df.iterrows():
            c, p = str(row['進行内容']), str(row['準備・動き'])
            # 行の高さを自動計算（改行対応）
            lines_c = self.multi_cell(col_widths[3], lh, c, split_only=True)
            lines_p = self.multi_cell(col_widths[2], lh, p, split_only=True)
            row_h = max(lh, len(lines_c) * lh, len(lines_p) * lh) + 4
            # ページ跨ぎの処理
            if self.get_y() + row_h > 275: self.add_page()
            y = self.get_y()
            # 枠線の描画
            for i in range(4): self.rect(self.get_x() + sum(col_widths[:i]), y, col_widths[i], row_h)
            self.cell(col_widths[0], row_h, str(row['時間']), align='C')
            self.cell(col_widths[1], row_h, str(row['担当']), align='C')
            self.set_xy(self.get_x(), y+2); self.multi_cell(col_widths[2], lh, p)
            self.set_xy(self.get_x()+col_widths[2], y+2); self.multi_cell(col_widths[3], lh, c)
            self.set_y(y + row_h)

# --- CSVを読み込む（引用符などのゴミを掃除） ---
def load_naha_master():
    path = "master_script.csv"
    if not os.path.exists(path): return None
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.strip().strip('"') for line in f]
    return pd.read_csv(io.StringIO("\n".join(lines)))

# --- アプリ画面 ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：運営DXシステム（最終完成版）")

uploaded_file = st.sidebar.file_uploader("今回の名簿（Excel/CSV）を選択", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    cols = df.columns.tolist()
    
    # 列名の設定（KeyErrorを回避）
    st.sidebar.subheader("列の確認")
    c_s = st.sidebar.selectbox("「守成役」の列", cols, index=0)
    c_n = st.sidebar.selectbox("「氏名」の列", cols, index=0)
    c_i = st.sidebar.selectbox("「紹介者」の列", cols, index=0)
    c_c = st.sidebar.selectbox("「会社名」の列", cols, index=0)
    c_p = st.sidebar.selectbox("「二次会」の列", cols, index=0)

    # データの自動抽出
    tms = df[df[c_s].str.contains('★', na=False)][c_n].tolist()
    guests = df[df[c_s].str.contains('ゲスト', na=False)]
    party_members = df[df[c_p].str.contains('参加予定', na=False)] if c_p else pd.DataFrame()
    
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ 基本設定", "📜 次第", "🖋️ 台本編集・PDF出力", "🍶 二次会名簿"])

    with tab1:
        st.header("1. 役割の最終確認")
        mcs = st.text_input("司会担当", "桜井 有里、神田橋 あずさ")
        tk = st.text_input("タイムキーパー", "普天間 忍")
        map_p = st.text_input("マップ担当", "比嘉 太一")
        dep = st.text_input("出発進行", "安里 正直")
        rep = st.text_input("代表挨拶", "伊集 比佐乃")

    with tab2:
        st.header("2. タイムスケジュール（式次第）")
        shiki = [["14:00", "開会・オープニング動画"], ["14:08", "代表世話人挨拶"], ["14:15", "ゲスト紹介"], ["14:31", "車座商談会①"], ["15:10", "ブースPRタイム"], ["16:18", "出発進行"], ["16:22", "閉会・片付け"]]
        st.table(pd.DataFrame(shiki, columns=["予定時間", "項目"]))

    with tab3:
        st.header("3. 進行シナリオ（全16ページ）の編集")
        st.info("💡 下の表を編集すると、その下の『プレビュー』に即座に反映されます。")
        master_df = load_naha_master()
        if master_df is not None:
            # タグの置換とゲスト挿入
            final_rows = []
            for _, r in master_df.iterrows():
                if "[GUESTS]" in str(r['時間']):
                    for i, (_, g) in enumerate(guests.iterrows(), 1):
                        final_rows.append(["", "", "", f"{i}) 紹介者:{g[c_i]} / ゲスト:{g[c_c]} {g[c_n]}様"])
                else:
                    txt = str(r['進行内容']).replace("{mcs}", mcs).replace("{tk}", tk).replace("{tms}", "、".join(tms[:12])).replace("{rep}", rep).replace("{dep}", dep).replace("{mapper}", map_p).replace("{len_guests}", str(len(guests)))
                    final_rows.append([r['時間'], r['担当'], r['準備・動き'], txt])
            
            # エディタ（編集用）
            ed_df = st.data_editor(pd.DataFrame(final_rows, columns=["時間", "担当", "準備・動き", "進行内容"]), num_rows="dynamic", use_container_width=True)
            
            st.subheader("👀 全文表示プレビュー（印刷イメージ）")
            st.table(ed_df) # 全文が自動改行されて表示されます

            if st.button("🖨️ PDFを作成して保存"):
                pdf = NahaDX_PDF()
                pdf.add_page(); pdf.draw_table(ed_df)
                st.download_button("📥 ダウンロード", data=bytes(pdf.output()), file_name="naha_perfect_script.pdf")
        else:
            st.error("GitHubに 'master_script.csv' が見つかりません。")

    with tab4:
        st.header(f"4. 二次会参加者リスト ({len(party_members)}名)")
        if not party_members.empty:
            st.table(party_members[[c_n, c_c, c_p]])
