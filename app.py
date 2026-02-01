import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- PDF作成クラス（那覇会場専用 4列レイアウト） ---
class NahaPDF(FPDF):
    def header(self):
        # 日本語フォントの設定（フォントファイルをGitHubに入れておく必要あり）
        try:
            self.add_font('IPAexGothic', '', 'IPAexGothic.ttf')
            self.set_font('IPAexGothic', '', 12)
        except:
            self.set_font('helvetica', 'B', 12)
        self.cell(0, 10, '第56回 守成クラブ那覇会場 仕事バンバンプラザ 進行シナリオ', ln=True, align='C')
        self.ln(5)

    def scenario_table(self, data):
        # 列の幅設定 [時間, 担当, 準備・動き, 進行内容]
        widths = [15, 15, 40, 120]
        self.set_font('IPAexGothic', '', 9)
        
        for row in data:
            # 行の高さを計算（内容に合わせて自動調整）
            line_height = 6
            self.cell(widths[0], line_height, str(row[0]), border=1)
            self.cell(widths[1], line_height, str(row[1]), border=1)
            self.cell(widths[2], line_height, str(row[2]), border=1)
            # 進行内容は長くなるのでマルチセル
            self.multi_cell(widths[3], line_height, str(row[3]), border=1)

# --- アプリ画面 ---
st.title("守成クラブ那覇会場：全自動運営システム")

# 1. 名簿アップロード（お写真のリストを想定）
st.header("📋 名簿アップロード")
uploaded_file = st.file_uploader("ExcelまたはCSVをアップロード（ゲスト・会員・他会場）", type=['xlsx', 'csv'])

if uploaded_file:
    # データ読み込み（写真はExcel形式が多いのでExcelを優先）
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, sheet_name=None) # 全シート読み込み
        st.success("名簿の読み込みに成功しました！")
    except:
        st.error("読み込みに失敗しました。形式を確認してください。")

# 2. シナリオ生成用の設定
st.header("⚙️ 詳細設定")
col1, col2 = st.columns(2)
with col1:
    meeting_num = st.text_input("例会回数", "第56回")
    mc_1 = st.text_input("司会1（桜井さん等）", "桜井 有里")
with col2:
    event_date = st.date_input("開催日")
    mc_2 = st.text_input("司会2（あずささん等）", "神田橋 あずさ")

# 3. PDF作成ロジック（お写真のデータを反映）
if st.button("🖨️ 那覇会場専用シナリオ(PDF)を作成"):
    pdf = NahaPDF()
    pdf.add_page()
    
    # シナリオデータ（一部抜粋して作成）
    # IMG_1, IMG_2のデータを元に名前を自動挿入するロジックをここに書きます
    data = [
        ["14:00", "司会", "照明OFF", "オープニング動画開始。皆様スクリーンに注目をお願いします。"],
        ["14:03", "司会", "照明ON", f"仕事バンバンプラザ那覇を開会いたします。本日の司会は {mc_1} と {mc_2} です。"],
        ["14:15", "司会", "マイク準備", "本日お越しのゲストをご紹介します。"],
    ]
    
    # ゲスト紹介の自動生成例（IMG_1のリストを想定）
    # 紹介者：中島 啓吾さん、ゲスト：勇和工業 赤間 勇介さん
    data.append(["", "司会", "", "① 紹介者：中島 啓吾さん、ゲスト：勇和工業 赤間 勇介さん"])
    
    pdf.scenario_table(data)
    
    # PDFダウンロード
    pdf_output = pdf.output()
    st.download_button(label="📥 PDFをダウンロード", data=bytes(pdf_output), file_name="naha_scenario.pdf", mime="application/pdf")
