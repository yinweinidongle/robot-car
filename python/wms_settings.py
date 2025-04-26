import sqlite3
import json
import os

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'wms_settings.db')

def init_db():
    """Initialize the SQLite database with the wms_layers table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create wms_layers table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wms_layers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        layer_id TEXT NOT NULL,
        opacity REAL DEFAULT 0.8,
        enabled INTEGER DEFAULT 1
    )
    ''')
    
    conn.commit()
    conn.close()

def get_all_layers():
    """Get all WMS layers from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM wms_layers ORDER BY id')
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    results = []
    for row in rows:
        results.append({
            'id': row['id'],
            'name': row['name'],
            'url': row['url'],
            'layer_id': row['layer_id'],
            'opacity': row['opacity'],
            'enabled': bool(row['enabled'])
        })
    
    conn.close()
    return results

def get_layer_by_id(layer_id):
    """Get WMS layer by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM wms_layers WHERE id = ?', (layer_id,))
    row = cursor.fetchone()
    
    if row:
        result = {
            'id': row['id'],
            'name': row['name'],
            'url': row['url'],
            'layer_id': row['layer_id'],
            'opacity': row['opacity'],
            'enabled': bool(row['enabled'])
        }
    else:
        result = None
    
    conn.close()
    return result

def add_layer(layer_data):
    """Add a new WMS layer to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO wms_layers (name, url, layer_id, opacity, enabled) VALUES (?, ?, ?, ?, ?)',
        (
            layer_data['name'],
            layer_data['url'],
            layer_data['layer_id'],
            layer_data.get('opacity', 0.8),
            1 if layer_data.get('enabled', True) else 0
        )
    )
    
    layer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return layer_id

def update_layer(layer_id, layer_data):
    """Update an existing WMS layer in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        '''UPDATE wms_layers SET 
           name = ?, 
           url = ?, 
           layer_id = ?, 
           opacity = ?, 
           enabled = ? 
           WHERE id = ?''',
        (
            layer_data['name'],
            layer_data['url'],
            layer_data['layer_id'],
            layer_data.get('opacity', 0.8),
            1 if layer_data.get('enabled', True) else 0,
            layer_id
        )
    )
    
    conn.commit()
    conn.close()
    
    return cursor.rowcount > 0

def delete_layer(layer_id):
    """Delete a WMS layer from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM wms_layers WHERE id = ?', (layer_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def toggle_layer(layer_id, enabled):
    """Toggle a WMS layer's enabled status."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE wms_layers SET enabled = ? WHERE id = ?',
        (1 if enabled else 0, layer_id)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

# Initialize database when the module is imported
init_db()

# Add default WMS layer if none exists
def add_default_layer():
    layers = get_all_layers()
    if not layers:
        default_layer = {
            'name': '博研湖地图',
            'url': 'http://121.40.132.51:6080/arcgis/services/fengzhi/boyanhu/MapServer/WMSServer',
            'layer_id': '0',
            'opacity': 0.8,
            'enabled': True
        }
        add_layer(default_layer)

# Add default layer when module is loaded
add_default_layer() 