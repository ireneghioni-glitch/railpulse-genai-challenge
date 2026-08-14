import sqlite3

conn = sqlite3.connect("railpulse.db")
cursor = conn.cursor()

# 1. check if there are stations for Antwerp.
cursor.execute("SELECT stop_id, stop_name FROM stops WHERE LOWER(stop_name) LIKE '%antwer%' LIMIT 5;")
print("🚉 Stazioni Anversa trovate:", cursor.fetchall())

# 2. check how many dates there are in `calendar_dates` for Mondays (`%w = '1'`).
cursor.execute("""
    SELECT COUNT(*) 
    FROM calendar_dates 
    WHERE exception_type = 1 
      AND strftime('%w', substr(date, 1, 4) || '-' || substr(date, 5, 2) || '-' || substr(date, 7, 2)) = '1';
""")
print("📅 Giorni Lunedì trovati in 'calendar_dates':", cursor.fetchone()[0])

# 3. check if the 'calendar' table exists and contains data for Monday.
try:
    cursor.execute("SELECT COUNT(*) FROM calendar WHERE monday = 1 OR monday = '1';")
    print("📅 Servizi del Lunedì trovati in tabella 'calendar':", cursor.fetchone()[0])
except Exception as e:
    print("⚠️ Tabella 'calendar' non presente o vuota:", e)

conn.close()