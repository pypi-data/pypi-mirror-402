# @yitech/yitool 工具包

<div align="center">
  <img src="https://via.placeholder.com/200" alt="yitool Logo" style="max-width: 200px;" />
  <h1>yitool</h1>
  <p>功能丰富的 Python 工具包，让开发更高效、更简单</p>
  <div style="display: flex; justify-content: center; gap: 10px; margin-top: 10px;">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python Version" />
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
    <img src="https://img.shields.io/badge/test-passed-brightgreen" alt="Test Status" />
    <img src="https://img.shields.io/badge/coverage-high-blueviolet" alt="Code Coverage" />
  </div>
</div>

## 快速开始

### 安装

使用 pip 安装（推荐开发模式）：

```bash
# 直接安装
pip install .

# 开发模式安装（推荐）
pip install -e .
```

使用 uv 安装（更快速的包管理器）：

```bash
# 安装 uv（如果尚未安装）
pip install uv

# 使用 uv 安装 yitool
uv pip install -e .
```

### 基本使用示例

```python
# 导入并配置日志
from yitool import log

# 创建日志配置对象
log_config = log.LogConfig()
log_config.level = log.INFO
log_config.terminal.enabled = True
log_config.file.enabled = True
log_config.file.path = 'app.log'   # 可选，日志文件路径
log_config.file.rotation = '10 MB'     # 可选，日志轮转配置
log_config.file.retention = '7 days'    # 可选，日志保留时间

# 初始化日志系统
log.setup_logging(log_config)

# 使用日志功能
log.info("欢迎使用 yitool 工具包！")
log.debug("这是一条调试信息")

# 初始化 Redis 连接
from yitool.yi_cache import YiRedis
redis_client = YiRedis.from_env()  # 从环境变量加载配置
log.info(f"Redis 连接成功")

# 设置和获取键值
redis_client.set("greeting", "Hello, yitool!")
greeting = redis_client.get("greeting")
log.info(f"获取到的问候语: {greeting}")

# 初始化数据库连接
from yitool.yi_db import YiDB
try:
    # 从环境变量创建数据库实例
    # db = YiDB.from_env(database="test_db")
    log.info("数据库连接配置已加载")
except Exception as e:
    log.error(f"数据库连接配置加载失败: {e}")

# 使用字符串工具函数
from yitool.utils import str_utils
camel_case = str_utils.StrUtils.camel_ize("hello_world")
log.info(f"驼峰命名转换: hello_world -> {camel_case}")

# 使用日期时间工具
from yitool.utils import date_utils
from datetime import datetime
current_time = datetime.now()
formatted_time = date_utils.DateUtils.format(current_time, "%Y-%m-%d %H:%M:%S")
log.info(f"当前时间: {formatted_time}")

# 使用字典工具
from yitool.utils import dict_utils
dict1 = {"a": 1, "b": 2}
dict2 = {"b": 3, "c": 4}
merged = dict_utils.DictUtils.shallow_merge(dict1, dict2)
log.info(f"字典合并结果: {merged}")
```

## 项目介绍

yitool 是一个功能丰富、架构完善的 Python 工具包，旨在提供全面的开发支持，从基础工具函数到高级框架组件，助力开发者快速构建高质量应用。该工具包采用模块化设计，集成了日志管理、数据库操作、缓存系统、异步编程、事件驱动、中间件框架等多种核心功能，可满足从简单脚本到复杂应用的各种开发需求。

### 为什么选择 yitool？

- **全面的功能覆盖**：从基础工具函数到高级架构组件，提供一站式开发解决方案
- **现代化架构设计**：采用清晰的模块化结构，遵循单一职责原则，便于使用和维护
- **异步编程支持**：内置异步工具和上下文管理，支持高并发应用开发
- **完善的类型安全**：全面的类型注解，提供更好的 IDE 支持和代码提示
- **强大的日志系统**：基于 rich 的增强日志框架，支持结构化日志和异步上下文
- **灵活的配置管理**：支持环境变量和配置文件，便于不同环境部署
- **可扩展的架构**：提供抽象接口和扩展点，便于自定义实现和功能扩展
- **完整的测试覆盖**：全面的单元测试和集成测试，确保代码质量和稳定性

### 主要特点

