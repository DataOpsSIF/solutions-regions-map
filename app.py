import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.features import GeoJson
from streamlit_folium import st_folium
from controller import Database
from sql import COMMAND

# Load data
db = Database()
cnx = db.connect()
df_php = db.fetch(connection=cnx, command=COMMAND)
df_php = pd.DataFrame(df_php)

df_php['geoLatitude'] = df_php['geoLatitude'].astype(float)
df_php['geoLongitude'] = df_php['geoLongitude'].astype(float)
geojson_file = "contours-geographiques-des-nouvelles-regions-metropole.geojson"
df_regions = gpd.read_file(geojson_file)

# Sidebar for region selection
st.sidebar.title("Filter Options")
region_list = df_regions['region'].unique()
selected_region = st.sidebar.selectbox("Select a Region", options=region_list)

# Filter regions GeoDataFrame
selected_region_geo = df_regions[df_regions['region'] == selected_region]

# Convert df_php to GeoDataFrame
points = gpd.GeoDataFrame(
    df_php, 
    geometry=gpd.points_from_xy(df_php.geoLongitude, df_php.geoLatitude),
    crs='EPSG:4326'
)

# Spatial join
points_within = gpd.sjoin(points, selected_region_geo, op='within')

# Create Folium map
m = folium.Map(location=[selected_region_geo.geometry.centroid.y.values[0], 
                         selected_region_geo.geometry.centroid.x.values[0]], 
               zoom_start=7)

# Add region polygon
folium.GeoJson(
    selected_region_geo.geometry,
    name='Selected Region',
    style_function=lambda x: {'fillColor': 'orange'}
).add_to(m)

# Add points
for idx, row in points_within.iterrows():
    folium.CircleMarker(
        location=[row['geoLatitude'], row['geoLongitude']],
        radius=3,
        color='blue',
        fill=True,
        fill_color='blue'
    ).add_to(m)

# Display map
st.title("Interactive Map of Solutions")
st_data = st_folium(m, width=700, height=500)

# Display filtered data
st.subheader(f"Solutions in {selected_region}")
st.dataframe(points_within.drop(columns='geometry'))

# Download button
csv = points_within.drop(columns='geometry').to_csv(index=False)
st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name=f'solutions_{selected_region}.csv',
    mime='text/csv',
)
