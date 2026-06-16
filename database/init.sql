-- 智能生产线监控系统数据库初始化脚本
-- Database: production_system
-- Author: System
-- Version: 1.0.0

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 注意：不使用USE语句，因为数据库由docker-compose自动创建
-- 数据库名称: production_system (与docker-compose.yml一致)

-- ============================================
-- 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS t_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码(BCrypt加密)',
    email VARCHAR(100) COMMENT '邮箱',
    role ENUM('admin', 'user') DEFAULT 'user' COMMENT '角色',
    status TINYINT DEFAULT 1 COMMENT '状态: 0禁用/1启用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_username (username),
    INDEX idx_email (email),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 分类表
-- ============================================
CREATE TABLE IF NOT EXISTS t_category (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '分类ID',
    name VARCHAR(50) NOT NULL COMMENT '分类名称',
    parent_id BIGINT DEFAULT 0 COMMENT '父分类ID',
    sort_order INT DEFAULT 0 COMMENT '排序',
    status TINYINT DEFAULT 1 COMMENT '状态: 0删除/1正常',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_parent_id (parent_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分类表';

-- ============================================
-- 数据表
-- ============================================
CREATE TABLE IF NOT EXISTS t_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '数据ID',
    name VARCHAR(100) NOT NULL COMMENT '数据名称',
    type VARCHAR(50) NOT NULL COMMENT '数据类型',
    value TEXT COMMENT '数据值',
    description TEXT COMMENT '描述',
    category_id BIGINT COMMENT '分类ID',
    user_id BIGINT NOT NULL COMMENT '创建用户ID',
    status TINYINT DEFAULT 1 COMMENT '状态: 0删除/1正常',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name),
    INDEX idx_type (type),
    INDEX idx_user_id (user_id),
    INDEX idx_category_id (category_id),
    INDEX idx_create_time (create_time),
    INDEX idx_status (status),
    CONSTRAINT fk_data_user FOREIGN KEY (user_id) REFERENCES t_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_data_category FOREIGN KEY (category_id) REFERENCES t_category(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据表';

-- ============================================
-- 操作日志表
-- ============================================
CREATE TABLE IF NOT EXISTS t_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    user_id BIGINT COMMENT '操作用户ID',
    username VARCHAR(50) COMMENT '操作用户名',
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    module VARCHAR(50) COMMENT '操作模块',
    description TEXT COMMENT '操作描述',
    ip VARCHAR(50) COMMENT 'IP地址',
    user_agent VARCHAR(500) COMMENT '用户代理',
    status TINYINT DEFAULT 1 COMMENT '状态: 0删除/1正常',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_module (module),
    INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ============================================
-- 系统配置表
-- ============================================
CREATE TABLE IF NOT EXISTS t_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    config_type VARCHAR(20) DEFAULT 'string' COMMENT '配置类型',
    description VARCHAR(200) COMMENT '配置描述',
    status TINYINT DEFAULT 1 COMMENT '状态: 0删除/1正常',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- ============================================
-- 生产线表
-- ============================================
CREATE TABLE IF NOT EXISTS production_line (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    line_code VARCHAR(50) NOT NULL COMMENT '生产线编号',
    line_name VARCHAR(100) NOT NULL COMMENT '生产线名称',
    description TEXT COMMENT '生产线描述',
    status ENUM('running', 'stopped', 'maintenance', 'error') DEFAULT 'stopped' COMMENT '状态',
    capacity INT DEFAULT 0 COMMENT '产能',
    location VARCHAR(100) COMMENT '位置',
    supervisor VARCHAR(50) COMMENT '负责人',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_line_code (line_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产线表';

-- ============================================
-- 设备表
-- ============================================
CREATE TABLE IF NOT EXISTS equipment (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
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
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_equipment_code (equipment_code),
    INDEX idx_line_id (line_id),
    INDEX idx_status (status),
    CONSTRAINT fk_equipment_line FOREIGN KEY (line_id) REFERENCES production_line(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备表';

-- ============================================
-- 传感器表
-- ============================================
CREATE TABLE IF NOT EXISTS sensor (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    sensor_code VARCHAR(50) NOT NULL COMMENT '传感器编号',
    sensor_name VARCHAR(100) NOT NULL COMMENT '传感器名称',
    sensor_type VARCHAR(50) COMMENT '传感器类型',
    equipment_id BIGINT COMMENT '所属设备ID',
    unit VARCHAR(20) COMMENT '单位',
    min_value DECIMAL(10,4) COMMENT '最小值',
    max_value DECIMAL(10,4) COMMENT '最大值',
    threshold_low DECIMAL(10,4) COMMENT '告警阈值-低',
    threshold_high DECIMAL(10,4) COMMENT '告警阈值-高',
    status ENUM('normal', 'warning', 'error', 'offline') DEFAULT 'normal' COMMENT '状态',
    `last_value` DECIMAL(10,4) COMMENT '最后读数',
    last_read_time DATETIME COMMENT '最后读取时间',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_sensor_code (sensor_code),
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_status (status),
    CONSTRAINT fk_sensor_equipment FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='传感器表';

-- ============================================
-- 生产任务表
-- ============================================
CREATE TABLE IF NOT EXISTS production_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
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
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_task_code (task_code),
    INDEX idx_line_id (line_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产任务表';

-- ============================================
-- 生产记录表
-- ============================================
CREATE TABLE IF NOT EXISTS production_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
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
    status TINYINT DEFAULT 1 COMMENT '状态: 0删除/1正常',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_task_id (task_id),
    INDEX idx_record_time (record_time),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产记录表';

-- ============================================
-- 告警记录表
-- ============================================
CREATE TABLE IF NOT EXISTS alert_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
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
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_alert_code (alert_code),
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_sensor_id (sensor_id),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='告警记录表';

-- ============================================
-- 初始数据
-- ============================================

-- 插入默认管理员账号 (密码: admin123)
-- BCrypt hash generated by backend
INSERT INTO t_user (username, password, email, role, status) VALUES
('admin', '$2b$12$8lv876iYPjXEm6WLqi90FOeWtigrH3/1TBPgy1A7COsNpuBWzkA0C', 'admin@example.com', 'admin', 1)
ON DUPLICATE KEY UPDATE username = username;

-- 插入默认分类
INSERT INTO t_category (name, parent_id, sort_order) VALUES
('默认分类', 0, 0),
('文本数据', 0, 1),
('数字数据', 0, 2),
('日期数据', 0, 3)
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- 插入默认系统配置
INSERT INTO t_config (config_key, config_value, config_type, description) VALUES
('system_name', '数据管理系统', 'string', '系统名称'),
('page_size', '10', 'integer', '默认分页大小'),
('theme', 'light', 'string', '系统主题'),
('language', 'zh-CN', 'string', '系统语言'),
('backup_enabled', 'true', 'boolean', '是否启用自动备份')
ON DUPLICATE KEY UPDATE config_key = config_key;

-- 插入示例数据
INSERT INTO t_data (name, type, value, description, user_id, category_id) VALUES
('示例数据1', '文本', '这是一个示例文本数据', '用于演示的示例数据', 1, 1),
('示例数据2', '数字', '12345', '示例数字数据', 1, 2),
('示例数据3', '日期', '2024-01-01', '示例日期数据', 1, 3);

-- 插入生产线示例数据
INSERT INTO production_line (line_code, line_name, description, status, capacity, location, supervisor) VALUES
('LINE001', '生产线A', '主要生产线，负责产品组装', 'running', 1000, '车间1', '张三'),
('LINE002', '生产线B', '辅助生产线，负责产品包装', 'running', 800, '车间2', '李四'),
('LINE003', '生产线C', '备用生产线', 'stopped', 500, '车间3', '王五')
ON DUPLICATE KEY UPDATE line_code = line_code;

-- 插入设备示例数据
INSERT INTO equipment (equipment_code, equipment_name, equipment_type, line_id, status, model, manufacturer, temperature, pressure, speed) VALUES
('EQ001', '组装机器人1号', '机器人', 1, 'running', 'RB-2000', 'TechCorp', 35.5, 1.2, 120.5),
('EQ002', '组装机器人2号', '机器人', 1, 'running', 'RB-2000', 'TechCorp', 36.2, 1.1, 118.8),
('EQ003', '包装机1号', '包装设备', 2, 'running', 'PK-500', 'PackMaster', 28.0, 0.8, 85.0),
('EQ004', '检测仪1号', '检测设备', 1, 'idle', 'DT-100', 'DetectPro', 25.0, 1.0, 0),
('EQ005', '输送带1号', '传输设备', 1, 'running', 'CV-300', 'ConveyTech', 30.5, 0.5, 150.0)
ON DUPLICATE KEY UPDATE equipment_code = equipment_code;

-- 插入传感器示例数据
INSERT INTO sensor (sensor_code, sensor_name, sensor_type, equipment_id, unit, min_value, max_value, threshold_low, threshold_high, status, `last_value`, last_read_time) VALUES
('S001', '温度传感器1', '温度', 1, '°C', 0, 100, 20, 60, 'normal', 35.5, NOW()),
('S002', '压力传感器1', '压力', 1, 'MPa', 0, 5, 0.5, 2.0, 'normal', 1.2, NOW()),
('S003', '速度传感器1', '速度', 1, 'm/s', 0, 200, 50, 150, 'normal', 120.5, NOW()),
('S004', '温度传感器2', '温度', 2, '°C', 0, 100, 20, 60, 'normal', 36.2, NOW()),
('S005', '压力传感器2', '压力', 2, 'MPa', 0, 5, 0.5, 2.0, 'normal', 1.1, NOW())
ON DUPLICATE KEY UPDATE sensor_code = sensor_code;

-- 插入生产任务示例数据
INSERT INTO production_task (task_code, task_name, line_id, product_name, product_spec, quantity, completed_quantity, status, priority, start_time, end_time) VALUES
('TASK001', '产品A批量生产', 1, '产品A', 'A-100', 500, 250, 'in_progress', 8, DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_ADD(NOW(), INTERVAL 1 DAY)),
('TASK002', '产品B批量生产', 2, '产品B', 'B-200', 300, 0, 'pending', 5, DATE_ADD(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 3 DAY)),
('TASK003', '产品C批量生产', 1, '产品C', 'C-300', 200, 200, 'completed', 6, DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY))
ON DUPLICATE KEY UPDATE task_code = task_code;

-- ============================================
-- 创建视图
-- ============================================

-- 数据统计视图
CREATE OR REPLACE VIEW v_data_statistics AS
SELECT
    type,
    COUNT(*) as count,
    MAX(update_time) as last_update
FROM t_data
WHERE status = 1
GROUP BY type;

-- 用户活动视图
CREATE OR REPLACE VIEW v_user_activity AS
SELECT
    u.id as user_id,
    u.username,
    COUNT(l.id) as action_count,
    MAX(l.create_time) as last_action
FROM t_user u
LEFT JOIN t_log l ON u.id = l.user_id
WHERE u.status = 1
GROUP BY u.id, u.username;

-- ============================================
-- 创建存储过程
-- ============================================

DELIMITER //

-- 清理过期日志存储过程
CREATE PROCEDURE IF NOT EXISTS sp_clean_old_logs(IN days INT)
BEGIN
    DELETE FROM t_log
    WHERE create_time < DATE_SUB(NOW(), INTERVAL days DAY);
    SELECT ROW_COUNT() as deleted_count;
END //

-- 获取统计数据存储过程
CREATE PROCEDURE IF NOT EXISTS sp_get_statistics()
BEGIN
    SELECT
        (SELECT COUNT(*) FROM t_data WHERE status = 1) as total_data,
        (SELECT COUNT(*) FROM t_user WHERE status = 1) as total_users,
        (SELECT COUNT(*) FROM t_data WHERE status = 1 AND DATE(create_time) = CURDATE()) as today_data,
        (SELECT COUNT(DISTINCT type) FROM t_data WHERE status = 1) as type_count;
END //

DELIMITER ;

-- ============================================
-- 完成提示
-- ============================================
SELECT '数据库初始化完成!' as message;
