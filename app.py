import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from datetime import datetime

# --- 那覇会場専用 PDF作成クラス（自動改行・自動改ページ・複数セクション対応） ---
class NahaMasterPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')

    def header(self):
        self.set_font('IPAexGothic', '', 10)
        self.cell(0, 10, '守成クラブ那覇会場 仕事バンバンプラザ 進行資料', ln=True, align='C')

    def draw_section_title(self, title):
        self.set_font('IPAexGothic', '', 14)
        self.ln(5)
        self.cell(0, 10, title, ln=True, border='B')
        self.ln(5)

    def draw_scenario_table(self, df):
        self.set_font('IPAexGothic', '', 8.5)
        w = [12, 12, 35, 131] 
        lh = 5.0 
        for _, row in df.iterrows():
            content = str(row['進行内容'])
            prep = str(row['準備・動き'])
            lines_content = self.multi_cell(w[3], lh, content, split_only=True)
            lines_prep = self.multi_cell(w[2], lh, prep, split_only=True)
            row_h = max(lh, len(lines_content) * lh, len(lines_prep) * lh) + 4
            
            if self.get_y() + row_h > 275: self.add_page()
            
            x, y = self.get_x(), self.get_y()
            self.rect(x, y, w[0], row_h)
            self.rect(x + w[0], y, w[1], row_h)
            self.rect(x + w[0] + w[1], y, w[2], row_h)
            self.rect(x + w[0] + w[1] + w[2], y, w[3], row_h)
            
            self.cell(w[0], row_h, str(row['時間']), align='C')
            self.cell(w[1], row_h, str(row['担当']), align='C')
            self.set_xy(x + w[0] + w[1], y + 2)
            self.multi_cell(w[2], lh, prep, align='L')
            self.set_xy(x + w[0] + w[1] + w[2], y + 2)
            self.multi_cell(w[3], lh, content, align='L')
            self.set_y(y + row_h)

    def draw_party_list(self, df):
        self.set_font('IPAexGothic', '', 10)
        cols = ["No", "氏名", "会社名", "紹介者"]
        widths = [10, 40, 90, 40]
        for i, col in enumerate(cols):
            self.cell(widths[i], 10, col, border=1, align='C')
        self.ln()
        for i, (_, row) in enumerate(df.iterrows(), 1):
            if self.get_y() > 270: self.add_page()
            self.cell(widths[0], 8, str(i), border=1)
            self.cell(widths[1], 8, str(row.get('氏名','-')), border=1)
            self.cell(widths[2], 8, str(row.get('会社名','-')), border=1)
            self.cell(widths[3], 8, str(row.get('紹介者','-')), border=1)
            self.ln()

# --- 16ページ分の全セリフを網羅したマスターデータ ---
def get_full_script_data(mcs, tms, guests, rep, tm_boss, departure):
    tm_text = "、".join(tms[:12]) if tms else "（未配置）"
    script = [
        {"時間": "13:45", "担当": "司会", "準備・動き": "壇上照明OFF / 受付状況確認", "進行内容": "まもなく開会10分前です。携帯電話は音が出ないようにお願いします。お車の方は守衛所で駐車券に印鑑を。懇親会は定員に達したため受付終了しました。"},
        {"時間": "13:50", "担当": "司会", "準備・動き": "石川さんへ合図", "進行内容": "例会前の体操をします。指導者は「整体ここからの石川一久」さんです。"},
        {"時間": "14:03", "担当": "司会", "準備・動き": "壇上照明ON", "進行内容": f"ただいまより、第56回仕事バンバンプラザ那覇を開会いたします。本日の司会は {mcs} です。"},
        {"時間": "14:05", "担当": "司会", "準備・動き": "全員起立", "進行内容": f"タイムキーパーは {tm_boss} さん。テーブルマスターは {tm_text} さんです。ウェルカムドリンクは綿谷さんのBENI、お菓子は知花さんの蜂蜜飴です。"},
        {"時間": "14:05", "担当": "司会", "準備・動き": "西川さんへ", "進行内容": "開会宣言「宝の山」の朗読を西川結音子さんに、07番をお願いします。"},
        {"時間": "14:08", "担当": "代表", "準備・動き": "伊集さん登壇", "進行内容": f"代表挨拶。{rep}さん、宜しくお願い致します。"},
        {"時間": "14:15", "担当": "司会", "準備・動き": "センターマイク", "進行内容": f"本日お越しの {len(guests)} 名のゲストをご紹介します。"},
    ]
    for i, (_, g) in enumerate(guests.iterrows(), 1):
        script.append({"時間": "", "担当": "", "準備・動き": "", "進行内容": f"{i}) 紹介者:{g.get('紹介者','-')}さん / ゲスト:{g.get('会社名','-')} {g.get('氏名','-')}様"})
    
    script.extend([
        {"時間": "15:10", "担当": "比嘉", "準備・動き": "ブースPR担当", "進行内容": "ブースPRタイムです。綿谷、中島、仲本、伊敷、小林、山崎、知花、セントローレント、天野、座安、會澤、生藤、若林、谷水の順です。"},
        {"時間": "16:04", "担当": "司会", "準備・動き": "紹介者・ゲスト登壇", "進行内容": "入会予定者紹介。皆様、せーの！！めんそ〜れ〜！"},
        {"時間": "16:18", "担当": "安里", "準備・動き": "出発進行", "進行内容": f"本日の出発進行は {departure} さんです。皆様、ご起立下さい。"},
        {"時間": "16:21", "担当": "司会", "準備・動き": "終了・片付け", "進行内容": "本日はありがとうございました。名札の返却、ゴミの持ち帰り、新規入会オリエンテーションへの参加をお願いします！"}
    ])
    return script

