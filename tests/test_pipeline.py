"""Automated Unit & Integration Tests for India Construction & Infra Intelligence Hub (₹)."""

import os
import unittest
import tempfile
import sqlite3
from datetime import datetime, timedelta

from database import (
    init_db, 
    insert_investment_opportunity, 
    insert_many_investments, 
    get_investments, 
    insert_event, 
    insert_many_events, 
    get_upcoming_events, 
    get_intel_metrics
)
from collector import (
    detect_sub_sector, 
    extract_capex_cr, 
    extract_beneficiary_tickers, 
    calculate_impact_score, 
    generate_investment_thesis,
    clean_html
)


class TestDatabaseLayer(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_schema_tables_exist(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='investment_opportunities';")
        self.assertIsNotNone(cursor.fetchone())
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events_tracker';")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_investment_insert_and_deduplication(self):
        opp = {
            "title": "NHAI Awards ₹4,200 Cr Highway Package",
            "url": "https://example.com/nhai-pkg1",
            "published_date": "2026-09-01",
            "summary": "HAM concession for 80 km 6-lane road.",
            "sub_sector": "Roads & Highways",
            "estimated_capex_cr": 4200.0,
            "beneficiary_tickers": "PNC Infratech, KNR Constructions",
            "investment_thesis": "HAM concession guarantees 40% upfront funding and stable annuities.",
            "impact_score": 4
        }
        
        # 1st insert
        self.assertTrue(insert_investment_opportunity(opp, self.db_path))
        # Duplicate insert
        self.assertFalse(insert_investment_opportunity(opp, self.db_path))
        
        results = get_investments(db_path=self.db_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["estimated_capex_cr"], 4200.0)
        self.assertIn("PNC Infratech", results[0]["beneficiary_tickers"])

    def test_events_insert_and_deadline_filtering(self):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        past_date = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")
        future_date = (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d")
        
        event_active = {
            "event_name": "CTAI National ConTech Hackathon",
            "organizer": "CTAI",
            "category": "Hackathon/Pitch",
            "last_application_date": future_date,
            "event_dates": "Sept 20-22, 2026",
            "url": "https://ctai.in/hackathon",
            "details": "AI in preconstruction challenge."
        }
        event_expired = {
            "event_name": "Old Expired Summit",
            "organizer": "CII",
            "category": "Expo/Conference",
            "last_application_date": past_date,
            "event_dates": "August 10, 2026",
            "url": "https://cii.in/old-summit",
            "details": "Concluded summit."
        }
        
        insert_many_events([event_active, event_expired], self.db_path)
        
        all_events = get_upcoming_events(only_active=False, current_date=today, db_path=self.db_path)
        self.assertEqual(len(all_events), 2)
        
        active_events = get_upcoming_events(only_active=True, current_date=today, db_path=self.db_path)
        self.assertEqual(len(active_events), 1)
        self.assertEqual(active_events[0]["event_name"], "CTAI National ConTech Hackathon")

    def test_metrics_calculation(self):
        opps = [
            {
                "title": "A", "url": "https://a.com", "sub_sector": "Railways & Metro", 
                "estimated_capex_cr": 10000.0, "beneficiary_tickers": "L&T, RVNL", "impact_score": 5
            },
            {
                "title": "B", "url": "https://b.com", "sub_sector": "Roads & Highways", 
                "estimated_capex_cr": 2500.0, "beneficiary_tickers": "L&T, PNC Infratech", "impact_score": 4
            },
            {
                "title": "C", "url": "https://c.com", "sub_sector": "Cement & Steel", 
                "estimated_capex_cr": 500.0, "beneficiary_tickers": "UltraTech Cement", "impact_score": 3
            }
        ]
        insert_many_investments(opps, self.db_path)
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        metrics = get_intel_metrics(current_date=today, db_path=self.db_path)
        
        self.assertEqual(metrics["total_opportunities"], 3)
        self.assertEqual(metrics["total_pipeline_capex_cr"], 13000.0)
        self.assertEqual(metrics["high_impact_count"], 2)
        self.assertEqual(metrics["top_beneficiaries"]["L&T"], 2)


class TestCollectorExtraction(unittest.TestCase):
    def test_capex_extraction(self):
        # ₹ Crore variations
        c1 = extract_capex_cr("Cabinet approves ₹24,650 Cr expansion of Bengaluru Metro")
        self.assertEqual(c1, 24650.0)
        
        c2 = extract_capex_cr("NHAI awards project worth Rs 4,500 crore in UP")
        self.assertEqual(c2, 4500.0)
        
        # Lakh crore
        c3 = extract_capex_cr("National highway plan of Rs 1.5 lakh crore unveiled")
        self.assertEqual(c3, 150000.0)
        
        # USD Billion conversion (~8,300 Cr per $1B)
        c4 = extract_capex_cr("International consortium secures $2 billion port development")
        self.assertEqual(c4, 16600.0)

    def test_sub_sector_classification(self):
        sec_road = detect_sub_sector("NHAI invites tenders for 6-lane greenfield expressway", "")
        self.assertEqual(sec_road, "Roads & Highways")
        
        sec_rail = detect_sub_sector("Indian Railways clears Vande Bharat sleeper rake manufacturing", "")
        self.assertEqual(sec_rail, "Railways & Metro")
        
        sec_cement = detect_sub_sector("UltraTech Cement expands clinker production in Rajasthan", "")
        self.assertEqual(sec_cement, "Cement & Steel")
        
        sec_re = detect_sub_sector("DLF achieves record pre-sales in Gurugram luxury housing", "")
        self.assertEqual(sec_re, "Real Estate & REITs")

    def test_beneficiary_ticker_extraction(self):
        tickers = extract_beneficiary_tickers(
            "L&T and NCC joint venture secures major package", 
            "UltraTech Cement to supply materials."
        )
        self.assertIn("L&T", tickers)
        self.assertIn("NCC", tickers)
        self.assertIn("UltraTech Cement", tickers)

    def test_impact_score_computation(self):
        # Mega capex (> 5000 Cr) -> 5
        score_5 = calculate_impact_score(12500.0, "Mega Corridor Approved", "Summary")
        self.assertEqual(score_5, 5)
        
        # High capex (1000 - 5000 Cr) -> 4
        score_4 = calculate_impact_score(3200.0, "Expressway Package", "Summary")
        self.assertEqual(score_4, 4)
        
        # Moderate capex (100 - 1000 Cr) -> 3
        score_3 = calculate_impact_score(450.0, "Urban Flyover", "Summary")
        self.assertEqual(score_3, 3)

    def test_url_live_verification(self):
        from collector import verify_url_live
        # Test valid URL
        ok, valid_url = verify_url_live("https://credai.org/")
        self.assertTrue(ok)
        self.assertTrue(valid_url.startswith("http"))
        
        # Test 404 URL -> auto-heals to domain root or search fallback
        ok, healed_url = verify_url_live("https://ctai.in/fake-broken-path-12345", title="ConTech Hackathon")
        self.assertTrue(ok)
        self.assertTrue(healed_url.startswith("https://"))


if __name__ == "__main__":
    unittest.main()

