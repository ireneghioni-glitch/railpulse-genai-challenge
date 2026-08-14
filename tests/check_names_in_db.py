import sqlite3

conn = sqlite3.connect("railpulse.db")
cursor = conn.cursor()

print("🔍 Ricerca Stazioni nel DB:\n")

# Cercamo Anversa (Anvers)
cursor.execute("SELECT stop_name FROM stops WHERE LOWER(stop_name) LIKE '%anvers%' LIMIT 5;")
print("Anversa (Anvers):", cursor.fetchall())

# Cerchiamo Gand (Gand / Gent)
cursor.execute("SELECT stop_name FROM stops WHERE LOWER(stop_name) LIKE '%gand%' OR LOWER(stop_name) LIKE '%gent%' LIMIT 5;")
print("Gand (Gent/Gand):", cursor.fetchall())

# Cerchiamo Bruges (Bruges / Brugge)
cursor.execute("SELECT stop_name FROM stops WHERE LOWER(stop_name) LIKE '%brug%' LIMIT 5;")
print("Bruges (Brugge/Bruges):", cursor.fetchall())

# Vediamo 10 stazioni a caso per capire la sintassi usata
cursor.execute("SELECT stop_name FROM stops LIMIT 10;")
print("\nEsempio di 10 stazioni a caso nel DB:", cursor.fetchall())

conn.close()