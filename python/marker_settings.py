import json
import os
import sqlite3
from datetime import datetime

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'markers_data.db')

# Ensure the data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create marker groups table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS marker_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        color TEXT NOT NULL,
        is_visible INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Create markers table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS markers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        marker_number INTEGER,
        latitude REAL,
        longitude REAL,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (group_id) REFERENCES marker_groups (id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

#
# Marker Group functions
#

def get_all_marker_groups():
    """Get all marker groups"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM marker_groups ORDER BY name')
    groups = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return groups

def get_marker_group_by_id(group_id):
    """Get a marker group by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM marker_groups WHERE id = ?', (group_id,))
    group = cursor.fetchone()
    
    conn.close()
    
    if group:
        return dict(group)
    return None

def add_marker_group(group_data):
    """Add a new marker group"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        INSERT INTO marker_groups (
            name, color, is_visible, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?)
        ''',
        (
            group_data.get('name', ''),
            group_data.get('color', '#FF0000'),
            1 if group_data.get('is_visible', True) else 0,
            now,
            now
        )
    )
    
    group_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return group_id

def update_marker_group(group_id, group_data):
    """Update an existing marker group"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if group exists
    cursor.execute('SELECT id FROM marker_groups WHERE id = ?', (group_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        UPDATE marker_groups
        SET name = ?, color = ?, is_visible = ?, updated_at = ?
        WHERE id = ?
        ''',
        (
            group_data.get('name', ''),
            group_data.get('color', '#FF0000'),
            1 if group_data.get('is_visible', True) else 0,
            now,
            group_id
        )
    )
    
    conn.commit()
    conn.close()
    
    return True

def toggle_marker_group_visibility(group_id, is_visible):
    """Toggle a marker group's visibility"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if group exists
    cursor.execute('SELECT id FROM marker_groups WHERE id = ?', (group_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        UPDATE marker_groups
        SET is_visible = ?, updated_at = ?
        WHERE id = ?
        ''',
        (
            1 if is_visible else 0,
            now,
            group_id
        )
    )
    
    conn.commit()
    conn.close()
    
    return True

def delete_marker_group(group_id):
    """Delete a marker group by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if group exists
    cursor.execute('SELECT id FROM marker_groups WHERE id = ?', (group_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Delete the group (will cascade delete related markers)
    cursor.execute('DELETE FROM marker_groups WHERE id = ?', (group_id,))
    
    conn.commit()
    conn.close()
    
    return True

#
# Marker functions
#

def get_all_markers():
    """Get all markers with group information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
    SELECT m.*, g.name as group_name, g.color as group_color, g.is_visible as group_visible
    FROM markers m
    JOIN marker_groups g ON m.group_id = g.id
    ORDER BY g.name, m.marker_number
    '''
    
    cursor.execute(query)
    markers = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return markers

def get_markers_by_group(group_id):
    """Get all markers for a specific group"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
    SELECT m.*, g.name as group_name, g.color as group_color, g.is_visible as group_visible
    FROM markers m
    JOIN marker_groups g ON m.group_id = g.id
    WHERE m.group_id = ?
    ORDER BY m.marker_number
    '''
    
    cursor.execute(query, (group_id,))
    markers = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return markers

def get_marker_by_id(marker_id):
    """Get a marker by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
    SELECT m.*, g.name as group_name, g.color as group_color, g.is_visible as group_visible
    FROM markers m
    JOIN marker_groups g ON m.group_id = g.id
    WHERE m.id = ?
    '''
    
    cursor.execute(query, (marker_id,))
    marker = cursor.fetchone()
    
    conn.close()
    
    if marker:
        return dict(marker)
    return None

def add_marker(marker_data):
    """Add a new marker"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the group exists
    cursor.execute('SELECT id FROM marker_groups WHERE id = ?', (marker_data.get('group_id'),))
    if not cursor.fetchone():
        conn.close()
        return False, "Marker group not found"
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        INSERT INTO markers (
            group_id, marker_number, latitude, longitude, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (
            marker_data.get('group_id'),
            marker_data.get('marker_number', 1),
            marker_data.get('latitude'),
            marker_data.get('longitude'),
            now,
            now
        )
    )
    
    marker_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return True, marker_id

def update_marker(marker_id, marker_data):
    """Update an existing marker"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if marker exists
    cursor.execute('SELECT id FROM markers WHERE id = ?', (marker_id,))
    if not cursor.fetchone():
        conn.close()
        return False, "Marker not found"
    
    # Check if the group exists
    cursor.execute('SELECT id FROM marker_groups WHERE id = ?', (marker_data.get('group_id'),))
    if not cursor.fetchone():
        conn.close()
        return False, "Marker group not found"
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        UPDATE markers
        SET group_id = ?, marker_number = ?, latitude = ?, longitude = ?, updated_at = ?
        WHERE id = ?
        ''',
        (
            marker_data.get('group_id'),
            marker_data.get('marker_number', 1),
            marker_data.get('latitude'),
            marker_data.get('longitude'),
            now,
            marker_id
        )
    )
    
    conn.commit()
    conn.close()
    
    return True, None

def delete_marker(marker_id):
    """Delete a marker by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if marker exists
    cursor.execute('SELECT id FROM markers WHERE id = ?', (marker_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute('DELETE FROM markers WHERE id = ?', (marker_id,))
    
    conn.commit()
    conn.close()
    
    return True 