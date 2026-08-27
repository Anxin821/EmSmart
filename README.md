# 智能工厂工作任务管理平台

## 🏭 项目简介

这是一个面向智能工厂的综合工作任务管理系统，专注于以下三大业务模块：

1. **AOI&AI 设备管理** - 设备部署、生产数据管理、数据看板
2. **车间网络管理** - 服务器/老化架/WiFi AP管理、心跳检测、网络看板  
3. **MES 系统管理** - 日常工单、异常BUG、二次开发需求、MES看板

## 📁 项目结构

```
worktask_platform_deploy/     # 工作任务平台部署版本
├── main.py                   # FastAPI 主入口
├── config.py                 # 配置管理
├── database.py               # SQLAlchemy 引擎
├── models.py                 # ORM 模型（11张表）
├── schemas.py                # Pydantic 请求/响应模型
├── auth.py                   # JWT 认证
├── crud.py                   # 数据库 CRUD 操作
├── routers/                  # 模块化路由
│   ├── devices.py           # AOI&AI 设备管理
│   ├── production.py        # 生产数据管理
│   ├── network.py           # 车间网络管理
│   ├── mes.py               # MES 系统管理
│   └── dashboard.py         # 数据看板
├── templates/               # HTML模板
├── static/                  # 静态资源
├── init_db.sql              # SQL Server 建库建表脚本
├── requirements.txt         # Python 依赖
├── deploy.bat              # 部署脚本
├── start_server.bat        # 启动脚本
└── README.md               # 详细文档
```

## 🚀 快速开始

### 1. 环境要求
- **操作系统**: Windows / Linux / macOS
- **Python**: 3.10+
- **数据库**: SQL Server 2019+
- **ODBC 驱动**: ODBC Driver 17 for SQL Server

### 2. 数据库初始化
执行 `init_db.sql` 脚本创建数据库和表结构：
```bash
sqlcmd -S localhost -U sa -P YourPassword123 -i init_db.sql
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
设置数据库连接信息：
```bash
# Windows PowerShell
$env:DB_SERVER = "localhost"
$env:DB_NAME = "WorkTaskDB"
$env:DB_USER = "sa"
$env:DB_PASSWORD = "YourPassword123"
```

### 5. 启动应用
```bash
python main.py
# 或使用批处理文件
start_server.bat
```

访问：**http://localhost:8000**

### 6. 登录账号
- **admin / admin123** - 全部权限
- **engineer / admin123** - 增改查权限
- **viewer / admin123** - 仅查看权限

## 📋 功能特性

### 🔧 AOI&AI 管理
- 设备CRUD操作、Excel批量导入导出
- 周报/月报录入、自动汇总
- 数据看板：设备状态、产量趋势、合格率对比

### 🌐 车间网络管理
- 服务器/老化架/WiFi AP管理
- 自动心跳检测（每30分钟）
- 网络拓扑图、在线率仪表盘

### 📊 MES 系统管理
- 工单状态流转（表格/泳道双视图）
- BUG严重等级管理
- 二次开发需求进度跟踪
- MES看板：工单饼图、BUG环形图、燃尽图

## 🔐 权限体系
| 操作       | admin | engineer | viewer |
|-----------|:-----:|:--------:|:------:|
| 查看数据   |   ✅   |    ✅    |   ✅   |
| 新增数据   |   ✅   |    ✅    |   ❌   |
| 编辑数据   |   ✅   |    ✅    |   ❌   |
| 删除数据   |   ✅   |    ❌    |   ❌   |
| 导入导出   |   ✅   |    ✅    |   ❌   |

## ⚙️ 定时任务
- 每30分钟自动执行服务器心跳检测
- 更新在线/离线状态
- 记录最后检测时间

## 🛠 技术栈
- **后端**: FastAPI + SQLAlchemy + SQL Server
- **前端**: Bootstrap 5 + Jinja2 + ECharts
- **认证**: JWT + python-jose
- **定时任务**: APScheduler
- **文件处理**: openpyxl

## 📦 部署说明
完整的部署包已包含所有必要文件：
1. 复制整个 `worktask_platform_deploy` 文件夹
2. 配置环境变量
3. 执行数据库初始化脚本
4. 安装Python依赖
5. 启动应用

生产环境建议使用：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

> 📌 **注意**: 此目录仅包含工作任务管理平台的部署版本。所有开发文件、测试数据和辅助文档已清理，确保项目干净整洁。