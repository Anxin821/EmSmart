# 智能工厂工作任务管理平台

## 项目简介

面向智能工厂的综合工作任务管理系统，采用 **FastAPI + Vue 3** 前后端分离架构，覆盖三大核心业务：

1. **AOI&AI 设备管理** — 设备部署、生产数据管理、数据看板
2. **车间网络管理** — 服务器/老化架/WiFi AP 管理、心跳检测、网络看板
3. **MES 系统管理** — 日常工单、异常 BUG、二次开发需求、MES 看板

## 项目结构

```
EmSmart/
├── backend/                    # 后端（FastAPI）
│   ├── core/                   # 核心模块
│   │   ├── config.py           # 配置管理（Pydantic Settings + .env）
│   │   ├── database.py         # SQLAlchemy 引擎 & 会话管理
│   │   ├── auth.py             # JWT 认证 & 权限控制
│   │   └── crud.py             # 通用 CRUD 操作
│   ├── models/                 # ORM 模型（15 张表，按业务域拆分）
│   │   ├── users.py            # 用户 & 权限
│   │   ├── device.py           # AOI/AI 设备
│   │   ├── production.py       # 周报 & 月报
│   │   ├── network.py          # 服务器 / 老化架 / WiFi AP
│   │   ├── mes.py              # 工单 / BUG / 二次开发需求
│   │   └── system.py           # 项目 / 操作日志 / 杀毒 / 岗位职责
│   ├── routers/                # 路由模块
│   │   ├── auth.py             # 登录 / 当前用户 / 枚举选项
│   │   ├── devices.py          # 设备管理
│   │   ├── production.py       # 生产数据
│   │   ├── network.py          # 网络设施
│   │   ├── mes.py              # MES 系统
│   │   ├── dashboard.py        # 数据看板
│   │   ├── antivirus.py        # 杀毒记录
│   │   ├── users.py            # 用户管理
│   │   ├── projects.py         # 项目管理
│   │   └── responsibilities.py # 岗位职责
│   ├── schemas/                # Pydantic 请求/响应模型
│   ├── tasks/                  # 定时任务（心跳检测）
│   ├── main.py                 # FastAPI 主入口
│   ├── .env.example            # 环境变量模板
│   └── requirements.txt        # Python 依赖
│
├── frontend/                   # 前端（Vue 3 + Vite）
│   ├── src/
│   │   ├── api/                # API 层（按业务域拆分）
│   │   │   ├── index.js        # axios 实例 & 拦截器 & 统一导出
│   │   │   ├── auth.js         # 认证 API
│   │   │   ├── devices.js      # 设备 & 枚举 API
│   │   │   ├── production.js   # 生产 API
│   │   │   ├── network.js      # 网络 API
│   │   │   ├── mes.js          # MES API
│   │   │   ├── antivirus.js    # 杀毒 API
│   │   │   ├── dashboard.js    # 看板 API
│   │   │   ├── users.js        # 用户 API
│   │   │   ├── projects.js     # 项目 API
│   │   │   └── duties.js       # 岗位职责 API
│   │   ├── components/         # 公共组件
│   │   │   ├── Layout.vue      # 主布局（侧边栏 + 顶栏）
│   │   │   └── common/         # 通用组件（分页、弹窗、筛选栏等）
│   │   ├── composables/        # 组合式函数（CRUD、通知）
│   │   ├── views/              # 页面
│   │   │   ├── dashboard/      # 数据看板（5 个）
│   │   │   ├── business/       # 业务管理（11 个）
│   │   │   └── Login.vue       # 登录页
│   │   ├── router/             # Vue Router 路由
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── App.vue             # 根组件
│   │   └── main.js             # 前端入口
│   ├── index.html
│   ├── vite.config.js          # Vite 配置（代理 & 构建）
│   └── package.json
│
├── database/                   # 数据库脚本
│   ├── init_db.sql             # SQL Server 建库建表脚本
│   └── WorkTaskDB_完整导出SQL_0822.sql
│
└── README.md
```

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI 0.115 + Uvicorn |
| **ORM** | SQLAlchemy 2.0 + PyODBC |
| **数据库** | SQL Server |
| **认证** | JWT (python-jose) + Passlib (bcrypt) |
| **定时任务** | APScheduler 3.10 |
| **前端框架** | Vue 3.4 + Vue Router 4 + Pinia 2 |
| **UI 组件** | Element Plus 2.14 + Bootstrap Icons |
| **图表** | ECharts 5.5 |
| **构建工具** | Vite 5 |
| **文件处理** | openpyxl (Excel 导入导出) |

