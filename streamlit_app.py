import streamlit as st
import pandas as pd
import math
from pathlib import Path
import numpy as np
import geopandas as gpd

import folium
from streamlit_folium import st_folium
from streamlit_gsheets import GSheetsConnection

import geopandas as gpd
conn = st.connection("gsheets", type=GSheetsConnection)


# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='ATQ Travel',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

# Cached data loading
@st.cache_data
def get_counties_data():
    url = "https://raw.githubusercontent.com/GabrielRondelli/geojson/main/romania-counties.geojson"
    gdf = gpd.read_file(url)
    gdf['County'] = (
        gdf['NAME_1'].str.normalize('NFKD')
        .str.encode('ascii', errors='ignore')
        .str.decode('utf-8')
    )
    return gdf

def load_counties_visit_data(conn):
    df_counties = conn.read(
        spreadsheet=st.secrets.connections.gsheets.sheet_visits, worksheet="Counties",
        ttl=0
    )[['County', 'Capital', 'Code', 'Been to']]

    df_counties['County'] = (
        df_counties['County'].str.normalize('NFKD')
        .str.encode('ascii', errors='ignore')
        .str.decode('utf-8')
    )
    df_counties["status"] = df_counties['Been to'].astype(int)
    return df_counties

def style_polygon(color):
    return lambda _: {
        'fillColor': color,
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.5,
    }

def add_polygon_and_label(map_obj, geometry, county_name, color):
    folium.GeoJson(
        geometry,
        style_function=style_polygon(color),
        tooltip=county_name
    ).add_to(map_obj)

    centroid = geometry.centroid
    folium.Marker(
        location=[centroid.y, centroid.x],
        icon=folium.DivIcon(
            html=f'<div style="font-size:8pt;color:black;text-align:center;">{county_name}</div>'
        ),
    ).add_to(map_obj)

# Main execution
gdf = get_counties_data()
df_counties = load_counties_visit_data(conn)

merged = gdf.merge(df_counties, on="County", how="left")
merged["status"] = merged["status"].fillna(0).astype(int)

# Metrics for display
total_counties = len(merged)
visited_counties = merged['status'].sum()
percentage_visited = (visited_counties / total_counties) * 100

color_map = {0: "transparent", 1: "green"}

m = folium.Map(
    location=[45.9432, 24.9668], zoom_start=6, tiles="cartodbpositron"
)

for _, row in merged.iterrows():
    add_polygon_and_label(m, row['geometry'], row['County'], color_map[row['status']])



# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :romania: Romania Travels
'''


# Render map in Streamlit
st_folium(m, width=700, height=500)

col1, col2, col3 = st.columns(3)
col1.metric("Total Counties", total_counties)
col2.metric("Visited Counties", visited_counties)
col3.metric("Percentage Visited", f"{percentage_visited:.1f}%")


'''
# :earth_americas: International Travels
'''