from db_service import get_db_schema

if __name__ == "__main__":
    print("--- Testing Database Schema Extraction ---\n")
    try:
        schema = get_db_schema()
        print(schema)
        print("\n[OK] Schema extraction successful")
    except Exception as e:
        print(f"[ERROR] Error extracting schema: {e}")





'''
=================================== TEST OUTPUT ===================================

--- Testing Database Schema Extraction ---

Table: agency
  - agency_fare_url (TEXT)
  - agency_id (TEXT)
  - agency_lang (TEXT)
  - agency_name (TEXT)
  - agency_phone (TEXT)
  - agency_timezone (TEXT)
  - agency_url (TEXT)

Table: calendar
  - end_date (DATE)
  - friday (INTEGER)
  - monday (INTEGER)
  - saturday (INTEGER)
  - service_id (TEXT)
  - start_date (DATE)
  - sunday (INTEGER)
  - thursday (INTEGER)
  - tuesday (INTEGER)
  - wednesday (INTEGER)

Table: routes
  - agency_id (TEXT)
  - route_color (TEXT)
  - route_desc (TEXT)
  - route_id (TEXT)
  - route_long_name (TEXT)
  - route_short_name (TEXT)
  - route_text_color (TEXT)
  - route_type (INTEGER)
  - route_url (TEXT)

Table: stop_times
  - arrival_time (TIME)
  - departure_time (TIME)
  - drop_off_type (INTEGER)
  - pickup_type (INTEGER)
  - shape_dist_traveled (TEXT)
  - stop_headsign (TEXT)
  - stop_id (TEXT)
  - stop_sequence (INTEGER)
  - trip_id (TEXT)

Table: stops
  - location_type (INTEGER)
  - parent_station (TEXT)
  - platform_code (INTEGER)
  - stop_code (TEXT)
  - stop_desc (TEXT)
  - stop_id (TEXT)
  - stop_lat (REAL)
  - stop_lon (REAL)
  - stop_name (TEXT)
  - stop_url (TEXT)
  - wheelchair_boarding (INTEGER)
  - zone_id (TEXT)

Table: trips
  - bikes_allowed (INTEGER)
  - block_id (INTEGER)
  - direction_id (TEXT)
  - route_id (TEXT)
  - service_id (TEXT)
  - shape_id (TEXT)
  - trip_headsign (TEXT)
  - trip_id (TEXT)
  - trip_short_name (INTEGER)
  - wheelchair_accessible (TEXT)

[OK] Schema extraction successful

===================================================================================
'''