#!/usr/bin/env python3
"""
Demo Data Seeder

Generates realistic demo data for the AI Compliance Platform.
Run this script to populate the database with sample data for pilots and demos.

Usage:
    python seed_data.py [--days 30] [--requests 1000]
"""

import argparse
import hashlib
import os
import random
import sys
from datetime import datetime, timedelta
from uuid import uuid4

import psycopg2
from psycopg2.extras import execute_values

# Configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://compliance_user:change-this-secure-password@localhost:5432/ai_compliance"
)

# Demo data configuration
DEMO_ORGS = [
    {"id": "org-acme", "name": "ACME Corporation"},
    {"id": "org-globex", "name": "Globex Industries"},
    {"id": "org-initech", "name": "Initech"},
]

DEMO_APPS = [
    "customer-support",
    "sales-assistant",
    "hr-chatbot",
    "code-assistant",
    "document-analyzer",
    "email-composer",
    "meeting-summarizer",
    "knowledge-base",
]

DEMO_MODELS = [
    ("gpt-4o", 0.4),
    ("gpt-4-turbo", 0.25),
    ("gpt-3.5-turbo", 0.3),
    ("gpt-4o-mini", 0.05),
]

DEMO_USERS = [
    "user-alice",
    "user-bob",
    "user-charlie",
    "user-diana",
    "user-eve",
    None,  # Anonymous requests
]

PII_TYPES = [
    ("EMAIL", 0.15, "medium"),
    ("PHONE", 0.10, "medium"),
    ("CREDIT_CARD", 0.03, "critical"),
    ("PAN", 0.02, "critical"),
    ("AADHAAR", 0.02, "critical"),
    ("SSN", 0.01, "critical"),
    ("IP_ADDRESS", 0.05, "low"),
    ("DATE_OF_BIRTH", 0.04, "medium"),
]

ACTIONS = {
    "critical": ["blocked"],
    "medium": ["masked", "warned"],
    "low": ["warned", "allowed"],
}


def weighted_choice(choices):
    """Select a random item based on weights."""
    items, weights = zip(*choices)
    return random.choices(items, weights=weights, k=1)[0]


def generate_prompt_hash():
    """Generate a random prompt hash."""
    return hashlib.sha256(str(uuid4()).encode()).hexdigest()


def generate_audit_log(timestamp: datetime, org_id: str) -> dict:
    """Generate a single audit log entry."""
    app_id = random.choice(DEMO_APPS)
    user_id = random.choice(DEMO_USERS)
    model = weighted_choice(DEMO_MODELS)
    
    # Determine if this request has PII
    risk_flags = []
    action = "allowed"
    max_severity = "none"
    
    for pii_type, probability, severity in PII_TYPES:
        if random.random() < probability:
            risk_flags.append(pii_type)
            if severity == "critical" or (severity == "medium" and max_severity != "critical"):
                max_severity = severity
            elif severity == "low" and max_severity == "none":
                max_severity = severity
    
    if risk_flags and max_severity != "none":
        action = random.choice(ACTIONS[max_severity])
    
    # Generate realistic token counts
    token_input = random.randint(50, 800)
    token_output = random.randint(20, 500)
    latency = random.randint(200, 3000)
    
    metadata = {"action": action}
    if risk_flags:
        metadata["violations"] = risk_flags
    
    return {
        "id": str(uuid4()),
        "org_id": org_id,
        "app_id": app_id,
        "user_id": user_id,
        "model": model,
        "provider": "openai",
        "prompt_hash": generate_prompt_hash(),
        "token_count_input": token_input,
        "token_count_output": token_output,
        "latency_ms": latency,
        "risk_flags": risk_flags,
        "metadata": metadata,
        "created_at": timestamp,
    }


def seed_database(days: int = 30, requests_per_day: int = 100):
    """Seed the database with demo data."""
    print(f"Connecting to database...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Create organizations
        print("Creating demo organizations...")
        for org in DEMO_ORGS:
            cur.execute(
                """
                INSERT INTO organizations (id, name)
                VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                """,
                (org["id"], org["name"])
            )
        
        # Generate audit logs
        print(f"Generating {days} days of audit logs...")
        end_date = datetime.utcnow()
        logs = []
        
        for day in range(days):
            date = end_date - timedelta(days=day)
            # Vary requests per day (weekends have fewer)
            day_of_week = date.weekday()
            daily_requests = requests_per_day
            if day_of_week >= 5:  # Weekend
                daily_requests = int(requests_per_day * 0.3)
            
            # Add some variance
            daily_requests = int(daily_requests * random.uniform(0.7, 1.3))
            
            for _ in range(daily_requests):
                # Random time during the day (business hours weighted)
                hour = random.choices(
                    range(24),
                    weights=[1, 1, 1, 1, 1, 2, 3, 5, 8, 10, 10, 8, 6, 8, 10, 10, 8, 5, 3, 2, 1, 1, 1, 1],
                    k=1
                )[0]
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                timestamp = date.replace(hour=hour, minute=minute, second=second)
                org_id = random.choice([o["id"] for o in DEMO_ORGS])
                
                log = generate_audit_log(timestamp, org_id)
                logs.append(log)
        
        # Batch insert logs
        print(f"Inserting {len(logs)} audit logs...")
        
        # Convert to tuples for execute_values
        log_tuples = [
            (
                log["id"],
                log["org_id"],
                log["app_id"],
                log["user_id"],
                log["model"],
                log["provider"],
                log["prompt_hash"],
                log["token_count_input"],
                log["token_count_output"],
                log["latency_ms"],
                psycopg2.extras.Json(log["risk_flags"]),
                psycopg2.extras.Json(log["metadata"]),
                log["created_at"],
            )
            for log in logs
        ]
        
        execute_values(
            cur,
            """
            INSERT INTO audit_logs (
                id, org_id, app_id, user_id, model, provider, prompt_hash,
                token_count_input, token_count_output, latency_ms,
                risk_flags, metadata, created_at
            ) VALUES %s
            ON CONFLICT (id) DO NOTHING
            """,
            log_tuples,
        )
        
        conn.commit()
        
        # Print summary
        cur.execute("SELECT COUNT(*) FROM audit_logs")
        total_logs = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM audit_logs WHERE jsonb_array_length(risk_flags) > 0")
        total_violations = cur.fetchone()[0]
        
        print(f"\n✅ Demo data seeded successfully!")
        print(f"   Total audit logs: {total_logs:,}")
        print(f"   Total violations: {total_violations:,}")
        print(f"   Organizations: {len(DEMO_ORGS)}")
        print(f"   Applications: {len(DEMO_APPS)}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        sys.exit(1)


def clear_demo_data():
    """Clear all demo data from the database."""
    print("Clearing demo data...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Delete audit logs for demo orgs
        for org in DEMO_ORGS:
            cur.execute("DELETE FROM audit_logs WHERE org_id = %s", (org["id"],))
        
        conn.commit()
        print("✅ Demo data cleared!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Seed demo data for AI Compliance Platform")
    parser.add_argument("--days", type=int, default=30, help="Number of days of data to generate")
    parser.add_argument("--requests", type=int, default=100, help="Average requests per day")
    parser.add_argument("--clear", action="store_true", help="Clear existing demo data first")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_demo_data()
    
    seed_database(days=args.days, requests_per_day=args.requests)


if __name__ == "__main__":
    main()


