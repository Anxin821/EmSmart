-- ============================================================
-- 智能工厂工作任务管理平台 - 数据库初始化脚本
-- 适用数据库：SQL Server 2019+
-- 结构对齐：WorkTaskDB 现网结构（共 17 张表，含计算列）
-- 说明：本脚本仅建库、建表、建索引并写入默认账户，不含业务数据；
--       如需恢复完整业务数据，请改用 database/WorkTaskDB_备份_*.sql
-- 特性：幂等，可重复执行（IF NOT EXISTS 保护）
-- ============================================================

-- 创建数据库
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
        id INT NOT NULL IDENTITY(1,1),
        username VARCHAR(50) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NULL,
        role VARCHAR(20) NOT NULL,                -- admin / engineer / viewer
        email VARCHAR(100) NULL,
        is_active BIT NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_users PRIMARY KEY (id),
        CONSTRAINT UQ_users_username UNIQUE (username)
    );
END
GO

-- 默认账户：admin / engineer / viewer，初始密码均为 admin123
-- bcrypt hash for 'admin123'
IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
BEGIN
    INSERT INTO users (username, password_hash, full_name, role, email, is_active, created_at, updated_at)
    VALUES ('admin', '$2b$12$LJ3m4ys3Gy0KUMCGiGj0DOK7EppZgMq0KLq3HqPTpAsDxJkWJRn5e', N'系统管理员', 'admin', 'admin@factory.com', 1, GETDATE(), GETDATE());
END
GO

IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'engineer')
BEGIN
    INSERT INTO users (username, password_hash, full_name, role, email, is_active, created_at, updated_at)
    VALUES ('engineer', '$2b$12$LJ3m4ys3Gy0KUMCGiGj0DOK7EppZgMq0KLq3HqPTpAsDxJkWJRn5e', N'张工', 'engineer', 'engineer@factory.com', 1, GETDATE(), GETDATE());
END
GO

IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'viewer')
BEGIN
    INSERT INTO users (username, password_hash, full_name, role, email, is_active, created_at, updated_at)
    VALUES ('viewer', '$2b$12$LJ3m4ys3Gy0KUMCGiGj0DOK7EppZgMq0KLq3HqPTpAsDxJkWJRn5e', N'访客', 'viewer', 'viewer@factory.com', 1, GETDATE(), GETDATE());
END
GO

-- ============================================================
-- 2. 用户模块权限表（admin 角色在代码层直接放行，无需初始化数据）
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='user_permissions' AND xtype='U')
BEGIN
    CREATE TABLE user_permissions (
        id INT NOT NULL IDENTITY(1,1),
        user_id INT NOT NULL,
        module_key VARCHAR(50) NOT NULL,          -- devices / weekly / monthly / ...
        can_read BIT NULL,
        can_write BIT NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        can_delete BIT NOT NULL DEFAULT ((0)),
        CONSTRAINT PK_user_permissions PRIMARY KEY (id)
    );
END
GO

-- ============================================================
-- 3. 用户 MAC 绑定表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='user_macs' AND xtype='U')
BEGIN
    CREATE TABLE user_macs (
        id INT NOT NULL IDENTITY(1,1),
        mac VARCHAR(20) NOT NULL,
        owner_name VARCHAR(100) NULL,
        remark VARCHAR(max) NULL,
        status VARCHAR(10) NOT NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_user_macs PRIMARY KEY (id)
    );
END
GO

-- ============================================================
-- 4. AOI&AI 设备部署表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='aoi_ai_devices' AND xtype='U')
BEGIN
    CREATE TABLE aoi_ai_devices (
        id INT NOT NULL IDENTITY(1,1),
        device_id VARCHAR(50) NOT NULL,
        name VARCHAR(100) NOT NULL,
        device_type VARCHAR(10) NOT NULL,         -- AOI / AI
        production_line VARCHAR(10) NOT NULL,     -- 1线-8线
        location VARCHAR(100) NULL,
        ip_address VARCHAR(50) NULL,
        status VARCHAR(20) NOT NULL,              -- 正常 / 故障 / 保养中
        responsible_person VARCHAR(50) NULL,
        install_date DATE NULL,
        remark VARCHAR(max) NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_aoi_ai_devices PRIMARY KEY (id),
        CONSTRAINT UQ_aoi_ai_devices_device_id UNIQUE (device_id)
    );
END
GO

-- ============================================================
-- 5. 服务器部署表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='servers' AND xtype='U')
BEGIN
    CREATE TABLE servers (
        id INT NOT NULL IDENTITY(1,1),
        server_id VARCHAR(50) NOT NULL,
        name VARCHAR(100) NOT NULL,
        production_line VARCHAR(10) NOT NULL,
        rack_location VARCHAR(50) NULL,
        ip_address VARCHAR(50) NULL,
        model VARCHAR(100) NULL,
        os VARCHAR(50) NULL,
        status VARCHAR(20) NOT NULL,              -- 在线 / 离线 / 维护
        cpu_usage FLOAT NULL,
        memory_usage FLOAT NULL,
        disk_usage FLOAT NULL,
        responsible_person VARCHAR(50) NULL,
        last_check_time DATETIME NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_servers PRIMARY KEY (id),
        CONSTRAINT UQ_servers_server_id UNIQUE (server_id)
    );
