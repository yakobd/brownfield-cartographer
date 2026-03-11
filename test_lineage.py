from src.analyzers.sql_lineage import SQLLineageAnalyzer

analyzer = SQLLineageAnalyzer()

# Test Case: Complex dbt-like query with CTEs and an Insert
sql = """
WITH user_summary AS (
    SELECT user_id, count(*) as login_count 
    FROM raw.login_events 
    GROUP BY 1
)
INSERT INTO mart.user_metrics
SELECT 
    u.user_id, 
    s.login_count, 
    u.email
FROM staging.users u
JOIN user_summary s ON u.user_id = s.user_id
"""

lineage = analyzer.extract_lineage(sql, "postgres")
print(f"Sources: {lineage['sources']}") # Should be ['raw.login_events', 'staging.users']
print(f"Sinks:   {lineage['sinks']}")   # Should be ['mart.user_metrics']