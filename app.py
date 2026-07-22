


import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from openai import OpenAI

# -------------------------------
# PASSWORD PROTECTION
# -------------------------------

APP_PIN = st.secrets["APP_PIN"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:

    st.title("🔒 Secure Access")

    pin = st.text_input(
        "Enter PIN",
        type="password"
    )

    if st.button("Login"):

        if pin == APP_PIN:

            st.session_state.authenticated = True
            st.rerun()

        else:

            st.error("Incorrect PIN")

    st.stop()

# -------------------------------
# YOUR EXISTING APP STARTS HERE
# -------------------------------

st.set_page_config(...)
...

from openai import OpenAI

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

def optimize_query(user_query):

    prompt = f"""
You are an expert Google Search query optimizer for a social listening platform.

Convert the user's request into a short Google search query.

Rules:
- Keep only important keywords.
- Remove filler words.
- Maximum 6 keywords.
- Do NOT use quotes.
- Do NOT explain anything.
- Return ONLY the search query.

Examples

Input:
recent cases of cyber fraud or scam in karnataka people posting on social media

Output:
Karnataka cyber fraud scam

Input:
people discussing layoffs in Infosys

Output:
Infosys layoffs

Input:
negative comments about Coca Cola India

Output:
Coca Cola India complaints

User Input:
""" + user_query

    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()

# ==========================================================
# CONFIG
# ==========================================================

SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

SERPER_URL = "https://google.serper.dev/search"

# ==========================================================
# PAGE
# ==========================================================

st.set_page_config(
    page_title="Social Search",
    layout="wide"
)

st.title("🔍 Social Search Engine")

st.write("Search Facebook, Instagram, YouTube, Reddit and more using Google indexing.")

# ==========================================================
# USER INPUT
# ==========================================================

keyword = st.text_input(
    "Enter Keyword / Query",
    placeholder="Example: Karnataka cyber fraud"
)

platforms = st.multiselect(
    "Platforms",
    [
        "Facebook",
        "Instagram",
        "YouTube",
        "Reddit",
        "LinkedIn",
        "X (Twitter)",
        "News"
    ],
    default=["Facebook"]
)

# num_results = st.slider(
#     "Number of Results",
#     10,
#     100,
#     20,
#     10
# )
MAX_RESULTS = 10
# # ==========================================================
# # BUILD QUERY
# # ==========================================================

# def build_query(keyword, platforms):

#     if not platforms:
#         return keyword

#     site_map = {
#         "Facebook": "facebook.com",
#         "Instagram": "instagram.com",
#         "YouTube": "youtube.com",
#         "Reddit": "reddit.com",
#         "LinkedIn": "linkedin.com",
#         "X (Twitter)": "x.com",
#         "News": None
#     }

#     sites = []

#     for p in platforms:

#         domain = site_map.get(p)

#         if domain:
#             sites.append(f"site:{domain}")

#     if len(sites) == 0:
#         return keyword

#     if len(sites) == 1:
#         return f'{sites[0]} "{keyword}"'

#     return f'"{keyword}" ({" OR ".join(sites)})'


# ==========================================================
# SEARCH
# ==========================================================

def search_google(query):

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "q": query,
        "num": MAX_RESULTS
    }

    response = requests.post(
        SERPER_URL,
        json=payload,
        headers=headers,
        timeout=60
    )

    response.raise_for_status()
    print(response.status_code)
    print(response.text)

    return response.json()

# ==========================================================
# DOWNLOAD
# ==========================================================

def dataframe_to_excel(df):

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df.to_excel(
            writer,
            index=False
        )

    output.seek(0)

    return output

# ==========================================================
# RUN
# ==========================================================
if st.button("Search", use_container_width=True):
    
    if keyword.strip() == "":
        st.warning("Enter a keyword.")
        st.stop()

    try:

        # ---------------------------------------
        # Optimize User Query using OpenAI
        # ---------------------------------------

        with st.spinner("Optimizing search query..."):

            optimized_query = optimize_query(keyword)

        st.success(f"Optimized Query : {optimized_query}")

        # ---------------------------------------
        # Platform Mapping
        # ---------------------------------------

        site_map = {
            "Facebook": "facebook.com",
            "Instagram": "instagram.com",
            "YouTube": "youtube.com",
            "Reddit": "reddit.com",
            "LinkedIn": "linkedin.com",
            "X (Twitter)": "x.com",
            "News": None
        }

        records = []

        progress = st.progress(0)

        # ---------------------------------------
        # Search Each Platform
        # ---------------------------------------

        for i, selected_platform in enumerate(platforms):

            progress.progress((i + 1) / len(platforms))

            domain = site_map[selected_platform]

            if domain:

                query = f"site:{domain} {optimized_query}"

            else:

                query = optimized_query

            st.info(f"Searching : {query}")

            result = search_google(query)

            organic = result.get("organic", [])

            for item in organic:

                url = item.get("link", "")

                detected_platform = selected_platform

                records.append({

                    "Platform": detected_platform,

                    "Original Query": keyword,

                    "Optimized Query": optimized_query,

                    "Google Query": query,

                    "Title": item.get("title"),

                    "Snippet": item.get("snippet"),

                    "Date": item.get("date"),

                    "URL": url,

                    "Position": item.get("position")

                })

        progress.empty()

        # ---------------------------------------
        # DataFrame
        # ---------------------------------------

        df = pd.DataFrame(records)

        if df.empty:

            st.warning("No results found.")

            st.stop()

        df = df.drop_duplicates(subset=["URL"])

        st.success(f"{len(df)} unique results found.")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # ---------------------------------------
        # Download
        # ---------------------------------------

        excel = dataframe_to_excel(df)

        st.download_button(

            "📥 Download Excel",

            excel,

            file_name="search_results.xlsx",

            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        )

    except Exception as e:

        st.error(str(e))
