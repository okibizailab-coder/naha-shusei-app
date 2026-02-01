import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- 那覇会場専用 PDF作成クラス ---
class NahaPDF(FPDF):
    def header(self):
        # GitHubにアップロードしたフォントを読み込む
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')
        self.set_font('IPAexGothic', '', 14)
        self.cell(0, 10, '守成クラブ那覇会場 仕事バンバンプラザ 進行シナリオ', ln=True, align='C')
        self.ln(5)

    def draw_table_row(self, time, role, prep, content):
        self.set_font('IPAexGothic', '', 9)
        # 各列の幅 [時間, 担当, 準備, 内容]
        w = [15, 15, 40, 120]
        lh = 7 # 行の高さ
        
        # 現在のY座標を記録
        start_y = self.get_y()
        # 一番長いテキスト（進行内容）の高さを計算
        self.set_xy(self.x + sum(w[:3]), start_y)
        self.multi_cell(w[3], lh, content, border=1)
        end_y = self.get_y()
        
        # 他の短い列を、一番長い列の高さに合わせて描画
        h = end_y - start_y
        self.set_xy(self.x - sum(w), start_y)
        self.cell(w[0], h, time, border=1)
        self.cell(w[1], h, role, border=1)
        self.cell(w[2], h, prep, border=1)
        self.set_y(end_y)

st.title("守成クラブ那覇：全自動シナリオ生成システム")

# 1. 名簿アップロード
st.header("📋 名簿の取り込み")
uploaded_file = st.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.success(f"{len(df)} 名のデータを読み込みました")

    # 2. 自動抽出ロジック（お写真の列名に対応）
    # 守成役に「★」がある人をTMとして抽出
    tm_members = df[df['守成役・バッジ'].str.contains('★', na=False)]['氏名'].tolist()
    # 守成役が「ゲスト」の人を抽出
    guests = df[df['守成役・バッジ'].str.contains('ゲスト', na=False)]

    # 3. PDF作成
    if st.button("🖨️ 那覇会場専用シナリオ(PDF)を作成"):
        pdf = NahaPDF()
        pdf.add_page()
        
        # --- シナリオ構成（一部抜粋） ---
        rows = [
            ["14:00", "司会", "照明OFF", "オープニング動画開始。"],
            ["14:03", "司会", "照明ON", "ただいまより、第56回仕事バンバンプラザ那覇を開会いたします。"],
        ]
        
        # テーブルマスター紹介の自動生成
        tm_text = "本日のテーブルマスターは、" + "、".join(tm_members[:12]) + "さんです。ご起立ください。"
        rows.append(["14:05", "司会", "全員起立を確認", tm_text])
        
        # ゲスト紹介の自動生成
        rows.append(["14:15", "司会", "センターマイク", f"本日お越しの{len(guests)}名のゲストをご紹介します。"])
        for i, (_, g) in enumerate(guests.iterrows()):
            g_text = f"{i+1}) 紹介者：{g['紹介者']}さん、ゲスト：{g['会社名']} {g['氏名']}様"
            rows.append(["", "", "", g_text])

        # PDFに書き込み
        for r in rows:
            pdf.draw_table_row(r[0], r[1], r[2], r[3])
            
        pdf_out = pdf.output()
        st.download_button("📥 PDFを保存する", data=bytes(pdf_out), file_name="naha_scenario.pdf")
