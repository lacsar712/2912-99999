# 智能生产线监控系统

一个功能完善的智能生产线监控与调度系统，支持生产线、设备、传感器、生产任务的实时监控与管理。系统支持多种数据输入源，包括文件导入、模拟数据生成和实时API数据流。

## 技术栈

### 前端
- HTML5 + CSS3 + JavaScript（原生实现）
- Bootstrap 5（响应式UI）
- Chart.js（数据可视化）
- 基于Hash的路由系统

### 后端
- Python 3.9+
- Flask（Web框架）
- SQLAlchemy（ORM）
- JWT（身份认证）
- Flask-Limiter（请求限流）

### 数据库
- MySQL 8.0（主选）
- Redis（缓存和会话管理）

### 部署
- Docker & Docker Compose
- Nginx（前端静态服务）
- Gunicorn（Python WSGI服务器）

## 快速开始

### 使用 Docker Compose 部署

```bash
# 克隆项目
cd data_manage_system

# 启动服务（使用docker compose v2）
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

服务启动后：
- 前端访问地址：http://localhost:8085
- 后端API地址：http://localhost:5001
- MySQL数据库：localhost:3308
- Redis缓存：localhost:6381
- 默认管理员账号：admin / admin123

### 本地开发

#### 后端开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py
```

#### 前端开发

前端是纯静态文件，可以使用任意HTTP服务器：

```bash
# 进入前端目录
cd frontend

# 使用Python启动简单服务器
python -m http.server 8080
```

## 项目结构

```
data_manage_system/
├── backend/                    # 后端代码
│   ├── app.py                  # 应用入口
│   ├── config.py               # 配置文件
│   ├── requirements.txt        # Python依赖
│   ├── controllers/            # 控制器层
│   │   ├── auth_controller.py
│   │   ├── production_controller.py
│   │   ├── simulation_controller.py
│   │   ├── alert_controller.py
│   │   └── __init__.py
│   ├── services/               # 服务层
│   │   ├── auth_service.py
│   │   ├── production_service.py
│   │   ├── simulation_service.py
│   │   ├── data_source_service.py
│   │   ├── equipment_simulation_service.py
│   │   ├── alert_service.py
│   │   └── __init__.py
│   ├── models/                 # 数据模型
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── production.py
│   │   ├── alert.py
│   │   └── __init__.py
│   ├── database/               # 数据库配置
│   │   ├── db.py
│   │   └── __init__.py
│   ├── utils/                  # 工具模块
│   │   ├── response.py
│   │   ├── jwt_helper.py
│   │   └── password_helper.py
│   ├── middleware/             # 中间件
│   │   ├── auth_middleware.py
│   │   └── __init__.py
│   ├── tests/                  # 测试模块
│   │   ├── run_tests.py
│   │   ├── test_unit.py
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   ├── test_api_production.py
│   │   ├── test_integration.py
│   │   ├── test_functional.py
│   │   ├── test_security.py
│   │   └── conftest.py
│   └── Dockerfile
├── frontend/                   # 前端代码
│   ├── index.html              # 主页面
│   ├── login.html              # 登录页面
│   ├── css/                    # 样式文件
│   │   ├── style.css
│   │   └── dashboard.css
│   └── js/                     # JavaScript文件
│       ├── config.js           # 配置
│       ├── app.js              # 应用入口
│       ├── router.js           # 路由系统
│       ├── utils/              # 工具模块
│       │   ├── storage.js
│       │   ├── request.js
│       │   └── validator.js
│       ├── services/           # API服务
│       │   ├── auth.js
│       │   ├── production.js
│       │   ├── simulation.js
│       │   ├── alert.js
│       │   ├── equipmentSimulation.js
│       │   └── __init__.py
│       ├── components/         # UI组件
│       │   ├── header.js
│       │   ├── sidebar.js
│       │   └── modal.js
│       └── pages/              # 页面模块
│           ├── dashboard.js
│           ├── lines.js
│           ├── equipment.js
│           ├── tasks.js
│           ├── alerts.js
│           └── simulation.js
│   ├── Dockerfile
│   └── nginx.conf              # Nginx配置
├── database/                   # 数据库脚本
│   ├── init_db.py              # Python初始化脚本（符合题目要求：数据库代码用Python单独一个文件）
│   └── init.sql                # SQL初始化脚本
├── sample_data/                # 示例数据文件
│   ├── production_lines.csv    # 生产线示例数据
│   ├── equipments.csv          # 设备示例数据
│   ├── sensors.csv             # 传感器示例数据
│   ├── tasks.csv               # 生产任务示例数据
│   ├── records.json            # 生产记录示例数据
│   ├── alerts.json             # 告警记录示例数据
│   └── README.md               # 示例数据说明
├── docker-compose.yml          # Docker Compose配置
├── .env.example                # 环境变量示例
├── .gitignore                  # Git忽略文件
├── .dockerignore               # Docker忽略文件
├── README.md                   # 本文档
├── 需求文档_v2.md              # 系统需求文档
└── 题目要求.md                 # 项目题目要求
```

