# MangoTools 测试工具库

MangoTools 是一个功能强大的Python测试工具库，专为简化测试数据生成、数据库操作、断言验证和通知发送等常见测试任务而设计。

## 功能特性

### 🎲 数据生成与处理
- **随机数据生成**：支持生成随机字符串、数字、时间、个人信息等各类测试数据
- **JSON处理**：提供JSON数据解析、提取和转换功能
- **缓存工具**：内置缓存机制，提高数据访问效率
- **编码与加密**：支持数据编码和加密处理

### 🗄️ 数据库连接
- **MySQL支持**：提供同步和异步MySQL数据库连接
- **SQLite支持**：轻量级SQLite数据库操作接口
- **连接池管理**：高效的数据库连接池管理

### ✅ 断言验证
- **文本断言**：支持多种文本匹配和验证方式
- **文件断言**：Excel文件内容验证
- **SQL断言**：数据库查询结果验证
- **自定义断言**：灵活的自定义断言规则

### 🔔 通知发送
- **邮件通知**：SMTP邮件发送功能
- **微信通知**：企业微信消息推送

### 🧰 装饰器工具
- **重试机制**：自动重试失败的操作
- **单例模式**：确保类实例唯一性
- **参数转换**：自动参数类型转换
- **方法回调**：支持同步和异步方法回调

## 安装方式

```bash
pip install mangotools
```

或者从源码安装：

```bash
git clone https://gitee.com/mao-peng/testkit.git
cd mangotools
pip install -r requirements.txt
```

## 使用示例

### 数据生成
```python
from mangotools.data_processor import DataProcessor

# 创建数据处理器实例
processor = DataProcessor()

# 生成随机数据
random_name = processor.name()  # 随机姓名
random_phone = processor.phone()  # 随机手机号
random_time = processor.time_now_ymdhms()  # 当前时间
```

### 数据库操作
```python
from mangotools.database import MysqlConnect

# 创建数据库连接
db = MysqlConnect(host='localhost', user='root', password='password', database='test')

# 执行查询
result = db.select('SELECT * FROM users WHERE id = %s', (1,))
```

### 断言验证
```python
from mangotools.assertion import MangoAssertion

# 创建断言实例
asserter = MangoAssertion()

# 文本断言
asserter.ass('equal', 'actual_value', 'expected_value')

# SQL断言
asserter.ass('sql_equal', 'SELECT COUNT(*) FROM users', 10)
```

## 技术栈

- **Python版本**：3.10+
- **异步支持**：aiomysql
- **数据库**：PyMySQL, SQLite
- **数据处理**：Faker, jsonpath, deepdiff
- **缓存**：cachetools, diskcache
- **日志**：colorlog, concurrent-log-handler
- **模型验证**：pydantic
- **文件处理**：openpyxl

## Docker部署

```bash
# 构建镜像
docker build -t mango_kit .

# 运行容器
docker run -d --name mango_kit mango_kit
```

## 项目结构

```
mangotools/
├── assertion/          # 断言模块
├── data_processor/     # 数据处理模块
├── database/           # 数据库连接模块
├── decorator/          # 装饰器工具
├── notice/             # 通知发送模块
├── log_collector/      # 日志收集模块
└── models/             # 数据模型
```

## 联系方式

📧 邮箱：729164035@qq.com  
👨‍💻 作者：毛鹏  
🔗 项目地址：https://gitee.com/mao-peng/testkit

## 许可证

MIT License