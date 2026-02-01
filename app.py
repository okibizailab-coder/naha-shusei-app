import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- PDF作成クラス（フォント設定済み） ---
class NahaDX_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')

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

# --- メイン処理 ---
st.title("那覇会場：運営DXアプリ（列名自動判別版）")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # 【改良】列名を自動で探す機能
    def find_col(target_keywords):
        for col in df.columns:
            if any(key in str(col) for key in target_keywords):
                return col
        return None

    # 各列の特定
    col_shusei = find_col(['守成', '役'])
    col_name = find_col(['氏名', '氏', '名'])
    col_intro = find_col(['紹介者', '紹介'])
    col_comp = find_col(['会社', '所属'])
    col_party = find_col(['二次会', '懇親会'])

    if not col_name:
        st.error("「氏名」列が見つかりません。エクセルの項目名を確認してください。")
    else:
        # データ抽出
        tms = df[df[col_shusei].str.contains('★', na=False)][col_name].tolist() if col_shusei else []
        guests = df[df[col_shusei].str.contains('ゲスト', na=False)] if col_shusei else pd.DataFrame()
        party_members = df[df[col_party].str.contains('参加予定', na=False)] if col_party else pd.DataFrame()

        tab1, tab2, tab3 = st.tabs(["📋 配置確認", "🖊️ 台本編集・PDF", "🍶 二次会リスト"])

        with tab1:
            st.header("1. 基本設定")
            mc_names = st.text_input("司会担当", "桜井 有里、神田橋 あずさ")
            st.write(f"読み込まれたテーブルマスター: {', '.join(tms[:12])}")

        with tab2:
            st.header("2. シナリオの手直しと保存")
            # 台本の初期データ作成
            initial_data = [
                {"時間": "14:00", "担当": "司会", "準備・動き": "照明OFF", "進行内容": "オープニング動画開始。"},
                {"時間": "14:03", "担当": "司会", "準備・動き": "照明ON", "進行内容": f"第56回例会を開会します。司会は {mc_names} です。"},
                {"時間": "14:05", "担当": "司会", "準備・動き": "起立", "進行内容": f"本日のTMは {', '.join(tms[:12])} さんです。"}
            ]
            if not guests.empty:
                for i, (_, g) in enumerate(guests.iterrows(), 1):
                    initial_data.append({"時間": "", "担当": "", "準備・動き": "", "進行内容": f"{i}) 紹介者:{g[col_intro]} / ゲスト:{g[col_comp]} {g[col_name]}様"})

            # エディタで直接編集可能
            edited_df = st.data_editor(pd.DataFrame(initial_data), num_rows="dynamic", use_container_width=True)

            if st.button("🖨️ PDFを作成してダウンロード"):
                pdf = NahaDX_PDF()
                pdf.add_page()
                pdf.draw_scenario_table(edited_df)
                st.download_button("📥 ダウンロード", data=bytes(pdf.output()), file_name="naha_scenario.pdf")

        with tab3:
            st.header(f"3. 二次会リスト ({len(party_members)}名)")
            if not party_members.empty:
                st.dataframe(party_members[[col_name, col_comp, col_party]])
            else:
                st.write("「参加予定」と記載されたデータが見つかりません。")
