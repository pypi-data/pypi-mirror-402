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
        self.assertEqual(len(districts), 77)
        # Check backward compatibility (UPPERCASE)
        self.assertIn("KATHMANDU", districts)
        self.assertIn("JHAPA", districts)
        
    def test_get_district(self):
        # Case insensitive check
        district = nepal_geo_data.get_district("kathmandu")
        self.assertIsNotNone(district)
        # Check backward compatibility key
        self.assertEqual(district['properties']['DISTRICT'], "KATHMANDU")
        # Check new key
        self.assertEqual(district['properties']['district_name_en'], "Kathmandu")
        self.assertTrue('district_name_np' in district['properties'])
        
        # Non-existent
        self.assertIsNone(nepal_geo_data.get_district("NonExistentDistrict"))

    def test_get_boundaries(self):
        geom = nepal_geo_data.get_boundaries("JHAPA")
        self.assertIsNotNone(geom)
        self.assertTrue(geom['type'] in ["Polygon", "MultiPolygon"])

    def test_province_districts(self):
        # Province 1 districts (JHAPA is in Province 1)
        p1 = nepal_geo_data.get_province_districts(1)
        self.assertIn("JHAPA", p1)
        
    def test_get_provinces(self):
        provinces = nepal_geo_data.get_provinces()
        self.assertIsInstance(provinces, list)
        self.assertEqual(len(provinces), 7)
        
        # Check for Prov 1 details - new schema
        # New keys: province_code, province_name_en, province_name_np
        p1 = next((p for p in provinces if str(p.get('province_code')) == "1"), None)
        if not p1:
             p1 = next((p for p in provinces if p.get('province_code') == 1), None)
             
        self.assertIsNotNone(p1)
        self.assertIn("Province No. 1", p1['province_name_en']) 

    def test_get_municipalities(self):
        munis = nepal_geo_data.get_municipalities()
        self.assertIsInstance(munis, list)
        self.assertGreater(len(munis), 700) # There are 753 local levels
        
        # Filter by district (KATHMANDU)
        ktm_munis = nepal_geo_data.get_municipalities("KATHMANDU")
        self.assertGreater(len(ktm_munis), 0)
        # Kathmandu Metropolitan City should be there
        self.assertTrue(any("Kathmandu" in m for m in ktm_munis))
        
    def test_get_municipality(self):
        # Search for Kathmandu Metropolitan City (exact name might vary in data, usually "Kathmandu Metropolitan City")
        # Let's search for something generic or specific if we know exact name
        # In the data snippet or just pick one from the list in previous test step if I could run it interactive.
        # But I'll assume "Kathmandu Metropolitan City" or "Kathmandu" exists as 'gapa_napa'
        
        # Actually safer to get list first then check
         pass

    def test_municipality_logic(self):
        # Retrieve all
        all_munis = nepal_geo_data.get_municipalities()
        first_muni = all_munis[0]
        
        # Get data for that muni
        muni_data = nepal_geo_data.get_municipality(first_muni)
        self.assertIsNotNone(muni_data)
        self.assertEqual(muni_data['properties']['gapa_napa'], first_muni)

if __name__ == '__main__':
    unittest.main()
