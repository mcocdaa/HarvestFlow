# HarvestFlow 插件系统

## 目录结构

```
plugins/
├── collectors/      # 采集插件
├── curators/        # 自动审核插件
├── reviewers/       # 人工审核插件
├── services/        # 服务插件
├── examples/       # 插件示例模板
├── plugins.yaml    # 插件配置文件
└── README.md       # 本文档
```

## 插件类型

### 1. Collector (采集插件)

负责从各种来源采集会话数据。

**接口定义：
```python
class CollectorPlugin:
    name: str
    description: str

    def scan() -> List[str]:
        """扫描并返回文件路径列表"""
        pass

    def parse(file_path: str) -> dict:
        """解析文件内容为会话数据"""
        pass
```

### 2. Curator (自动审核插件)

基于规则或 AI 自动评估会话质量。

**接口定义：**
```python
class CuratorPlugin:
    name: str
    description: str

    def evaluate(session: dict) -> dict:
        """评估会话质量，返回评分结果

        Returns:
            dict: {
                'score': int,  # 1-5 分
                'is_high_value': bool,
                'tags': List[str]
            }
        """
        pass
```

### 3. Reviewer (人工审核插件)

扩展人工审核界面的功能。

**接口定义：**
```python
class ReviewerPlugin:
    name: str
    description: str

    def get_extra_fields() -> List[dict]:
        """返回额外字段定义"""
        pass

    def validate(session: dict) -> bool:
        """验证会话"""
        pass
```

### 4. Service (服务插件)

提供额外的服务功能，如密钥管理、外部 API 集成等。

## 插件配置

在 `plugins.yaml` 中配置插件启用状态：

```yaml
plugins:
  collectors/default:
    enabled: true
  collectors/openclaw:
    enabled: true
  curators/default:
    enabled: true
  curators/openclaw:
    enabled: true
  reviewers/default:
    enabled: true
  services/infisical:
    enabled: true
```

## 开发新插件

1. 在对应类型目录下创建插件文件夹
2. 实现插件接口
3. 创建 `plugin.yaml` 配置文件
4. 在 `plugins.yaml` 中注册插件
5. 重启后端服务生效

## 钩子语义

插件通过 `@hook_manager.hook("hook_name")` 在模块级注册钩子，作用于对应 Manager 方法的 before/after 时机：

- **before 钩子**：签名与被包装方法一致（实例方法含 `self`）。返回非 `None` 时短路，跳过原方法并作为方法结果返回。
- **after 钩子**：签名 `(result, *被包装方法参数)`。返回非 `None` 时替换 `result`，多个钩子按 priority 链式传递。

示例（拦截 jsonl 解析）：

```python
from core.hook_manager import hook_manager

@hook_manager.hook("collector_manager_parse_before")
def my_parse(self, file_path):
    if file_path.endswith(".jsonl"):
        parsed = my_parser(file_path)
        if parsed:
            return parsed  # 短路内置解析
    return None
```

**注意**: 钩子通过 `hooks.py` 中的 `@hook_manager.hook` 装饰器注册，`plugin.yaml` 中的 `hooks:` 字段仅为文档说明，不会被系统读取。

启用/禁用插件可通过 `POST /api/v1/plugins/enable|disable?key=<plugin_key>`（写入 `plugins.yaml`）或直接编辑 `plugins.yaml` 后重启服务。

## 现有插件

### Collectors
- **openclaw**: OpenClaw 格式采集器

### Curators
- **openclaw**: OpenClaw 审核器

### Reviewers

### Services
- **infisical**: Infisical 密钥管理服务
