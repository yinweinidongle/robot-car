import sqlite3
import json
import os
import datetime

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'vehicle_settings.db')

def init_db():
    """Initialize the SQLite database with the vehicle_settings table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create vehicle_settings table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicle_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_name TEXT NOT NULL,
        longitude_offset REAL DEFAULT 0,
        latitude_offset REAL DEFAULT 0,
        line_width REAL DEFAULT 2,
        line_color TEXT DEFAULT '#0000FF'
    )
    ''')
    
    # Create offset_history table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS offset_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER NOT NULL,
        vehicle_name TEXT NOT NULL,
        longitude_offset REAL NOT NULL,
        latitude_offset REAL NOT NULL,
        timestamp TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (vehicle_id) REFERENCES vehicle_settings (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_all_vehicles():
    """Get all vehicle settings from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM vehicle_settings ORDER BY id')
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'vehicle_name': row['vehicle_name'],
            'longitude_offset': row['longitude_offset'],
            'latitude_offset': row['latitude_offset'],
            'line_width': row['line_width'],
            'line_color': row['line_color']
        })
    
    conn.close()
    return results

def get_vehicle_by_id(vehicle_id):
    """Get vehicle settings by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM vehicle_settings WHERE id = ?', (vehicle_id,))
    row = cursor.fetchone()
    
    if row:
        result = {
            'id': row['id'],
            'vehicle_name': row['vehicle_name'],
            'longitude_offset': row['longitude_offset'],
            'latitude_offset': row['latitude_offset'],
            'line_width': row['line_width'],
            'line_color': row['line_color']
        }
    else:
        result = None
    
    conn.close()
    return result

def add_vehicle(vehicle_data):
    """Add a new vehicle setting to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO vehicle_settings (vehicle_name, longitude_offset, latitude_offset, line_width, line_color) VALUES (?, ?, ?, ?, ?)',
        (
            vehicle_data['vehicle_name'],
            vehicle_data.get('longitude_offset', 0),
            vehicle_data.get('latitude_offset', 0),
            vehicle_data.get('line_width', 2),
            vehicle_data.get('line_color', '#0000FF')
        )
    )
    
    vehicle_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return vehicle_id

def update_vehicle(vehicle_id, vehicle_data):
    """Update an existing vehicle setting in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        '''UPDATE vehicle_settings SET 
           vehicle_name = ?, 
           longitude_offset = ?, 
           latitude_offset = ?, 
           line_width = ?, 
           line_color = ? 
           WHERE id = ?''',
        (
            vehicle_data['vehicle_name'],
            vehicle_data.get('longitude_offset', 0),
            vehicle_data.get('latitude_offset', 0),
            vehicle_data.get('line_width', 2),
            vehicle_data.get('line_color', '#0000FF'),
            vehicle_id
        )
    )
    
    conn.commit()
    conn.close()
    
    return cursor.rowcount > 0

def delete_vehicle(vehicle_id):
    """Delete a vehicle setting from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM vehicle_settings WHERE id = ?', (vehicle_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def record_offset_history(vehicle_id, vehicle_name, longitude_offset, latitude_offset, notes=None):
    """Record an offset setting history entry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Current timestamp in ISO format
    timestamp = datetime.datetime.now().isoformat()
    
    cursor.execute(
        'INSERT INTO offset_history (vehicle_id, vehicle_name, longitude_offset, latitude_offset, timestamp, notes) VALUES (?, ?, ?, ?, ?, ?)',
        (vehicle_id, vehicle_name, longitude_offset, latitude_offset, timestamp, notes)
    )
    
    history_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return history_id

def get_offset_history(page=1, page_size=10):
    """Get offset history with pagination."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) as count FROM offset_history')
    total_count = cursor.fetchone()['count']
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get paginated history
    cursor.execute(
        'SELECT * FROM offset_history ORDER BY timestamp DESC LIMIT ? OFFSET ?',
        (page_size, offset)
    )
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'vehicle_id': row['vehicle_id'],
            'vehicle_name': row['vehicle_name'],
            'longitude_offset': row['longitude_offset'],
            'latitude_offset': row['latitude_offset'],
            'timestamp': row['timestamp'],
            'notes': row['notes']
        })
    
    conn.close()
    return {
        'records': results,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size
    }

def get_vehicle_offset_history(vehicle_id, page=1, page_size=10):
    """Get offset history for a specific vehicle with pagination."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get total count for this vehicle
    cursor.execute('SELECT COUNT(*) as count FROM offset_history WHERE vehicle_id = ?', (vehicle_id,))
    total_count = cursor.fetchone()['count']
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get paginated history for this vehicle
    cursor.execute(
        'SELECT * FROM offset_history WHERE vehicle_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?',
        (vehicle_id, page_size, offset)
    )
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'vehicle_id': row['vehicle_id'],
            'vehicle_name': row['vehicle_name'],
            'longitude_offset': row['longitude_offset'],
            'latitude_offset': row['latitude_offset'],
            'timestamp': row['timestamp'],
            'notes': row['notes']
        })
    
    conn.close()
    return {
        'records': results,
        'total': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size
    }

# Initialize database when the module is imported
init_db()

# Add default vehicle if none exists
def add_default_vehicles():
    vehicles = get_all_vehicles()
    if not vehicles:
        default_vehicles = [
            {
                'vehicle_name': '1',
                'longitude_offset': 0,
                'latitude_offset': 0,
                'line_width': 2,
                'line_color': '#FF0000'
            },
            {
                'vehicle_name': '2',
                'longitude_offset': 0,
                'latitude_offset': 0,
                'line_width': 2,
                'line_color': '#0000FF'
            },
            {
                'vehicle_name': '3',
                'longitude_offset': 0,
                'latitude_offset': 0,
                'line_width': 2,
                'line_color': '#00FF00'
            },
            {
                'vehicle_name': '4',
                'longitude_offset': 0,
                'latitude_offset': 0,
                'line_width': 2,
                'line_color': '#FFA500'
            },
            {
                'vehicle_name': '5',
                'longitude_offset': 0,
                'latitude_offset': 0,
                'line_width': 2,
                'line_color': '#800080'
            },
            {
                'vehicle_name': '6',
                'longitude_offset': 0,
                'latitude_offset': 0,
                'line_width': 2,
                'line_color': '#00FFFF'
            },
            {
                'vehicle_name': '7',
                'longitude_offset': 0,
                'latitude_offset': 0,
                'line_width': 2,
                'line_color': '#FF00FF'
            }
        ]
        
        for vehicle in default_vehicles:
            add_vehicle(vehicle)

# Add default vehicles when module is loaded
add_default_vehicles() 