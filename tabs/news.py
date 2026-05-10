import streamlit as st
import pandas as pd

def render_news_tab(df_news, stichtag):
    trump_count = df_news[(df_news.index.date == stichtag) & (df_news["category"] == "Trump Post")].shape[0]
    events_count = df_news[(df_news.index.date == stichtag) & (df_news["category"] == "Newsmeldung")].shape[0]

    c1, c2 = st.columns(2)
    c1.metric("Trump Posts", trump_count)
    c2.metric("Newsmeldungen", events_count)

    df_news_filtered = df_news[df_news.index.date == stichtag]

    for _, row in df_news_filtered.iterrows():

        # Nur Trump Posts haben eine URL
        is_trump = row["category"] == "Trump Post"
        url = row.get("post_url", None) if is_trump else None

        clickable_start = (
            f'<a href="{url}" target="_blank" style="text-decoration:none; color:inherit;">'
            if url else ""
        )
        clickable_end = "</a>" if url else ""

        st.markdown(
            f"""
            {clickable_start}
            <div style="
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 12px;
                transition: all 0.15s ease-in-out;
            "
                onmouseover="this.style.backgroundColor='#f1f3f5';"
                onmouseout="this.style.backgroundColor='#f8f9fa';"
            >
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; font-weight: 600; color: #555;">
                        <span>{row['category']}</span>
                        <span style="font-size: 13px; color: #333;">{row['sentiment']:+.2f}</span>
                    </div>
                    <div style="font-size: 15px; margin-top: 4px; line-height: 1.4;">
                        {row['text']}
                    </div>
                    {("<div style='margin-top:6px; font-size:12px; color:#888;'>🔗 Truth Social öffnen</div>" 
                      if url else "")}
            </div>
            {clickable_end}
            """,
            unsafe_allow_html=True
        )
