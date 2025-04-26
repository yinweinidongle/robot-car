from flask import Flask, request, jsonify
from flask_cors import CORS
import csv
import json
from geopy import Point
from geopy.distance import distance
import math
import vehicle_settings
import wms_settings
import obstacle_settings
import table_settings
import marker_settings

app = Flask(__name__)
CORS(app)  # 启用CORS以允许前端访问

class Waypoint:
    def __init__(self, line):
        parts = line.strip().split('\t')
        # 检查行是否为空或格式不正确
        if not line.strip() or len(parts) < 12:
            raise ValueError("Invalid line format")
            
        self.index = int(parts[0])
        self.fixed_zero = int(parts[1])
        self.mode = int(parts[2])
        self.function = int(parts[3])
        self.param1 = float(parts[4])
        self.param2 = float(parts[5])
        self.param3 = float(parts[6])
        self.param4 = float(parts[7])
        self.latitude = float(parts[8]) if parts[8] else None
        self.longitude = float(parts[9]) if parts[9] else None
        self.altitude = float(parts[10]) if parts[10] else None
        self.fixed_one = int(parts[11])

    def to_dict(self):
        return {
            'index': self.index,
            'mode': self.mode,
            'function': self.function,
            'params': [self.param1, self.param2, self.param3, self.param4],
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude
        }

@app.route('/api/waypoints', methods=['POST'])
def upload_waypoints():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if not file:
            return jsonify({'error': 'Empty file'}), 400

        # 读取文件内容
        content = file.read().decode('utf-8').splitlines()
        
        # 检查文件格式
        if not content or content[0] != 'QGC WPL 110':
            return jsonify({'error': 'Invalid file format'}), 400

        # 解析数据
        waypoints = []

        # 过滤掉空行
        valid_lines = [line for line in content[2:] if line.strip()]

        for line in valid_lines:  # 跳过标题行
            try:
                waypoint = Waypoint(line)
                # 只添加有效的经纬度坐标点
                if (waypoint.latitude is not None and waypoint.longitude is not None and 
                    waypoint.latitude != 0 and waypoint.longitude != 0):
                    waypoints.append(waypoint.to_dict())
            except Exception as e:
                return jsonify({'error': f'Error parsing line: {str(e)}'}), 400

        return jsonify({
            'waypoints': waypoints
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'message': 'API is working'})

