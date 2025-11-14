import streamlit as st
import pandas as pd
from pathlib import Path

# ---------- 資料讀取 ----------

@st.cache_data
def load_data():
    # 如果你把 Excel 放在 data/ 底下，就改成：
    # excel_path = Path("data/credit_card_rewards_example.xlsx")
    excel_path = Path("credit_card_rewards_example.xlsx")

    xls = pd.ExcelFile(excel_path)
    cards_df = pd.read_excel(xls, "cards")
    rules_df = pd.read_excel(xls, "reward_rules")

    return cards_df, rules_df


def find_best_rate_for_card(card_row, rules_df, merchant_name,
                            spend_channel="online", merchant_category="online_digital"):
    """
    給一張卡＋店家名稱，回傳：
    - 使用的回饋% (float)
    - 使用到的規則文字說明
    """

    card_id = card_row["card_id"]

    # 篩出這張卡的所有規則
    card_rules = rules_df[rules_df["card_id"] == card_id].copy()

    # 1. 先找「符合特定店家/通路」的規則
    #    條件：
    #    - spend_channel 相同或為 all
    #    - merchant_category 相同或為 all
    #    - merchant_keywords 有包含該店家名稱（不分大小寫）
    card_rules["merchant_keywords"] = card_rules["merchant_keywords"].fillna("")
    special_rules = card_rules[
        (card_rules["spend_channel"].isin([spend_channel, "all"])) &
        (card_rules["merchant_category"].isin([merchant_category, "all"])) &
        (card_rules["merchant_keywords"]
         .str.contains(merchant_name, case=False, na=False))
    ]

    # 如果有多條，使用 priority 最小的那一條（優先級最高）
    if not special_rules.empty:
        best_rule = special_rules.sort_values("priority").iloc[0]
        rate = float(best_rule["rate_percent"])
        desc = f"{best_rule['rule_name']}（{rate:.2f}%）"
        return rate, desc

    # 2. 找不到特定規則，就 fallback 到一般消費
    #    這裡可以用 priority 最大、或 rule_name 包含「一般消費」
    general_rule = card_rules[card_rules["rule_name"].str.contains("一般消費", na=False)]
    if not general_rule.empty:
        general_rule = general_rule.sort_values("priority", ascending=False).iloc[0]
        rate = float(general_rule["rate_percent"])
        desc = f"{general_rule['rule_name']}（一般消費 {rate:.2f}%）"
        return rate, desc

    # 3. 再不行，就用 cards 表裡的 general_rate_percent
    if "general_rate_percent" in card_row:
        rate = float(card_row["general_rate_percent"])
        desc = f"一般消費（卡片基本回饋 {rate:.2f}%）"
        return rate, desc

    # 4. 真的完全沒資料，就回 0
    return 0.0, "未找到回饋規則"


# ---------- Streamlit 介面 ----------

def main():
    st.set_page_config(page_title="信用卡回饋比較小工具", page_icon="💳")
    st.title("💳 信用卡回饋比較：YouTube / Netflix / 蝦皮")

    cards_df, rules_df = load_data()

    # 建一個 card_id → 顯示名稱 的 mapping，讓前端比較好看
    card_display_map = {
        "cathay_cube": "國泰 CUBE 卡",
        "fubon_j": "富邦 J 卡",
        "ctbc_linepay": "中信 LINE Pay 卡",
    }

    # 從 cards_df 過濾出有在 mapping 裡的卡
    cards_df = cards_df[cards_df["card_id"].isin(card_display_map.keys())].copy()
    cards_df["display_name"] = cards_df["card_id"].map(card_display_map)

    # ---- 使用者選擇 ----
    st.sidebar.header("設定條件")

    # 要比較的卡片（預設選全部三張）
    card_choices = list(cards_df["display_name"])
    selected_cards_display = st.sidebar.multiselect(
        "選擇要比較的信用卡",
        options=card_choices,
        default=card_choices
    )

    # 店家（先用你說的三個）
    merchant_options = ["YouTube", "Netflix", "蝦皮購物"]
    selected_merchant = st.sidebar.selectbox("選擇消費店家 / 類型", merchant_options)

    # 刷卡金額
    amount = st.sidebar.number_input(
        "刷卡金額 (NT$)",
        min_value=0.0,
        value=300.0,
        step=100.0
    )

    st.write(f"目前設定：在 **{selected_merchant}** 刷卡 **NT$ {amount:.0f}**")

    if not selected_cards_display:
        st.warning("請至少選擇一張信用卡來比較。")
        return

    # 將 display_name 轉回 card_id
    display_to_id = {v: k for k, v in card_display_map.items()}
    selected_card_ids = [display_to_id[name] for name in selected_cards_display]

    # ---- 計算回饋 ----
    if st.button("計算回饋比較"):
        results = []

        for card_id in selected_card_ids:
            card_row = cards_df[cards_df["card_id"] == card_id].iloc[0]

            rate, rule_desc = find_best_rate_for_card(
                card_row,
                rules_df,
                merchant_name=selected_merchant,
                spend_channel="online",
                merchant_category="online_digital",
            )

            reward_amount = amount * rate / 100.0

            results.append({
                "銀行": card_row["bank"],
                "卡片": card_row["card_name"],
                "顯示名稱": card_row["display_name"],
                "回饋%數": rate,
                "預估回饋金額 (NT$)": reward_amount,
                "套用規則": rule_desc,
            })

        if not results:
            st.warning("目前沒有找到任何回饋規則，請檢查資料。")
            return

        results_df = pd.DataFrame(results)
        # 依照回饋金額排序
        results_df = results_df.sort_values(
            by="預估回饋金額 (NT$)",
            ascending=False
        ).reset_index(drop=True)

        # 顯示最佳卡片
        best_row = results_df.iloc[0]
        st.subheader("🏆 最佳選擇")
       best_name = best_row["顯示名稱"]
best_bank = best_row["銀行"]
best_rate = best_row["回饋%數"]
best_reward = best_row["預估回饋金額 (NT$)"]
best_rule = best_row["套用規則"]

st.markdown(
    f"""
- **{best_name}**（{best_bank}）  
- 回饋：**{best_rate:.2f}%**  
- 預估可拿：**NT$ {best_reward:.0f}**  
- 套用規則：{best_rule}
"""
)


        st.subheader("📊 詳細比較")
        st.dataframe(
            results_df[["顯示名稱", "回饋%數", "預估回饋金額 (NT$)", "套用規則"]],
            hide_index=True
        )

        with st.expander("查看原始計算資料"):
            st.dataframe(results_df, hide_index=True)


if __name__ == "__main__":
    main()
