import streamlit as st
import pandas as pd

st.set_page_config(page_title="完整比較", page_icon="📊", layout="centered")
st.title("📊 完整比較")

if "results" not in st.session_state:
    st.warning("尚未計算任何結果，請先回到首頁輸入條件。")
    st.page_link("app.py", label="⟵ 回首頁", icon="🏠")
    st.stop()

results = st.session_state["results"]
merchant = st.session_state.get("merchant", "?")
amount = st.session_state.get("amount", 0)

st.caption(f"條件：店家 {merchant}，消費金額 NT${amount:.0f}")

df = pd.DataFrame(results)[["卡片", "店家", "回饋%", "預估回饋(元)", "說明"]]
st.dataframe(df, use_container_width=True)

st.page_link("app.py", label="⟵ 回首頁", icon="🏠")