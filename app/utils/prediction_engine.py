import os
import json
import re
from pymongo import MongoClient

class JudicialPredictor:
    def __init__(self, dataset_path="datasets/high_court_metadata/json"):
        self.dataset_path = dataset_path
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client["naya_court_db"]
        self.analysis_col = self.db["historical_analysis"]

    def _extract_data_from_html(self, html_content):
        """Extract key metrics from the raw_html field in the dataset."""
        data = {}
        # Simple regex for CNR, Dates, and Disposal
        cnr_match = re.search(r'CNR :</span><font color=\'green\'>\s*([^<]+)', html_content)
        reg_date_match = re.search(r'Date of registration :</span><font color=\'green\'>\s*([^<]+)', html_content)
        decision_date_match = re.search(r'Decision Date :</span><font color=\'green\'>\s*([^<]+)', html_content)
        disposal_match = re.search(r'Disposal Nature :</span><font color=\'green\'>\s*([^<]+)', html_content)
        
        if cnr_match: data['cnr'] = cnr_match.group(1).strip()
        if reg_date_match: data['reg_date'] = reg_date_match.group(1).strip()
        if decision_date_match: data['decision_date'] = decision_date_match.group(1).strip()
        if disposal_match: data['disposal_nature'] = disposal_match.group(1).strip()
        
        return data

    def get_outcome_stats(self, query_string):
        """Find historical patterns matching the query."""
        # In a real app, we'd use a massive index. 
        # Here we simulate by sampling recent records from the dataset.
        results = []
        sample_limit = 50
        count = 0
        
        # Walk through a specific year (e.g. 2000) for demo speed
        demo_path = os.path.join(self.dataset_path, "year=2000", "court=24_17", "bench=gujarathc")
        
        if os.path.exists(demo_path):
            for filename in os.listdir(demo_path):
                if filename.endswith(".json"):
                    with open(os.path.join(demo_path, filename), "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        parsed = self._extract_data_from_html(meta.get("raw_html", ""))
                        if parsed:
                            results.append(parsed)
                            count += 1
                if count >= sample_limit: break

        # Aggregation
        stats = {
            "total_analyzed": len(results),
            "disposal_distribution": {},
            "avg_duration_days": 0,
            "likely_outcome": "Pending Analysis"
        }
        
        durations = []
        for r in results:
            dn = r.get("disposal_nature", "Unknown")
            stats["disposal_distribution"][dn] = stats["disposal_distribution"].get(dn, 0) + 1
            
            # Duration calculation
            try:
                from datetime import datetime
                d1 = datetime.strptime(r['reg_date'], "%d-%m-%Y")
                d2 = datetime.strptime(r['decision_date'], "%d-%m-%Y")
                durations.append((d2 - d1).days)
            except:
                pass

        if durations:
            stats["avg_duration_days"] = int(sum(durations) / len(durations))

        # Determine "Likely Outcome"
        if stats["disposal_distribution"]:
            top_outcome = max(stats["disposal_distribution"], key=stats["disposal_distribution"].get)
            stats["likely_outcome"] = top_outcome

        return stats

predictor_engine = JudicialPredictor()