- **模块化设计**：清晰的模块划分，各模块职责明确，耦合度低
- **异步安全**：使用 contextvars 实现异步安全的上下文管理
- **结构化日志**：支持 JSON 格式化和结构化数据记录，便于日志分析
- **中间件支持**：可扩展的中间件框架，支持请求/响应处理链
- **事件驱动**：内置事件发布/订阅机制，支持松耦合系统设计
- **缓存抽象**：统一的缓存接口，支持多种缓存实现
- **数据库增强**：基于 SQLAlchemy 的高级封装，支持 ORM 操作
- **工具函数集**：丰富的工具函数，涵盖数据处理、文件操作、网络工具等
- **错误处理**：详细的异常信息和日志记录，便于调试和问题定位
- **环境友好**：支持从环境变量加载配置，便于容器化部署和 CI/CD 集成

## 功能列表

### 核心模块

| 模块名称 | 主要功能 | 使用场景 |
|---------|---------|---------|
| **日志系统** | 基于 rich 的增强日志框架，支持结构化日志、异步上下文、多处理器等 | 应用日志记录、调试、监控、生产环境日志管理 |
| **数据库操作** | 基于 SQLAlchemy 的高级封装，支持 ORM 操作，提供重试机制、查询缓存、批量操作优化等 | 数据库应用开发、数据处理、ORM 操作、数据分析 |
| **缓存管理** | 抽象缓存接口，支持内存缓存和 Redis 缓存，提供统一管理、缓存装饰器等 | 缓存管理、性能优化、状态存储 |
| **异步工具** | 异步事件和中间件支持，简化异步编程 | 高并发应用、异步 API 开发 |
| **事件驱动** | 事件发布/订阅机制，支持事件中心和监听器模式、优先级、过滤等 | 事件驱动架构、松耦合系统设计 |
| **中间件框架** | 可扩展的中间件系统，支持请求/响应处理链、优先级、异常处理等 | Web 应用、API 网关、请求处理 |
| **FastAPI 集成** | FastAPI 扩展，包括会话管理、中间件、响应处理、请求节流等 | FastAPI 应用开发、会话管理、用户认证 |
| **Celery 集成** | Celery 任务队列封装，支持任务优先级、监控、健康检查等 | 异步任务处理、定时任务、后台处理 |
| **配置管理** | 多源配置管理，支持环境变量、配置文件、热重载、敏感配置加密等 | 应用配置管理、环境切换、配置监控 |
| **安全工具** | 密码处理、JWT 管理、安全随机数、密码复杂度验证、登录失败限制等 | 身份认证、授权、数据安全 |
| **测试工具** | 测试数据生成、测试覆盖率、性能基准测试等 | 单元测试、集成测试、性能测试 |
| **监控与可观测性** | Prometheus 集成、结构化日志、分布式追踪等 | 系统监控、性能分析、故障排查 |
| **共享组件** | 通用组件如定时任务、发布/订阅、栈结构等 | 组件复用、基础架构构建 |
| **示例演示** | 提供丰富的示例代码，展示各模块的使用方法 | 学习和参考各模块的使用方式 |

### 工具函数集

**基础数据处理**

| 模块名称 | 主要功能 |
|---------|---------|
| **数组/列表处理** | 数组去重、合并、分割、查找、排序等实用操作 |
| **字典处理** | 字典合并、深拷贝、扁平化、结构化、差异比较等实用函数 |
| **字符串处理** | 字符串格式化、转换、验证、命名规范转换等工具函数 |
| **转换工具** | 不同数据类型之间的相互转换，提供安全的数据类型转换 |

**文件与配置**

| 模块名称 | 主要功能 |
|---------|---------|
| **文件操作** | 文件读写、复制、移动、删除、压缩解压等功能 |
| **文件路径** | 路径解析、创建、检查、规范化等工具函数 |
| **JSON 处理** | JSON 文件和数据的增强处理，支持复杂数据结构 |
| **YAML 处理** | YAML 文件和数据的处理，支持配置文件读写 |
| **配置工具** | 配置文件加载、解析和管理 |

**安全与加密**

| 模块名称 | 主要功能 |
|---------|---------|
| **加密工具** | 哈希计算、编码解码、加密解密等安全相关功能 |
| **安全工具** | 安全相关的工具函数 |
| **验证工具** | 数据验证和校验功能 |

**日期与时间**