# --- メインアプリ ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：運営DXアプリ（完全統合版）")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # 列名の自動判別
    def find_col(keys):
        for c in df.columns:
            if any(k in str(c) for k in keys): return c
        return None

    col_name = find_col(['氏名', '名前'])
    col_shusei = find_col(['守成', '役'])
    col_comp = find_col(['会社'])
    col_party = find_col(['二次会', '懇親会'])

    tms = df[df[col_shusei].str.contains('★', na=False)][col_name].tolist() if col_shusei else []
    guests = df[df[col_shusei].str.contains('ゲスト', na=False)] if col_shusei else pd.DataFrame()
    party_members = df[df[col_party].str.contains('参加予定', na=False)] if col_party else pd.DataFrame()
    rep = df[df[col_shusei].str.contains('代表', na=False)][col_name].iloc[0] if col_shusei and not df[df[col_shusei].str.contains('代表', na=False)].empty else "伊集 比佐乃"
    dep = df[df[col_shusei].str.contains('旗手', na=False)][col_name].iloc[0] if col_shusei and not df[df[col_shusei].str.contains('旗手', na=False)].empty else "安里 正直"

    # タブの作成
    tab_setup, tab_script, tab_party = st.tabs(["📋 配置・設定", "🖋️ 台本編集・PDF出力", "🍶 二次会名簿"])

    with tab_setup:
        st.header("1. 例会の基本設定")
        mc_input = st.text_input("司会担当", "桜井 有里、神田橋 あずさ")
        tm_boss = st.text_input("タイムキーパー", "普天間 忍")
        st.write(f"抽出結果: TM {len(tms)}名 / ゲスト {len(guests)}名 / 二次会 {len(party_members)}名")

    with tab_script:
        st.header("2. 台本（シナリオ）の編集")
        full_data = get_full_script_data(mc_input, tms, guests, rep, tm_boss, dep)
        edited_df = st.data_editor(pd.DataFrame(full_data), num_rows="dynamic", use_container_width=True)

        if st.button("🖨️ 全ての資料をPDFでダウンロード"):
            pdf = NahaMasterPDF()
            pdf.add_page()
            pdf.draw_section_title("進行シナリオ（全ページ）")
            pdf.draw_scenario_table(edited_df)
            
            if not party_members.empty:
                pdf.add_page()
                pdf.draw_section_title("二次会参加予定者リスト")
                pdf.draw_party_list(party_members)
                
            st.download_button("📥 PDFを保存", data=bytes(pdf.output()), file_name="naha_event_all.pdf")

    with tab_party:
        st.header("3. 二次会参加者リスト")
        if not party_members.empty:
            st.dataframe(party_members[[col_name, col_comp, col_party]], use_container_width=True)
        else:
            st.warning("「参加予定」と記載されたデータが見つかりません。名簿の『二次会』列を確認してください。")
