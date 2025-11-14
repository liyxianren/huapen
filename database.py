import sqlite3
import json
from datetime import datetime, timedelta
import os
import pytz

class SensorDatabase:
    def __init__(self, db_path="sensor_data.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库，创建表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建传感器数据表，添加年月日时字段
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                humidity REAL NOT NULL,
                temperature REAL NOT NULL,
                light_intensity INTEGER NOT NULL,
                servo_angle INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                hour INTEGER NOT NULL,
                date_key TEXT NOT NULL,
                datetime_key TEXT NOT NULL
            )
        ''')
        
        # 数据库迁移：为现有表添加servo_angle字段（如果不存在）
        try:
            cursor.execute('ALTER TABLE sensor_data ADD COLUMN servo_angle INTEGER DEFAULT 0')
            print("数据库迁移：已添加servo_angle字段")
        except sqlite3.OperationalError:
            # 字段已存在，忽略错误
            pass

        # 创建索引以提高查询性能
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data(timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON sensor_data(created_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_year ON sensor_data(year)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_month ON sensor_data(year, month)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_day ON sensor_data(year, month, day)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date_key ON sensor_data(date_key)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hour ON sensor_data(year, month, day, hour)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_datetime_key ON sensor_data(datetime_key)
        ''')

        conn.commit()
        conn.close()
        print(f"数据库初始化完成: {self.db_path}")

    def add_sensor_data(self, humidity, temperature, light_intensity, servo_angle=0):
        """添加传感器数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 使用北京时间 (UTC+8)
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        timestamp = now.isoformat()
        created_at = now.strftime('%Y-%m-%d %H:%M:%S')
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        date_key = now.strftime('%Y-%m-%d')
        datetime_key = now.strftime('%Y-%m-%d-%H')

        cursor.execute('''
            INSERT INTO sensor_data
            (humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key))

        conn.commit()
        data_id = cursor.lastrowid
        conn.close()

        return {
            'id': data_id,
            'humidity': humidity,
            'temperature': temperature,
            'light_intensity': light_intensity,
            'servo_angle': servo_angle,
            'timestamp': timestamp,
            'created_at': created_at,
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'date_key': date_key,
            'datetime_key': datetime_key
        }

    def get_all_data(self, limit=None, offset=0):
        """获取所有传感器数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if limit:
            cursor.execute('''
                SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
                FROM sensor_data
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        else:
            cursor.execute('''
                SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
                FROM sensor_data
                ORDER BY id DESC
            ''')

        rows = cursor.fetchall()
        conn.close()

        # 转换为字典格式
        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            })

        return data

    def get_latest_data(self):
        """获取最新的传感器数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
            FROM sensor_data
            ORDER BY id DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            }
        return None

    def get_data_count(self):
        """获取数据总数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM sensor_data')
        count = cursor.fetchone()[0]
        conn.close()

        return count

    def get_data_by_date_range(self, start_date, end_date):
        """根据日期范围获取数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
            FROM sensor_data
            WHERE created_at BETWEEN ? AND ?
            ORDER BY id DESC
        ''', (start_date, end_date))

        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            })

        return data

    def get_data_by_year(self, year):
        """根据年份获取数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
            FROM sensor_data
            WHERE year = ?
            ORDER BY id DESC
        ''', (year,))

        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            })

        return data

    def get_data_by_month(self, year, month):
        """根据年月获取数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
            FROM sensor_data
            WHERE year = ? AND month = ?
            ORDER BY id DESC
        ''', (year, month))

        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            })

        return data

    def get_data_by_day(self, year, month, day):
        """根据具体日期获取数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
            FROM sensor_data
            WHERE year = ? AND month = ? AND day = ?
            ORDER BY id DESC
        ''', (year, month, day))

        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            })

        return data

    def get_data_by_date_key(self, date_key):
        """根据日期键获取数据 (格式: YYYY-MM-DD)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
            FROM sensor_data
            WHERE date_key = ?
            ORDER BY id DESC
        ''', (date_key,))

        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            })

        return data

    def get_data_by_hour(self, year, month, day, hour):
        """根据具体小时获取数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
            FROM sensor_data
            WHERE year = ? AND month = ? AND day = ? AND hour = ?
            ORDER BY id DESC
        ''', (year, month, day, hour))

        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            })

        return data

    def get_data_by_datetime_key(self, datetime_key):
        """根据日期时间键获取数据 (格式: YYYY-MM-DD-HH)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, humidity, temperature, light_intensity, servo_angle, timestamp, created_at, year, month, day, hour, date_key, datetime_key
            FROM sensor_data
            WHERE datetime_key = ?
            ORDER BY id DESC
        ''', (datetime_key,))

        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'humidity': row[1],
                'temperature': row[2],
                'light_intensity': row[3],
                'servo_angle': row[4],
                'timestamp': row[5],
                'created_at': row[6],
                'year': row[7],
                'month': row[8],
                'day': row[9],
                'hour': row[10],
                'date_key': row[11],
                'datetime_key': row[12]
            })

        return data

    def get_available_dates(self):
        """获取有数据的所有日期"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT date_key, year, month, day, COUNT(*) as count
            FROM sensor_data
            GROUP BY date_key
            ORDER BY date_key DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        dates = []
        for row in rows:
            dates.append({
                'date_key': row[0],
                'year': row[1],
                'month': row[2],
                'day': row[3],
                'count': row[4]
            })

        return dates

    def get_available_hours(self, date_key=None):
        """获取有数据的所有小时"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if date_key:
            cursor.execute('''
                SELECT DISTINCT datetime_key, year, month, day, hour, COUNT(*) as count
                FROM sensor_data
                WHERE date_key = ?
                GROUP BY datetime_key
                ORDER BY datetime_key DESC
            ''', (date_key,))
        else:
            cursor.execute('''
                SELECT DISTINCT datetime_key, year, month, day, hour, COUNT(*) as count
                FROM sensor_data
                GROUP BY datetime_key
                ORDER BY datetime_key DESC
            ''')

        rows = cursor.fetchall()
        conn.close()

        hours = []
        for row in rows:
            hours.append({
                'datetime_key': row[0],
                'year': row[1],
                'month': row[2],
                'day': row[3],
                'hour': row[4],
                'count': row[5]
            })

        return hours

    def get_statistics(self):
        """获取数据统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取基本统计
        cursor.execute('''
            SELECT
                COUNT(*) as total_count,
                AVG(humidity) as avg_humidity,
                MIN(humidity) as min_humidity,
                MAX(humidity) as max_humidity,
                AVG(temperature) as avg_temperature,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                AVG(light_intensity) as avg_light,
                MIN(light_intensity) as min_light,
                MAX(light_intensity) as max_light,
                AVG(servo_angle) as avg_servo,
                MIN(servo_angle) as min_servo,
                MAX(servo_angle) as max_servo,
                MIN(created_at) as first_record,
                MAX(created_at) as last_record
            FROM sensor_data
        ''')

        row = cursor.fetchone()
        conn.close()

        if row and row[0] > 0:
            return {
                'total_count': row[0],
                'humidity': {
                    'avg': round(row[1], 2) if row[1] else 0,
                    'min': row[2] if row[2] else 0,
                    'max': row[3] if row[3] else 0
                },
                'temperature': {
                    'avg': round(row[4], 2) if row[4] else 0,
                    'min': row[5] if row[5] else 0,
                    'max': row[6] if row[6] else 0
                },
                'light_intensity': {
                    'avg': round(row[7], 2) if row[7] else 0,
                    'min': row[8] if row[8] else 0,
                    'max': row[9] if row[9] else 0
                },
                'servo_angle': {
                    'avg': round(row[10], 2) if row[10] else 0,
                    'min': row[11] if row[11] else 0,
                    'max': row[12] if row[12] else 0
                },
                'time_range': {
                    'first_record': row[13],
                    'last_record': row[14]
                }
            }
        else:
            return {
                'total_count': 0,
                'humidity': {'avg': 0, 'min': 0, 'max': 0},
                'temperature': {'avg': 0, 'min': 0, 'max': 0},
                'light_intensity': {'avg': 0, 'min': 0, 'max': 0},
                'servo_angle': {'avg': 0, 'min': 0, 'max': 0},
                'time_range': {'first_record': None, 'last_record': None}
            }

    def delete_old_data(self, days_to_keep=30):
        """删除指定天数之前的旧数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('DELETE FROM sensor_data WHERE created_at < ?', (cutoff_str,))
        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()

        return deleted_count

    def clear_all_data(self):
        """清空所有数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM sensor_data')
        deleted_count = cursor.rowcount

        conn.commit()
        conn.close()

        return deleted_count

    def export_to_json(self, file_path=None):
        """导出数据到JSON文件"""
        if not file_path:
            file_path = f"sensor_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = self.get_all_data()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return file_path, len(data)

    def import_from_json(self, file_path):
        """从JSON文件导入数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        imported_count = 0
        for item in data:
            try:
                servo_angle = item.get('servo_angle', 0)  # 兼容旧数据
                self.add_sensor_data(
                    item['humidity'],
                    item['temperature'],
                    item['light_intensity'],
                    servo_angle
                )
                imported_count += 1
            except Exception as e:
                print(f"导入数据时发生错误: {e}")

        return imported_count

    def backup_database(self, backup_path=None):
        """备份数据库"""
        if not backup_path:
            backup_path = f"sensor_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

        import shutil
        shutil.copy2(self.db_path, backup_path)
        return backup_path