END
GO

-- ============================================================
-- 6. 老化架部署表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='aging_racks' AND xtype='U')
BEGIN
    CREATE TABLE aging_racks (
        id INT NOT NULL IDENTITY(1,1),
        rack_id VARCHAR(50) NOT NULL,
        name VARCHAR(100) NOT NULL,
        production_line VARCHAR(10) NOT NULL,
        location VARCHAR(100) NULL,
        ip_address VARCHAR(50) NULL,
        total_slots INT NOT NULL,
        used_slots INT NOT NULL,
        status VARCHAR(20) NOT NULL,              -- 正常 / 故障 / 维护
        responsible_person VARCHAR(50) NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_aging_racks PRIMARY KEY (id),
        CONSTRAINT UQ_aging_racks_rack_id UNIQUE (rack_id)
    );
END
GO

-- ============================================================
-- 7. WiFi AP 部署表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='wifi_aps' AND xtype='U')
BEGIN
    CREATE TABLE wifi_aps (
        id INT NOT NULL IDENTITY(1,1),
        ap_id VARCHAR(50) NOT NULL,
        ssid VARCHAR(100) NOT NULL,
        production_line VARCHAR(10) NOT NULL,
        ip_address VARCHAR(50) NULL,
        location VARCHAR(100) NULL,
        channel INT NULL,
        connected_devices INT NULL,
        status VARCHAR(20) NOT NULL,              -- 在线 / 离线
        responsible_person VARCHAR(50) NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_wifi_aps PRIMARY KEY (id),
        CONSTRAINT UQ_wifi_aps_ap_id UNIQUE (ap_id)
    );
END
GO

-- ============================================================
-- 8. 每周生产数据表（defect_count / yield_rate 为计算列）
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='weekly_production' AND xtype='U')
BEGIN
    CREATE TABLE weekly_production (
        id INT NOT NULL IDENTITY(1,1),
        year INT NOT NULL,
        week_number INT NOT NULL,
        production_line VARCHAR(10) NOT NULL,
        project VARCHAR(50) NOT NULL,
        total_output INT NOT NULL,
        qualified_count INT NOT NULL,
        defect_count AS ([total_output] - [qualified_count]),
        yield_rate AS (CASE WHEN [total_output] > 0 THEN ROUND(CONVERT([float], [qualified_count]) / [total_output] * 100, 2) ELSE 0 END),
        recorder VARCHAR(50) NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_weekly_production PRIMARY KEY (id)
    );
END
GO

-- ============================================================
-- 9. 每月生产数据表（monthly_defect_count / monthly_yield_rate 为计算列）
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='monthly_production' AND xtype='U')
BEGIN
    CREATE TABLE monthly_production (
        id INT NOT NULL IDENTITY(1,1),
        year INT NOT NULL,
        month INT NOT NULL,
        production_line VARCHAR(10) NOT NULL,
        project VARCHAR(50) NOT NULL,
        monthly_total_output INT NOT NULL,
        monthly_qualified_count INT NOT NULL,
        monthly_defect_count AS ([monthly_total_output] - [monthly_qualified_count]),
        monthly_yield_rate AS (CASE WHEN [monthly_total_output] > 0 THEN ROUND(CONVERT([float], [monthly_qualified_count]) / [monthly_total_output] * 100, 2) ELSE 0 END),
        recorder VARCHAR(50) NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_monthly_production PRIMARY KEY (id)
    );
END
GO

-- ============================================================
-- 10. 项目表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='projects' AND xtype='U')
BEGIN
    CREATE TABLE projects (
        id INT NOT NULL IDENTITY(1,1),
        project_code VARCHAR(20) NOT NULL,
        project_name VARCHAR(100) NOT NULL,
        description VARCHAR(max) NULL,
        is_active BIT NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_projects PRIMARY KEY (id),
        CONSTRAINT UQ_projects_project_code UNIQUE (project_code)
    );
END
GO

-- ============================================================
-- 11. ESOP 工序件表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='esop_parts' AND xtype='U')
BEGIN
    CREATE TABLE esop_parts (
        id INT NOT NULL IDENTITY(1,1),
        station_name VARCHAR(100) NOT NULL,
        process_name VARCHAR(100) NOT NULL,
        part_number VARCHAR(100) NOT NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        file_name NVARCHAR(255) NULL,
        CONSTRAINT PK_esop_parts PRIMARY KEY (id)
    );
END
GO