| 模块名称 | 主要功能 |
|---------|---------|
| **日期时间** | 日期时间格式化、转换、计算、时区处理等工具 |

**系统与网络**

| 模块名称 | 主要功能 |
|---------|---------|
| **系统信息** | 获取系统信息、网络信息、进程管理、性能监控等功能 |
| **URL 处理** | URL 解析、构建、编码解码、验证等工具 |

**高级功能**

| 模块名称 | 主要功能 |
|---------|---------|
| **类操作** | 类属性和方法操作、动态属性、单例模式等高级特性 |
| **函数工具** | 函数装饰器、重试机制、性能监控、异步支持等高级功能 |
| **ID 生成** | 唯一 ID 生成工具，支持 UUID、雪花算法、自定义 ID 等 |
| **随机数生成** | 安全随机数、随机字符串、随机选择等功能 |

### 日志系统特性

| 特性名称 | 主要功能 |
|---------|---------|
| **多级别日志** | 支持 DEBUG、INFO、WARNING、ERROR、CRITICAL 级别 |
| **多处理器支持** | 同时支持终端日志和文件日志 |
| **日志轮转** | 支持按大小、时间等策略进行日志轮转 |
| **结构化日志** | 支持 JSON 格式化和结构化数据记录 |
| **上下文管理** | 异步安全的日志上下文，支持请求 ID 等追踪信息 |
| **装饰器支持** | 提供日志执行时间、异常记录等装饰器 |

### 数据库操作特性

| 特性名称 | 主要功能 |
|---------|---------|
| **ORM 支持** | 集成 SQLAlchemy ORM 进行对象关系映射 |
| **事务管理** | 支持数据库事务操作 |
| **重试机制** | 自动重试失败的数据库操作 |
| **环境配置** | 支持从环境变量加载数据库配置 |
| **表结构管理** | 支持表结构查询和管理 |
| **会话管理** | 提供 SQLAlchemy ORM 会话管理 |
| **批量操作** | 支持批量数据插入和更新，优化性能 |
| **查询缓存** | 内置查询结果缓存，减少数据库交互 |
| **连接池管理** | 增强数据库连接池配置和监控 |
| **索引建议工具** | 基于查询模式的索引建议 |

### 缓存管理特性

| 特性名称 | 主要功能 |
|---------|---------|
| **多种缓存实现** | 支持内存缓存和 Redis 缓存 |
| **统一接口** | 提供一致的缓存操作接口 |
| **缓存管理器** | 集中管理多个缓存实例 |
| **YiRedis 扩展** | 扩展 Redis 功能，提供更便捷的操作 |
| **缓存装饰器** | 便捷的函数缓存装饰器 |
| **缓存键自动生成** | 基于函数参数自动生成缓存键 |
| **缓存过期策略** | 支持多种缓存过期策略 |

### 配置管理特性

| 特性名称 | 主要功能 |
|---------|---------|
| **多源配置** | 支持从环境变量、配置文件等多个来源加载配置 |
| **类型安全** | 提供类型安全的配置访问 |
| **模块化配置** | 按功能模块组织配置，便于管理和扩展 |
| **默认值支持** | 支持配置项的默认值 |
| **热重载功能** | 支持配置文件热重载，无需重启应用 |
| **敏感配置加密** | 支持敏感配置项的加密存储 |
| **配置验证** | 增强的配置验证和错误处理 |
| **环境变量集成** | 增强环境变量与配置文件的集成 |

### Celery 集成特性

| 特性名称 | 主要功能 |
|---------|---------|
| **任务优先级** | 支持任务优先级配置和调度 |
| **任务监控** | 任务执行状态监控和统计 |
| **任务报警** | 任务执行超时报警 |
| **健康检查** | 优化的健康检查机制 |
| **任务重试策略** | 灵活的任务重试策略配置 |

### FastAPI 集成特性

| 特性名称 | 主要功能 |
|---------|---------|
| **会话管理** | 完整的会话创建、存储、过期管理 |
| **请求节流** | 基于 IP、用户和端点的限流 |
| **响应缓存** | 内置响应缓存中间件 |
| **统一异常处理** | 提供统一的异常处理机制 |
| **统一响应格式** | 提供统一的响应格式 |
| **中间件链** | 可扩展的中间件链处理 |

### 安全工具特性

