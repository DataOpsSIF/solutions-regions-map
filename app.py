import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from controller import Database
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Configurer la page
st.set_page_config(
    page_title="Carte interactive des solutions Françaises",
    page_icon="🌍",
    initial_sidebar_state="expanded",
    layout="wide"
)

COMMAND = st.secrets["COMMAND"]

# Load data
db = Database()
cnx = db.connect()
df_php = db.fetch(connection=cnx, command=COMMAND)
df_php = pd.DataFrame(df_php)

df_php['geoLatitude'] = df_php['geoLatitude'].astype(float)
df_php['geoLongitude'] = df_php['geoLongitude'].astype(float)
geojson_file = "contours-geographiques-des-nouvelles-regions-metropole.geojson"
df_regions = gpd.read_file(geojson_file)

# Convert df_php to GeoDataFrame
all_points = gpd.GeoDataFrame(
    df_php,
    geometry=gpd.points_from_xy(df_php.geoLongitude, df_php.geoLatitude),
    crs='EPSG:4326'
)

# Initialize session state for selected point and region
if 'selected_point' not in st.session_state:
    st.session_state['selected_point'] = {'lat': None, 'lon': None}
if 'selected_region' not in st.session_state:
    st.session_state['selected_region'] = 'Toutes les régions'  # Set default value here

# Sidebar for region selection and branding
with st.sidebar:
    # Ajouter le logo en haut
    st.image("logo.svg", use_container_width=True)
    st.markdown("---")

    # Options de filtrage
    st.title("Carte interactive des solutions Françaises 🇫🇷")
    st.markdown("Cet outil développé par la Fondation Solar Impulse permet à nos villes et régions partenaires d'explorer notre portefeuille de solutions du territoire français de manière interactive.")
    st.markdown("---")

    region_list = df_regions['region'].unique()
    region_list = ['Toutes les régions'] + list(region_list)  # Add "Toutes les régions" at the beginning
    selected_region = st.selectbox(
        "Sélectionnez une région",
        options=region_list,
        key='selected_region'  # Use session state key
    )

    # Branding dans la barre latérale
    st.markdown("---")

    # Conditions d'utilisation
    with st.expander("Conditions d'utilisation"):
        st.write("""
        Les données présentées sont confidentielles et ne doivent pas être partagées sans l'autorisation de la Fondation Solar Impulse.
        Cet outil est la propriété de la Fondation Solar Impulse et ne doit pas être diffusé ou reproduit sans son consentement explicite.
        En utilisant cet outil, vous acceptez de respecter les termes de cette licence d'utilisation standard et reconnaissez les droits de propriété intellectuelle de la Fondation.
        """)

# Remove this line since 'selected_region' is managed by the selectbox key
# st.session_state['selected_region'] = selected_region

# Use 'selected_region' from session state
selected_region = st.session_state['selected_region']

# Filter regions GeoDataFrame based on selected region
if selected_region == 'Toutes les régions':
    filtered_regions_geo = df_regions
    filtered_points = all_points
else:
    filtered_regions_geo = df_regions[df_regions['region'] == selected_region]
    # Spatial join to get points within the selected region
    filtered_points = gpd.sjoin(all_points, filtered_regions_geo, predicate='within')

# Function to create the map
def create_map():
    if st.session_state['selected_point']['lat'] is not None and st.session_state['selected_point']['lon'] is not None:
        # Center the map on the selected point
        m = folium.Map(location=[st.session_state['selected_point']['lat'], st.session_state['selected_point']['lon']], zoom_start=12)
    else:
        # Center the map on the selected region or France
        if selected_region == 'Toutes les régions':
            # Center the map on France with a fixed zoom level
            m = folium.Map(location=[46.2276, 2.2137], zoom_start=5)
        else:
            # Center the map on the selected region
            region_centroid = filtered_regions_geo.geometry.centroid.iloc[0]
            m = folium.Map(location=[region_centroid.y, region_centroid.x], zoom_start=7)
    # Add selected regions
    folium.GeoJson(
        filtered_regions_geo.geometry,
        name='Régions',
        style_function=lambda x: {'fillColor': 'orange', 'color': 'black', 'weight': 1, 'fillOpacity': 0.2}
    ).add_to(m)
    # Add points
    for idx, row in filtered_points.iterrows():
        folium.CircleMarker(
            location=[row['geoLatitude'], row['geoLongitude']],
            radius=3,
            color='blue',
            fill=True,
            fill_color='blue',
            popup=folium.Popup(f"""
                <strong>{row['solution_name']}</strong><br>
                {row['solution_status']}<br>
                Informations supplémentaires : {row['solution_description']}
            """, max_width=250),
            tooltip=folium.Tooltip(f"{row['solution_name']}")
        ).add_to(m)
    return m

# Create the map
m = create_map()

# Display the map
st.title("Carte interactive des solutions")
st_data = st_folium(m, width=700, height=500, key='solutions_map')

# Retrieve map bounds
if st_data and 'bounds' in st_data and st_data['bounds']:
    bounds = st_data['bounds']
    min_lon = bounds['_southWest']['lng']
    min_lat = bounds['_southWest']['lat']
    max_lon = bounds['_northEast']['lng']
    max_lat = bounds['_northEast']['lat']

    # Filter points within the current map view
    filtered_points_in_view = filtered_points[
        (filtered_points['geoLongitude'] >= min_lon) &
        (filtered_points['geoLongitude'] <= max_lon) &
        (filtered_points['geoLatitude'] >= min_lat) &
        (filtered_points['geoLatitude'] <= max_lat)
    ]
else:
    # On initial load, display all points
    filtered_points_in_view = filtered_points

# Build grid options
gb = GridOptionsBuilder.from_dataframe(filtered_points_in_view.drop(columns='geometry'))
gb.configure_selection(selection_mode='single', use_checkbox=True)
grid_options = gb.build()

# Display the grid with the number of solutions
num_solutions = len(filtered_points_in_view)
st.subheader(f"{num_solutions} solutions dans la vue filtrée")
grid_response = AgGrid(
    filtered_points_in_view.drop(columns='geometry'),
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    theme='streamlit',
    height=300,
    allow_unsafe_jscode=True,
    key='solutions_grid'  # Add a unique key to maintain state
)

# Get the selected row
selected = grid_response['selected_rows']

# Update the selected point in session state
if selected is not None and not selected.empty:
    selected_row = selected.iloc[0]
    st.session_state['selected_point']['lat'] = selected_row['geoLatitude']
    st.session_state['selected_point']['lon'] = selected_row['geoLongitude']
else:
    st.session_state['selected_point']['lat'] = None
    st.session_state['selected_point']['lon'] = None

# Download button
csv = filtered_points_in_view.drop(columns='geometry').to_csv(index=False)
st.download_button(
    label="Télécharger les données au format CSV",
    data=csv,
    file_name='solutions_filtrées.csv',
    mime='text/csv',
)

