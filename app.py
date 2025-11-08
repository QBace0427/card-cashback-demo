
import streamlit as st
from dataclasses import dataclass
from typing import Dict, List

st.set_page_config(page_title="刷卡回饋推薦（Demo）", page_icon="💳", layout="centered")

# --------- Domain Model ---------
@dataclass
class Card:
    id: str
    name: str
    cashback_by_merchant: Dict[str, float]  # percent, e.g., 1.5 for 1.5%

CARDS: List[Card] = [
    Card(id="cathay", name="國泰卡", cashback_by_merchant={
        "A": 3.0,
        "B": 2.5,
        "C": 1.0,
        "D": 0.5,
        "E": 1.0,
        "F": 1.0
    }),
    Card(id="ctbc", name="中信卡", cashback_by_merchant={
        "A": 1.0,
        "B": 1.2,
        "C": 3.5,
        "D": 2.8,
        "E": 1.0,
        "F": 1.5
    }),
]

MERCHANTS = ["A", "B", "C", "D", "E", "F"]

def recommend_card(merchant: str, amount: float):
    merchant = merchant.strip().upper()
    results = []
    for card in CARDS:
        pct = card.cashback_by_merchant.get(merchant, 0.0)
        cashback = round(amount * pct / 100.0, 2)
        explanation = f"{card.name} 在店家 {merchant} 的回饋為 {pct}%，預估回饋 NT${cashback}"
        results.append({
            "card_id": card.id,
            "卡片": card.name,
            "店家": merchant,
            "回饋%": pct,
            "預估回饋(元)": cashback,
            "說明": explanation
        })
    results_sorted = sorted(results, key=lambda x: (x["預估回饋(元)"], x["回饋%"]), reverse=True)
    return results_sorted

# --------- UI ---------
st.title("💳 刷卡回饋推薦（虛擬示範）")
st.caption("兩張卡（國泰卡 / 中信卡）＋ 六個店家（A–F）的最小可行示範。")

with st.container(border=True):
    st.subheader("輸入消費條件")
    c1, c2 = st.columns(2)
    with c1:
        merchant = st.selectbox("選擇店家", MERCHANTS, index=0, help="此 Demo 僅提供 A–F 六個店家")
    with c2:
        amount = st.number_input("消費金額（NT$）", min_value=1.0, value=500.0, step=50.0)

    run = st.button("計算推薦", type="primary")

if run:
    results = recommend_card(merchant, amount)
    top = results[0]

    st.success(f"推薦卡片：**{top['卡片']}**，預估回饋 **NT${top['預估回饋(元)']}**（{top['回饋%']}%）", icon="✅")
    st.write(top["說明"])

    st.divider()
    st.subheader("完整比較")
    import pandas as pd
    df = pd.DataFrame(results)[["卡片", "店家", "回饋%", "預估回饋(元)", "說明"]]
    st.dataframe(df, use_container_width=True)

with st.expander("關於這個 Demo"):
    st.markdown("""
- **卡片與回饋**為寫死的示範資料：
  - 國泰卡：A=3.0%、B=2.5%、C=1.0%、D=0.5%、E=1.0%、F=1.0
  - 中信卡：A=1.0%、B=1.2%、C=3.5%、D=2.8%、E=1.0%、F=1.5
- 演算法：將金額 × 回饋% 計算預估回饋並排序。
- 你可以後續要求：
  1) 新增可視化編輯卡片與回饋規則；
  2) 支援上限、期間活動等進階條件；
  3) 上傳 CSV/JSON 管理規則；
  4) 部署為共用的 Web 服務。
""")