## 功能模块

### 监控中心
- 实时生产线状态监控
- 设备运行状态展示
- 传感器数据实时显示
- 告警信息及时推送

### 生产线管理
- 生产线列表查看
- 生产线详情查看
- 生产线创建/编辑/删除
- 状态管理

### 设备管理
- 设备列表查看
- 设备详情和传感器数据
- 远程启动/停止控制
- 设备状态筛选

### 生产任务
- 任务列表管理
- 任务创建
- 进度跟踪
- 状态更新

### 告警中心
- 告警列表展示
- 告警级别分类
- 告警处理

### 统计仪表盘
- 生产统计图表
- 设备运行趋势
- 效率分析

### 数据模拟与导入
- **模拟数据生成**
  - 支持正态分布、均匀分布、随机分布
  - 参数化配置数据规模、类型和分布
  - 实时数据流模拟
- **文件数据导入**
  - CSV格式数据导入
  - JSON格式数据导入
  - 数据验证和关联关系检查
- **模拟数据源创建**
  - API数据源模拟
  - WebSocket实时数据流
  - 文件流模拟
  - 用户输入数据源
- **设备管理数据模拟**（新增）
  - 为设备管理页面提供完整的模拟数据
  - 支持多数据源接入（API、WebSocket、文件流、用户输入）
  - 支持分页、筛选和动态参数调整
  - 生成符合JSON结构的随机设备数据
  - 提供定时/手动数据刷新机制
  - 统一时间格式（YYYY-MM-DD HH:mm:ss）
- **数据导出功能**
  - Excel格式导出
  - CSV格式导出
  - PDF格式导出（需要时）

## API接口

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出

### 生产线接口
- `GET /api/production/lines` - 获取生产线列表
- `POST /api/production/lines` - 创建生产线
- `PUT /api/production/lines/{id}` - 更新生产线
- `DELETE /api/production/lines/{id}` - 删除生产线

### 设备接口
- `GET /api/production/equipments` - 获取设备列表
- `POST /api/production/equipments/{id}/control` - 控制设备

### 传感器接口
- `GET /api/production/sensors` - 获取传感器列表
- `GET /api/production/sensors/realtime` - 获取实时数据

### 任务接口
- `GET /api/production/tasks` - 获取任务列表
- `POST /api/production/tasks` - 创建任务
- `PUT /api/production/tasks/{id}/status` - 更新任务状态

### 统计接口
- `GET /api/production/dashboard` - 获取仪表盘数据
- `GET /api/production/trend` - 获取运行趋势

### 告警接口
- `GET /api/alerts/list` - 获取告警列表
- `POST /api/alerts` - 创建告警
- `PUT /api/alerts/{id}/confirm` - 确认告警
- `PUT /api/alerts/{id}/resolve` - 解决告警
- `GET /api/alerts/stats` - 获取告警统计

### 模拟接口
- `POST /api/simulation/source/create` - 创建模拟数据源
- `GET /api/simulation/source/list` - 获取数据源列表
- `DELETE /api/simulation/source/{id}` - 删除数据源
- `POST /api/simulation/source/{id}/generate` - 从数据源生成数据
- `GET /api/simulation/equipment/data` - 获取设备模拟数据（支持分页参数page/size）
- `POST /api/simulation/equipment/source/create` - 创建设备数据源
- `POST /api/simulation/equipment/refresh` - 手动刷新设备模拟数据

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DB_TYPE | 数据库类型 | mysql |
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 3306 |
| DB_USER | 数据库用户 | root |
| DB_PASSWORD | 数据库密码 | 123456 |
| DB_NAME | 数据库名称 | production_system |
| SECRET_KEY | JWT密钥 | - |
| REDIS_HOST | Redis主机 | localhost |
| REDIS_PORT | Redis端口 | 6379 |

## 开发规范

详细开发规范请参考 `.codebuddy/rules.md` 文件。

## 测试

```bash
# 进入后端目录
cd backend

# 安装测试依赖
pip install pytest pytest-cov

# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/test_unit.py -v

# 运行集成测试
pytest tests/test_integration.py -v
```

## 许可证

MIT License
