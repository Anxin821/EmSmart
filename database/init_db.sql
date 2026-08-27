-- ============================================================
-- 智能工厂工作任务管理平台 - 数据库初始化脚本
-- 适用数据库：SQL Server 2019+
-- ============================================================

-- 创建数据库（请根据实际环境修改文件路径）
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'WorkTaskDB')
BEGIN
    CREATE DATABASE WorkTaskDB;
END
GO

USE WorkTaskDB;
GO

-- ============================================================
-- 1. 用户表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
BEGIN
    CREATE TABLE users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) NOT NULL UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        full_name NVARCHAR(100),
        role NVARCHAR(20) NOT NULL DEFAULT 'viewer',   -- admin / engineer / viewer
        email NVARCHAR(100),
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- 默认管理员账户：admin / admin123
-- bcrypt hash for 'admin123'
IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
BEGIN
    INSERT INTO users (username, password_hash, full_name, role, email)
    VALUES ('admin', '$2b$12$LJ3m4ys3Gy0KUMCGiGj0DOK7EppZgMq0KLq3HqPTpAsDxJkWJRn5e', N'系统管理员', 'admin', 'admin@factory.com');
END
GO

-- 默认工程师账户
IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'engineer')
BEGIN
    INSERT INTO users (username, password_hash, full_name, role, email)
    VALUES ('engineer', '$2b$12$LJ3m4ys3Gy0KUMCGiGj0DOK7EppZgMq0KLq3HqPTpAsDxJkWJRn5e', N'张工', 'engineer', 'engineer@factory.com');
END
GO

-- 默认访客账户
IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'viewer')
BEGIN
    INSERT INTO users (username, password_hash, full_name, role, email)
    VALUES ('viewer', '$2b$12$LJ3m4ys3Gy0KUMCGiGj0DOK7EppZgMq0KLq3HqPTpAsDxJkWJRn5e', N'访客', 'viewer', 'viewer@factory.com');
END
GO

-- ============================================================
-- 2. AOI&AI 设备部署表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='aoi_ai_devices' AND xtype='U')
BEGIN
    CREATE TABLE aoi_ai_devices (
        id INT IDENTITY(1,1) PRIMARY KEY,
        device_id NVARCHAR(50) NOT NULL UNIQUE,
        name NVARCHAR(100) NOT NULL,
        device_type NVARCHAR(10) NOT NULL,          -- AOI / AI
        production_line NVARCHAR(10) NOT NULL,       -- 1线-8线
        location NVARCHAR(100),
        ip_address NVARCHAR(50),
        status NVARCHAR(20) NOT NULL DEFAULT N'正常',  -- 正常 / 故障 / 保养中
        responsible_person NVARCHAR(50),
        install_date DATE,
        remark NVARCHAR(500),
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
-- 3. 每周生产数据表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='weekly_production' AND xtype='U')
BEGIN
    CREATE TABLE weekly_production (
        id INT IDENTITY(1,1) PRIMARY KEY,
        year INT NOT NULL,
        week_number INT NOT NULL,
        production_line NVARCHAR(10) NOT NULL,
        project NVARCHAR(50) NOT NULL,              -- A / B / C
        total_output INT NOT NULL DEFAULT 0,
        qualified_count INT NOT NULL DEFAULT 0,
        defect_count AS (total_output - qualified_count),  -- 计算列：不良数
        yield_rate AS (CASE WHEN total_output > 0 THEN ROUND(CAST(qualified_count AS FLOAT) / total_output * 100, 2) ELSE 0 END), -- 计算列：直通率(%)
        recorder NVARCHAR(50),
        updated_at DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT UQ_weekly UNIQUE (year, week_number, production_line, project)
    );
END
GO

-- ============================================================
-- 4. 每月生产数据表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='monthly_production' AND xtype='U')
BEGIN
    CREATE TABLE monthly_production (
        id INT IDENTITY(1,1) PRIMARY KEY,
        year INT NOT NULL,
        month INT NOT NULL,
        production_line NVARCHAR(10) NOT NULL,
        project NVARCHAR(50) NOT NULL,
        monthly_total_output INT NOT NULL DEFAULT 0,
        monthly_qualified_count INT NOT NULL DEFAULT 0,
        monthly_defect_count AS (monthly_total_output - monthly_qualified_count),
        monthly_yield_rate AS (CASE WHEN monthly_total_output > 0 THEN ROUND(CAST(monthly_qualified_count AS FLOAT) / monthly_total_output * 100, 2) ELSE 0 END),
        recorder NVARCHAR(50),
        updated_at DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT UQ_monthly UNIQUE (year, month, production_line, project)
    );
END
GO