| 特性名称 | 主要功能 |
|---------|---------|
| **密码处理** | 使用强哈希算法处理密码 |
| **JWT 管理** | 安全生成和验证 JWT |
| **安全随机数** | 使用加密安全的随机数生成器 |
| **密码复杂度验证** | 支持自定义密码策略配置 |
| **登录失败限制** | 基于 IP 和用户名的登录失败限制 |
| **CORS 配置工具** | 增强的 CORS 配置和管理 |

### 监控与可观测性特性

| 特性名称 | 主要功能 |
|---------|---------|
| **Prometheus 集成** | 添加 Prometheus 指标收集功能 |
| **结构化日志** | 增强的结构化日志能力 |
| **分布式追踪** | 集成分布式追踪功能 |
| **性能指标** | 系统性能指标收集和分析 |

## 安装指南

### 方式一：使用 uv（推荐）

uv 是一个快速的 Python 包管理器，推荐用于安装 yitool：

```bash
# 安装 uv 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或者使用 pip
pip install uv

# 安装 yitool 包
uv pip install .

# 开发模式安装（推荐用于开发环境）
uv pip install -e .
```

### 方式二：使用 pip

```bash
# 直接安装
pip install .

# 开发模式安装
pip install -e .
```

## 示例演示

项目提供了丰富的示例代码，位于 `examples/` 目录下，涵盖了各个模块的使用方法。这些示例可以帮助您快速了解和学习 yitool 工具包的功能。

### 示例列表

| 示例文件 | 功能描述 |
|---------|---------|
| `log_example.py` | 日志系统演示，包括日志配置、不同级别日志、结构化日志和上下文管理 |
| `db_example.py` | 数据库操作演示，包括数据库连接、DataFrame 集成、事务管理和重试机制 |
| `cache_example.py` | 缓存管理演示，包括内存缓存、Redis 缓存、缓存管理器和 YiRedis 扩展 |
| `event_example.py` | 事件驱动演示，包括事件定义、发布、监听器、优先级、过滤和重试机制 |
| `celery_example.py` | Celery 任务队列演示，包括任务定义、发布和执行 |
| `custom_celery_example.py` | 自定义 Celery 应用演示，包括高级配置和扩展 |
| `optimized_example.py` | 优化示例，展示如何高效使用 yitool 工具包 |
| `utils_example.py` | 工具函数演示，包括字符串处理、字典操作、数组处理、日期处理和转换工具 |
| `system_example.py` | 系统工具演示，包括环境变量、文件操作、路径处理、系统信息和安全工具 |

### 如何运行示例

```bash
# 运行日志示例
python examples/log_example.py

# 运行数据库示例
python examples/db_example.py

# 运行缓存示例
python examples/cache_example.py

# 运行事件示例
python examples/event_example.py

# 运行 Celery 示例
python examples/celery_example.py

# 运行自定义 Celery 示例
python examples/custom_celery_example.py

# 运行优化示例
python examples/optimized_example.py

# 运行工具函数示例
python examples/utils_example.py

# 运行系统工具示例
python examples/system_example.py
```

### 示例依赖

部分示例需要外部服务支持：

| 示例文件 | 额外依赖 |
|---------|---------|
| `db_example.py` | 数据库服务（如 MySQL、PostgreSQL） |
| `cache_example.py` | Redis 服务 |

## 环境配置

项目支持通过 `.env` 文件进行配置。复制 `env.example` 到 `.env` 并根据需要修改配置项：

```bash
cp env.example .env
# 使用您喜欢的编辑器编辑 .env 文件
vi .env
```

### 主要环境变量配置

```env
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USERNAME=root
MYSQL_PASSWORD=password

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

```

## 使用示例

### 1. 数据库操作示例