# 测试函数
def test_database():
    """测试数据库功能"""
    print("测试SQLite数据库功能...")

    # 创建数据库实例
    db = SensorDatabase("test_sensor.db")

    # 添加测试数据
    print("添加测试数据...")
    for i in range(5):
        data = db.add_sensor_data(
            humidity=50.0 + i,
            temperature=25.0 + i,
            light_intensity=500 + i * 100
        )
        print(f"添加数据: {data}")

    # 获取所有数据
    print("\n获取所有数据:")
    all_data = db.get_all_data()
    for data in all_data:
        print(f"ID: {data['id']}, 湿度: {data['humidity']}%, 温度: {data['temperature']}°C, 光照: {data['light_intensity']} lux")

    # 获取最新数据
    print("\n获取最新数据:")
    latest = db.get_latest_data()
    if latest:
        print(f"最新数据: 湿度{latest['humidity']}%, 温度{latest['temperature']}°C, 光照{latest['light_intensity']} lux")

    # 获取统计信息
    print("\n获取统计信息:")
    stats = db.get_statistics()
    print(f"总记录数: {stats['total_count']}")
    print(f"湿度范围: {stats['humidity']['min']}% - {stats['humidity']['max']}% (平均: {stats['humidity']['avg']}%)")
    print(f"温度范围: {stats['temperature']['min']}°C - {stats['temperature']['max']}°C (平均: {stats['temperature']['avg']}°C)")

    print("数据库测试完成!")

if __name__ == "__main__":
    test_database()