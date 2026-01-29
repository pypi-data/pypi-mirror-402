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

## API Reference

### `get_districts()`
Returns a sorted list of all 77 district names (UPPERCASE).

### `get_district(name)`
Returns the GeoJSON feature for a district.
*   `name`: Name of the district (case-insensitive).
*   **Returns**: Dictionary with `type`, `properties`, and `geometry`.

### `get_province_districts(province_id)`
Returns a list of district names in a specific province.
*   `province_id`: Integer ID of the province (1-7).

### `get_municipalities(district_name=None)`
Returns a list of municipality names.
*   `district_name` (Optional): If provided, filters the list to return only municipalities within that district.
*   **Returns**: Sorted list of strings.

### `get_municipality(name)`
Returns the GeoJSON feature for a specific municipality.
*   `name`: Name of the municipality (English, case-insensitive).

### `get_geojson()` / `get_provinces_geojson()` / `get_municipalities_geojson()`
Returns the complete raw GeoJSON FeatureCollection for Districts, Provinces, or Municipalities respectively.

## Contributing

We welcome contributions!
**GitHub Repository**: [https://github.com/bedbyaspokhrel/nepal-geo-data](https://github.com/bedbyaspokhrel/nepal-geo-data)

## License

MIT License - see the LICENSE file for details.

---

**Keywords**: Nepal GIS, Nepal Map Python, GeoJSON Nepal, Nepal Districts Data, Nepal Municipalities, Local Level Nepal, Gaunpalika, Nepal Provinces JSON, Python GIS Nepal.
