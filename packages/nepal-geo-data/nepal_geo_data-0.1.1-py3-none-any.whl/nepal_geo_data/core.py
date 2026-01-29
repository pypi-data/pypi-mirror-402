import json
import importlib.resources
from typing import List, Dict, Any, Optional, Union

# Cache to store loaded data
_DISTRICTS_CACHE = None
_PROVINCES_CACHE = None

def _load_json(filename: str) -> Dict[str, Any]:
    """Helper to load json data from the package."""
    # Using try-except for compatibility across python versions if needed, 
    # but importlib.resources.files is standard in 3.9+. 
    # For older versions (3.8), we can use open_text or similar, but files() is cleaner.
    # We'll assume a standard structure.
    try:
        from importlib.resources import files
        ref = files('nepal_geo_data.data').joinpath(filename)
        with ref.open('r', encoding='utf-8') as f:
            return json.load(f)
    except ImportError:
        # Fallback for older python if necessary (though 3.8+ is requested)
        import pkg_resources
        return json.loads(pkg_resources.resource_string('nepal_geo_data.data', filename).decode('utf-8'))

def _get_districts_data() -> Dict[str, Any]:
    global _DISTRICTS_CACHE
    if _DISTRICTS_CACHE is None:
        _DISTRICTS_CACHE = _load_json('districts.geojson')
    return _DISTRICTS_CACHE

def _get_provinces_data() -> Dict[str, Any]:
    global _PROVINCES_CACHE
    if _PROVINCES_CACHE is None:
        _PROVINCES_CACHE = _load_json('provinces.geojson')
    return _PROVINCES_CACHE

def get_geojson() -> Dict[str, Any]:
    """
    Returns the complete GeoJSON data for districts.
    """
    return _get_districts_data()

def get_provinces_geojson() -> Dict[str, Any]:
    """
    Returns the complete GeoJSON data for provinces.
    """
    return _get_provinces_data()

def get_districts() -> List[str]:
    """
    Returns a list of all district names (uppercase).
    """
    data = _get_districts_data()
    return sorted([feature['properties']['DISTRICT'] for feature in data['features']])

def get_provinces() -> List[Dict[str, Any]]:
    """
    Returns a list of province properties.
    """
    data = _get_provinces_data()
    return [feature['properties'] for feature in data['features']]

def get_district(name: str) -> Optional[Dict[str, Any]]:
    """
    Get data (properties + geometry) for a specific district.
    Returns None if not found.
    Case-insensitive search.
    """
    data = _get_districts_data()
    name_upper = name.upper()
    for feature in data['features']:
        if feature['properties']['DISTRICT'].upper() == name_upper:
            return feature
    return None

def get_province_districts(province_id: int) -> List[str]:
    """
    Get list of districts in a specific province.
    param province_id: 1-7
    """
    data = _get_districts_data()
    districts = []
    for feature in data['features']:
        # Ensure we handle checking province ID correctly (it's int in json)
        if feature['properties'].get('PROVINCE') == province_id:
            districts.append(feature['properties']['DISTRICT'])
    return sorted(districts)

def get_boundaries(district_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the geometry (Polygon/MultiPolygon) for a specific district.
    """
    district = get_district(district_name)
    if district:
        return district['geometry']
    return None
