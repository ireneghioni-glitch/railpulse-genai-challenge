"# railpulse-genai-challenge" 

# THINGS TO TEST

## 1. Mapping dei nomi delle stazioni (Inglese ➔ Francese/Olandese)
Servono a verificare se l'LLM converte correttamente i toponimi inglesi in quelli del database GTFS.

* "How many trains depart from Antwerp Central on Mondays?"
Cosa verificare nella SQL: Deve cercare 'Antwerpen%' e usare strftime('%w', ...) = '1'.
* "How many trains pass through Ghent on Fridays?"
Cosa verificare nella SQL: Deve cercare 'Gent%' e usare strftime('%w', ...) = '5'.
* "How many trains stop at Bruges on Saturdays?"
Cosa verificare nella SQL: Deve cercare 'Brugge%' e usare strftime('%w', ...) = '6'.

## 2. Filtri per giorni della settimana e fine settimana
Servono a verificare se la logica di conversione della data (YYYYMMDD ➔ YYYY-MM-DD ➔ %w) funziona su tutti i giorni.

* "How many trains run through Brussels Midi on Sundays?"
Cosa verificare nella SQL: Deve usare strftime('%w', ...) = '0'.
* "How many trains stop at Brussels Central on Wednesdays?"
Cosa verificare nella SQL: Deve usare strftime('%w', ...) = '3'.

## 3. Filtri orari e fasce orarie
Servono a testare la capacità dell'LLM di filtrare la colonna departure_time o arrival_time nella tabella stop_times.

* "How many trains depart from Brussels Midi on Friday between 07:00 and 09:00?"
Cosa verificare nella SQL: Deve includere st.departure_time >= '07:00:00' AND st.departure_time <= '09:00:00'.
* "Which trains arrive at Brussels North after 22:00 on a Saturday?"
Cosa verificare nella SQL: Deve includere st.arrival_time > '22:00:00'.

## 4. Distinzione tra fermate intermedie e capolinea d'origine
Servono a verificare se la regola su stop_sequence = 1 viene applicata soltanto quando richiesto esplicitamente.

* "How many trains originate from Brussels Midi on Fridays?"
Cosa verificare nella SQL: Trattandosi di treni che iniziano la corsa lì, deve includere st.stop_sequence = 1.
* "How many trains serve Brussels Midi on Fridays?"
Cosa verificare nella SQL: Trattandosi di tutti i treni di passaggio, NON deve includere st.stop_sequence = 1.

## 5. Query di aggregazione e classifica (JOIN avanzati)
Servono a testare aggregazioni complesse con GROUP BY, ORDER BY e LIMIT.

* "What are the top 5 busiest stations on Fridays?"
Cosa verificare nella SQL: GROUP BY s.stop_name ORDER BY COUNT(DISTINCT t.trip_id) DESC LIMIT 5.
* "Which route has the highest number of trips on Mondays?"
Cosa verificare nella SQL: JOIN tra routes, trips e calendar_dates con GROUP BY r.route_id.

