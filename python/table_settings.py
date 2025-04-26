import json
import os
import sqlite3
from datetime import datetime

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'tables_data.db')

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
    
    # Create table records table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS table_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        c_car_no TEXT,
        c_last_time TEXT,
        h_car_no TEXT,
        h_last_time TEXT,
        z_car_no TEXT,
        z_last_time TEXT,
        point_distance TEXT,
        sample_file TEXT,
        notes TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

def get_all_records(page=1, page_size=10):
    """Get all table records with pagination"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM table_records')
    total = cursor.fetchone()[0]
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get records with pagination
    cursor.execute(
        'SELECT * FROM table_records ORDER BY id DESC LIMIT ? OFFSET ?',
        (page_size, offset)
    )
    records = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'total': total,
        'records': records,
        'page': page,
        'page_size': page_size
    }

def get_record_by_id(record_id):
    """Get a table record by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM table_records WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    
    conn.close()
    
    if record:
        return dict(record)
    return None

def add_record(record_data):
    """Add a new table record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        INSERT INTO table_records (
            c_car_no, c_last_time, h_car_no, h_last_time,
            z_car_no, z_last_time, point_distance, sample_file,
            notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            record_data.get('c_car_no', ''),
            record_data.get('c_last_time', ''),
            record_data.get('h_car_no', ''),
            record_data.get('h_last_time', ''),
            record_data.get('z_car_no', ''),
            record_data.get('z_last_time', ''),
            record_data.get('point_distance', ''),
            record_data.get('sample_file', ''),
            record_data.get('notes', ''),
            now,
            now
        )
    )
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return record_id

def update_record(record_id, record_data):
    """Update an existing table record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if record exists
    cursor.execute('SELECT id FROM table_records WHERE id = ?', (record_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        UPDATE table_records
        SET c_car_no = ?, c_last_time = ?, h_car_no = ?, h_last_time = ?,
            z_car_no = ?, z_last_time = ?, point_distance = ?, sample_file = ?,
            notes = ?, updated_at = ?
        WHERE id = ?
        ''',
        (
            record_data.get('c_car_no', ''),
            record_data.get('c_last_time', ''),
            record_data.get('h_car_no', ''),
            record_data.get('h_last_time', ''),
            record_data.get('z_car_no', ''),
            record_data.get('z_last_time', ''),
            record_data.get('point_distance', ''),
            record_data.get('sample_file', ''),
            record_data.get('notes', ''),
            now,
            record_id
        )
    )
    
    conn.commit()
    conn.close()
    
    return True

def delete_record(record_id):
    """Delete a table record by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if record exists
    cursor.execute('SELECT id FROM table_records WHERE id = ?', (record_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute('DELETE FROM table_records WHERE id = ?', (record_id,))
    
    conn.commit()
    conn.close()
    
    return True

def get_all_records_for_export():
    """Get all table records for export (no pagination)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM table_records ORDER BY id')
    records = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return records 