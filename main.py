import streamlit as st
import requests

API_KEY = st.secrets["AIRROI_API_KEY"]
BASE_URL = "https://api.airroi.com"

st.title("API Debug Test")

# Test 1 - show that key loaded
st.write("API Key loaded:", API_KEY[:8] + "...")

# Test 2 - raw API call
response = requests.post(
    f"{BASE_URL}/listings/search/market",
    headers={"x-api-key": API_KEY},
    json={
        "market": {
            "country": "Canada",
            "region": "Nova Scotia",
            "locality": "Halifax"
        },
        "pagination": {
            "page_size": 5,
            "offset": 0
        }
    }
)

st.write("Status code:", response.status_code)
st.write("Response:", response.text)
