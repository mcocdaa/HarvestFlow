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

## 现有插件

### Collectors
- **default**: 默认文件系统采集器
- **openclaw**: OpenClaw 格式采集器

### Curators
- **default**: 默认规则审核器
- **openclaw**: OpenClaw 审核器

### Reviewers
- **default**: 默认审核界面

### Services
- **infisical**: Infisical 密钥管理服务