```python
from yitool.db import YiDB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# 定义ORM模型
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    email = Column(String(100), nullable=False, unique=True)

# 从环境变量创建数据库实例
# db = YiDB.from_env()

# 或手动创建实例
from sqlalchemy import create_engine
engine = create_engine('mysql+pymysql://username:password@host:port/database')
db = YiDB(engine)

# 连接数据库
if db.connect():
    print("数据库连接成功")
    
    # 执行查询并返回字典列表
    users = db.read('SELECT * FROM users LIMIT 10')
    print(f"查询到 {len(users)} 条记录")
    
    # 使用字典列表进行插入
    new_data = [
        {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'},
        {'name': 'Bob', 'age': 25, 'email': 'bob@example.com'}
    ]
    db.write(new_data, 'users')
    
    # 使用ORM添加数据
    new_user = User(name='Charlie', age=35, email='charlie@example.com')
    db.add(new_user)
    
    # 批量添加ORM实例
    more_users = [
        User(name='David', age=40, email='david@example.com'),
        User(name='Eve', age=28, email='eve@example.com')
    ]
    db.add_all(more_users)
    
    # 使用ORM查询
    orm_users = db.query(User, User.age > 30)
    print(f"ORM查询到 {len(orm_users)} 条年龄大于30的记录")
    
    # 执行事务
    db.begin()
    try:
        db.execute('UPDATE users SET status = :status WHERE id = :id', {'status': 1, 'id': 1})
        db.execute('INSERT INTO audit_log (action, user_id) VALUES (:action, :user_id)', 
                  {'action': 'update', 'user_id': 1})
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"事务执行失败: {e}")
    
    # 关闭连接
    db.close()
else:
    print("数据库连接失败")
```

### 2. Redis 操作示例

```python
from yitool.cache import YiRedis

# 从环境变量创建实例（推荐）
# redis_client = YiRedis.from_env()

# 或手动创建实例
redis_client = YiRedis(
    host='localhost',
    port=6379,
    db=0,
    password='your_password'
)

# 设置带过期时间的值
redis_client.set('key', 'value', ex=3600)  # 1小时后过期

# 获取值
value = redis_client.get('key')
print(value)  # 输出: b'value'

# 哈希操作
redis_client.hset('user:1', 'name', 'John')
redis_client.hset('user:1', 'age', 30)
user_info = redis_client.hgetall('user:1')
print(user_info)  # 输出: {b'name': b'John', b'age': b'30'}

# 列表操作
redis_client.lpush('tasks', 'task1', 'task2')
task = redis_client.rpop('tasks')
print(task)  # 输出: b'task1'

# 发布/订阅
redis_client.publish('notifications', 'New message')

# 清除匹配模式的键
count = redis_client.clear('cache:*')
print(f'清除了 {count} 个缓存键')

# 使用缓存管理器
from yitool.cache import cache_manager, MemoryCache, RedisCache

# 注册缓存实例
cache_manager.register('memory', MemoryCache())
cache_manager.register('redis', redis_client)

# 使用缓存
cache_manager.get('memory').set('local_key', 'local_value')
cache_manager.get('redis').set('remote_key', 'remote_value')
```

### 3. 日志使用示例

```python
from yitool.log import logger, setup_logging, LogConfig
import logging

# 配置日志
log_config = LogConfig()
log_config.level = logging.DEBUG
log_config.terminal.enabled = True
log_config.file.enabled = True
log_config.file.path = 'app.log'   # 日志文件（可选）
log_config.file.rotation = '10 MB'     # 日志轮转（可选）
log_config.file.retention = '7 days'    # 日志保留时间（可选）

# 初始化日志系统
setup_logging(log_config)

# 记录不同级别的日志
logger.debug('这是一条调试信息')
logger.info('这是一条普通信息')
logger.warning('这是一条警告信息')
logger.error('这是一条错误信息')
logger.critical('这是一条严重错误信息')

# 记录异常信息
try:
    1/0
except Exception as e:
    logger.exception('发生异常')  # 自动记录异常栈信息

# 使用丰富的格式化功能
user = {'id': 1, 'name': 'John'}
logger.info('用户信息: %s', user)  # 自动美化输出
```

### 4. 工具函数使用示例

