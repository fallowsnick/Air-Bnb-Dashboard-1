import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

API_KEY = st.secrets["AIRROI_API_KEY"]
BASE_URL = "https://api.airroi.com"

st.set_page_config(
    page_title="Halifax Airbnb Dashboard",
    page_icon="🏠",
    layout="wide"
)

# ── Sidebar Filters ──────────────────────────────────────────────
st.sidebar.title("🔍 Filters")

room_type = st.sidebar.selectbox(
    "Property Type",
    ["All", "entire_home", "private_room", "shared_room"]
)

bedrooms = st.sidebar.slider("Min Bedrooms", 0, 6, 0)
min_reviews = st.sidebar.slider("Min Reviews", 0, 100, 0)

sort_by = st.sidebar.selectbox(
    "Sort By",
    ["ttm_revenue", "ttm_occupancy", "ttm_avg_rate", "num_reviews", "rating_overall"]
)

sort_dir = st.sidebar.radio("Sort Direction", ["desc", "asc"])
page_size = st.sidebar.slider("Listings to show", 10, 100, 25)

st.sidebar.markdown("---")
st.sidebar.caption("⚠️ ttm = trailing 12 months | l90d = last 90 days")

# ── Build Filter Object ──────────────────────────────────────────
filters = {}

# Only show active listings by default
filters["ttm_revenue"] = {"gt": 0}

if room_type != "All":
    filters["room_type"] = {"eq": room_type}

if bedrooms > 0:
    filters["bedrooms"] = {"gte": bedrooms}

if min_reviews > 0:
    filters["num_reviews"] = {"gte": min_reviews}

