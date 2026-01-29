# agent-android - Claude AI 项目文档

> **Version**: 1.0.1
> **Last Updated**: 2026-01-17
> **Purpose**: 为 Claude AI 提供 agent-android 的高效上下文

---

## 🎯 项目概述

**agent-android** 是一个完整的 Android 自动化工具库，专为 AI Agents 设计，提供零代码控制 Android 设备的能力。

### 核心特性
- ✅ **Snapshot + Ref 模式** - 确定性元素定位（对标 agent-browser）
- ✅ **自然语言控制** - 中文 NLP 查找和点击元素
- ✅ **多设备支持** - 并行控制多个 Android 设备
- ✅ **CLI 工具** - 命令行接口
- ✅ **Python API** - 完整的类型注解和异步支持

### 技术栈
- **语言**: Python 3.7+
- **框架**: ADB (Android Debug Bridge)
- **并发**: ThreadPoolExecutor
- **许可证**: Apache 2.0

---

## 📁 项目结构

```
agent-android/
├── core/                      # 核心模块
│   ├── android.py            # AndroidDeviceManager (917 行)
│   ├── nlp_icon_helper.py    # NLPIconHelper (330 行) ⭐
│   ├── icon_helper.py        # IconHelper (286 行)
│   ├── multi_device.py       # MultiDeviceManager (519 行)
│   └── adb_config.py         # ADBConfig (234 行)
│
├── docs/                      # 文档目录
│   └── NLP_FEATURE_ANALYSIS.md  # NLP 详细分析
│
├── CLAUDE_NLP.md             # NLP 功能概述 ⭐
├── NLP_QUICK_REF.md          # NLP 快速参考
├── NLP_EXAMPLES.md           # NLP 使用示例
├── CONTEXT_INDEX.md          # Context 索引
└── CONTEXT_GUIDELINES.md     # Context 使用规范
```

---

## 🚀 快速开始

### 安装
```bash
cd /Users/fansc/fast2/RPA/laite/rpa/agent-android
pip install -r requirements.txt
```

### 基础使用
```python
from agent_android.core.android import create_android_device

# 创建设备连接
device = create_android_device()

# 截图
device.screenshot()

# 点击
device.tap(540, 1200)

# 关闭
device.close()
```

---

## 🎓 核心功能模块

### 1. AndroidDeviceManager - 设备管理

**核心方法**:
```python
device.connect()              # 连接设备
device.tap(x, y)             # 点击屏幕
device.swipe(x1, y1, x2, y2) # 滑动
device.input_text(text)      # 输入文本
device.screenshot()          # 截图
device.get_ui_dump()         # 获取 UI dump
device.find_element(...)     # 查找元素
```

**7 种定位策略**:
- `id` - resource-id
- `text` - 精确文本
- `text_contains` - 文本包含
- `class` - class name
- `content-desc` - content-description
- `position` - 位置索引
- `near_text` - 文本附近

### 2. NLPIconHelper - 自然语言控制 ⭐

**零代码控制 Android 设备**:
```python
from agent_android.core.nlp_icon_helper import NLPIconHelper

nlp = NLPIconHelper(device)

# 使用自然语言
nlp.tap_by_nlp("点击设置按钮")
nlp.tap_by_nlp("点击右上角的菜单图标")
nlp.tap_by_nlp("点击底部的学习标签")
```

**详见**: `CLAUDE_NLP.md` (位于 Obsidian Vault)

### 3. IconHelper - 图标操作

**7 种查找方法**:
```python
from agent_android.core.icon_helper import IconHelper

helper = IconHelper(device)

helper.find_icon_by_text("设置")
helper.find_icon_by_description("menu")
helper.find_icon_by_id("btn_settings")
helper.find_clickable_icons()
helper.find_icon_near_text("用户名")
```

### 4. MultiDeviceManager - 多设备管理