```python
# 字符串处理
def str_utils_example():
    from yitool.utils.str_utils import StrUtils
    
    # 驼峰命名转换
    camel_case = StrUtils.camel_ize('hello_world')  # 'helloWorld'
    snake_case = StrUtils.de_camelize('helloWorld')  # 'hello_world'
    pascal_case = StrUtils.pascal_ize('hello_world')  # 'HelloWorld'
    kebab_case = StrUtils.kebab_ize('hello_world')  # 'hello-world'
    
    # 字典键转换
    test_dict = {'user_name': 'test', 'user_age': 20}
    camel_dict = StrUtils.camelize_dict_keys(test_dict)  # {'userName': 'test', 'userAge': 20}
    
    print(f"字符串处理示例: {camel_case}, {snake_case}, {pascal_case}, {kebab_case}")
    print(f"字典键转换: {camel_dict}")

# 字典处理
def dict_utils_example():
    from yitool.utils.dict_utils import DictUtils
    
    # 字典合并
    dict1 = {'a': 1, 'b': 2}
    dict2 = {'b': 3, 'c': 4}
    
    # 浅合并
    shallow_merged = DictUtils.shallow_merge(dict1, dict2)  # {'a': 1, 'b': 3, 'c': 4}
    
    # 深合并
    dict3 = {'a': 1, 'b': {'c': 2}}
    dict4 = {'b': {'d': 3}, 'e': 4}
    deep_merged = DictUtils.deep_merge(dict3, dict4)  # {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}
    
    # 字典值操作
    test_dict = {'name': 'test', 'age': 20}
    name = DictUtils.get(test_dict, 'name')  # 'test'
    phone = DictUtils.get(test_dict, 'phone', '未设置')  # '未设置'
    
    print(f"字典处理示例: 浅合并={shallow_merged}, 深合并={deep_merged}")
    print(f"字典值操作: name={name}, phone={phone}")

# 日期时间处理
def date_utils_example():
    from yitool.utils.date_utils import DateUtils
    from datetime import datetime, timedelta
    
    # 获取当前时间
    now = datetime.now()
    
    # 格式化日期
    formatted = DateUtils.format(now, '%Y-%m-%d %H:%M:%S')
    
    # 解析日期字符串
    parsed = DateUtils.parse('2023-01-01 12:00:00', '%Y-%m-%d %H:%M:%S')
    
    # 日期计算（使用Python内置timedelta）
    tomorrow = now + timedelta(days=1)
    days_diff = (tomorrow - now).days  # 1
    
    # 转换为时间戳
    timestamp = DateUtils.to_timestamp(now)
    
    print(f"日期处理示例: 现在={formatted}, 明天={DateUtils.format(tomorrow, '%Y-%m-%d')}")
    print(f"日期差: {days_diff}天, 时间戳: {timestamp}")

# 运行示例
def run_examples():
    str_utils_example()
    dict_utils_example()
    date_utils_example()

if __name__ == "__main__":
    run_examples()
```

### 5. 系统工具使用示例

```python
from yitool.utils.system_utils import SystemUtils

# 获取系统信息
def system_info_example():
    # 操作系统信息
    os_info = SystemUtils.get_os_info()
    print(f"操作系统: {os_info['system']} {os_info['version']}")
    
    # Python 解释器信息
    python_info = SystemUtils.get_python_info()
    print(f"Python 版本: {python_info['version']} ({python_info['implementation']})")
    
    # CPU 信息
    cpu_info = SystemUtils.get_cpu_info()
    print(f"CPU 核心数: {cpu_info['physical_cores']} 物理核心, {cpu_info['total_cores']} 总核心")
    
    # 内存信息
    memory_info = SystemUtils.get_memory_info()
    total_gb = memory_info['total'] / (1024**3)  # 转换为 GB
    used_gb = memory_info['used'] / (1024**3)
    print(f"内存使用: {used_gb:.2f}/{total_gb:.2f} GB ({memory_info['percent']}%)")
    
    # 磁盘信息
    disk_info = SystemUtils.get_disk_info('/')
    disk_total_gb = disk_info['total'] / (1024**3)
    disk_used_gb = disk_info['used'] / (1024**3)
    print(f"磁盘使用: {disk_used_gb:.2f}/{disk_total_gb:.2f} GB ({disk_info['percent']}%)")
    
    # IP 地址信息
    ip_addresses = SystemUtils.get_ip_addresses()
    print("网络接口 IP 地址:")
    for if_name, ip in ip_addresses:
        print(f"  {if_name}: {ip}")

if __name__ == "__main__":
    system_info_example()
```

### 6. FastAPI 会话管理示例

