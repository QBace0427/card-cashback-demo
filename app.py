import streamlit as st
from dataclasses import dataclass
from typing import Dict, List
import string
import pandas as pd

st.set_page_config(page_title="刷卡回饋推薦（Demo）", page_icon="💳", layout="centered")

# --------- Domain Model ---------
@dataclass
class Card:
    id: str
    name: str
    cashback_by_merchant: Dict[str, float]  # percent

LETTERS = list(string.ascii_uppercase)  # A-Z

def build_cards():
    base = 1.0
    cathay = {L: base for L in LETTERS}
    ctbc   = {L: base for L in LETTERS}

    for L in ["A","B","E","F","M","N"]:
        cathay[L] = 3.0; ctbc[L] = 1.2
    for L in ["C","D","G","H","O","P"]:
        ctbc[L] = 3.5; cathay[L] = 1.0
    for L in ["Q","R","S"]:
        cathay[L] = 2.2; ctbc[L] = 1.5
    for L in ["T","U","V"]:
        ctbc[L] = 2.4; cathay[L] = 1.6

    cards = [
        Card(id="cathay", name="國泰卡", cashback_by_merchant=cathay),
        Card(id="ctbc", name="中信卡", cashback_by_merchant=ctbc),
    ]
    return cards

CARDS: List[Card] = build_cards()

def recommend_card(merchant: str, amount: float):
    merchant = merchant.strip().upper()
    results = []
    for card in CARDS:
        pct = card.cashback_by_merchant.get(merchant, 0.0)
        cashback = round(amount * pct / 100.0, 2)
        explanation = f"{card.name} 在店家 {merchant} 的回饋為 {pct}%，預估回饋 NT${cashback}"
        results.append({
            "卡片": card.name,
            "店家": merchant,
            "回饋%": pct,
            "預估回饋(元)": cashback,
            "說明": explanation
        })
    results_sorted = sorted(results, key=lambda x: (x["預估回饋(元)"], x["回饋%"]), reverse=True)
    return results_sorted

# --------- View state ---------
if "view" not in st.session_state:
    st.session_state["view"] = "home"  # home or compare

def go_home():
    st.session_state["view"] = "home"

def go_compare():
    st.session_state["view"] = "compare"

# --------- HOME VIEW ---------
if st.session_state["view"] == "home":
    st.title("💳 刷卡回饋推薦（虛擬示範）")
    st.caption("兩張卡（國泰卡 / 中信卡）＋ 26 個店家（A–Z）。支援「打字搜尋」。")

    with st.container(border=True):
        st.subheader("輸入消費條件")

        with st.form("input_form", clear_on_submit=False):
            q = st.text_input("搜尋店家（輸入 A-Z 的任意字）", value=st.session_state.get("q",""), placeholder="例如：A、B、C...")
            st.session_state["q"] = q

            LETTERS_local = [c for c in LETTERS]
            if q:
                cand = [m for m in LETTERS_local if q.strip().upper() in m]
                if not cand:
                    st.info("沒有找到符合的店家，已顯示全部店家。")
                    cand = LETTERS_local
            else:
                cand = LETTERS_local

            # 記住上次選擇
            default_idx = 0
            last_m = st.session_state.get("merchant_last")
            if last_m in cand:
                default_idx = cand.index(last_m)

            merchant = st.selectbox("選擇店家", cand, index=default_idx, help="可打字縮小選項範圍；此 Demo 為 A–Z 虛擬店家")
            amount = st.number_input("消費金額（NT$）", min_value=1.0, value=float(st.session_state.get("amount_last", 500.0)), step=50.0)

            submit = st.form_submit_button("計算推薦")

        if submit:
            st.session_state["merchant_last"] = merchant
            st.session_state["amount_last"] = amount
            results = recommend_card(merchant, amount)
            st.session_state["results"] = results
            st.session_state["amount"] = amount
            st.session_state["merchant"] = merchant

    if "results" in st.session_state:
        results = st.session_state["results"]
        top = results[0]
        st.success(f"推薦卡片：**{top['卡片']}**，預估回饋 **NT${top['預估回饋(元)']}**（{top['回饋%']}%）", icon="✅")
        st.write(top["說明"])

        st.divider()
        if st.button("📊 前往：完整比較 ➜"):
            go_compare()

    with st.expander("關於這個 Demo"):
        st.markdown("""
- **卡片與回饋**為示範資料（A–Z 虛擬店家）：
  - 國泰卡：在 A、B、E、F、M、N 等店家較高回饋；Q、R、S 為 2.2%；其他 1.0%。
  - 中信卡：在 C、D、G、H、O、P 等店家較高回饋；T、U、V 為 2.4%；其他 1.0%。
- 演算法：將金額 × 回饋% 計算預估回饋並排序。
- 你可以再要求：
  1) 可視化編輯卡片與回饋規則；
  2) 上限、期間活動、指定支付方式等條件；
  3) 匯入/匯出 JSON 或 CSV；
  4) 美化 UI 與加入更多提示。
""")

# --------- COMPARE VIEW ---------
if st.session_state["view"] == "compare":
    st.title("📊 完整比較")
    if "results" not in st.session_state:
        st.warning("尚未計算任何結果，請先回到首頁輸入條件。")
        if st.button("⟵ 回首頁"):
            go_home()
        st.stop()

    results = st.session_state["results"]
    merchant = st.session_state.get("merchant", "?")
    amount = st.session_state.get("amount", 0)
    st.caption(f"條件：店家 {merchant}，消費金額 NT${amount:.0f}")

    df = pd.DataFrame(results)[["卡片", "店家", "回饋%", "預估回饋(元)", "說明"]]
    st.dataframe(df, use_container_width=True)

    if st.button("⟵ 回首頁"):
        go_home()
