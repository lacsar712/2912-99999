"""
生产线监控系统 - 数据库初始化脚本
使用Python实现数据库表创建和初始数据插入
支持MySQL, PostgreSQL, SQLite
"""
import pymysql
import pymysql.cursors
import sys
import os


class DatabaseInitializer:
    """数据库初始化类"""

    def __init__(self, db_type='mysql', host='localhost', port=3306,
                 user='root', password='123456', database='production_system'):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        """建立数据库连接"""
        try:
            if self.db_type == 'mysql':
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
            elif self.db_type == 'sqlite':
                import sqlite3
                self.connection = sqlite3.connect(self.database)
            else:
                raise ValueError(f"不支持的数据库类型: {self.db_type}")

            print(f"✓ 成功连接到 {self.db_type} 数据库")
            return True
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
            return False

    def create_database(self):
        """创建数据库"""
        try:
            if self.db_type == 'mysql':
                # 先连接不带数据库名的连接
                conn = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    charset='utf8mb4'
                )
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn.close()
                print(f"✓ 数据库 {self.database} 创建成功")
            elif self.db_type == 'sqlite':
                # SQLite会自动创建数据库
                print(f"✓ SQLite数据库将自动创建")
        except Exception as e:
            print(f"✗ 创建数据库失败: {e}")
            return False
        return True

    def create_tables(self):
        """创建所有数据表"""
        tables = [
            # 生产线表
            """
            CREATE TABLE IF NOT EXISTS production_line (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '生产线ID',
                line_code VARCHAR(50) NOT NULL COMMENT '生产线编号',
                line_name VARCHAR(100) NOT NULL COMMENT '生产线名称',
                description TEXT COMMENT '生产线描述',
                status ENUM('running', 'stopped', 'maintenance', 'error') DEFAULT 'stopped' COMMENT '状态',
                capacity INT DEFAULT 0 COMMENT '产能',
                location VARCHAR(100) COMMENT '位置',
                supervisor VARCHAR(50) COMMENT '负责人',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_line_code (line_code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生产线表'
            """,

            # 生产设备表
            """
            CREATE TABLE IF NOT EXISTS equipment (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '设备ID',
                equipment_code VARCHAR(50) NOT NULL COMMENT '设备编号',
                equipment_name VARCHAR(100) NOT NULL COMMENT '设备名称',
                equipment_type VARCHAR(50) COMMENT '设备类型',
                line_id BIGINT COMMENT '所属生产线ID',
                status ENUM('running', 'idle', 'maintenance', 'error', 'offline') DEFAULT 'offline' COMMENT '状态',
                model VARCHAR(100) COMMENT '型号',
                manufacturer VARCHAR(100) COMMENT '制造商',
                purchase_date DATE COMMENT '购买日期',
                install_date DATE COMMENT '安装日期',
                runtime_hours DECIMAL(10,2) DEFAULT 0 COMMENT '运行时长(小时)',
                temperature DECIMAL(5,2) COMMENT '当前温度',
                pressure DECIMAL(7,2) COMMENT '当前压力',
                speed DECIMAL(8,2) COMMENT '运行速度',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_equipment_code (equipment_code),
                KEY idx_line_id (line_id),
                KEY idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生产设备表'
            """,

            # 传感器表
            """
            CREATE TABLE IF NOT EXISTS sensor (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '传感器ID',
                sensor_code VARCHAR(50) NOT NULL COMMENT '传感器编号',
                sensor_name VARCHAR(100) NOT NULL COMMENT '传感器名称',
                sensor_type VARCHAR(50) COMMENT '传感器类型(温度/压力/湿度/速度等)',
                equipment_id BIGINT COMMENT '所属设备ID',
                unit VARCHAR(20) COMMENT '单位',
                min_value DECIMAL(10,4) COMMENT '最小值',
                max_value DECIMAL(10,4) COMMENT '最大值',
                threshold_low DECIMAL(10,4) COMMENT '告警阈值-低',
                threshold_high DECIMAL(10,4) COMMENT '告警阈值-高',
                status ENUM('normal', 'warning', 'error', 'offline') DEFAULT 'normal' COMMENT '状态',
                `last_value` DECIMAL(10,4) COMMENT '最后读数',
                last_read_time DATETIME COMMENT '最后读取时间',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_sensor_code (sensor_code),
                KEY idx_equipment_id (equipment_id),
                KEY idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器表'
            """,

            # 生产任务表
            """
            CREATE TABLE IF NOT EXISTS production_task (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
                task_code VARCHAR(50) NOT NULL COMMENT '任务编号',
                task_name VARCHAR(100) NOT NULL COMMENT '任务名称',
                line_id BIGINT COMMENT '生产线ID',
                product_name VARCHAR(100) COMMENT '产品名称',
                product_spec VARCHAR(100) COMMENT '产品规格',
                quantity INT COMMENT '计划数量',
                completed_quantity INT DEFAULT 0 COMMENT '已完成数量',
                status ENUM('pending', 'in_progress', 'paused', 'completed', 'cancelled') DEFAULT 'pending' COMMENT '状态',
                priority INT DEFAULT 5 COMMENT '优先级(1-10)',
                start_time DATETIME COMMENT '计划开始时间',
                end_time DATETIME COMMENT '计划结束时间',
                actual_start_time DATETIME COMMENT '实际开始时间',
                actual_end_time DATETIME COMMENT '实际结束时间',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_task_code (task_code),
                KEY idx_line_id (line_id),
                KEY idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生产任务表'
            """,

            # 生产数据记录表
            """
            CREATE TABLE IF NOT EXISTS production_record (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
                equipment_id BIGINT NOT NULL COMMENT '设备ID',
                task_id BIGINT COMMENT '任务ID',
                product_count INT DEFAULT 0 COMMENT '生产数量',
                qualified_count INT DEFAULT 0 COMMENT '合格数量',
                defect_count INT DEFAULT 0 COMMENT '缺陷数量',
                yield_rate DECIMAL(5,2) COMMENT '良品率',
                temperature DECIMAL(5,2) COMMENT '平均温度',
                humidity DECIMAL(5,2) COMMENT '平均湿度',
                duration INT COMMENT '运行时长(秒)',
                efficiency DECIMAL(5,2) COMMENT '生产效率',
                record_time DATETIME NOT NULL COMMENT '记录时间',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                KEY idx_equipment_id (equipment_id),
                KEY idx_task_id (task_id),
                KEY idx_record_time (record_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生产数据记录表'
            """,

            # 告警记录表
            """
            CREATE TABLE IF NOT EXISTS alert_record (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '告警ID',
                alert_code VARCHAR(50) NOT NULL COMMENT '告警编号',
                alert_type VARCHAR(50) COMMENT '告警类型',
                equipment_id BIGINT COMMENT '设备ID',
                sensor_id BIGINT COMMENT '传感器ID',
                severity ENUM('info', 'warning', 'error', 'critical') DEFAULT 'warning' COMMENT '严重程度',
                message TEXT COMMENT '告警消息',
                value DECIMAL(10,4) COMMENT '告警值',
                threshold DECIMAL(10,4) COMMENT '阈值',
                status ENUM('active', 'acknowledged', 'resolved') DEFAULT 'active' COMMENT '状态',
                resolved_time DATETIME COMMENT '解决时间',
                resolve_note TEXT COMMENT '解决备注',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                KEY idx_equipment_id (equipment_id),
                KEY idx_sensor_id (sensor_id),
                KEY idx_status (status),
                KEY idx_severity (severity),
                KEY idx_create_time (create_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警记录表'
            """,

            # 用户表
            """
            CREATE TABLE IF NOT EXISTS user (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
                username VARCHAR(50) NOT NULL COMMENT '用户名',
                password VARCHAR(255) NOT NULL COMMENT '密码',
                email VARCHAR(100) COMMENT '邮箱',
                role ENUM('admin', 'operator', 'viewer') DEFAULT 'viewer' COMMENT '角色',
                status TINYINT DEFAULT 1 COMMENT '状态(0禁用/1启用)',
                last_login DATETIME COMMENT '最后登录时间',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_username (username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表'
            """,

            # 操作日志表
            """
            CREATE TABLE IF NOT EXISTS operation_log (
                id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
                user_id BIGINT COMMENT '操作用户ID',
                username VARCHAR(50) COMMENT '操作用户名',
                action VARCHAR(50) NOT NULL COMMENT '操作类型',
                target_type VARCHAR(50) COMMENT '目标类型',
                target_id BIGINT COMMENT '目标ID',
                description TEXT COMMENT '操作描述',
                ip VARCHAR(50) COMMENT 'IP地址',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                KEY idx_user_id (user_id),
                KEY idx_action (action),
                KEY idx_create_time (create_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表'
            """
        ]

        try:
            with self.connection.cursor() as cursor:
                for sql in tables:
                    cursor.execute(sql)
            self.connection.commit()
            print(f"✓ 所有数据表创建成功")
            return True
        except Exception as e:
            print(f"✗ 创建数据表失败: {e}")
            return False

    def insert_initial_data(self):
        """插入初始数据"""
        import bcrypt
        from datetime import datetime, timedelta
        import random

        # 加密密码
        admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        operator_password = bcrypt.hashpw('operator123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        initial_data = [
            # 用户数据
            """
            INSERT INTO user (username, password, email, role, status) VALUES
            ('admin', %s, 'admin@production.com', 'admin', 1),
            ('operator', %s, 'operator@production.com', 'operator', 1),
            ('viewer', %s, 'viewer@production.com', 'viewer', 1)
            ON DUPLICATE KEY UPDATE username = username
            """,
            admin_password, operator_password, admin_password,

            # 生产线数据
            """
            INSERT INTO production_line (line_code, line_name, description, status, capacity, location, supervisor) VALUES
            ('LINE-001', '汽车零部件生产线', '主要生产汽车发动机零部件', 'running', 1000, '车间A-1', '张工'),
            ('LINE-002', '电子产品生产线', '生产电子控制单元', 'running', 800, '车间A-2', '李工'),
            ('LINE-003', '包装生产线', '产品包装线', 'stopped', 2000, '车间B-1', '王工')
            ON DUPLICATE KEY UPDATE line_name = VALUES(line_name)
            """,

            # 设备数据
            """
            INSERT INTO equipment (equipment_code, equipment_name, equipment_type, line_id, status, model, manufacturer, purchase_date, install_date, runtime_hours, temperature, pressure, speed) VALUES
            ('EQ-001', '数控车床A1', 'CNC', 1, 'running', 'CNC-5000', '西门子', '2023-01-15', '2023-03-01', 4500.00, 45.5, 0.8, 1200),
            ('EQ-002', '数控车床A2', 'CNC', 1, 'running', 'CNC-5000', '西门子', '2023-01-15', '2023-03-01', 4200.00, 42.3, 0.75, 1150),
            ('EQ-003', '焊接机器人B1', 'Robot', 1, 'running', 'XR-200', 'ABB', '2023-02-20', '2023-04-15', 3200.00, 35.0, 0.5, 800),
            ('EQ-004', '贴片机C1', 'SMT', 2, 'running', 'SM-480', '松下', '2023-03-10', '2023-05-01', 2800.00, 28.5, 0.3, 2000),
            ('EQ-005', '回流焊D1', 'Reflow', 2, 'idle', 'RF-300', '劲拓', '2023-03-10', '2023-05-01', 1500.00, 180.0, 0.1, 50),
            ('EQ-006', '包装机E1', 'Packaging', 3, 'offline', 'PK-100', '发那科', '2023-04-01', '2023-06-01', 800.00, 22.0, 0.2, 100)
            ON DUPLICATE KEY UPDATE equipment_name = VALUES(equipment_name)
            """,

            # 传感器数据
            """
            INSERT INTO sensor (sensor_code, sensor_name, sensor_type, equipment_id, unit, min_value, max_value, threshold_low, threshold_high, status, `last_value`, last_read_time) VALUES
            ('TEMP-001', '主轴温度传感器', 'temperature', 1, '℃', 0, 100, 20, 60, 'normal', 45.5, NOW()),
            ('TEMP-002', '主轴温度传感器', 'temperature', 2, '℃', 0, 100, 20, 60, 'normal', 42.3, NOW()),
            ('TEMP-003', '环境温度传感器', 'temperature', 3, '℃', -20, 80, 10, 50, 'normal', 35.0, NOW()),
            ('PRES-001', '气压传感器', 'pressure', 1, 'MPa', 0, 2, 0.3, 1.0, 'normal', 0.8, NOW()),
            ('PRES-002', '气压传感器', 'pressure', 2, 'MPa', 0, 2, 0.3, 1.0, 'normal', 0.75, NOW()),
            ('SPEED-001', '主轴转速传感器', 'speed', 1, 'rpm', 0, 3000, 500, 2000, 'normal', 1200, NOW()),
            ('SPEED-002', '主轴转速传感器', 'speed', 2, 'rpm', 0, 3000, 500, 2000, 'normal', 1150, NOW()),
            ('VIB-001', '振动传感器', 'vibration', 1, 'mm/s', 0, 50, 0, 15, 'normal', 3.2, NOW()),
            ('HUM-001', '湿度传感器', 'humidity', 4, '%', 0, 100, 30, 70, 'normal', 45.0, NOW())
            ON DUPLICATE KEY UPDATE sensor_name = VALUES(sensor_name)
            """,

            # 生产任务数据
            """
            INSERT INTO production_task (task_code, task_name, line_id, product_name, product_spec, quantity, completed_quantity, status, priority, start_time, end_time, actual_start_time) VALUES
            ('TASK-20240201', '发动机缸体生产', 1, '发动机缸体', 'D4-2.0L', 500, 320, 'in_progress', 9, '2024-02-01 08:00:00', '2024-02-05 18:00:00', '2024-02-01 08:15:00'),
            ('TASK-20240202', '曲轴加工', 1, '曲轴', 'Q5-1.5L', 300, 150, 'in_progress', 8, '2024-02-02 08:00:00', '2024-02-04 18:00:00', '2024-02-02 08:30:00'),
            ('TASK-20240203', 'ECU板生产', 2, 'ECU控制板', 'ECU-9000', 1000, 600, 'in_progress', 7, '2024-02-01 08:00:00', '2024-02-10 18:00:00', '2024-02-01 09:00:00'),
            ('TASK-20240204', '产品包装', 3, '包装箱', 'BOX-001', 2000, 0, 'pending', 5, '2024-02-05 08:00:00', '2024-02-07 18:00:00', NULL)
            ON DUPLICATE KEY UPDATE task_name = VALUES(task_name)
            """,
        ]

        try:
            with self.connection.cursor() as cursor:
                # 插入用户数据
                cursor.execute(initial_data[0], initial_data[1:4])

                # 插入其他初始数据
                for sql in initial_data[4:]:
                    cursor.execute(sql)

            self.connection.commit()
            print(f"✓ 初始数据插入成功")
            return True
        except Exception as e:
            print(f"✗ 插入初始数据失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("✓ 数据库连接已关闭")


def main():
    """主函数"""
    print("=" * 50)
    print("生产线监控系统 - 数据库初始化")
    print("=" * 50)

    # 数据库配置
    db_type = os.environ.get('DB_TYPE', 'mysql')
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', 3306))
    user = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASSWORD', '123456')
    database = os.environ.get('DB_NAME', 'production_system')

    print(f"\n数据库类型: {db_type}")
    print(f"主机: {host}:{port}")
    print(f"数据库: {database}")
    print("-" * 50)

    # 初始化数据库
    initializer = DatabaseInitializer(
        db_type=db_type,
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

    # 执行初始化
    if initializer.connect():
        if initializer.create_database():
            initializer.create_tables()
            initializer.insert_initial_data()

    initializer.close()
    print("\n" + "=" * 50)
    print("数据库初始化完成!")
    print("=" * 50)


if __name__ == '__main__':
    main()
