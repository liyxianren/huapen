from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json
from database import SensorDatabase

app = Flask(__name__)
# 允许Flask处理text/plain内容类型
app.config['JSON_AS_ASCII'] = False

# 初始化数据库
db = SensorDatabase("sensor_data.db")

def parse_sensor_string(data_string):
    """
    解析ESP8266发送的字符串格式数据
    格式: "Light:850,Humidity:65.2,Temperature:25.6,Servo_angle:90"
    返回: dict包含解析后的数据
    """
    try:
        # 去除首尾空白
        data_string = data_string.strip()
        
        # 解析数据
        result = {}
        parts = data_string.split(',')
        
        for part in parts:
            part = part.strip()
            if ':' in part:
                key, value = part.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # 根据键名转换数据类型
                if key == 'Light':
                    result['light_intensity'] = int(float(value))
                elif key == 'Humidity':
                    result['humidity'] = float(value)
                elif key == 'Temperature':
                    result['temperature'] = float(value)
                elif key == 'Servo_angle':
                    result['servo_angle'] = int(float(value))
        
        # 验证必需字段
        required_fields = ['humidity', 'temperature', 'light_intensity']
        for field in required_fields:
            if field not in result:
                raise ValueError(f'Missing required field: {field}')
        
        # 如果servo_angle不存在，默认为0
        if 'servo_angle' not in result:
            result['servo_angle'] = 0
            
        return result
    except Exception as e:
        raise ValueError(f'Failed to parse sensor string: {str(e)}')