## 快速开始

### 1. 环境要求

- **Python**: 3.12+
- **Node.js**: 18+
- **数据库**: SQL Server 2019+
- **ODBC 驱动**: ODBC Driver 17 for SQL Server

### 2. 数据库初始化

```bash
sqlcmd -S localhost -U sa -P YourPassword123 -i database/init_db.sql
```

### 3. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv ../venv
../venv/Scripts/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 填入实际数据库连接信息

# 启动（开发模式，端口 8001）
python main.py
```

### 4. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式（端口 3000，自动代理 /api 到后端 8001）
npm run dev

# 生产构建
npm run build
```

### 5. 访问

- **开发环境**: http://localhost:3000（Vite 自动代理 API）
- **生产环境**: http://localhost:8001（后端直接提供 SPA 静态文件）

### 6. 登录账号

| 账号 | 密码 | 角色 | 权限 |
|------|------|------|------|
| admin | admin123 | 系统管理员 | 全部权限 |
| engineer | admin123 | 工程师 | 增改查 |
| viewer | admin123 | 只读用户 | 仅查看 |

> 首次启动时自动创建默认账号（如已存在则跳过）。

## 功能特性

### AOI&AI 管理
- 设备 CRUD、Excel 批量导入导出
- 周报/月报录入、自动汇总生成
- 数据看板：设备状态、产量趋势、合格率对比

### 车间网络管理
- 服务器 / 老化架 / WiFi AP 管理
- 自动心跳检测（每 30 分钟）
- 网络拓扑图、在线率仪表盘

### MES 系统管理
- 工单状态流转（表格/泳道双视图）
- BUG 严重等级管理
- 二次开发需求进度跟踪
- MES 看板：工单饼图、BUG 环形图、燃尽图

### 其他
- 杀毒记录管理 & 看板
- 用户权限管理（模块级读/写控制）
- 项目 & 岗位职责管理
- 操作日志审计

## 权限体系

| 操作 | admin | engineer | viewer |
|------|:-----:|:--------:|:------:|
| 查看数据 | ✅ | ✅ | ✅ |
| 新增数据 | ✅ | ✅ | ❌ |
| 编辑数据 | ✅ | ✅ | ❌ |
| 删除数据 | ✅ | ❌ | ❌ |
| 导入导出 | ✅ | ✅ | ❌ |

## API 设计

- 统一前缀：`/api/v1`
- 认证方式：Bearer Token（JWT）
- 响应格式：`{ "code": 200, "message": "success", "data": {...} }`

主要端点：

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `/api/v1/login` | 用户登录 |
| 设备 | `/api/v1/devices` | 设备 CRUD |
| 生产 | `/api/v1/production/weekly` | 周报管理 |
| 生产 | `/api/v1/production/monthly` | 月报管理 |
| 网络 | `/api/v1/network/servers` | 服务器管理 |
| MES | `/api/v1/mes/work-orders` | 工单管理 |
| MES | `/api/v1/mes/bugs` | BUG 管理 |
| 看板 | `/api/v1/dashboard/*` | 各维度看板 |

## 部署说明

### 生产部署

```bash
# 1. 构建前端
cd frontend && npm run build

# 2. 启动后端（自动提供前端静态文件 + SPA fallback）
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

后端会自动检测 `frontend/dist/` 目录并提供静态文件服务，无需额外配置 Nginx。

### 环境变量

复制 `backend/.env.example` 为 `backend/.env`，关键配置项：

```ini
DB_SERVER=localhost
DB_PORT=1433
DB_NAME=WorkTaskDB
DB_USER=sa
DB_PASSWORD=YourPassword123
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

---

> 所有 API 均通过 `/api/v1` 前缀访问，前端开发环境通过 Vite proxy 自动转发，生产环境由后端统一提供服务。