```python
from fastapi import FastAPI, Depends, HTTPException
from yitool.yi_fast.sessions import YiSessionMiddleware, yi_get_session, yi_get_session_id, yi_get_session_manager

# 创建 FastAPI 应用
app = FastAPI()

# 添加会话中间件
app.add_middleware(YiSessionMiddleware)

# 示例路由：获取当前会话数据
@app.get("/session/data")
async def get_session_data(session: dict = Depends(yi_get_session)):
    return {"session_data": session}

# 示例路由：设置会话数据
@app.post("/session/set")
async def set_session_data(
    key: str,
    value: str,
    session: dict = Depends(yi_get_session),
    session_id: str = Depends(yi_get_session_id)
):
    # 更新会话数据
    session[key] = value
    return {"message": f"设置会话数据 {key} = {value} 成功", "session_id": session_id}

# 示例路由：清除会话数据
@app.post("/session/clear")
async def clear_session_data(session: dict = Depends(yi_get_session)):
    session.clear()
    return {"message": "会话数据已清除"}

# 示例路由：获取会话统计信息
@app.get("/session/stats")
async def get_session_stats(
    session_id: str = Depends(yi_get_session_id),
    manager = Depends(yi_get_session_manager)
):
    stats = manager.get_stats()
    return {"session_id": session_id, "stats": stats}

# 运行应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
```

## 项目结构

```
yitool/
├── log/                 # 日志系统
│   ├── __init__.py
│   ├── config.py       # 日志配置
│   ├── context.py      # 日志上下文
│   ├── core.py         # 核心日志功能
│   ├── decorators.py   # 日志装饰器
│   ├── formatters.py   # 日志格式化器
│   └── handlers.py     # 日志处理器
├── misc/               # 杂项功能
│   ├── __init__.py
│   ├── file_modified.py # 文件修改监控
│   └── job_store.py    # 任务存储系统
├── shared/             # 共享组件
│   ├── __init__.py
│   ├── cron.py         # 定时任务调度器
│   ├── kv_storage.py   # KV存储
│   ├── modified.py     # 修改监控
│   ├── pubsub.py       # 发布/订阅模式
│   ├── stack.py        # 栈数据结构
│   └── subscriber.py   # 订阅者模式
├── utils/              # 工具函数集合
│   ├── __init__.py
│   ├── _humps.py       # 命名转换工具
│   ├── arr_utils.py    # 数组/列表处理
│   ├── class_utils.py  # 类操作工具
│   ├── compress_utils.py # 压缩工具
│   ├── config_utils.py # 配置工具
│   ├── convert_utils.py # 类型转换
│   ├── crypto_utils.py # 加密工具
│   ├── date_utils.py   # 日期时间工具
│   ├── dict_utils.py   # 字典处理
│   ├── env_utils.py    # 环境变量工具
│   ├── file_utils.py   # 文件操作
│   ├── fun_utils.py    # 函数处理工具
│   ├── id_utils.py     # ID生成
│   ├── json_utils.py   # JSON处理
│   ├── path_utils.py   # 文件路径工具
│   ├── random_utils.py # 随机数生成
│   ├── security_utils.py # 安全工具
│   ├── str_utils.py    # 字符串处理
│   ├── system_utils.py # 系统信息
│   ├── url_utils.py    # URL处理
│   ├── validator_utils.py # 验证工具
│   └── yaml_utils.py   # YAML处理
├── yi_cache/           # 缓存管理
│   ├── __init__.py
│   ├── _abc.py         # 抽象基类
│   ├── yi_cache.py     # 缓存核心功能
│   ├── yi_cache_manager.py # 缓存管理器
│   ├── yi_cache_memory.py # 内存缓存实现
│   ├── yi_cache_redis.py  # Redis缓存实现
│   ├── yi_cache_ttl.py    # TTL缓存实现
│   └── yi_redis.py     # Redis工具类
├── yi_celery/          # Celery集成
│   ├── __init__.py
│   ├── email_tasks.py  # 邮件任务
│   ├── router.py       # 路由配置
│   └── yi_celery.py    # Celery核心功能
├── yi_config/          # 配置管理
│   ├── __init__.py
│   ├── api_key.py      # API密钥配置
│   ├── app.py          # 应用配置
│   ├── celery.py       # Celery配置
│   ├── cors.py         # CORS配置
│   ├── database.py     # 数据库配置
│   ├── datasource.py   # 数据源配置
│   ├── jwt.py          # JWT配置
│   ├── middleware.py   # 中间件配置
│   ├── server.py       # 服务器配置
│   └── yi_config.py    # 配置核心功能
├── yi_db/              # 数据库操作
│   ├── __init__.py
│   ├── _abc.py         # 抽象基类
│   ├── db.py           # 数据库核心功能
│   ├── engine.py       # 引擎管理
│   ├── session.py      # 会话管理
│   ├── yi_db.py        # 高级数据库工具
│   └── yi_db_sqlalchemy.py # SQLAlchemy实现
├── yi_event/           # 事件驱动框架
│   ├── __init__.py
│   ├── _abc.py         # 抽象基类
│   ├── _base.py        # 事件基类
│   ├── yi_event.py     # 事件定义
│   ├── yi_event_async.py # 异步事件中心
│   ├── yi_event_decorator.py # 事件装饰器
│   └── yi_event_sync.py # 同步事件中心
├── yi_fast/            # FastAPI集成
│   ├── sessions/       # 会话管理
│   │   ├── __init__.py
│   │   ├── config.py   # 会话配置
│   │   ├── dependencies.py # 依赖项
│   │   ├── manager.py  # 会话管理器
│   │   ├── middleware.py # 会话中间件
│   │   └── storage.py  # 会话存储
│   ├── __init__.py
│   ├── exceptions.py   # 异常处理
│   ├── middlewares.py  # 中间件
│   ├── yi_fast.py      # FastAPI核心功能
│   └── yi_response.py  # 响应处理
├── __init__.py         # 包初始化文件
├── __main__.py         # 命令行入口
├── cli.py              # 命令行接口
├── cli.conf            # 命令行配置
├── const.py            # 常量定义
├── enums.py            # 枚举类型定义
└── exceptions.py       # 自定义异常类
```

