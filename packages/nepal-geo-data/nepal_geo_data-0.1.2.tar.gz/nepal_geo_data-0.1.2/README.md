# Nepal Geo Data

A Python package that bundles GeoJSON data for Nepal's districts and provinces, providing a simple and efficient API to access geographical data without handling external files.

## Installation

```bash
pip install nepal-geo-data
```

## Quick Start

```python
import nepal_geo_data

# Get all district names
print(nepal_geo_data.get_districts())

# Get data for a specific district
ktm = nepal_geo_data.get_district("Kathmandu")
print(ktm['properties'])
```

## detailed Usability & API Reference

### 1. Retrieve District Keys
Get a sorted list of all 77 districts in uppercase. Useful for populating dropdowns or validation.

```python
from nepal_geo_data import get_districts

districts = get_districts()
# Output: ['ACHHAM', 'ARGHAKHANCHI', ..., 'UDAYAPUR']
```

### 2. Get District Details
Search for a district by name (case-insensitive). Returns a GeoJSON Feature dictionary containing `properties` and `geometry`.

```python
from nepal_geo_data import get_district

data = get_district('Lalitpur')
if data:
    # Access Properties
    props = data['properties']
    print(f"District: {props['DISTRICT']}")
    print(f"Headquarters: {props['HQ']}")
    print(f"Province ID: {props['PROVINCE']}")
    
    # Access Geometry
    geometry = data['geometry']
    print(f"Type: {geometry['type']}") # e.g., Polygon
```

### 3. Get Districts by Province
Filter districts based on their Province ID (1-7).

```python
from nepal_geo_data import get_province_districts

# Get all districts in Bagmati Province (Province 3)
province_3_districts = get_province_districts(3)
print(province_3_districts)
# Output: ['BHAKTAPUR', 'CHITWAN', 'DHADING', 'DOLAKHA', 'KATHMANDU', 'KAVREPALANCHOK', 'LALITPUR', 'MAKWANPUR', 'NUWAKOT', 'RAMECHHAP', 'RASUWA', 'SINDHULI', 'SINDHUPALCHOK']
```

### 4. Get Province Data
Get a list of all 7 provinces with their metadata.

```python
from nepal_geo_data import get_provinces

provinces = get_provinces()
for p in provinces:
    print(f"Province {p['id']}: {p['name']} (Capital: {p['capital']})")
```

### 5. Access Raw GeoJSON
If you need the full GeoJSON object for plotting (e.g., with Plotly, Folium, or GeoPandas), you can fetch the raw data directly.

```python
from nepal_geo_data import get_geojson

data = get_geojson()
# data is a dictionary representing the FeatureCollection
# {'type': 'FeatureCollection', 'features': [...]}
```

## Integration Examples

### Plotting with Plotly Express
```python
import plotly.express as px
from nepal_geo_data import get_geojson

geo_data = get_geojson()

fig = px.choropleth_mapbox(
    geojson=geo_data,
    locations=['KATHMANDU', 'LALITPUR', 'BHAKTAPUR'], # Example subset
    featureidkey="properties.DISTRICT",
    mapbox_style="carto-positron",
    center={"lat": 27.7, "lon": 85.3},
    zoom=7
)
fig.show()
```

## Development

To install locally for development:
```bash
git clone https://github.com/bedbyaspokhrel/nepal-geo-data.git
cd nepal-geo-data
pip install -e .
```

## License

MIT