**并行操作**:
```python
from agent_android.core.multi_device import MultiDeviceManager

multi = MultiDeviceManager()
multi.connect_all()

# 并行截图
multi.parallel_screenshot()

# 并行点击
multi.parallel_tap(540, 1200)

# 自定义并行执行
multi.parallel_execute(lambda d: d.start_app("com.example.app"))
```

---

## 📚 Context 使用指南

> **注意**: 详细文档已迁移至 Obsidian Vault (`/Users/fansc/Documents/Obsidian Vault/RPA/agent-android/`)

### Context 分层架构

```
Layer 0: 核心概述 (始终加载)
├── CLAUDE.md (本文件) - 项目总览
└── CLAUDE_NLP.md (在 Obsidian Vault) - NLP 功能概述

Layer 1: 详细参考 (按需加载)
├── NLP_QUICK_REF.md (在 Obsidian Vault) - 完整参数表
├── NLP_EXAMPLES.md (在 Obsidian Vault) - 使用示例
└── NLP_LOGGING_GUIDE.md (在 Obsidian Vault) - 日志使用指南

Layer 2: 深度分析 (仅需要时)
├── NLP_FEATURE_ANALYSIS.md (在 Obsidian Vault) - 技术细节
├── CONTEXT_INDEX.md (在 Obsidian Vault) - 文档索引
└── CONTEXT_GUIDELINES.md (在 Obsidian Vault) - 使用规范
```

### 加载决策树

```
用户查询类型
    ↓
基础使用问题？
├─ 是 → 加载 CLAUDE_NLP.md (200 tokens)
│
└─ 否 → 需要详细参数？
    ├─ 是 → 加载 CLAUDE_NLP.md + NLP_QUICK_REF.md (500 tokens)
    │
    └─ 否 → 需要示例？
        ├─ 是 → 加载 CLAUDE_NLP.md + NLP_EXAMPLES.md (600 tokens)
        │
        └─ 否 → 深度技术问题？
            └─ 是 → 加载全部文档 (2500 tokens)
```

### 快速链接

> 所有文档位于: `/Users/fansc/Documents/Obsidian Vault/RPA/agent-android/`

| 需求 | 文档 | Token 预算 |
|------|------|-----------|
| NLP 快速上手 | CLAUDE_NLP.md | 200 |
| 完整关键词表 | NLP_QUICK_REF.md | 300 |
| 代码示例 | NLP_EXAMPLES.md | 400 |
| 日志使用指南 | NLP_LOGGING_GUIDE.md | 500 |
| 技术分析 | NLP_FEATURE_ANALYSIS.md | 2000 |
| 完整索引 | CONTEXT_INDEX.md | 100 |
| 使用规范 | CONTEXT_GUIDELINES.md | 150 |

---

## 🎯 常见使用场景

### 场景 1: AI Agent 控制 Android 设备

```python
class AndroidAgent:
    def __init__(self):
        self.device = create_android_device()
        self.nlp = NLPIconHelper(self.device)

    def execute_task(self, task):
        steps = self.ai_generate_steps(task)
        for step in steps:
            self.nlp.tap_by_nlp(step)

agent = AndroidAgent()
agent.execute_task("退出登录")
```

### 场景 2: UI 自动化测试

```python
def test_login():
    device = create_android_device()

    # 使用 NLP 快速编写测试
    nlp.tap_by_nlp("点击用户名输入框")
    device.input_text("test@example.com")
    nlp.tap_by_nlp("点击密码输入框")
    device.input_text("password")
    nlp.tap_by_nlp("点击登录按钮")

    device.close()
```

### 场景 3: 数据采集

```python
def scrape_data():
    device = create_android_device()
    nlp = NLPIconHelper(device)

    for i in range(10):
        nlp.tap_by_nlp("点击第一个项目")
        # 采集数据
        data = extract_data(device)
        nlp.tap_by_nlp("点击返回按钮")

    device.close()
```

---

## ⚡ 性能优化

### Token 使用优化