# ── Fetch Listings ───────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_listings(filters_key, sort_by, sort_dir, page_size, filters_json):
    response = requests.post(
        f"{BASE_URL}/listings/search/market",
        headers={"x-api-key": API_KEY},
        json={
            "market": {
                "country": "Canada",
                "region": "Nova Scotia",
                "locality": "Halifax"
            },
            "filter": filters_json,
            "sort": {sort_by: sort_dir},
            "pagination": {
                "page_size": page_size,
                "offset": 0
            }
        }
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API error {response.status_code}: {response.text}")
        return None

with st.spinner("Fetching Halifax listings..."):
    data = fetch_listings(
        filters_key=str(sorted(filters.items())),
        sort_by=sort_by,
        sort_dir=sort_dir,
        page_size=page_size,
        filters_json=filters
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API error {response.status_code}: {response.text}")
        return None

with st.spinner("Fetching Halifax listings..."):
    data = fetch_listings(
        filters=str(filters),
        sort_by=sort_by,
        sort_dir=sort_dir,
        page_size=page_size
    )

if not data:
    st.error("Failed to fetch listings. Check your API key.")
    st.stop()

listings = data.get("results", [])
total = data.get("pagination", {}).get("total_count", 0)

st.title("🏠 Halifax Airbnb Market Dashboard")
st.caption(f"Showing {len(listings)} of {total:,} total active listings in Halifax")

# ── Tabs ─────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🗺️ Map", "📋 Listings Table", "🔍 Listing Detail"])

# ── TAB 1: Map ───────────────────────────────────────────────────
with tab1:
    st.subheader("Halifax Listings Map")

    m = folium.Map(location=[44.6488, -63.5752], zoom_start=12)

    for listing in listings:
        loc = listing.get("location_info", {})
        perf = listing.get("performance_metrics", {})
        info = listing.get("listing_info", {})
        prop = listing.get("property_details", {})

        lat = loc.get("latitude")
        lng = loc.get("longitude")

        if lat and lng:
            revenue = perf.get("ttm_revenue", 0)
            occupancy = perf.get("ttm_occupancy", 0)
            available = perf.get("ttm_available_days", 0)
            reserved = perf.get("ttm_days_reserved", 0)
            blocked = perf.get("ttm_blocked_days", 0)
            name = info.get("listing_name", "Unknown")
            bedrooms_n = prop.get("bedrooms", "?")
            avg_rate = perf.get("ttm_avg_rate", 0)

            popup_html = f"""
            <b>{name}</b><br>
            🛏️ {bedrooms_n} bed | 💰 ${avg_rate:.0f}/night<br>
            📅 TTM Revenue: ${revenue:,.0f}<br>
            📊 Occupancy: {occupancy*100:.1f}%<br>
            ✅ Available: {available} days<br>
            📦 Reserved: {reserved} days<br>
            🚫 Blocked: {blocked} days
            """

            folium.CircleMarker(
                location=[lat, lng],
                radius=6,
                color="crimson",
                fill=True,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)

    st_folium(m, width=None, height=500)

# ── TAB 2: Listings Table ────────────────────────────────────────
with tab2:
    st.subheader("All Listings")

    rows = []
    for listing in listings:
        info = listing.get("listing_info", {})
        perf = listing.get("performance_metrics", {})
        prop = listing.get("property_details", {})
        ratings = listing.get("ratings", {})
        host = listing.get("host_info", {})

        rows.append({
            "ID": info.get("listing_id"),
            "Name": info.get("listing_name"),
            "Type": info.get("room_type"),
            "Beds": prop.get("bedrooms"),
            "Baths": prop.get("baths"),
            "Guests": prop.get("guests"),
            "Avg Rate": f"${perf.get('ttm_avg_rate', 0):,.0f}",
            "TTM Revenue": f"${perf.get('ttm_revenue', 0):,.0f}",
            "Occupancy": f"{perf.get('ttm_occupancy', 0)*100:.1f}%",
            "Available Days": perf.get("ttm_available_days"),
            "Reserved Days": perf.get("ttm_days_reserved"),
            "Blocked Days": perf.get("ttm_blocked_days"),
            "Total Days": perf.get("ttm_total_days"),
            "Avg Stay": f"{perf.get('ttm_avg_length_of_stay', 0) or 0:.1f} nights",
            "Reviews": ratings.get("num_reviews"),
            "Rating": ratings.get("rating_overall"),
            "Superhost": "✅" if host.get("superhost") else "❌",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ── TAB 3: Listing Detail ────────────────────────────────────────
with tab3:
    st.subheader("Individual Listing Profile")

    listing_options = [
        f"{l.get('listing_info', {}).get('listing_id')} — {l.get('listing_info', {}).get('listing_name', 'Unknown')}"
        for l in listings
    ]

    selected = st.selectbox("Select a listing", listing_options)

    if selected:
        selected_id = int(selected.split(" — ")[0])

        @st.cache_data(ttl=3600)
        def fetch_detail(listing_id):
            response = requests.get(
                f"{BASE_URL}/listings",
                headers={"x-api-key": API_KEY},
                params={"id": listing_id, "currency": "native"}
            )
            if response.status_code == 200:
                return response.json()
            return None

        detail = fetch_detail(selected_id)

        if detail:
            info = detail.get("listing_info", {})
            perf = detail.get("performance_metrics", {})
            prop = detail.get("property_details", {})
            host = detail.get("host_info", {})
            pricing = detail.get("pricing_info", {})
            ratings = detail.get("ratings", {})
            booking = detail.get("booking_settings", {})

            # Photos
            photos = info.get("photo_urls", [])
            if photos:
                cols = st.columns(min(len(photos), 4))
                for i, url in enumerate(photos[:4]):
                    with cols[i]:
                        st.image(url, use_container_width=True)

            st.markdown(f"## {info.get('listing_name', 'Unknown')}")
            st.caption(info.get("description", "") or "")

            # Key metrics row 1
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("TTM Revenue", f"${perf.get('ttm_revenue', 0):,.0f}")
            col2.metric("Avg Nightly Rate", f"${perf.get('ttm_avg_rate', 0):,.0f}")
            col3.metric("Occupancy", f"{perf.get('ttm_occupancy', 0)*100:.1f}%")
            col4.metric("Avg Stay", f"{perf.get('ttm_avg_length_of_stay', 0) or 0:.1f} nights")

            # Key metrics row 2
            col5, col6, col7, col8 = st.columns(4)
            col5.metric("Total Days Tracked", perf.get("ttm_total_days", 0))
            col6.metric("Available Days", perf.get("ttm_available_days", 0))
            col7.metric("Reserved Days", perf.get("ttm_days_reserved", 0))
            col8.metric("Blocked Days", perf.get("ttm_blocked_days", 0))

            st.markdown("---")

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("### 🏠 Property")
                st.write(f"**Type:** {info.get('listing_type', 'N/A')}")
                st.write(f"**Bedrooms:** {prop.get('bedrooms', 'N/A')}")
                st.write(f"**Beds:** {prop.get('beds', 'N/A')}")
                st.write(f"**Baths:** {prop.get('baths', 'N/A')}")
                st.write(f"**Guests:** {prop.get('guests', 'N/A')}")
                st.write(f"**Min Nights:** {booking.get('min_nights', 'N/A')}")
                st.write(f"**Cancellation:** {booking.get('cancellation_policy', 'N/A')}")
                st.write(f"**Check-in:** {info.get('checkin_time', 'N/A')}")
                st.write(f"**Check-out:** {info.get('checkout_time', 'N/A')}")

                st.markdown("### 💰 Pricing")
                st.write(f"**Cleaning Fee:** ${pricing.get('cleaning_fee', 0):,.0f}")
                st.write(f"**Extra Guest Fee:** ${pricing.get('extra_guest_fee', 0):,.0f}")
                st.write(f"**Currency:** {pricing.get('currency', 'N/A')}")

            with col_b:
                st.markdown("### ⭐ Ratings")
                st.write(f"**Overall:** {ratings.get('rating_overall', 'N/A')} ({ratings.get('num_reviews', 0)} reviews)")
                st.write(f"**Cleanliness:** {ratings.get('rating_cleanliness', 'N/A')}")
                st.write(f"**Accuracy:** {ratings.get('rating_accuracy', 'N/A')}")
                st.write(f"**Check-in:** {ratings.get('rating_checkin', 'N/A')}")
                st.write(f"**Communication:** {ratings.get('rating_communication', 'N/A')}")
                st.write(f"**Location:** {ratings.get('rating_location', 'N/A')}")
                st.write(f"**Value:** {ratings.get('rating_value', 'N/A')}")

                st.markdown("### 👤 Host")
                st.write(f"**Name:** {host.get('host_name', 'N/A')}")
                st.write(f"**Superhost:** {'✅' if host.get('superhost') else '❌'}")
                st.write(f"**Professional Mgmt:** {'✅' if host.get('professional_management') else '❌'}")
                st.write(f"**Instant Book:** {'✅' if booking.get('instant_book') else '❌'}")

            # Amenities
            st.markdown("### 🛋️ Amenities")
            amenities = prop.get("amenities", [])
            if amenities:
                cols = st.columns(4)
                for i, amenity in enumerate(amenities):
                    cols[i % 4].write(f"✓ {amenity}")
            else:
                st.write("No amenities listed")

            # TTM vs L90D comparison
            st.markdown("---")
            st.markdown("### 📊 Trailing 12 Months vs Last 90 Days")
            compare_df = pd.DataFrame({
                "Metric": [
                    "Revenue",
                    "Avg Nightly Rate",
                    "Occupancy",
                    "Avg Length of Stay",
                    "Total Days",
                    "Available Days",
                    "Reserved Days",
                    "Blocked Days"
                ],
                "Trailing 12 Months": [
                    f"${perf.get('ttm_revenue', 0):,.0f}",
                    f"${perf.get('ttm_avg_rate', 0):,.0f}",
                    f"{perf.get('ttm_occupancy', 0)*100:.1f}%",
                    f"{perf.get('ttm_avg_length_of_stay', 0) or 0:.1f} nights",
                    perf.get("ttm_total_days", 0),
                    perf.get("ttm_available_days", 0),
                    perf.get("ttm_days_reserved", 0),
                    perf.get("ttm_blocked_days", 0),
                ],
                "Last 90 Days": [
                    f"${perf.get('l90d_revenue', 0):,.0f}",
                    f"${perf.get('l90d_avg_rate', 0):,.0f}",
                    f"{perf.get('l90d_occupancy', 0)*100:.1f}%",
                    f"{perf.get('l90d_avg_length_of_stay', 0) or 0:.1f} nights",
                    perf.get("l90d_total_days", 0),
                    perf.get("l90d_available_days", 0),
                    perf.get("l90d_days_reserved", 0),
                    perf.get("l90d_blocked_days", 0),
                ]
            })
            st.dataframe(compare_df, use_container_width=True, hide_index=True)

        else:
            st.error("Could not load listing details.")