## 运行测试

项目包含完整的测试套件，分为单元测试和集成测试，确保代码质量和功能正确性：

```bash
# 使用项目提供的测试脚本（推荐）
./bin/run_test

# 直接运行所有测试
python -m pytest

# 详细模式运行测试
python -m pytest -v

# 运行特定文件的测试
python -m pytest tests/integration/db/test_yi_db.py
python -m pytest tests/unit/core/test_log.py

# 运行特定模块的测试
python -m pytest tests/unit/utils/  # 运行所有工具函数测试
python -m pytest tests/integration/  # 运行所有集成测试

# 生成测试覆盖率报告
python -m pytest --cov=yitool tests/

# 运行lint检查
./bin/run_lint
```

## 常见问题

### 1. 安装时出现依赖错误

**问题**：安装过程中出现依赖包版本冲突或安装失败。

**解决方案**：
- 使用 uv 包管理器可以解决大多数依赖冲突问题：`uv pip install -e .`
- 确保您的 Python 版本符合要求（>=3.10）
- 尝试先更新 pip：`pip install --upgrade pip`

### 2. 数据库连接失败

**问题**：无法连接到数据库，出现连接错误。

**解决方案**：
- 检查 `.env` 文件中的数据库配置是否正确
- 确保数据库服务正在运行
- 验证数据库用户权限是否正确
- 检查网络连接和防火墙设置

### 3. Redis 操作超时

**问题**：执行 Redis 操作时出现超时错误。

**解决方案**：
- 检查 Redis 服务器是否正在运行
- 验证 Redis 连接配置是否正确
- 检查网络连接状况
- 考虑增加超时时间配置

### 4. 导入错误

**问题**：导入 yitool 模块时出现错误。

**解决方案**：
- 确保已正确安装 yitool 包
- 检查 Python 路径配置
- 尝试使用开发模式重新安装：`pip install -e .`

## 贡献指南

我们欢迎社区贡献，共同改进 yitool 工具包。贡献的方式包括但不限于：

1. **报告问题**：在项目仓库中提交 Issue，描述问题的详细情况
2. **修复 Bug**：解决已报告的问题，提交 Pull Request
3. **添加功能**：实现新功能或改进现有功能
4. **完善文档**：修正文档错误，补充使用示例

### 代码规范

- 遵循 PEP 8 代码风格指南
- 使用类型提示提升代码可读性
- 为新函数和类添加详细的文档字符串
- 确保所有测试通过

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 联系方式

如有问题或建议，请联系项目维护者：

- Tony Chen
- Email: chruit@outlook.com
- 项目地址：https://gitee.com/yi_tech/yitool