-- ============================================================
-- 12. 日常工单表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='work_orders' AND xtype='U')
BEGIN
    CREATE TABLE work_orders (
        id INT NOT NULL IDENTITY(1,1),
        order_number VARCHAR(50) NOT NULL,
        order_type VARCHAR(20) NOT NULL,          -- 组装 / 包装
        product_name VARCHAR(100) NOT NULL,
        priority VARCHAR(10) NOT NULL,            -- 紧急 / 高 / 中 / 低
        planned_start DATETIME NULL,
        planned_end DATETIME NULL,
        actual_start DATETIME NULL,
        actual_end DATETIME NULL,
        status VARCHAR(20) NOT NULL,              -- 待开始 / 进行中 / 已完成 / 挂起
        responsible_person VARCHAR(50) NULL,
        description VARCHAR(max) NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_work_orders PRIMARY KEY (id),
        CONSTRAINT UQ_work_orders_order_number UNIQUE (order_number)
    );
END
GO

-- ============================================================
-- 13. 异常 BUG 表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='bugs' AND xtype='U')
BEGIN
    CREATE TABLE bugs (
        id INT NOT NULL IDENTITY(1,1),
        bug_id VARCHAR(50) NOT NULL,
        title VARCHAR(200) NOT NULL,
        severity VARCHAR(10) NOT NULL,            -- 致命 / 严重 / 一般 / 建议
        module VARCHAR(100) NULL,
        status VARCHAR(20) NOT NULL,              -- 新建 / 确认 / 修复中 / 已解决 / 关闭
        discoverer VARCHAR(50) NULL,
        assignee VARCHAR(50) NULL,
        created_date DATE NULL,
        deadline DATE NULL,
        solution VARCHAR(max) NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_bugs PRIMARY KEY (id),
        CONSTRAINT UQ_bugs_bug_id UNIQUE (bug_id)
    );
END
GO

-- ============================================================
-- 14. 二次开发需求表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='dev_requests' AND xtype='U')
BEGIN
    CREATE TABLE dev_requests (
        id INT NOT NULL IDENTITY(1,1),
        request_id VARCHAR(50) NOT NULL,
        title VARCHAR(200) NOT NULL,
        source VARCHAR(100) NULL,
        priority VARCHAR(10) NOT NULL,            -- 紧急 / 高 / 中 / 低
        status VARCHAR(20) NOT NULL,              -- 收集 / 评估 / 开发中 / 测试 / 上线
        expected_date DATE NULL,
        responsible_person VARCHAR(50) NULL,
        progress FLOAT NULL,                      -- 进度 0-100
        description VARCHAR(max) NULL,
        created_at DATETIME NULL,
        updated_at DATETIME NULL,
        submitter NVARCHAR(50) NULL,
        assignee NVARCHAR(50) NULL,
        CONSTRAINT PK_dev_requests PRIMARY KEY (id),
        CONSTRAINT UQ_dev_requests_request_id UNIQUE (request_id)
    );
END
GO

-- ============================================================
-- 15. 设备杀毒记录表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='antivirus_records' AND xtype='U')
BEGIN
    CREATE TABLE antivirus_records (
        id INT NOT NULL IDENTITY(1,1),
        device_id NVARCHAR(50) NOT NULL,
        antivirus_time DATETIME2 NOT NULL,
        production_line NVARCHAR(10) NOT NULL,
        operator NVARCHAR(50) NOT NULL,
        cycle NVARCHAR(10) NOT NULL DEFAULT (N'每天'),
        next_antivirus_time DATETIME2 NOT NULL,
        remark NVARCHAR(max) NULL,
        created_at DATETIME2 NULL DEFAULT (getutcdate()),
        updated_at DATETIME2 NULL DEFAULT (getutcdate()),
        CONSTRAINT PK_antivirus_records PRIMARY KEY (id)
    );
END
GO

-- ============================================================
-- 16. 岗位职责表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='job_responsibilities' AND xtype='U')
BEGIN
    CREATE TABLE job_responsibilities (
        id INT NOT NULL IDENTITY(1,1),
        name VARCHAR(50) NOT NULL,
        title VARCHAR(50) NOT NULL,
        items VARCHAR(max) NULL,
        sort_order INT NULL,
        updated_at DATETIME NULL,
        CONSTRAINT PK_job_responsibilities PRIMARY KEY (id)
    );
END
GO

-- ============================================================
-- 17. 操作日志表
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='operation_logs' AND xtype='U')
BEGIN
    CREATE TABLE operation_logs (
        id INT NOT NULL IDENTITY(1,1),
        username VARCHAR(50) NOT NULL,
        action VARCHAR(50) NOT NULL,              -- CREATE / UPDATE / DELETE / LOGIN
        target_type VARCHAR(50) NULL,             -- 操作对象类型
        target_id VARCHAR(50) NULL,               -- 操作对象ID
        detail VARCHAR(max) NULL,
        ip_address VARCHAR(50) NULL,
        created_at DATETIME NULL,
        CONSTRAINT PK_operation_logs PRIMARY KEY (id)
    );
END
GO

-- ============================================================
-- 创建索引（与现网结构一致）
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_user_macs_mac' AND object_id = OBJECT_ID('user_macs'))
    CREATE UNIQUE INDEX ix_user_macs_mac ON user_macs (mac);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'ix_user_permissions_user_id' AND object_id = OBJECT_ID('user_permissions'))
    CREATE INDEX ix_user_permissions_user_id ON user_permissions (user_id);
GO

PRINT N'数据库初始化完成!';
GO
