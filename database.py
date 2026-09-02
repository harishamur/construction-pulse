"""Database layer for India Construction & Infra Intelligence Hub (₹).
Provides SQLite storage for Investment Opportunities and Industry Events/Deadlines.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "construction_intel.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a SQLite connection configured with sqlite3.Row for dict-like access."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Creates tables and indexes for investment opportunities and industry events."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # 1. Investment Opportunities Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investment_opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT UNIQUE NOT NULL,
        published_date TEXT,
        summary TEXT,
        sub_sector TEXT,
        estimated_capex_cr REAL,
        beneficiary_tickers TEXT,
        investment_thesis TEXT,
        impact_score INTEGER CHECK(impact_score BETWEEN 1 AND 5),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_url ON investment_opportunities(url);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_sub_sector ON investment_opportunities(sub_sector);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_impact ON investment_opportunities(impact_score);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_capex ON investment_opportunities(estimated_capex_cr);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_opp_date ON investment_opportunities(published_date);")
    
    # 2. Events Tracker Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events_tracker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT NOT NULL,
        organizer TEXT,
        category TEXT,
        last_application_date TEXT,
        event_dates TEXT,
        url TEXT UNIQUE NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_url ON events_tracker(url);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_deadline ON events_tracker(last_application_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events_tracker(category);")
    
    conn.commit()
    conn.close()


# =========================================================================
# Investment Opportunities CRUD
# =========================================================================

def insert_investment_opportunity(opp: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """
    Inserts an investment opportunity if URL is unique.
    Returns True if newly inserted, False if URL already exists or invalid.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    raw_impact = opp.get("impact_score", 3)
    try:
        impact_score = max(1, min(5, int(raw_impact)))
    except (ValueError, TypeError):
        impact_score = 3
        
    capex = opp.get("estimated_capex_cr")
    if capex is not None:
        try:
            capex = float(capex)
        except (ValueError, TypeError):
            capex = None

    try:
        cursor.execute("""
        INSERT INTO investment_opportunities (
            title, url, published_date, summary, sub_sector, 
            estimated_capex_cr, beneficiary_tickers, investment_thesis, impact_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opp.get("title", "").strip(),
            opp.get("url", "").strip(),
            opp.get("published_date", datetime.utcnow().strftime("%Y-%m-%d")),
            opp.get("summary", "").strip(),
            opp.get("sub_sector", "General Infra").strip(),
            capex,
            opp.get("beneficiary_tickers", "").strip(),
            opp.get("investment_thesis", "").strip(),
            impact_score
        ))
        conn.commit()
        inserted = True
    except sqlite3.IntegrityError:
        inserted = False
    finally:
        conn.close()
        
    return inserted


def insert_many_investments(opps: List[Dict[str, Any]], db_path: Optional[str] = None) -> int:
    """Batch inserts investment opportunities, returning count of newly added items."""
    count = 0
    for opp in opps:
        if insert_investment_opportunity(opp, db_path):
            count += 1
    return count


def get_investments(
    sub_sectors: Optional[List[str]] = None,
    min_capex: float = 0.0,
    min_impact: int = 1,
    max_impact: int = 5,
    beneficiary: Optional[str] = None,
    search_query: Optional[str] = None,
    sort_by: str = "impact_desc",
    limit: int = 250,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves filtered investment opportunities from the database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    query = "SELECT * FROM investment_opportunities WHERE impact_score BETWEEN ? AND ?"
    params: List[Any] = [min_impact, max_impact]
    
    if min_capex > 0:
        query += " AND (estimated_capex_cr >= ? OR estimated_capex_cr IS NULL)"
        params.append(min_capex)
        
    if sub_sectors and "All" not in sub_sectors:
        placeholders = ",".join(["?"] * len(sub_sectors))
        query += f" AND sub_sector IN ({placeholders})"
        params.extend(sub_sectors)
        
    if beneficiary and beneficiary.strip():
        query += " AND beneficiary_tickers LIKE ?"
        params.append(f"%{beneficiary.strip()}%")
        
    if search_query and search_query.strip():
        query += " AND (title LIKE ? OR summary LIKE ? OR investment_thesis LIKE ? OR beneficiary_tickers LIKE ?)"
        term = f"%{search_query.strip()}%"
        params.extend([term, term, term, term])
        
    if sort_by == "impact_desc":
        query += " ORDER BY impact_score DESC, estimated_capex_cr DESC NULLS LAST, published_date DESC, id DESC"
    elif sort_by == "capex_desc":
        query += " ORDER BY estimated_capex_cr DESC NULLS LAST, impact_score DESC, published_date DESC, id DESC"
    elif sort_by == "date_desc":
        query += " ORDER BY published_date DESC, impact_score DESC, id DESC"
    elif sort_by == "date_asc":
        query += " ORDER BY published_date ASC, id ASC"
    else:
        query += " ORDER BY impact_score DESC, id DESC"
        
    query += " LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


# =========================================================================
# Events & Deadlines Tracker CRUD
# =========================================================================

def insert_event(event: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Inserts an industry event if URL is unique. Returns True if inserted."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO events_tracker (
            event_name, organizer, category, last_application_date, 
            event_dates, url, details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get("event_name", "").strip(),
            event.get("organizer", "").strip(),
            event.get("category", "Expo/Conference").strip(),
            event.get("last_application_date", "").strip(),
            event.get("event_dates", "").strip(),
            event.get("url", "").strip(),
            event.get("details", "").strip()
        ))
        conn.commit()
        inserted = True
    except sqlite3.IntegrityError:
        inserted = False
    finally:
        conn.close()
        
    return inserted


def insert_many_events(events: List[Dict[str, Any]], db_path: Optional[str] = None) -> int:
    """Batch inserts events, returning count of newly added entries."""
    count = 0
    for evt in events:
        if insert_event(evt, db_path):
            count += 1
    return count


def get_upcoming_events(
    category: Optional[str] = None,
    organizer: Optional[str] = None,
    only_active: bool = False,
    current_date: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves events sorted chronologically by last_application_date ASC.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    query = "SELECT * FROM events_tracker WHERE 1=1"
    params: List[Any] = []
    
    ref_date = current_date or datetime.utcnow().strftime("%Y-%m-%d")
    
    if only_active:
        query += " AND last_application_date >= ?"
        params.append(ref_date)
        
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
        
    if organizer and organizer != "All":
        query += " AND organizer = ?"
        params.append(organizer)
        
    query += " ORDER BY last_application_date ASC, id ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


# =========================================================================
# Aggregate Metrics & Analytics
# =========================================================================

def get_intel_metrics(current_date: Optional[str] = None, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Computes comprehensive executive KPI metrics for the India Construction Pulse."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    ref_date = current_date or datetime.utcnow().strftime("%Y-%m-%d")
    
    # 1. Total Opportunities & Capex Pipeline
    cursor.execute("SELECT COUNT(*) as total, SUM(estimated_capex_cr) as total_capex FROM investment_opportunities")
    row_opp = cursor.fetchone()
    total_opportunities = row_opp["total"] or 0
    total_pipeline_capex_cr = round(row_opp["total_capex"] or 0.0, 2)
    
    # 2. High-Impact Count (>= 4)
    cursor.execute("SELECT COUNT(*) as high_cnt FROM investment_opportunities WHERE impact_score >= 4")
    high_impact_count = cursor.fetchone()["high_cnt"] or 0
    
    # 3. Active Upcoming Deadlines
    cursor.execute("SELECT COUNT(*) as active_deadlines FROM events_tracker WHERE last_application_date >= ?", (ref_date,))
    active_deadlines_count = cursor.fetchone()["active_deadlines"] or 0
    
    # 4. Sub-Sector Breakdown (Capex & Count)
    cursor.execute("""
        SELECT sub_sector, COUNT(*) as count, SUM(estimated_capex_cr) as capex 
        FROM investment_opportunities 
        GROUP BY sub_sector 
        ORDER BY capex DESC NULLS LAST, count DESC
    """)
    sub_sector_stats = []
    sub_sector_capex = {}
    sub_sector_counts = {}
    for r in cursor.fetchall():
        sub_sector_stats.append({
            "sub_sector": r["sub_sector"],
            "count": r["count"],
            "capex_cr": round(r["capex"] or 0.0, 2)
        })
        sub_sector_capex[r["sub_sector"]] = round(r["capex"] or 0.0, 2)
        sub_sector_counts[r["sub_sector"]] = r["count"]
        
    # 5. Top Mentioned Beneficiary Companies
    cursor.execute("SELECT beneficiary_tickers FROM investment_opportunities WHERE beneficiary_tickers IS NOT NULL AND beneficiary_tickers != ''")
    company_counts: Dict[str, int] = {}
    for r in cursor.fetchall():
        tickers = [t.strip() for t in r["beneficiary_tickers"].split(",") if t.strip()]
        for t in tickers:
            company_counts[t] = company_counts.get(t, 0) + 1
            
    sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
    top_beneficiaries = dict(sorted_companies[:8])
    
    # 6. Impact Score Distribution
    cursor.execute("""
        SELECT impact_score, COUNT(*) as count 
        FROM investment_opportunities 
        GROUP BY impact_score 
        ORDER BY impact_score ASC
    """)
    impact_counts = {r["impact_score"]: r["count"] for r in cursor.fetchall()}
    for s in range(1, 6):
        if s not in impact_counts:
            impact_counts[s] = 0
            
    conn.close()
    
    return {
        "total_opportunities": total_opportunities,
        "total_pipeline_capex_cr": total_pipeline_capex_cr,
        "high_impact_count": high_impact_count,
        "active_deadlines_count": active_deadlines_count,
        "sub_sector_stats": sub_sector_stats,
        "sub_sector_capex": sub_sector_capex,
        "sub_sector_counts": sub_sector_counts,
        "top_beneficiaries": top_beneficiaries,
        "impact_counts": impact_counts
    }