@app.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    try:
        # 接收JSON格式数据
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        # 验证必需字段
        required_fields = ['humidity', 'temperature', 'light_intensity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # 获取servo_angle字段（可选，默认为0）
        servo_angle = data.get('servo_angle', 0)

        # 保存数据到SQLite数据库
        sensor_reading = db.add_sensor_data(
            humidity=data['humidity'],
            temperature=data['temperature'],
            light_intensity=data['light_intensity'],
            servo_angle=servo_angle
        )

        print(f"Received and saved sensor data: ID={sensor_reading['id']}, "
              f"H={sensor_reading['humidity']}%, T={sensor_reading['temperature']}°C, "
              f"L={sensor_reading['light_intensity']} lux, S={sensor_reading['servo_angle']}°")

        return jsonify({
            'status': 'success',
            'message': 'Sensor data received and saved successfully',
            'data': {
                'id': sensor_reading['id'],
                'humidity': sensor_reading['humidity'],
                'temperature': sensor_reading['temperature'],
                'light_intensity': sensor_reading['light_intensity'],
                'servo_angle': sensor_reading['servo_angle'],
                'timestamp': sensor_reading['timestamp']
            }
        }), 200

    except ValueError as e:
        print(f"Error parsing sensor data: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error saving sensor data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    try:
        # 获取查询参数
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', default=0, type=int)

        # 从数据库获取数据
        data = db.get_all_data(limit=limit, offset=offset)
        total_count = db.get_data_count()

        # 转换数据格式以保持与前端的兼容性，并且反转顺序（最新数据在后）
        formatted_data = []
        for item in reversed(data):
            formatted_data.append({
                'id': item['id'],
                'humidity': item['humidity'],
                'temperature': item['temperature'],
                'light_intensity': item['light_intensity'],
                'servo_angle': item.get('servo_angle', 0),
                'timestamp': item['timestamp']
            })

        return jsonify({
            'status': 'success',
            'count': total_count,
            'returned': len(formatted_data),
            'data': formatted_data
        }), 200

    except Exception as e:
        print(f"Error retrieving sensor data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/latest', methods=['GET'])
def get_latest_sensor_data():
    try:
        latest_data = db.get_latest_data()

        if not latest_data:
            return jsonify({
                'status': 'success',
                'message': 'No sensor data available',
                'data': None
            }), 200

        return jsonify({
            'status': 'success',
            'data': {
                'id': latest_data['id'],
                'humidity': latest_data['humidity'],
                'temperature': latest_data['temperature'],
                'light_intensity': latest_data['light_intensity'],
                'servo_angle': latest_data.get('servo_angle', 0),
                'timestamp': latest_data['timestamp']
            }
        }), 200

    except Exception as e:
        print(f"Error retrieving latest sensor data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/statistics', methods=['GET'])
def get_statistics():
    try:
        stats = db.get_statistics()
        return jsonify({
            'status': 'success',
            'statistics': stats
        }), 200

    except Exception as e:
        print(f"Error retrieving statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/export', methods=['GET'])
def export_data():
    try:
        file_path, count = db.export_to_json()
        return jsonify({
            'status': 'success',
            'message': f'Data exported successfully',
            'file_path': file_path,
            'exported_count': count
        }), 200

    except Exception as e:
        print(f"Error exporting data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/backup', methods=['POST'])
def backup_database():
    try:
        backup_path = db.backup_database()
        return jsonify({
            'status': 'success',
            'message': 'Database backup created successfully',
            'backup_path': backup_path
        }), 200

    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/clear', methods=['DELETE'])
def clear_all_data():
    try:
        deleted_count = db.clear_all_data()
        return jsonify({
            'status': 'success',
            'message': f'All data cleared successfully',
            'deleted_count': deleted_count
        }), 200

    except Exception as e:
        print(f"Error clearing data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/dates', methods=['GET'])
def get_available_dates():
    try:
        dates = db.get_available_dates()
        return jsonify({
            'status': 'success',
            'dates': dates
        }), 200

    except Exception as e:
        print(f"Error retrieving available dates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/year/<int:year>', methods=['GET'])
def get_data_by_year(year):
    try:
        data = db.get_data_by_year(year)

        # 转换数据格式以保持与前端的兼容性
        formatted_data = []
        for item in reversed(data):
            formatted_data.append({
                'id': item['id'],
                'humidity': item['humidity'],
                'temperature': item['temperature'],
                'light_intensity': item['light_intensity'],
                'servo_angle': item.get('servo_angle', 0),
                'timestamp': item['timestamp'],
                'date_key': item['date_key'],
                'datetime_key': item.get('datetime_key', '')
            })

        return jsonify({
            'status': 'success',
            'year': year,
            'count': len(formatted_data),
            'data': formatted_data
        }), 200

    except Exception as e:
        print(f"Error retrieving data by year: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/month/<int:year>/<int:month>', methods=['GET'])
def get_data_by_month(year, month):
    try:
        data = db.get_data_by_month(year, month)

        # 转换数据格式以保持与前端的兼容性
        formatted_data = []
        for item in reversed(data):
            formatted_data.append({
                'id': item['id'],
                'humidity': item['humidity'],
                'temperature': item['temperature'],
                'light_intensity': item['light_intensity'],
                'servo_angle': item.get('servo_angle', 0),
                'timestamp': item['timestamp'],
                'date_key': item['date_key'],
                'datetime_key': item.get('datetime_key', '')
            })

        return jsonify({
            'status': 'success',
            'year': year,
            'month': month,
            'count': len(formatted_data),
            'data': formatted_data
        }), 200

    except Exception as e:
        print(f"Error retrieving data by month: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/day/<int:year>/<int:month>/<int:day>', methods=['GET'])
def get_data_by_day(year, month, day):
    try:
        data = db.get_data_by_day(year, month, day)

        # 转换数据格式以保持与前端的兼容性
        formatted_data = []
        for item in reversed(data):
            formatted_data.append({
                'id': item['id'],
                'humidity': item['humidity'],
                'temperature': item['temperature'],
                'light_intensity': item['light_intensity'],
                'servo_angle': item.get('servo_angle', 0),
                'timestamp': item['timestamp'],
                'date_key': item['date_key'],
                'datetime_key': item.get('datetime_key', '')
            })

        return jsonify({
            'status': 'success',
            'year': year,
            'month': month,
            'day': day,
            'count': len(formatted_data),
            'data': formatted_data
        }), 200

    except Exception as e:
        print(f"Error retrieving data by day: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/date/<date_key>', methods=['GET'])
def get_data_by_date_key(date_key):
    try:
        data = db.get_data_by_date_key(date_key)

        # 转换数据格式以保持与前端的兼容性
        formatted_data = []
        for item in reversed(data):
            formatted_data.append({
                'id': item['id'],
                'humidity': item['humidity'],
                'temperature': item['temperature'],
                'light_intensity': item['light_intensity'],
                'servo_angle': item.get('servo_angle', 0),
                'timestamp': item['timestamp'],
                'date_key': item['date_key'],
                'datetime_key': item.get('datetime_key', '')
            })

        return jsonify({
            'status': 'success',
            'date_key': date_key,
            'count': len(formatted_data),
            'data': formatted_data
        }), 200

    except Exception as e:
        print(f"Error retrieving data by date key: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/hour/<int:year>/<int:month>/<int:day>/<int:hour>', methods=['GET'])
def get_data_by_hour(year, month, day, hour):
    try:
        data = db.get_data_by_hour(year, month, day, hour)

        # 转换数据格式以保持与前端的兼容性
        formatted_data = []
        for item in reversed(data):
            formatted_data.append({
                'id': item['id'],
                'humidity': item['humidity'],
                'temperature': item['temperature'],
                'light_intensity': item['light_intensity'],
                'servo_angle': item.get('servo_angle', 0),
                'timestamp': item['timestamp'],
                'date_key': item['date_key'],
                'datetime_key': item['datetime_key']
            })

        return jsonify({
            'status': 'success',
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'count': len(formatted_data),
            'data': formatted_data
        }), 200

    except Exception as e:
        print(f"Error retrieving data by hour: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/datetime/<datetime_key>', methods=['GET'])
def get_data_by_datetime_key(datetime_key):
    try:
        data = db.get_data_by_datetime_key(datetime_key)

        # 转换数据格式以保持与前端的兼容性
        formatted_data = []
        for item in reversed(data):
            formatted_data.append({
                'id': item['id'],
                'humidity': item['humidity'],
                'temperature': item['temperature'],
                'light_intensity': item['light_intensity'],
                'servo_angle': item.get('servo_angle', 0),
                'timestamp': item['timestamp'],
                'date_key': item['date_key'],
                'datetime_key': item['datetime_key']
            })

        return jsonify({
            'status': 'success',
            'datetime_key': datetime_key,
            'count': len(formatted_data),
            'data': formatted_data
        }), 200

    except Exception as e:
        print(f"Error retrieving data by datetime key: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/sensor-data/hours', methods=['GET'])
def get_available_hours():
    try:
        date_key = request.args.get('date_key')
        hours = db.get_available_hours(date_key)
        return jsonify({
            'status': 'success',
            'hours': hours
        }), 200

    except Exception as e:
        print(f"Error retrieving available hours: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api', methods=['GET'])
def api_info():
    total_records = db.get_data_count()
    latest = db.get_latest_data()

    return jsonify({
        'message': 'ESP8266 Sensor Data Server with SQLite Database',
        'database': {
            'type': 'SQLite',
            'total_records': total_records,
            'last_update': latest['timestamp'] if latest else None
        },
        'endpoints': {
            'POST /sensor-data': 'Receive sensor data',
            'GET /sensor-data': 'Get all sensor data (supports limit and offset)',
            'GET /sensor-data/latest': 'Get latest sensor data',
            'GET /sensor-data/statistics': 'Get data statistics',
            'GET /sensor-data/dates': 'Get available dates with data count',
            'GET /sensor-data/year/<year>': 'Get data by year',
            'GET /sensor-data/month/<year>/<month>': 'Get data by month',
            'GET /sensor-data/day/<year>/<month>/<day>': 'Get data by specific day',
            'GET /sensor-data/date/<date_key>': 'Get data by date key (YYYY-MM-DD)',
            'GET /sensor-data/hour/<year>/<month>/<day>/<hour>': 'Get data by specific hour',
            'GET /sensor-data/datetime/<datetime_key>': 'Get data by datetime key (YYYY-MM-DD-HH)',
            'GET /sensor-data/hours': 'Get available hours with data count (optional: ?date_key=YYYY-MM-DD)',
            'GET /sensor-data/export': 'Export data to JSON',
            'POST /sensor-data/backup': 'Create database backup',
            'DELETE /sensor-data/clear': 'Clear all data',
            'POST /sensor-command': 'Process sensor commands from frontend',
            'GET /get-pending-command': 'ESP8266 get pending commands'
        }
    })

@app.route('/sensor-command', methods=['POST'])
def sensor_command():
    """
    处理传感器指令接口
    接收前端指令并转发给ESP8266
    """
    try:
        print("=" * 50)
        print("[REQUEST] 收到前端命令请求")

        data = request.get_json()
        print(f"[DATA] 请求数据: {data}")

        if not data or 'command' not in data:
            print("[ERROR] 错误: 缺少command参数")
            return jsonify({
                'status': 'error',
                'message': 'Missing command parameter'
            }), 400

        command = data['command']
        print(f"[COMMAND] 提取命令: {command}")

        # 验证指令格式
        if not command.startswith(('Dataup_', 'Watering_', 'ServoTurnTo_')):
            print(f"[ERROR] 错误: 无效的命令格式 - {command}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid command format'
            }), 400

        # 这里可以通过WebSocket、轮询或其他方式与ESP8266通信
        # 由于ESP8266定期发送数据，我们可以将指令存储在全局变量中
        # ESP8266可以在下一次发送数据时检查是否有新指令

        # 使用指令管理器存储指令
        command_manager.set_command(command)

        print(f"[SUCCESS] 指令已存储到CommandManager: {command}")
        print("等待ESP8266获取并转发指令到Arduino Nano...")
        print("=" * 50)

        return jsonify({
            'status': 'success',
            'message': 'Command sent to ESP8266',
            'command': command
        }), 200

    except Exception as e:
        print(f"[ERROR] 处理传感器指令时出错: {str(e)}")
        print("=" * 50)
        return jsonify({
            'status': 'error',
            'message': f'Failed to process command: {str(e)}'
        }), 500

# 使用类来管理指令状态，避免全局变量问题
class CommandManager:
    def __init__(self):
        self.pending_command = None
        self.command_timestamp = None

    def set_command(self, command):
        """设置待处理指令"""
        self.pending_command = command
        self.command_timestamp = datetime.now().isoformat()
        print(f"[SEND] CommandManager: 指令已设置 -> {command} (时间: {self.command_timestamp})")

    def get_command(self):
        """获取并清除待处理指令"""
        command = self.pending_command
        if command:
            print(f"[RECEIVE] CommandManager: 指令已被取出 -> {command}")
            self.pending_command = None
            self.command_timestamp = None
        else:
            print("[EMPTY] CommandManager: 无待处理指令")
        return command

# 创建全局指令管理器实例
command_manager = CommandManager()

@app.route('/get-pending-command', methods=['GET'])
def get_pending_command():
    """
    ESP8266获取待处理指令的接口
    ESP8266定期调用此接口检查是否有新指令
    """
    try:
        print("[CHECK] ESP8266正在检查待处理指令...")
        command = command_manager.get_command()

        if command:
            print(f"[FOUND] 向ESP8266返回指令: {command}")
            return jsonify({
                'status': 'success',
                'has_command': True,
                'command': command
            }), 200
        else:
            print("[EMPTY] 无待处理指令返回给ESP8266")
            return jsonify({
                'status': 'success',
                'has_command': False,
                'command': None
            }), 200

    except Exception as e:
        print(f"[ERROR] 获取待处理指令时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get pending command: {str(e)}'
        }), 500

@app.route('/sensor-data/latest-id', methods=['GET'])
def get_latest_data_id():
    """获取最新数据的ID和时间戳，用于检测数据更新"""
    try:
        latest_data = db.get_latest_data()

        if latest_data:
            return jsonify({
                'status': 'success',
                'id': latest_data['id'],
                'timestamp': latest_data['timestamp'],
                'created_at': latest_data['created_at']
            }), 200
        else:
            return jsonify({
                'status': 'success',
                'id': None,
                'timestamp': None,
                'created_at': None
            }), 200

    except Exception as e:
        print(f"[ERROR] 获取最新数据ID时出错: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get latest data ID: {str(e)}',
            'id': None
        }), 500

@app.route('/admin')
def admin_panel():
    """管理面板页面"""
    try:
        stats = db.get_statistics()
        return render_template('admin.html', statistics=stats)
    except Exception as e:
        return f"Error loading admin panel: {str(e)}"

if __name__ == '__main__':
    import os

    # 获取端口号，云平台通常通过环境变量提供
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'

    print("=" * 60)
    print("ESP32 传感器数据服务器 (SQLite版本)")
    print("=" * 60)
    print(f"数据库文件: sensor_data.db")
    print(f"运行端口: {port}")
    print(f"调试模式: {debug}")
    if debug:
        print(f"本地访问: http://127.0.0.1:{port}")
        print(f"API信息: http://127.0.0.1:{port}/api")
        print(f"管理面板: http://127.0.0.1:{port}/admin")
    print("=" * 60)

    app.run(host='0.0.0.0', port=port, debug=debug)