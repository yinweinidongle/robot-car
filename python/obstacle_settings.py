import sqlite3
import json
import os

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'obstacle_settings.db')

def init_db():
    """Initialize the SQLite database with the obstacles table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create obstacles table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS obstacles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        area REAL NOT NULL,
        height REAL NOT NULL,
        color TEXT NOT NULL,
        coordinates TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

def get_all_obstacles():
    """Get all obstacles from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM obstacles ORDER BY id')
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'name': row['name'],
            'area': row['area'],
            'height': row['height'],
            'color': row['color'],
            'coordinates': json.loads(row['coordinates'])
        })
    
    conn.close()
    return results

def get_obstacle_by_id(obstacle_id):
    """Get obstacle by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM obstacles WHERE id = ?', (obstacle_id,))
    row = cursor.fetchone()
    
    if row:
        result = {
            'id': row['id'],
            'name': row['name'],
            'area': row['area'],
            'height': row['height'],
            'color': row['color'],
            'coordinates': json.loads(row['coordinates'])
        }
    else:
        result = None
    
    conn.close()
    return result

def add_obstacle(obstacle_data):
    """Add a new obstacle to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO obstacles (name, area, height, color, coordinates) VALUES (?, ?, ?, ?, ?)',
        (
            obstacle_data['name'],
            obstacle_data['area'],
            obstacle_data['height'],
            obstacle_data['color'],
            json.dumps(obstacle_data['coordinates'])
        )
    )
    
    obstacle_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return obstacle_id

def update_obstacle(obstacle_id, obstacle_data):
    """Update an existing obstacle in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        '''UPDATE obstacles SET 
           name = ?, 
           area = ?, 
           height = ?, 
           color = ?, 
           coordinates = ? 
           WHERE id = ?''',
        (
            obstacle_data['name'],
            obstacle_data['area'],
            obstacle_data['height'],
            obstacle_data['color'],
            json.dumps(obstacle_data['coordinates']),
            obstacle_id
        )
    )
    
    conn.commit()
    conn.close()
    
    return cursor.rowcount > 0

def delete_obstacle(obstacle_id):
    """Delete an obstacle from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM obstacles WHERE id = ?', (obstacle_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

# Initialize database when the module is imported
init_db() 