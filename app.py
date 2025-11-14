import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- 資料讀取 ----------
@st.cache_data
def load_data():
    excel_path = Path("credit_card_rewards_example.xlsx")  # 與 app.py 放同層
    xls = pd.ExcelFile(excel_path)
    cards_df = pd.read_excel(xls, "cards")
    rules_df = pd.read_excel(xls, "reward_rules")
    return cards_df, rules_df


def find_best_rate_for_card(card_row, rules_df, merchant_name,
                            spend_channel="online", merchant_category="online_digital"):
    """
    給一張卡 + 店家名稱，回傳：
    - 最佳回饋 % (float)
    - 套用的規則名稱
    """

    card_id = card_row["card_id"]

    # 篩出這張卡所有規則
    card_rules = rules_df[rules_df["card_id"] == card_id].copy()
    card_rules["merchant_keywords"] = card_rules["merchant_keywords"].fillna("")

    # 1. 找特定通路規則
    special = card_rules[
        (card_rules["spend_channel"].isin([spend_channel, "all"])) &
        (card_rules["merchant_category"].isin([merchant_category, "all"])) &
        (card_rules["merchant_keywords"].str.contains(merchant_name, case=False))
    ]

    if not special.empty:
        rule = special.sort_values("priority").iloc[0]
        return float(rule["rate_percent"]), rule["rule_name"]

    # 2. fallback：一般消費
    general = card_rules[card_rules["rule_name"].str.contains("一般消費", na=False)]
    if not general.empty:
        rule = general.sort_values("priority", ascending=False).iloc[0]
        return float(rule["rate_percent"]), rule["rule_name"]

    # 3. fallback：卡片 general_rate
    if "general_rate_percent" in card_row:
        return float(card_row["general_rate_percent"]), "一般消費（卡片基本回饋）"

    return 0.0, "未找到回饋規則"


# ---------- Streamlit UI ----------
def main():
    st.set_page_config(page_title="信用卡回饋比較工具", page_icon="💳")
    st.title("💳 信用卡回饋比較工具")

    cards_df, rules_df = load_data()

    # 卡片顯示名稱 mapping
    card_map = {
        "cathay_cube": "國泰 CUBE 卡",
        "fubon_j": "富邦 J 卡",
        "ctbc_linepay": "中信 LINE Pay 卡"
    }

    cards_df = cards_df[cards_df["card_id"].isin(card_map.keys())].copy()
    cards_df["display_name"] = cards_df["card_id"].map(card_map)

    # ------ Sidebar ------
    st.sidebar.header("設定條件")

    selected_cards = st.sidebar.multiselect(
        "選擇要比較的信用卡",
        options=list(cards_df["display_name"]),
        default=list(cards_df["display_name"])
    )

    merchant_options = ["YouTube", "Netflix", "蝦皮購物"]
    merchant = st.sidebar.selectbox("店家", merchant_options)

    amount = st.sidebar.number_input("刷卡金額 (NT$)", min_value=0.0, value=300.0)

    if not selected_cards:
        st.warning("請至少選一張信用卡")
        return

    st.write(f"📍 消費店家：**{merchant}**，金額 **NT$ {amount:.0f}**")

    # mapping display name back to card_id
    display_to_id = {v: k for k, v in card_map.items()}
    selected_card_ids = [display_to_id[name] for name in selected_cards]

    # ------ 計算按鈕 ------
    if st.button("計算回饋"):

        results = []

        for cid in selected_card_ids:
            card_row = cards_df[cards_df["card_id"] == cid].iloc[0]

            rate, rule_used = find_best_rate_for_card(
                card_row,
                rules_df,
                merchant_name=merchant,
                spend_channel="online",
                merchant_category="online_digital"
            )

            reward = amount * rate / 100

            results.append({
                "顯示名稱": card_row["display_name"],
                "銀行": card_row["bank"],
                "回饋%數": rate,
                "預估回饋金額 (NT$)": reward,
                "套用規則": rule_used
            })

        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values("預估回饋金額 (NT$)", ascending=False).reset_index(drop=True)

        # ------ 最佳選擇 ------
        st.subheader("🏆 最佳選擇")

        best = results_df.iloc[0]

        best_name = best["顯示名稱"]
        best_bank = best["銀行"]
        best_rate = float(best["回饋%數"])
        best_reward = float(best["預估回饋金額 (NT$)"])
        best_rule = best["套用規則"]

        st.markdown(
            f"""
### ⭐ {best_name}（{best_bank}）
- 回饋：**{best_rate:.2f}%**
- 預估可拿：**NT$ {best_reward:.0f}**
- 套用規則：{best_rule}
"""
        )

        # ------ 詳細比較 ------
        st.subheader("📊 詳細比較")
        st.dataframe(
            results_df[["顯示名稱", "回饋%數", "預估回饋金額 (NT$)", "套用規則"]],
            hide_index=True
        )

        with st.expander("查看原始資料"):
            st.dataframe(results_df)


if __name__ == "__main__":
    main()
