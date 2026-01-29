# Nepal Geo Data: Complete Geographical GeoJSON for Nepal

[![PyPI version](https://badge.fury.io/py/nepal-geo-data.svg)](https://badge.fury.io/py/nepal-geo-data)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Nepal Geo Data** is the most comprehensive Python package for Nepal's geographical data. It provides high-quality **GeoJSON** for all **77 Districts**, **7 Provinces**, and **753 Local Levels (Municipalities/Gaunpalikas)**, along with rich metadata (Nepali names, official codes).

Whether you are building a dashboard in **Streamlit**, analyzing spatial data with **Pandas/GeoPandas**, or creating interactive maps with **Plotly/Folium**, this package provides the map data you need with a simple API.

## Key Features

*   **Complete Administrative Coverage**:
    *   **7 Provinces** (Pradesh)
    *   **77 Districts** (Jilla)
    *   **753 Local Levels** (Palikas/Municipalities) - *New in v0.2.0!*
*   **Rich Metadata**: Includes English names, Nepali names (e.g., "Kathmandu", "काठमाडौँ"), and official government codes.
*   **Zero Dependencies**: Works with standard Python libraries.
*   **GIS Ready**: Outputs standard FeatureCollections compatible with GeoPandas (`gpd.read_file`), Folium, and Plotly.
*   **Coordinate Reference System (CRS)**: WGS84 (EPSG:4326). All coordinates are in Latitude/Longitude.
*   **Backward Compatible**: Preserves legacy behavior (UPPERCASE district keys) for existing projects.

## Installation

Install via pip from PyPI:

```bash
pip install nepal-geo-data
```

## Quick Start & Tutorials

### 1. Districts and Provinces

Get lists and details of administrative boundaries.

```python
import nepal_geo_data

# Print the built-in guide
nepal_geo_data.help()

# Get all district names
districts = nepal_geo_data.get_districts()
print(districts) 
# Output: ['ACHHAM', 'ARGHAKHANCHI', ..., 'UDAYAPUR']

# Get details for a specific district (Case Insensitive)
ktm = nepal_geo_data.get_district("Kathmandu")
print(ktm['properties']['district_name_np'])  # Output: काठमाडौँ
print(ktm['properties']['province_name_en'])  # Output: Bagmati Province

# Get all districts in a specific province (e.g., Karnali Province / Province 6)
karnali_districts = nepal_geo_data.get_province_districts(6)
```

### 2. Working with Municipalities (New!)

The package now supports all 753 Local Levels.

#### Get All Municipalities
```python
# Get a list of ALL municipalities in Nepal
all_munis = nepal_geo_data.get_municipalities()
print(f"Total Municipalities: {len(all_munis)}") # 753
print(all_munis[:5]) 
```

#### Filter Municipalities by District
The `get_municipalities` function accepts an optional `district_name` parameter.

```python
# Get only municipalities in 'Jhapa' district
jhapa_munis = nepal_geo_data.get_municipalities("Jhapa")

print(f"Municipalities in Jhapa: {len(jhapa_munis)}")
for muni in jhapa_munis:
    print(f"- {muni}")
    
# Output:
# - Arjundhara
# - Bhadrapur
# - Birtamod
# ...
```

#### Get Municipality Details & Map Data
Search for a specific municipality to get its full GeoJSON (coordinates, codes, Nepali name).

```python
# Get data for 'Kathmandu Metropolitan City'
# You can search by English name (case-insensitive)
ktm_metro = nepal_geo_data.get_municipality("Kathmandu Metropolitan City")

if ktm_metro:
    props = ktm_metro['properties']
    print(f"Name (EN): {props['gapa_napa']}")      # Kathmandu Metropolitan City
    print(f"Name (NP): {props['gapa_napa_np']}")  # काठमाडौँ महानगरपालिका
    print(f"Type: {props['type']}")                # Mahanagarpalika
    print(f"District ID: {props['district_code']}")
    
    # Access geometry for plotting
    # geometry = ktm_metro['geometry']
```

### 3. Integration with Plotly (Choropleth Maps)

Create stunning interactive maps using the GeoJSON data.

```python
import plotly.express as px
from nepal_geo_data import get_geojson

# Load District GeoJSON
nepal_geojson = get_geojson()

# Dummy data dictionary
data_dict = {'KATHMANDU': 100, 'LALITPUR': 80, 'BHAKTAPUR': 60}
# Convert to list of dicts for Plotly
data = [{'District': k, 'Value': v} for k, v in data_dict.items()]

fig = px.choropleth_mapbox(
    data_frame=data,
    geojson=nepal_geojson,
    locations='District',
    featureidkey="properties.DISTRICT", # Using the backward-compatible key
    color='Value',
    center={"lat": 28.3949, "lon": 84.1240},
    mapbox_style="carto-positron",
    zoom=6,
    title="Nepal District Density Map"
)
fig.show()
```

## 📚 API Reference & Examples

Here is a complete list of all available functions with examples.

### 1. Administrative Lists

#### `get_districts()`
Returns a list of all 77 districts in Nepal.
```python
import nepal_geo_data
districts = nepal_geo_data.get_districts()
print(districts[:5]) 
# output: ['ACHHAM', 'ARGHAKHANCHI', 'BAGLUNG', 'BAITADI', 'BAJHANG']
```

#### `get_provinces()`
Returns a list of metadata for all 7 provinces.
```python
provinces = nepal_geo_data.get_provinces()
for p in provinces:
    print(f"{p['province_name_en']} (ID: {p['province_code']})")
```

#### `get_province_districts(province_id)`
Returns a list of districts within a specific province (IDs 1-7).
```python
# Get districts in Karnali Province (ID: 6)
karnali = nepal_geo_data.get_province_districts(6)
print(karnali)
```

#### `get_municipalities(district_name=None)`
Returns a list of all 753 municipalities. Optionally filter by district.
```python
# All municipalities
all_munis = nepal_geo_data.get_municipalities()

# Filter by district (e.g., Chitwan)
chitwan_munis = nepal_geo_data.get_municipalities("Chitwan")
print(chitwan_munis)
```

#### `get_wards(municipality_name)`
Returns a list of ward numbers for a specific municipality.
```python
wards = nepal_geo_data.get_wards("Kathmandu Metropolitan City")
print(f"Total Wards: {len(wards)}") # 32
print(wards) # [1, 2, 3, ..., 32]
```

### 2. Search & Details (Rich Metadata)

#### `get_district(name)`
Get full details including geometry, headquarters, and codes.
```python
data = nepal_geo_data.get_district("Kaski")
props = data['properties']
print(f"District: {props['district_name_en']}")
print(f"Headquarter: {props['headquarter']}")
print(f"Area: {props['area_sq_km']} sq km")
```

#### `get_municipality(name)`
Get full details including wards, website, and geometry.
```python
muni = nepal_geo_data.get_municipality("Pokhara Lekhnath Metropolitan City")
props = muni['properties']
print(f"Website: {props.get('website')}")
print(f"Wards: {props.get('wards')}")
```

#### `get_boundaries(district_name)`
Get only the geometry (Polygon/MultiPolygon) for mapping.
```python
geom = nepal_geo_data.get_boundaries("Mustang")
# Use with Shapely or GeoPandas
# shape = shapely.geometry.shape(geom)
```

### 3. Raw GeoJSON Data

Access the raw FeatureCollections directly for use with GIS libraries like GeoPandas.

#### `get_geojson()`
All districts as a FeatureCollection.
```python
import geopandas as gpd
geojson = nepal_geo_data.get_geojson()
gdf = gpd.GeoDataFrame.from_features(geojson)
gdf.plot()
```

#### `get_provinces_geojson()`
All provinces as a FeatureCollection.

#### `get_municipalities_geojson()`
All municipalities as a FeatureCollection.

### 4. Interactive Help

#### `help()`
Prints a quick guide to the console.
```python
nepal_geo_data.help()
```

## 🚀 Advanced Usage & Integrations

### 1. Plotly Integration: Mapping Provinces
Here is a complete example of how to create a Choropleth map of Nepal's 7 Provinces using `plotly.express`.

```python
import plotly.express as px
from nepal_geo_data import get_provinces_geojson

# 1. Get Province GeoJSON
province_geojson = get_provinces_geojson()

# 2. Prepare Data (Example: Population or GDP by Province)
# Note: Keys must match the Feature properties (e.g., 'province_name_en' or 'province_code')
data = [
    {'Province': 'Koshi Province', 'Value': 10},
    {'Province': 'Madhesh Province', 'Value': 20},
    {'Province': 'Bagmati Province', 'Value': 50},
    {'Province': 'Gandaki Province', 'Value': 30},
    {'Province': 'Lumbini Province', 'Value': 40},
    {'Province': 'Karnali Province', 'Value': 5},
    {'Province': 'Sudurpaschim Province', 'Value': 15},
]

# 3. Create Map
fig = px.choropleth_mapbox(
    data_frame=data,
    geojson=province_geojson,
    locations='Province',             # Key in 'data'
    featureidkey="properties.province_name_en", # Key in GeoJSON properties
    color='Value',
    center={"lat": 28.3949, "lon": 84.1240},
    mapbox_style="carto-positron",
    zoom=6,
    title="Nepal Province-wise Distribution",
    opacity=0.7
)

fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
fig.show()
```

### 2. GeoPandas Integration (Static Maps)
Easily convert data for spatial analysis.

```python
import geopandas as gpd
from nepal_geo_data import get_municipalities_geojson

# Load all 753 municipalities into a GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(get_municipalities_geojson())

# Filter for a specific district
ktm_munis = gdf[gdf['district_name_en'] == 'Kathmandu']

# Plot
ktm_munis.plot(column='type', legend=True, figsize=(10, 10))
```

### 3. Folium Integration (Interactive Web Maps)
```python
import folium
from nepal_geo_data import get_boundaries

# Create base map
m = folium.Map(location=[28.3949, 84.1240], zoom_start=7)

# Add District Boundary (e.g., Mustang)
mustang_geom = get_boundaries("Mustang")
folium.GeoJson(
    mustang_geom,
    style_function=lambda x: {'color': 'red', 'fillOpacity': 0.3}
).add_to(m)

m.save("nepal_map.html")
```

## Contributing

We welcome contributions!
**GitHub Repository**: [https://github.com/bedbyaspokhrel/nepal-geo-data](https://github.com/bedbyaspokhrel/nepal-geo-data)

## License

MIT License - see the LICENSE file for details.

---

**Keywords**: Nepal GIS, Nepal Map Python, GeoJSON Nepal, Nepal Districts Data, Nepal Municipalities, Local Level Nepal, Gaunpalika, Nepal Provinces JSON, Python GIS Nepal.
