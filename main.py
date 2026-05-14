import streamlit as st
import requests
import pandas as pd

API_KEY = st.secrets["AIRROI_API_KEY"]
BASE_URL = "https://api.airroi.com"

st.title("Halifax Airbnb Market Dashboard")

# Test API connection
st.subheader("Testing API Connection...")

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
            "page_size": 10,
            "offset": 0
        }
    }
)

if response.status_code == 200:
    data = response.json()
    st.success("API connection successful!")
    st.write(f"Total listings found: {data.get('total', 'N/A')}")
    st.json(data)
else:
    st.error(f"API call failed: {response.status_code}")
    st.write(response.text)