**优化前**:
```
每次查询: 读取完整源代码 (330 行) + 文档
→ ~2500 tokens
```

**优化后**:
```
基础查询: CLAUDE_NLP.md
→ ~200 tokens (节省 92%)

详细查询: CLAUDE_NLP.md + NLP_QUICK_REF.md
→ ~500 tokens (节省 80%)

示例查询: CLAUDE_NLP.md + NLP_EXAMPLES.md
→ ~600 tokens (节省 76%)
```

### 运行时性能

| 操作 | 平均耗时 | 优化方法 |
|------|---------|---------|
| NLP 查找 | 450ms | 使用文本查找（<100ms） |
| UI dump | 200ms | 使用缓存 |
| 截图 | 300ms | 降低分辨率 |
| 多设备并行 | - | 使用 ThreadPoolExecutor |

---

## 🔗 相关资源

### 项目文档
- [README.md](./README.md) - 项目概述
- [CLAUDE.md](./CLAUDE.md) (本文件) - 项目总览

### Obsidian Vault 文档
> 详细文档位于: `/Users/fansc/Documents/Obsidian Vault/RPA/agent-android/`
- CLAUDE_NLP.md - NLP 功能概述
- NLP_QUICK_REF.md - 完整参数表
- NLP_EXAMPLES.md - 使用示例
- NLP_LOGGING_GUIDE.md - 日志使用指南
- NLP_FEATURE_ANALYSIS.md - 技术分析
- CONTEXT_INDEX.md - 文档索引
- CONTEXT_GUIDELINES.md - 使用规范

### 外部资源
- [ADB 官方文档](https://developer.android.com/studio/command-line/adb)
- [UI Automator](https://developer.android.com/training/testing/ui-automator)
- [Python ADB 文档](https://adb-shell.readthedocs.io/)

---

## 📝 开发规范

### 代码风格
- 遵循 PEP 8
- 使用类型注解
- 添加 docstrings
- 编写单元测试

### Git 提交
```
feat: 添加新功能
fix: 修复 bug
docs: 文档更新
refactor: 重构
test: 测试相关
```

---

## 🎓 学习路径

> 所有详细文档位于: `/Users/fansc/Documents/Obsidian Vault/RPA/agent-android/`

### 初学者
1. 阅读 CLAUDE_NLP.md
2. 查看 NLP_EXAMPLES.md 中的基础示例
3. 运行交互式模式

### 进阶用户
1. 阅读 NLP_QUICK_REF.md
2. 查看高级示例
3. 阅读 NLP_FEATURE_ANALYSIS.md
4. 学习 NLP_LOGGING_GUIDE.md (日志分析)

### 高级用户
1. 阅读源代码
2. 自定义扩展
3. 贡献代码
4. 查看 CONTEXT_INDEX.md 了解完整文档结构

---

## 🆘 故障排查

### 常见问题

**Q: ADB 连接失败？**
```bash
# 检查 ADB
adb devices

# 重启 ADB
adb kill-server && adb start-server
```

**Q: NLP 查找失败？**
- 检查描述是否清晰
- 尝试更明确的描述
- 使用交互式模式调试

**Q: 多设备操作失败？**
- 确保所有设备已连接
- 检查设备序列号
- 查看日志

---

## ✅ 最佳实践

1. **优先使用 NLP** - 快速开发和验证
2. **稳定后用确定性方法** - icon_helper.find_icon_by_id()
3. **复用设备连接** - 避免频繁创建
4. **错误处理** - 检查返回值
5. **批量操作** - 使用 batch 方法

---

## 📞 支持与反馈

- **Issues**: [GitHub Issues](https://github.com/your-org/agent-android/issues)
- **详细文档**: `/Users/fansc/Documents/Obsidian Vault/RPA/agent-android/`
- **Context 相关**: 见 Obsidian Vault 中的 CONTEXT_INDEX.md

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-17
**维护者**: Claude AI Team