@app.route('/api/export', methods=['POST'])
def export_waypoints():
    try:
        data = request.json
        weeding_type = data['weedingType']
        all_files = []
        
        print("\n=== 导出航点数据 ===")
        print(f"除草类型: {'行间除草' if weeding_type == 1 else '株间除草'}")
        
        for group in data['groups']:
            file_content = ['QGC WPL 110']  # 文件头
            
            # 添加编号为0的起始点，位置偏移5米
            if group['points']:
                first_point = group['points'][0]
                # 创建原始点
                orig = Point(first_point['latitude'], first_point['longitude'])
                
                # 计算偏移5米后的位置（向东北方向偏移）
                # 使用45度角，这样在东和北方向各偏移约3.535米
                d = distance(meters=5)
                bearing = 45  # 东北方向
                
                # 计算偏移后的位置
                offset_point = d.destination(orig, bearing)
                
                home_point = (
                    f"0\t1\t0\t16\t"
                    f"0.00000000\t0.00000000\t0.00000000\t0.00000000\t"
                    f"{offset_point.latitude:.8f}\t{offset_point.longitude:.8f}\t"
                    f"35.610000\t1"
                )
                file_content.append(home_point)
            
            current_index = 1  # 从1开始编号其他点
            
            for point in group['points']:
                # 添加航点行
                waypoint_line = (
                    f"{current_index}\t0\t0\t16\t"
                    f"0.00000000\t0.00000000\t0.00000000\t0.00000000\t"
                    f"{point['latitude']:.8f}\t{point['longitude']:.8f}\t"
                    f"8.300000\t1"
                )
                file_content.append(waypoint_line)
                
                if weeding_type == 1 and point['type'] == 1:  # 行间除草且为驶入点
                    # 添加继电器设置命令
                    current_index += 1
                    file_content.append(
                        f"{current_index}\t0\t0\t181\t"
                        f"0.00000000\t1.00000000\t0.00000000\t0.00000000\t"
                        f"0.00000000\t0.00000000\t0.000000\t1"
                    )
                    # 添加延时命令
                    current_index += 1
                    file_content.append(
                        f"{current_index}\t0\t0\t93\t"
                        f"2.00000000\t0.00000000\t0.00000000\t0.00000000\t"
                        f"0.00000000\t0.00000000\t0.000000\t1"
                    )

                if weeding_type == 1 and point['type'] == 2:  # 行间除草且为驶出点
                    # 添加继电器设置命令
                    current_index += 1
                    file_content.append(
                        f"{current_index}\t0\t0\t181\t"
                        f"0.00000000\t0.00000000\t0.00000000\t0.00000000\t"
                        f"0.00000000\t0.00000000\t0.000000\t1"
                    )
                    # 添加延时命令
                    current_index += 1
                    file_content.append(
                        f"{current_index}\t0\t0\t93\t"
                        f"2.00000000\t0.00000000\t0.00000000\t0.00000000\t"
                        f"0.00000000\t0.00000000\t0.000000\t1"
                    )
                
                # 株间除草模式，只对作业点(3)进行命令插入
                if weeding_type == 2 and point['type'] == 3:  # 株间除草模式且为作业区内的点
                    # 株间除草模式的额外命令保持不变
                    current_index += 1
                    file_content.append(
                        f"{current_index}\t0\t0\t181\t"
                        f"0.00000000\t1.00000000\t0.00000000\t0.00000000\t"
                        f"0.00000000\t0.00000000\t0.000000\t1"
                    )
                    current_index += 1
                    file_content.append(
                        f"{current_index}\t0\t0\t93\t"
                        f"2.00000000\t0.00000000\t0.00000000\t0.00000000\t"
                        f"0.00000000\t0.00000000\t0.000000\t1"
                    )
                    current_index += 1
                    file_content.append(
                        f"{current_index}\t0\t0\t181\t"
                        f"0.00000000\t0.00000000\t0.00000000\t0.00000000\t"
                        f"0.00000000\t0.00000000\t0.000000\t1"
                    )
                
                current_index += 1
            
            # 将文件内容和文件名一起存储
            all_files.append({
                'name': f"{group['fileName']}.waypoints",
                'content': '\n'.join(file_content)
            })
        
        return jsonify({
            'success': True,
            'files': all_files
        })

    except Exception as e:
        print(f"Error processing export: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add vehicle settings API endpoints
@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    try:
        vehicles = vehicle_settings.get_all_vehicles()
        return jsonify({
            'success': True,
            'vehicles': vehicles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vehicles/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    try:
        vehicle = vehicle_settings.get_vehicle_by_id(vehicle_id)
        if vehicle:
            return jsonify({
                'success': True,
                'vehicle': vehicle
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Vehicle with ID {vehicle_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vehicles', methods=['POST'])
def add_new_vehicle():
    try:
        vehicle_data = request.json
        if not vehicle_data or 'vehicle_name' not in vehicle_data:
            return jsonify({
                'success': False,
                'error': 'Missing required vehicle data'
            }), 400
        
        vehicle_id = vehicle_settings.add_vehicle(vehicle_data)
        return jsonify({
            'success': True,
            'id': vehicle_id,
            'message': 'Vehicle added successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vehicles/<int:vehicle_id>', methods=['PUT'])
def update_existing_vehicle(vehicle_id):
    try:
        vehicle_data = request.json
        if not vehicle_data or 'vehicle_name' not in vehicle_data:
            return jsonify({
                'success': False,
                'error': 'Missing required vehicle data'
            }), 400
        
        success = vehicle_settings.update_vehicle(vehicle_id, vehicle_data)
        if success:
            return jsonify({
                'success': True,
                'message': 'Vehicle updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Vehicle with ID {vehicle_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
def delete_existing_vehicle(vehicle_id):
    try:
        success = vehicle_settings.delete_vehicle(vehicle_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Vehicle deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Vehicle with ID {vehicle_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add offset history API endpoints
@app.route('/api/offset/history', methods=['GET'])
def get_offset_history():
    try:
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=10, type=int)
        
        history = vehicle_settings.get_offset_history(page, page_size)
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vehicles/<int:vehicle_id>/offset/history', methods=['GET'])
def get_vehicle_offset_history(vehicle_id):
    try:
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=10, type=int)
        
        history = vehicle_settings.get_vehicle_offset_history(vehicle_id, page, page_size)
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/offset/history', methods=['POST'])
def record_offset():
    try:
        offset_data = request.json
        if not offset_data or 'vehicle_id' not in offset_data or 'longitude_offset' not in offset_data or 'latitude_offset' not in offset_data:
            return jsonify({
                'success': False,
                'error': 'Missing required offset data'
            }), 400
        
        # Get vehicle details to include name
        vehicle = vehicle_settings.get_vehicle_by_id(offset_data['vehicle_id'])
        if not vehicle:
            return jsonify({
                'success': False,
                'error': f'Vehicle with ID {offset_data["vehicle_id"]} not found'
            }), 404
        
        history_id = vehicle_settings.record_offset_history(
            offset_data['vehicle_id'],
            vehicle['vehicle_name'],
            offset_data['longitude_offset'],
            offset_data['latitude_offset'],
            offset_data.get('notes')
        )
        
        return jsonify({
            'success': True,
            'id': history_id,
            'message': 'Offset history recorded successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add WMS layer management API endpoints
@app.route('/api/wms/layers', methods=['GET'])
def get_wms_layers():
    try:
        layers = wms_settings.get_all_layers()
        return jsonify({
            'success': True,
            'layers': layers
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wms/layers/<int:layer_id>', methods=['GET'])
def get_wms_layer(layer_id):
    try:
        layer = wms_settings.get_layer_by_id(layer_id)
        if layer:
            return jsonify({
                'success': True,
                'layer': layer
            })
        else:
            return jsonify({
                'success': False,
                'error': f'WMS layer with ID {layer_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wms/layers', methods=['POST'])
def add_wms_layer():
    try:
        layer_data = request.json
        if not layer_data or 'name' not in layer_data or 'url' not in layer_data or 'layer_id' not in layer_data:
            return jsonify({
                'success': False,
                'error': 'Missing required layer data'
            }), 400
        
        layer_id = wms_settings.add_layer(layer_data)
        return jsonify({
            'success': True,
            'id': layer_id,
            'message': 'WMS layer added successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wms/layers/<int:layer_id>', methods=['PUT'])
def update_wms_layer(layer_id):
    try:
        layer_data = request.json
        if not layer_data or 'name' not in layer_data or 'url' not in layer_data or 'layer_id' not in layer_data:
            return jsonify({
                'success': False,
                'error': 'Missing required layer data'
            }), 400
        
        success = wms_settings.update_layer(layer_id, layer_data)
        if success:
            return jsonify({
                'success': True,
                'message': 'WMS layer updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'WMS layer with ID {layer_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wms/layers/<int:layer_id>', methods=['DELETE'])
def delete_wms_layer(layer_id):
    try:
        success = wms_settings.delete_layer(layer_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'WMS layer deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'WMS layer with ID {layer_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wms/layers/<int:layer_id>/toggle', methods=['PUT'])
def toggle_wms_layer(layer_id):
    try:
        layer_data = request.json
        if 'enabled' not in layer_data:
            return jsonify({
                'success': False,
                'error': 'Missing enabled status'
            }), 400
        
        success = wms_settings.toggle_layer(layer_id, layer_data['enabled'])
        if success:
            return jsonify({
                'success': True,
                'message': f'WMS layer {"enabled" if layer_data["enabled"] else "disabled"} successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'WMS layer with ID {layer_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add obstacle API endpoints
@app.route('/api/obstacles', methods=['GET'])
def get_obstacles():
    try:
        obstacles = obstacle_settings.get_all_obstacles()
        return jsonify({
            'success': True,
            'obstacles': obstacles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/obstacles/<int:obstacle_id>', methods=['GET'])
def get_obstacle(obstacle_id):
    try:
        obstacle = obstacle_settings.get_obstacle_by_id(obstacle_id)
        if obstacle:
            return jsonify({
                'success': True,
                'obstacle': obstacle
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Obstacle with ID {obstacle_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/obstacles', methods=['POST'])
def add_new_obstacle():
    try:
        obstacle_data = request.json
        if not obstacle_data or 'name' not in obstacle_data or 'coordinates' not in obstacle_data:
            return jsonify({
                'success': False,
                'error': 'Missing required obstacle data'
            }), 400
        
        obstacle_id = obstacle_settings.add_obstacle(obstacle_data)
        return jsonify({
            'success': True,
            'id': obstacle_id,
            'message': 'Obstacle added successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/obstacles/<int:obstacle_id>', methods=['PUT'])
def update_existing_obstacle(obstacle_id):
    try:
        obstacle_data = request.json
        if not obstacle_data or 'name' not in obstacle_data or 'coordinates' not in obstacle_data:
            return jsonify({
                'success': False,
                'error': 'Missing required obstacle data'
            }), 400
        
        success = obstacle_settings.update_obstacle(obstacle_id, obstacle_data)
        if success:
            return jsonify({
                'success': True,
                'message': 'Obstacle updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Obstacle with ID {obstacle_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/obstacles/<int:obstacle_id>', methods=['DELETE'])
def delete_existing_obstacle(obstacle_id):
    try:
        success = obstacle_settings.delete_obstacle(obstacle_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Obstacle deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Obstacle with ID {obstacle_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add table management API endpoints
@app.route('/api/tables', methods=['GET'])
def get_table_records():
    try:
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=10, type=int)
        
        result = table_settings.get_all_records(page, page_size)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tables/<int:record_id>', methods=['GET'])
def get_table_record(record_id):
    try:
        record = table_settings.get_record_by_id(record_id)
        if record:
            return jsonify({
                'success': True,
                'data': record
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Record with ID {record_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tables', methods=['POST'])
def add_table_record():
    try:
        record_data = request.json
        if not record_data:
            return jsonify({
                'success': False,
                'error': 'Missing record data'
            }), 400
        
        record_id = table_settings.add_record(record_data)
        return jsonify({
            'success': True,
            'id': record_id,
            'message': 'Record added successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tables/<int:record_id>', methods=['PUT'])
def update_table_record(record_id):
    try:
        record_data = request.json
        if not record_data:
            return jsonify({
                'success': False,
                'error': 'Missing record data'
            }), 400
        
        success = table_settings.update_record(record_id, record_data)
        if success:
            return jsonify({
                'success': True,
                'message': 'Record updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Record with ID {record_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tables/<int:record_id>', methods=['DELETE'])
def delete_table_record(record_id):
    try:
        success = table_settings.delete_record(record_id)
        if success:
            return jsonify({
                'success': True,
                'message': 'Record deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Record with ID {record_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tables/export', methods=['GET'])
def export_table_records():
    try:
        records = table_settings.get_all_records_for_export()
        return jsonify({
            'success': True,
            'data': records
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add marker group API endpoints
@app.route('/api/marker-groups', methods=['GET'])
def get_marker_groups():
    try:
        groups = marker_settings.get_all_marker_groups()
        return jsonify({
            'success': True,
            'groups': groups
        })
    except Exception as e:
        print(f"Error getting marker groups: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/marker-groups', methods=['POST'])
def add_marker_group():
    try:
        group_data = request.json
        if not group_data or 'name' not in group_data:
            return jsonify({
                'success': False,
                'error': 'Group name is required'
            }), 400
            
        group_id = marker_settings.add_marker_group(group_data)
        
        return jsonify({
            'success': True,
            'id': group_id,
            'message': 'Marker group added successfully'
        })
    except Exception as e:
        print(f"Error adding marker group: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/marker-groups/<int:group_id>', methods=['PUT'])
def update_marker_group(group_id):
    try:
        group_data = request.json
        if not group_data or 'name' not in group_data:
            return jsonify({
                'success': False,
                'error': 'Group name is required'
            }), 400
            
        success = marker_settings.update_marker_group(group_id, group_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Marker group updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Marker group with ID {group_id} not found'
            }), 404
    except Exception as e:
        print(f"Error updating marker group: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/marker-groups/<int:group_id>/toggle', methods=['PUT'])
def toggle_marker_group(group_id):
    try:
        data = request.json
        if 'is_visible' not in data:
            return jsonify({
                'success': False,
                'error': 'Visibility status is required'
            }), 400
            
        success = marker_settings.toggle_marker_group_visibility(
            group_id, data['is_visible'])
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Marker group visibility updated'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Marker group with ID {group_id} not found'
            }), 404
    except Exception as e:
        print(f"Error toggling marker group: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/marker-groups/<int:group_id>', methods=['DELETE'])
def delete_marker_group(group_id):
    try:
        success = marker_settings.delete_marker_group(group_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Marker group deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Marker group with ID {group_id} not found'
            }), 404
    except Exception as e:
        print(f"Error deleting marker group: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Add marker API endpoints
@app.route('/api/markers', methods=['GET'])
def get_markers():
    try:
        group_id = request.args.get('group_id', type=int)
        
        if group_id:
            markers = marker_settings.get_markers_by_group(group_id)
        else:
            markers = marker_settings.get_all_markers()
            
        return jsonify({
            'success': True,
            'markers': markers
        })
    except Exception as e:
        print(f"Error getting markers: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/markers', methods=['POST'])
def add_marker():
    try:
        marker_data = request.json
        if not marker_data or 'group_id' not in marker_data:
            return jsonify({
                'success': False,
                'error': 'Group ID is required'
            }), 400
            
        success, result = marker_settings.add_marker(marker_data)
        
        if success:
            return jsonify({
                'success': True,
                'id': result,
                'message': 'Marker added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 400
    except Exception as e:
        print(f"Error adding marker: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/markers/<int:marker_id>', methods=['PUT'])
def update_marker(marker_id):
    try:
        marker_data = request.json
        if not marker_data or 'group_id' not in marker_data:
            return jsonify({
                'success': False,
                'error': 'Group ID is required'
            }), 400
            
        success, error = marker_settings.update_marker(marker_id, marker_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Marker updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 404
    except Exception as e:
        print(f"Error updating marker: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/markers/<int:marker_id>', methods=['DELETE'])
def delete_marker(marker_id):
    try:
        success = marker_settings.delete_marker(marker_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Marker deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Marker with ID {marker_id} not found'
            }), 404
    except Exception as e:
        print(f"Error deleting marker: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5005, host='0.0.0.0')
