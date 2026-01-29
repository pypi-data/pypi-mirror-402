import json
from typing import List, Dict, Any, Optional
try:
    from importlib.resources import files
except ImportError:
    import importlib_resources as files # type: ignore

def _load_json(filename: str) -> Dict[str, Any]:
    """Helper to load json data from the package."""
    try:
        from importlib.resources import files
        ref = files('nepal_geo_data.data').joinpath(filename)
        with ref.open('r', encoding='utf-8') as f:
            return json.load(f)
    except ImportError:
        # Fallback for older python if necessary (though 3.8+ is requested)
        import pkg_resources
        return json.loads(pkg_resources.resource_string('nepal_geo_data.data', filename).decode('utf-8'))

_DISTRICTS_DATA = None
_PROVINCES_DATA = None
_MUNICIPALITIES_DATA = None

def _get_districts_data() -> Dict[str, Any]:
    global _DISTRICTS_DATA
    if _DISTRICTS_DATA is None:
        _DISTRICTS_DATA = _load_json('districts.geojson')
        # Backward compatibility: Inject DISTRICT key
        for feature in _DISTRICTS_DATA['features']:
            props = feature['properties']
            if 'district_name_en' in props:
                props['DISTRICT'] = props['district_name_en'].upper()
            if 'province_code' in props:
                try:
                    # Map new string "1" to integer 1 if possible
                    props['PROVINCE'] = int(props['province_code'])
                except (ValueError, TypeError):
                    props['PROVINCE'] = 0 # Default or error code
    return _DISTRICTS_DATA

def _get_provinces_data() -> Dict[str, Any]:
    global _PROVINCES_DATA
    if _PROVINCES_DATA is None:
        _PROVINCES_DATA = _load_json('provinces.geojson')
    return _PROVINCES_DATA

def _get_municipalities_data() -> Dict[str, Any]:
    global _MUNICIPALITIES_DATA
    if _MUNICIPALITIES_DATA is None:
        _MUNICIPALITIES_DATA = _load_json('municipalities.geojson')
    return _MUNICIPALITIES_DATA

def get_geojson() -> Dict[str, Any]:
    """
    Returns the complete GeoJSON data for all districts.
    """
    return _get_districts_data()

def get_provinces_geojson() -> Dict[str, Any]:
    """
    Returns the complete GeoJSON data for provinces.
    """
    return _get_provinces_data()

def get_municipalities_geojson() -> Dict[str, Any]:
    """
    Returns the complete GeoJSON data for municipalities.
    """
    return _get_municipalities_data()

def get_districts() -> List[str]:
    """
    Returns a list of all district names (uppercase as per legacy behavior).
    """
    data = _get_districts_data()
    # Use the injected DISTRICT key
    return sorted([feature['properties'].get('DISTRICT', 'UNKNOWN') for feature in data['features']])

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
    Case-insensitive search against DISTRICT or district_name_en.
    """
    data = _get_districts_data()
    name_upper = name.upper()
    for feature in data['features']:
        props = feature['properties']
        # Check injected legacy key
        if props.get('DISTRICT') == name_upper:
            return feature
        # Check new key
        if props.get('district_name_en', '').upper() == name_upper:
            return feature
    return None

def get_province_districts(province_id: int) -> List[str]:
    """
    Get list of districts in a specific province.
    param province_id: 1-7 (supports int)
    """
    data = _get_districts_data()
    districts = []
    for feature in data['features']:
        props = feature['properties']
        # Handle both old 'PROVINCE' (int) and new schema if needed
        # We injected 'PROVINCE' as int in _get_districts_data
        p_id = props.get('PROVINCE')
        if p_id == province_id:
            districts.append(props.get('DISTRICT', 'UNKNOWN'))
    return sorted(districts)

def get_boundaries(district_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the geometry (Polygon/MultiPolygon) for a specific district.
    """
    district = get_district(district_name)
    if district:
        return district['geometry']
    return None

def get_municipalities(district_name: Optional[str] = None) -> List[str]:
    """
    Returns a list of municipality names.
    If district_name is provided, returns municipalities for that district.
    """
    data = _get_municipalities_data()
    munis = []
    
    # If filtering by district, we need the district code or name match
    # Since municipality data likely has district_code but maybe not district_name consistent with dist file
    target_district_code = None
    if district_name:
        dist_data = get_district(district_name)
        if dist_data:
            target_district_code = dist_data['properties'].get('district_code')
        else:
            return [] # District not found

    for feature in data['features']:
        props = feature['properties']
        if target_district_code:
            # Compare codes. Assuming they are strings in both or consistent.
            # In district.geojson, district_code is usually string like "101".
            if props.get('district_code') == target_district_code:
                munis.append(props.get('gapa_napa', 'Unknown'))
        else:
            munis.append(props.get('gapa_napa', 'Unknown'))
            
    return sorted(list(set(munis))) # Return unique sorted list

def get_municipality(name: str) -> Optional[Dict[str, Any]]:
    """
    Get data for a specific municipality by name (case-insensitive).
    Search against 'gapa_napa' (English/Romanized usually) property.
    """
    data = _get_municipalities_data()
    name_upper = name.upper()
    for feature in data['features']:
        if feature['properties'].get('gapa_napa', '').upper() == name_upper:
            return feature
        # Also check key maybe?
        if feature['properties'].get('key', '').upper() == name_upper:
            return feature
    return None
