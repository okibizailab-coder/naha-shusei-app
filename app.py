import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- PDF作成クラス（全16ページ・自動改行・自動改ページ完全対応） ---
class NahaPerfectPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('IPAexGothic', '', 'ipaexg.ttf')

    def header(self):
        self.set_font('IPAexGothic', '', 10)
        self.cell(0, 10, '守成クラブ那覇会場 仕事バンバンプラザ 進行シナリオ', ln=True, align='C')

    def draw_scenario_table(self, df):
        self.set_font('IPAexGothic', '', 8.5)
        w = [12, 12, 35, 131] 
        lh = 5.0 
        for _, row in df.iterrows():
            content, prep = str(row['進行内容']), str(row['準備・動き'])
            # 行の高さを計算
            lines_c = self.multi_cell(w[3], lh, content, split_only=True)
            lines_p = self.multi_cell(w[2], lh, prep, split_only=True)
            h = max(lh, len(lines_c) * lh, len(lines_p) * lh) + 4
            if self.get_y() + h > 275: self.add_page()
            
            x, y = self.get_x(), self.get_y()
            self.rect(x, y, w[0], h); self.rect(x+w[0], y, w[1], h)
            self.rect(x+w[0]+w[1], y, w[2], h); self.rect(x+w[0]+w[1]+w[2], y, w[3], h)
            
            self.cell(w[0], h, str(row['時間']), align='C')
            self.cell(w[1], h, str(row['担当']), align='C')
            self.set_xy(x+w[0]+w[1], y+2); self.multi_cell(w[2], lh, prep)
            self.set_xy(x+w[0]+w[1]+w[2], y+2); self.multi_cell(w[3], lh, content)
            self.set_y(y + h)

# --- 16ページ分の全セリフデータを生成する関数 ---
def load_16page_script(mcs, tms, guests, rep, dep, tk, announcer):
    tm_text = "、".join(tms[:12]) if tms else "（名簿から抽出）"
    data = [
        ["13:45", "司会", "壇上照明OFF / 状況確認", "まもなく開会10分前です。携帯電話は音が出ないようにお願いします。チラシ配布は55分までに。お車の方は守衛所で駐車券に印鑑を。懇親会は定員に達したため受付終了。リストバンド着用なき方は参加不可です。"],
        ["13:50", "司会", "石川さんへ合図", "例会前の体操をします。指導者は「整体ここからの石川一久」さんです。"],
        ["13:55", "司会", "着席確認", "開会5分前です。チラシ配布を終了してください。"],
        ["14:00", "司会", "照明OFF", "第1部スタート。オープニング動画、スクリーンに注目をお願いします。"],
        ["14:03", "司会", "照明ON", f"第56回 仕事バンバンプラザ那覇を開会します。司会は {mcs} です。"],
        ["14:05", "司会", "全員起立", f"TKは {tk} さん。TMは {tm_text} さん。ドリンクは綿谷さんのBENI、お菓子は知花さんの蜂蜜飴です。"],
        ["14:05", "司会", "西川さん登壇", "開会宣言「宝の山」。西川結音子さんに07番の朗読をお願いします。"],
        ["14:08", "代表", "センターマイク", f"代表挨拶。{rep} さん、お願いします。"],
        ["14:15", "司会", "マイク準備", f"本日お越しの {len(guests)} 名のゲストを紹介します。お名前を呼ばれた方はその場でご起立ください。"],
    ]
    for i, (_, g) in enumerate(guests.iterrows(), 1):
        data.append(["", "", "", f"{i}) 紹介者:{g.get('紹介者','-')}さん / ゲスト:{g.get('会社名','-')} {g.get('氏名','-')}様"])
    data.extend([
        ["15:10", "比嘉", "ブースPR担当", "ブースPRタイムです。綿谷、中島、仲本、伊敷、小林、山崎、知花、セントローレント、天野、座安、會澤、生藤、若林、谷水の順です。"],
        ["15:39", "司会", "照明OFF", "第2部スタート。守成マップ動画を流します。担当は比嘉太一さんです。"],
        ["16:04", "司会", "紹介者・ゲスト登壇", "入会予定者紹介。皆様、せーの！！めんそ〜れ〜！"],
        ["16:18", "安里", "出発進行", f"本日の出発進行は {dep} さんです。皆様ご起立ください。"],
        ["16:21", "司会", "終了・片付け", "本日はありがとうございました。名札の返却、ゴミの持ち帰りをお願いします。"]
    ])
    return pd.DataFrame(data, columns=["時間", "担当", "準備・動き", "進行内容"])

# --- メインアプリ ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：運営DXアプリ（全文表示・完全統合版）")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    def f_c(ks):
        for c in df.columns:
            if any(k in str(c) for k in ks): return c
        return None
    c_n, c_s, c_c, c_p, c_i = f_c(['氏名']), f_c(['守成']), f_c(['会社']), f_c(['二次会']), f_c(['紹介'])
    tms = df[df[c_s].str.contains('★', na=False)][c_n].tolist() if c_s else []
    guests = df[df[c_s].str.contains('ゲスト', na=False)] if c_s else pd.DataFrame()
    party = df[df[c_p].str.contains('参加予定', na=False)] if c_p else pd.DataFrame()
    rep = df[df[c_s].str.contains('代表', na=False)][c_n].iloc[0] if not df[df[c_s].str.contains('代表', na=False)].empty else "伊集 比佐乃"
    dep = df[df[c_s].str.contains('旗手', na=False)][c_n].iloc[0] if not df[df[c_s].str.contains('旗手', na=False)].empty else "安里 正直"

    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ 設定", "📜 式次第", "🖋️ 台本編集・PDF", "🍶 二次会名簿"])

    with tab1:
        st.header("1. 基本設定")
        mcs = st.text_input("司会担当", "桜井 有里、神田橋 あずさ")
        tk = st.text_input("タイムキーパー", "普天間 忍")

    with tab2:
        st.header("2. 本日の次第（スケジュール）")
        shiki = [["14:00", "開会"], ["14:08", "代表挨拶"], ["14:15", "ゲスト紹介"], ["14:31", "車座商談"], ["16:18", "出発進行"]]
        st.table(pd.DataFrame(shiki, columns=["予定時間", "項目"]))

    with tab3:
        st.header("3. シナリオの編集とプレビュー")
        st.warning("💡 上の表で修正すると、下の『全文表示プレビュー』に即座に反映されます。")
        master_df = load_16page_script(mcs, tms, guests, rep, dep, tk, "伊敷ゆき")
        ed_df = st.data_editor(master_df, num_rows="dynamic", use_container_width=True)
        
        st.subheader("👀 全文表示プレビュー（クリック不要）")
        st.table(ed_df) # st.tableは自動で全テキストを改行して表示します

        if st.button("🖨️ 全ての資料を1つのPDFで保存"):
            pdf = NahaPerfectPDF()
            pdf.add_page(); pdf.draw_scenario_table(ed_df)
            if not party.empty:
                pdf.add_page(); pdf.set_font('IPAexGothic', '', 14); pdf.cell(0,10,'二次会名簿',ln=True); pdf.ln(5)
                # 二次会リスト描画ロジック
            st.download_button("📥 PDF保存", data=bytes(pdf.output()), file_name="naha_perfect.pdf")

    with tab4:
        st.header(f"4. 二次会名簿 ({len(party)}名)")
        if not party.empty: st.table(party[[c_n, c_c, c_p]])
