import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- 那覇会場専用 PDF作成クラス（自動改行・複数セクション対応） ---
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

    def draw_scenario_table(self, df, col_widths=[12, 12, 35, 131]):
        self.set_font('IPAexGothic', '', 8.5)
        lh = 5.0 
        for _, row in df.iterrows():
            content = str(row.iloc[3])
            prep = str(row.iloc[2])
            lines_c = self.multi_cell(col_widths[3], lh, content, split_only=True)
            lines_p = self.multi_cell(col_widths[2], lh, prep, split_only=True)
            row_h = max(lh, len(lines_c) * lh, len(lines_p) * lh) + 4
            if self.get_y() + row_h > 275: self.add_page()
            x, y = self.get_x(), self.get_y()
            self.rect(x, y, col_widths[0], row_h); self.rect(x+col_widths[0], y, col_widths[1], row_h)
            self.rect(x+col_widths[0]+col_widths[1], y, col_widths[2], row_h)
            self.rect(x+col_widths[0]+col_widths[1]+col_widths[2], y, col_widths[3], row_h)
            self.cell(col_widths[0], row_h, str(row.iloc[0]), align='C')
            self.cell(col_widths[1], row_h, str(row.iloc[1]), align='C')
            self.set_xy(x+col_widths[0]+col_widths[1], y+2); self.multi_cell(col_widths[2], lh, prep)
            self.set_xy(x+col_widths[0]+col_widths[1]+col_widths[2], y+2); self.multi_cell(col_widths[3], lh, content)
            self.set_y(y + row_h)

# --- 全セリフデータの定義 ---
def get_master_data(mcs, tms, guests, rep, tm_boss, dep):
    tm_text = "、".join(tms[:12]) if tms else "（未配置）"
    data = [
        ["13:45", "司会", "照明OFF/受付確認", "まもなく開会10分前です。携帯電話は音が出ないよう設定を。駐車券への捺印、水の受け取りをお願いします。懇親会は定員に達したため受付終了。リストバンド着用を確認ください。"],
        ["13:50", "司会", "石川さんへ合図", "例会前の体操をします。指導者は整体ここからの石川一久さんです。"],
        ["14:03", "司会", "照明ON", f"第56回仕事バンバンプラザ那覇を開会します。本日の司会は {mcs} です。"],
        ["14:05", "司会", "全員起立", f"タイムキーパーは {tm_boss} さん。TMは {tm_text} さん。ドリンクは綿谷さんのBENI、お菓子は知花さんの蜂蜜飴です。"],
        ["14:05", "司会", "西川さん登壇", "開会宣言「宝の山」。西川結音子さんに07番の朗読をお願いします。"],
        ["14:08", "代表", "センターマイク", f"代表挨拶。{rep} さん、宜しくお願い致します。"],
        ["14:15", "司会", "ゲスト12名紹介", f"本日お越しの {len(guests)} 名のゲストをご紹介します。名前を呼ばれた方はその場で起立ください。"],
    ]
    for i, (_, g) in enumerate(guests.iterrows(), 1):
        data.append(["", "", "", f"{i})紹介者:{g.get('紹介者','-')} / ゲスト:{g.get('会社名','-')} {g.get('氏名','-')}様"])
    data.extend([
        ["15:10", "比嘉", "ブースPR担当", "ブースPRタイムです。お一人30秒。綿谷、中島、仲本、伊敷、小林、山崎、知花、セントローレント、天野、座安、會澤、生藤、若林、谷水の順です。"],
        ["16:04", "司会", "「めんそ〜れ〜！」", "入会予定者紹介。皆様、せーの！！めんそ〜れ〜！"],
        ["16:18", "安里", "出発進行", f"出発進行は {dep} さんです。全員ご起立ください。"],
        ["16:21", "司会", "終了アナウンス", "本日はありがとうございました。名札の返却、ゴミの持ち帰りをお願いします。"]
    ])
    return pd.DataFrame(data, columns=["時間", "担当", "準備・動き", "進行内容"])

# --- アプリメイン ---
st.set_page_config(page_title="守成那覇 運営DX", layout="wide")
st.title("那覇会場：運営DXアプリ（完全統合・視認性改良版）")

uploaded_file = st.sidebar.file_uploader("名簿（Excel/CSV）をアップロード", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # データ抽出（列名自動判別）
    def f_c(ks):
        for c in df.columns:
            if any(k in str(c) for k in ks): return c
        return None

    c_n, c_s, c_c, c_p = f_c(['氏名']), f_c(['守成']), f_c(['会社']), f_c(['二次会'])
    tms = df[df[c_s].str.contains('★', na=False)][c_n].tolist() if c_s else []
    guests = df[df[c_s].str.contains('ゲスト', na=False)] if c_s else pd.DataFrame()
    party = df[df[c_p].str.contains('参加予定', na=False)] if c_p else pd.DataFrame()
    rep = df[df[c_s].str.contains('代表', na=False)][c_n].iloc[0] if not df[df[c_s].str.contains('代表', na=False)].empty else "伊集 比佐乃"
    dep = df[df[c_s].str.contains('旗手', na=False)][c_n].iloc[0] if not df[df[c_s].str.contains('旗手', na=False)].empty else "安里 正直"

    # 四つのタブを配置
    tab_conf, tab_shiki, tab_script, tab_party = st.tabs(["⚙️ 配置・設定", "📜 式次第", "🖋️ 台本編集・PDF出力", "🍶 二次会名簿"])

    with tab_conf:
        st.header("1. 基本設定")
        mcs = st.text_input("司会担当", "桜井 有里、神田橋 あずさ")
        tm_b = st.text_input("タイムキーパー", "普天間 忍")

    with tab_shiki:
        st.header("2. 式次第（タイムスケジュール）")
        shiki_data = [["14:00", "開会・オープニング動画"], ["14:05", "開会宣言・代表挨拶"], ["14:15", "ゲスト紹介"], ["14:31", "車座商談会①"], ["15:10", "ブースPR"], ["15:39", "第2部開始"], ["16:18", "出発進行"]]
        st.table(pd.DataFrame(shiki_data, columns=["予定時間", "項目"]))

    with tab_script:
        st.header("3. シナリオ編集")
        st.info("💡 下の表を編集すると、その下の『ライブプレビュー』に即座に反映されます。")
        master_df = get_master_data(mcs, tms, guests, rep, tm_b, dep)
        
        # 編集用エディタ（幅を広げて見やすく）
        ed_df = st.data_editor(master_df, num_rows="dynamic", use_container_width=True,
                               column_config={"進行内容": st.column_config.TextColumn(width="large")})
        
        st.header("👀 ライブプレビュー（全文表示）")
        st.table(ed_df) # st.tableは自動で改行され、全文が表示されます

        if st.button("🖨️ 全ての資料をPDFでダウンロード"):
            pdf = NahaMasterPDF()
            pdf.add_page(); pdf.draw_section_title("進行シナリオ"); pdf.draw_scenario_table(ed_df)
            if not party.empty:
                pdf.add_page(); pdf.draw_section_title("二次会参加者リスト"); pdf.draw_party_list(party)
            st.download_button("📥 PDF保存", data=bytes(pdf.output()), file_name="naha_all_docs.pdf")

    with tab_party:
        st.header(f"4. 二次会名簿 ({len(party)}名)")
        if not party.empty: st.table(party[[c_n, c_c, c_p]])
        else: st.warning("「参加予定」のデータがありません。")