-- ============================================================
-- 5. 服务器部署表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='servers' AND xtype='U')
BEGIN
    CREATE TABLE servers (
        id INT IDENTITY(1,1) PRIMARY KEY,
        server_id NVARCHAR(50) NOT NULL UNIQUE,
        name NVARCHAR(100) NOT NULL,
        production_line NVARCHAR(10) NOT NULL,
        rack_location NVARCHAR(50),
        ip_address NVARCHAR(50),
        model NVARCHAR(100),
        os NVARCHAR(50),
        status NVARCHAR(20) NOT NULL DEFAULT N'在线',   -- 在线 / 离线 / 维护
        cpu_usage DECIMAL(5,2) DEFAULT 0,
        memory_usage DECIMAL(5,2) DEFAULT 0,
        disk_usage DECIMAL(5,2) DEFAULT 0,
        responsible_person NVARCHAR(50),
        last_check_time DATETIME,
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
-- 6. 老化架部署表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='aging_racks' AND xtype='U')
BEGIN
    CREATE TABLE aging_racks (
        id INT IDENTITY(1,1) PRIMARY KEY,
        rack_id NVARCHAR(50) NOT NULL UNIQUE,
        name NVARCHAR(100) NOT NULL,
        production_line NVARCHAR(10) NOT NULL,
        location NVARCHAR(100),
        ip_address NVARCHAR(50),
        total_slots INT NOT NULL DEFAULT 0,
        used_slots INT NOT NULL DEFAULT 0,
        status NVARCHAR(20) NOT NULL DEFAULT N'正常',
        responsible_person NVARCHAR(50),
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
-- 7. WiFi AP 部署表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='wifi_aps' AND xtype='U')
BEGIN
    CREATE TABLE wifi_aps (
        id INT IDENTITY(1,1) PRIMARY KEY,
        ap_id NVARCHAR(50) NOT NULL UNIQUE,
        ssid NVARCHAR(100) NOT NULL,
        production_line NVARCHAR(10) NOT NULL,
        ip_address NVARCHAR(50),
        location NVARCHAR(100),
        channel INT DEFAULT 0,
        connected_devices INT DEFAULT 0,
        status NVARCHAR(20) NOT NULL DEFAULT N'在线',
        responsible_person NVARCHAR(50),
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
-- 8. 日常工单表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='work_orders' AND xtype='U')
BEGIN
    CREATE TABLE work_orders (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_number NVARCHAR(50) NOT NULL UNIQUE,
        order_type NVARCHAR(20) NOT NULL,              -- 组装 / 包装
        product_name NVARCHAR(100) NOT NULL,
        priority NVARCHAR(10) NOT NULL DEFAULT N'中',  -- 紧急 / 高 / 中 / 低
        planned_start DATETIME,
        planned_end DATETIME,
        actual_start DATETIME,
        actual_end DATETIME,
        status NVARCHAR(20) NOT NULL DEFAULT N'待开始', -- 待开始 / 进行中 / 已完成 / 挂起
        responsible_person NVARCHAR(50),
        description NVARCHAR(1000),
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
-- 9. 异常BUG表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='bugs' AND xtype='U')
BEGIN
    CREATE TABLE bugs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        bug_id NVARCHAR(50) NOT NULL UNIQUE,
        title NVARCHAR(200) NOT NULL,
        severity NVARCHAR(10) NOT NULL,               -- 致命 / 严重 / 一般 / 建议
        module NVARCHAR(100),
        status NVARCHAR(20) NOT NULL DEFAULT N'新建',  -- 新建 / 确认 / 修复中 / 已解决 / 关闭
        discoverer NVARCHAR(50),
        assignee NVARCHAR(50),
        created_date DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
        deadline DATE,
        solution NVARCHAR(2000),
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
-- 10. 二次开发需求表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='dev_requests' AND xtype='U')
BEGIN
    CREATE TABLE dev_requests (
        id INT IDENTITY(1,1) PRIMARY KEY,
        request_id NVARCHAR(50) NOT NULL UNIQUE,
        title NVARCHAR(200) NOT NULL,
        source NVARCHAR(100),
        priority NVARCHAR(10) NOT NULL DEFAULT N'中',
        status NVARCHAR(20) NOT NULL DEFAULT N'收集',  -- 收集 / 评估 / 开发中 / 测试 / 上线
        expected_date DATE,
        responsible_person NVARCHAR(50),
        progress DECIMAL(5,2) DEFAULT 0,              -- 进度 0-100
        description NVARCHAR(2000),
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
-- 11. 操作日志表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='operation_logs' AND xtype='U')
BEGIN
    CREATE TABLE operation_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) NOT NULL,
        action NVARCHAR(50) NOT NULL,                 -- CREATE / UPDATE / DELETE / LOGIN
        target_type NVARCHAR(50),                     -- 操作对象类型
        target_id NVARCHAR(50),                       -- 操作对象ID
        detail NVARCHAR(1000),
        ip_address NVARCHAR(50),
        created_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- ============================================================
-- 创建索引
-- ============================================================
CREATE NONCLUSTERED INDEX IX_aoi_devices_line ON aoi_ai_devices(production_line);
CREATE NONCLUSTERED INDEX IX_aoi_devices_status ON aoi_ai_devices(status);
CREATE NONCLUSTERED INDEX IX_weekly_line ON weekly_production(production_line);
CREATE NONCLUSTERED INDEX IX_weekly_year_week ON weekly_production(year, week_number);
CREATE NONCLUSTERED INDEX IX_monthly_year_month ON monthly_production(year, month);
CREATE NONCLUSTERED INDEX IX_work_orders_status ON work_orders(status);
CREATE NONCLUSTERED INDEX IX_bugs_status ON bugs(status);
CREATE NONCLUSTERED INDEX IX_bugs_severity ON bugs(severity);
CREATE NONCLUSTERED INDEX IX_dev_requests_status ON dev_requests(status);
GO

PRINT N'数据库初始化完成!';
GO
