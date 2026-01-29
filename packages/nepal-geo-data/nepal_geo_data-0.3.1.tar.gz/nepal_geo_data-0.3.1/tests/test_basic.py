import sys
import os
import unittest

# Add package root to path so we can import without installing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import nepal_geo_data
print(f"IMPORTED FROM: {nepal_geo_data.__file__}")

class TestNepalGeoData(unittest.TestCase):
    
    def test_districts_list(self):
        districts = nepal_geo_data.get_districts()
        self.assertIsInstance(districts, list)
        self.assertEqual(len(districts), 77)
        self.assertIn("KATHMANDU", districts)
        self.assertIn("JHAPA", districts)
        
    def test_get_district(self):
        district = nepal_geo_data.get_district("kathmandu")
        self.assertIsNotNone(district)
        self.assertEqual(district['properties']['DISTRICT'], "KATHMANDU")
        self.assertEqual(district['properties']['district_name_en'], "Kathmandu")
        self.assertIsNone(nepal_geo_data.get_district("NonExistentDistrict"))

    def test_get_boundaries(self):
        geom = nepal_geo_data.get_boundaries("JHAPA")
        self.assertIsNotNone(geom)
        self.assertTrue(geom['type'] in ["Polygon", "MultiPolygon"])

    def test_province_districts(self):
        p1 = nepal_geo_data.get_province_districts(1)
        self.assertIn("JHAPA", p1)
        
    def test_get_provinces(self):
        provinces = nepal_geo_data.get_provinces()
        self.assertIsInstance(provinces, list)
        self.assertEqual(len(provinces), 7)
        p1 = next((p for p in provinces if str(p.get('province_code')) == "1"), None)
        if not p1: p1 = next((p for p in provinces if p.get('province_code') == 1), None)
        self.assertIsNotNone(p1)

    def test_get_municipalities(self):
        munis = nepal_geo_data.get_municipalities()
        self.assertIsInstance(munis, list)
        self.assertGreater(len(munis), 700)
        
        ktm_munis = nepal_geo_data.get_municipalities("KATHMANDU")
        self.assertGreater(len(ktm_munis), 0)
        # Check known munis
        self.assertTrue(any("Kathmandu" in m or "Budhanilkantha" in m for m in ktm_munis))

    
    
    def test_get_municipality_v3_features(self):
        # Test new metadata integration
        # Use a name we saw in the JSON file earlier: "Bhojpur Municipality"
        muni_name = "Bhojpur Municipality"
        
        muni = nepal_geo_data.get_municipality(muni_name)
        self.assertIsNotNone(muni, f"Could not find {muni_name}")
        
        props = muni['properties']
        # Check Basic
        self.assertEqual(props['gapa_napa'], muni_name)
        
        # Check New v0.3.0 Metadata
        self.assertIn('wards', props)
        self.assertIsInstance(props['wards'], list)
        self.assertIn(1, props['wards'])
        # Bhojpur has 12 wards
        self.assertIn(12, props['wards'])
        
        # Check Website if available
        if 'website' in props:
            self.assertTrue(props['website'].startswith("http"))

    def test_get_wards(self):
        # New function test
        wards = nepal_geo_data.get_wards("Bhojpur Municipality")
        self.assertIsInstance(wards, list)
        self.assertGreaterEqual(len(wards), 12)
        self.assertIn(1, wards)
        self.assertIn(12, wards)
        
        # Test non-existent
        
        # Test non-existent
        self.assertEqual(nepal_geo_data.get_wards("Mars Municipality"), [])

if __name__ == '__main__':
    unittest.main()
