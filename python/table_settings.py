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
    
    # Create excel_tables table to store table metadata
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS excel_tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Create table records table with a foreign key to excel_tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS table_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER NOT NULL,
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
        updated_at TEXT,
        FOREIGN KEY (table_id) REFERENCES excel_tables(id) ON DELETE CASCADE
    )
    ''')
    
    # Check if we need to migrate data from old schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='table_records'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Check if the table_id column exists
        cursor.execute("PRAGMA table_info(table_records)")
        columns = cursor.fetchall()
        has_table_id = any(column[1] == 'table_id' for column in columns)
        
        # If the old schema exists but doesn't have table_id, we need to migrate
        if not has_table_id:
            # Create default table
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                '''
                INSERT OR IGNORE INTO excel_tables (table_name, display_name, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ''',
                ('default_table', '协和成地块作业地块', now, now)
            )
            conn.commit()
            
            # Get the default table id
            cursor.execute('SELECT id FROM excel_tables WHERE table_name = ?', ('default_table',))
            default_table_id = cursor.fetchone()[0]
            
            # Create a temporary table with the new schema
            cursor.execute('''
            CREATE TEMPORARY TABLE table_records_backup(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
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
            
            # Copy data from the old table to the new table
            cursor.execute(f'''
            INSERT INTO table_records_backup (
                table_id, c_car_no, c_last_time, h_car_no, h_last_time, 
                z_car_no, z_last_time, point_distance, sample_file,
                notes, created_at, updated_at
            )
            SELECT 
                ?, c_car_no, c_last_time, h_car_no, h_last_time, 
                z_car_no, z_last_time, point_distance, sample_file,
                notes, created_at, updated_at
            FROM table_records
            ''', (default_table_id,))
            
            # Drop the old table
            cursor.execute('DROP TABLE table_records')
            
            # Create the new table
            cursor.execute('''
            CREATE TABLE table_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
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
                updated_at TEXT,
                FOREIGN KEY (table_id) REFERENCES excel_tables(id) ON DELETE CASCADE
            )
            ''')
            
            # Copy data from the backup table to the new table
            cursor.execute('''
            INSERT INTO table_records
            SELECT * FROM table_records_backup
            ''')
            
            # Drop the backup table
            cursor.execute('DROP TABLE table_records_backup')
            
            conn.commit()
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Excel tables management functions
def get_all_tables():
    """Get all Excel tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM excel_tables ORDER BY id')
    tables = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return tables

def get_table_by_id(table_id):
    """Get an Excel table by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM excel_tables WHERE id = ?', (table_id,))
    table = cursor.fetchone()
    
    conn.close()
    
    if table:
        return dict(table)
    return None

def get_table_by_name(table_name):
    """Get an Excel table by name"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM excel_tables WHERE table_name = ?', (table_name,))
    table = cursor.fetchone()
    
    conn.close()
    
    if table:
        return dict(table)
    return None

def add_table(table_data):
    """Add a new Excel table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Check if table name already exists
    cursor.execute('SELECT id FROM excel_tables WHERE table_name = ?', (table_data['table_name'],))
    if cursor.fetchone():
        conn.close()
        return None, "Table name already exists"
    
    cursor.execute(
        '''
        INSERT INTO excel_tables (
            table_name, display_name, created_at, updated_at
        ) VALUES (?, ?, ?, ?)
        ''',
        (
            table_data['table_name'],
            table_data['display_name'],
            now,
            now
        )
    )
    
    table_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return table_id, None

def update_table(table_id, table_data):
    """Update an existing Excel table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute('SELECT id FROM excel_tables WHERE id = ?', (table_id,))
    if not cursor.fetchone():
        conn.close()
        return False, "Table not found"
    
    # Check if new table name already exists (if changing the name)
    if 'table_name' in table_data:
        cursor.execute(
            'SELECT id FROM excel_tables WHERE table_name = ? AND id != ?', 
            (table_data['table_name'], table_id)
        )
        if cursor.fetchone():
            conn.close()
            return False, "Table name already exists"
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        UPDATE excel_tables
        SET display_name = ?, updated_at = ?
        WHERE id = ?
        ''',
        (
            table_data['display_name'],
            now,
            table_id
        )
    )
    
    conn.commit()
    conn.close()
    
    return True, None

def delete_table(table_id):
    """Delete an Excel table and all its records"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute('SELECT id FROM excel_tables WHERE id = ?', (table_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Delete all records for this table
    cursor.execute('DELETE FROM table_records WHERE table_id = ?', (table_id,))
    
    # Delete the table
    cursor.execute('DELETE FROM excel_tables WHERE id = ?', (table_id,))
    
    conn.commit()
    conn.close()
    
    return True

# Table records management functions
def get_all_records(page=1, page_size=10, table_id=None):
    """Get all table records with pagination, optionally filtered by table_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query_params = []
    where_clause = ""
    
    if table_id:
        where_clause = "WHERE table_id = ?"
        query_params.append(table_id)
    
    # Get total count
    count_query = f'SELECT COUNT(*) FROM table_records {where_clause}'
    cursor.execute(count_query, query_params)
    total = cursor.fetchone()[0]
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get records with pagination
    params = query_params.copy()
    params.extend([page_size, offset])
    
    records_query = f'''
        SELECT r.*, t.table_name, t.display_name 
        FROM table_records r
        JOIN excel_tables t ON r.table_id = t.id
        {where_clause}
        ORDER BY r.id DESC LIMIT ? OFFSET ?
    '''
    
    cursor.execute(records_query, params)
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
    
    cursor.execute('''
        SELECT r.*, t.table_name, t.display_name 
        FROM table_records r
        JOIN excel_tables t ON r.table_id = t.id
        WHERE r.id = ?
    ''', (record_id,))
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
            table_id, c_car_no, c_last_time, h_car_no, h_last_time,
            z_car_no, z_last_time, point_distance, sample_file,
            notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            record_data.get('table_id', 1),  # Default to first table if not specified
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

def get_all_records_for_export(table_id=None):
    """Get all table records for export (no pagination), optionally filtered by table_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT r.*, t.table_name, t.display_name 
        FROM table_records r
        JOIN excel_tables t ON r.table_id = t.id
    '''
    params = []
    
    if table_id:
        query += ' WHERE r.table_id = ?'
        params.append(table_id)
        
    query += ' ORDER BY r.id'
    
    cursor.execute(query, params)
    records = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return records 

def import_excel_records(excel_data, table_name=None):
    """Import records from Excel file data
    
    Args:
        excel_data (list): List of dictionaries containing Excel records
        table_name (str): Name of the Excel file (without extension) to associate records with
        
    Returns:
        dict: Import results with counts of added and failed records
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_records = len(excel_data)
    added_records = 0
    failed_records = 0
    
    try:
        # If table_name is provided, check if a table with this name exists
        table_id = None
        if table_name:
            # Clean up the table_name (remove extension if present)
            if table_name.endswith('.xlsx') or table_name.endswith('.xls'):
                table_name = os.path.splitext(table_name)[0]
            
            cursor.execute('SELECT id FROM excel_tables WHERE table_name = ?', (table_name,))
            result = cursor.fetchone()
            
            if result:
                # Table exists, use its ID
                table_id = result[0]
            else:
                # Table doesn't exist, create it
                display_name = table_name  # Use table_name as display_name by default
                cursor.execute(
                    '''
                    INSERT INTO excel_tables (
                        table_name, display_name, created_at, updated_at
                    ) VALUES (?, ?, ?, ?)
                    ''',
                    (table_name, display_name, now, now)
                )
                table_id = cursor.lastrowid
        else:
            # If no table_name is provided, use the first table
            cursor.execute('SELECT id FROM excel_tables LIMIT 1')
            result = cursor.fetchone()
            
            if result:
                table_id = result[0]
            else:
                # No tables exist, create a default one
                cursor.execute(
                    '''
                    INSERT INTO excel_tables (
                        table_name, display_name, created_at, updated_at
                    ) VALUES (?, ?, ?, ?)
                    ''',
                    ('default_table', '协和成地块作业地块', now, now)
                )
                table_id = cursor.lastrowid
        
        for record in excel_data:
            try:
                # Process each record from Excel
                cursor.execute(
                    '''
                    INSERT INTO table_records (
                        table_id, c_car_no, c_last_time, h_car_no, h_last_time,
                        z_car_no, z_last_time, point_distance, sample_file,
                        notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        table_id,
                        record.get('c_car_no', ''),
                        record.get('c_last_time', ''),
                        record.get('h_car_no', ''),
                        record.get('h_last_time', ''),
                        record.get('z_car_no', ''),
                        record.get('z_last_time', ''),
                        record.get('point_distance', ''),
                        record.get('sample_file', ''),
                        record.get('notes', ''),
                        now,
                        now
                    )
                )
                added_records += 1
            except Exception as e:
                print(f"Error importing record: {str(e)}")
                failed_records += 1
                
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Database error during import: {str(e)}")
        raise
    finally:
        conn.close()
    
    return {
        'total': total_records,
        'added': added_records,
        'failed': failed_records,
        'table_id': table_id
    } 