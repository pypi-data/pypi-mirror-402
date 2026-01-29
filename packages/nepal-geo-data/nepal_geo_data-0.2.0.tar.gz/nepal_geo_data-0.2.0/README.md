# Nepal Geo Data: Python Package for Nepal's Geographical GeoJSON

[![PyPI version](https://badge.fury.io/py/nepal-geo-data.svg)](https://badge.fury.io/py/nepal-geo-data)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Nepal Geo Data** is a complete, lightweight Python package designed for GIS developers, data scientists, and researchers who need accurate and easy-to-access geographical properties for Nepal. It bundles high-quality **GeoJSON** data for all **77 Districts** and **7 Provinces**, eliminating the need to search for clean map data files.

Whether you are building a dashboard in **Streamlit**, analyzing spatial data with **Pandas/GeoPandas**, or creating interactive maps with **Plotly/Folium**, this package provides the map data you need with a simple API.

## Key Features

*   **Complete Coverage**: Includes GeoJSON for all 77 districts and 7 provinces.
*   **Zero Dependencies**: Works with standard Python libraries; perfect for lightweight environments.
*   **Developer Friendly**: Simple functions to get district lists, boundaries, and province hierarchies.
*   **GIS Ready**: Outputs standard FeatureCollections compatible with GeoPandas (`gpd.read_file`), Folium, and Plotly.
*   **Searchable**: Case-insensitive lookup for districts (e.g., "Kathmandu", "Lalitpur").

## Installation

Install via pip from PyPI:

```bash
pip install nepal-geo-data
```

## Quick Start Guide

### 1. Retrieve List of Nepal Districts

Get a sorted list of all 77 districts. This is useful for creating dropdown menus or validation lists in your applications.

```python
import nepal_geo_data

# Get all district names
districts = nepal_geo_data.get_districts()
print(districts)
# Output: ['ACHHAM', 'ARGHAKHANCHI', ..., 'UDAYAPUR']
```

### 2. Get District Maps & Coordinates

Fetch the full GeoJSON Feature for a specific district. This includes the polygon geometry (coordinates) and metadata (Headquarters, Province ID).

```python
# Search for a district (Case Insensitive)
ktm = nepal_geo_data.get_district("Kathmandu")

if ktm:
    print(f"Headquarters: {ktm['properties']['HQ']}")
    print(f"Province: {ktm['properties']['PROVINCE']}")
    # ktm['geometry'] contains the Polygon coordinates for plotting
```

### 3. Filter Districts by Province

Easily group districts. For example, find all districts in **Bagmati Province** (Province 3).

```python
# Get districts in Province 3 (Bagmati)
bagmati_districts = nepal_geo_data.get_province_districts(3)
print(bagmati_districts)
```

## Integration Examples for Data Science

### Using with Plotly Express (Interactive Maps)

This package integrates seamlessly with Plotly to create stunning choropleth maps of Nepal.

```python
import plotly.express as px
from nepal_geo_data import get_geojson

# Load the full GeoJSON Data
nepal_geojson = get_geojson()

# Dummy data for visualization
data = {'District': ['KATHMANDU', 'LALITPUR', 'BHAKTAPUR'], 'Value': [100, 80, 60]}

fig = px.choropleth_mapbox(
    data_frame=data,
    geojson=nepal_geojson,
    locations='District',
    featureidkey="properties.DISTRICT",
    color='Value',
    center={"lat": 28.3949, "lon": 84.1240},
    mapbox_style="carto-positron",
    zoom=6,
    title="Nepal District Density Map"
)
fig.show()
```

## Contributing

We welcome contributions! If you have improved GeoJSON data or new features for Nepal's geography analysis, please check out our repository.

**GitHub Repository**: [https://github.com/bedbyaspokhrel/nepal-geo-data](https://github.com/bedbyaspokhrel/nepal-geo-data)

### Local Development

```bash
git clone https://github.com/bedbyaspokhrel/nepal-geo-data.git
cd nepal-geo-data
pip install -e .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Keywords**: Nepal GIS, Nepal Map Python, GeoJSON Nepal, Nepal Districts Data, Kathmandu Map, Nepal Provinces JSON, Python GIS Nepal.
