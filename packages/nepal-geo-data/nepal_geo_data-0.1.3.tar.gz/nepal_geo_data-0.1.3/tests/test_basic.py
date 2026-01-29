import sys
import os
import unittest

# Add package root to path so we can import without installing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import nepal_geo_data

class TestNepalGeoData(unittest.TestCase):
    
    def test_districts_list(self):
        districts = nepal_geo_data.get_districts()
        self.assertIsInstance(districts, list)
        self.assertGreater(len(districts), 0)
        self.assertIn("KATHMANDU", districts) # Assumption based on standard data
        
    def test_get_district(self):
        # Case insensitive check
        district = nepal_geo_data.get_district("kathmandu")
        self.assertIsNotNone(district)
        self.assertEqual(district['properties']['DISTRICT'], "KATHMANDU")
        
        # Non-existent
        self.assertIsNone(nepal_geo_data.get_district("NonExistentDistrict"))

    def test_get_boundaries(self):
        geom = nepal_geo_data.get_boundaries("JHAPA")
        self.assertIsNotNone(geom)
        self.assertEqual(geom['type'], "Polygon")

    def test_province_districts(self):
        # JHAPA is in Province 1 (from our initial view of the file)
        p1 = nepal_geo_data.get_province_districts(1)
        self.assertIn("JHAPA", p1)
        
    def test_get_provinces(self):
        provinces = nepal_geo_data.get_provinces()
        self.assertIsInstance(provinces, list)
        self.assertGreater(len(provinces), 0)
        # Check for Prov 1 details
        p1 = next((p for p in provinces if p['id'] == 1), None)
        self.assertIsNotNone(p1)
        self.assertEqual(p1['capital'], "Biratnagar")

if __name__ == '__main__':
    unittest.main()
