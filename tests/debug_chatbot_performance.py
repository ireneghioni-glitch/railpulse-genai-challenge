import sqlite3
import time

conn = sqlite3.connect("railpulse.db")
cursor = conn.cursor()

# 1. verify that indexes really exist in file .db
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';")
indexes = cursor.fetchall()
print(f"📌 Indici trovati nel DB ({len(indexes)}):", [idx[0] for idx in indexes])

# 2. measure execution time of this single SQL query
query = """
WITH station_ids AS (
    -- 1. Filters the station in the small table (stops) and retrieve only the IDs (instantaneous).
    SELECT stop_id 
    FROM stops 
    WHERE LOWER(stop_name) LIKE '%bruxelles-midi%'
),
station_trips AS (
    -- 2. Finds the trip_ids using the numeric index idx_stop_times_stop_id.
    SELECT DISTINCT trip_id 
    FROM stop_times 
    WHERE stop_id IN (SELECT stop_id FROM station_ids)
),
friday_services AS (
    -- 3. Isolates the Friday services.
    SELECT DISTINCT service_id 
    FROM calendar_dates 
    WHERE exception_type = 1 
      AND strftime('%w', substr(date, 1, 4) || '-' || substr(date, 5, 2) || '-' || substr(date, 7, 2)) = '5'
)
-- 4. It only merges datasets that have already been drastically reduced.
SELECT COUNT(DISTINCT t.trip_id)
FROM trips t
JOIN station_trips st ON t.trip_id = st.trip_id
JOIN friday_services fs ON t.service_id = fs.service_id;
"""

# The `stops` table has a few hundred rows, whereas `stop_times` has hundreds of thousands.

# If we instruct SQLite to search for `%bruxelles-midi%` only within the small `stops` 
# table (retrieving the corresponding `stop_id` values ​​and then using the `idx_stop_times_stop_id` index) 
# the query no longer needs to read the stop names; instead, it performs only extremely fast numerical comparisons.

start_time = time.time()
cursor.execute(query)
result = cursor.fetchone()
execution_time = time.time() - start_time

print(f"⏱️ Database Real Execution Time: {execution_time:.4f} secondi")
print(f"📊 Query Result: {result[0]}")
conn.close()




'''
=================================== TEST OUTPUT ===================================

📌 Indici trovati nel DB (6): ['idx_stop_times_trip_id', 'idx_stop_times_stop_id', 'idx_trips_service_id', 'idx_trips_route_id', 'idx_calendar_dates_service', 'idx_stops_name']
⏱️ Database Real Execution Time: 9.0056 secondi
📊 Query Result: 13396

===================================================================================
'''