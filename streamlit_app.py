import streamlit as st
from notion_client import Client
import google.generativeai as genai
import json

# 1. Load Secrets from Streamlit Cloud Settings
NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATABASE_ID = st.secrets["DATABASE_ID"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# 2. Setup Clients
notion = Client(auth=NOTION_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 3. Simple UI
st.title("Threads & Link Curator")
st.write("Paste a link to automatically categorize it into your Notion.")

url_input = st.text_input("URL to save:", placeholder="https://www.threads.net/...")

if st.button("Analyze & Save"):
    if url_input:
        with st.spinner("Gemini is analyzing the link..."):
            prompt = f"""
            Analyze this URL: {url_input}
            1. Determine Category: Foodie, Travel, or Growth.
            2. Extract Location: (e.g., Mong Kok, TST, Tokyo, Denmark). If none, put "N/A".
            3. Create a 1-sentence summary.
            4. Create a concise title.
            
            Return ONLY a JSON object:
            {{"title": "Title", "category": "Category", "location": "Location", "summary": "Summary"}}
            """
            
            try:
                response = model.generate_content(prompt)
                # Clean up the AI response
                raw_json = response.text.replace('```json', '').replace('```', '').strip()
                res_data = json.loads(raw_json)

                # 4. Push to your Notion Table (Matches your screenshot columns)
                notion.pages.create(
                    parent={"database_id": DATABASE_ID},
                    properties={
                        "Post/Article": {"title": [{"text": {"content": res_data['title']}}]},
                        "Source Link": {"url": url_input},
                        "Category": {"select": {"name": res_data['category']}},
                        "Location": {"select": {"name": res_data['location']}},
                        "AI Summary": {"rich_text": [{"text": {"content": res_data['summary']}}]}
                    }
                )
                st.success(f"Saved to Notion under {res_data['category']}!")
                st.balloons()
            except Exception as e:
                st.error(f"Something went wrong: {e}")
    else:
        st.warning("Please paste a URL first!")
