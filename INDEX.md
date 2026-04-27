# 分子识别 Skills - 文档导航

## 📚 文档体系

本skills包含完整的文档体系，支持任何LLM模型理解和执行。

---

## 🎯 核心文档（必读）

| 文档 | 用途 | 适用对象 | 长度 |
|------|------|---------|------|
| **[SKILL.md](SKILL.md)** | Skill定义与触发 | LLM模型识别 | 中等 |
| **[QUICK_START.md](QUICK_START.md)** | 快速执行卡片 | LLM快速参考 | 短 |
| **[RUNTIME_GUIDE.md](RUNTIME_GUIDE.md)** | 详细执行手册 | LLM完整流程 | 详细 |

---

## 📖 技术文档（参考）

| 文档 | 内容 | 用途 |
|------|------|------|
| **[SKILLS_README.md](SKILLS_README.md)** | 系统功能说明 | 了解技术架构 |
| **[README.md](README.md)** | 项目概述 | 项目介绍 |

---

## 🚀 快速开始

### 对于LLM模型

**最简流程**（3文档）：
```
1. 读取 SKILL.md → 理解触发条件和7步流程
2. 参考 QUICK_START.md → 查看核心命令和关键标记
3. 查阅 RUNTIME_GUIDE.md → 获取详细执行细节
```

**执行要点**：
- ✓ 触发：用户说"分子识别"、"提取化学结构"等
- ✓ 流程：7步骤交互式执行
- ✓ 环境：decimer conda环境（必须）
- ✓ 超时：≥300秒
- ✓ 输出：Excel + 图片文件夹 + JSON总结

### 对于用户

**快速使用**：
```
对LLM说："运行一下分子识别skill吧"
LLM会引导你完成整个流程
```

---

## 📊 文档内容对比

### SKILL.md（Skill定义）

**包含内容**：
- ✓ Skill名称和描述
- ✓ 触发关键词
- ✓ 7步执行流程（详细步骤）
- ✓ 输出文件结构
- ✓ 技术架构
- ✓ LLM执行要点
- ✓ 示例执行对话

**适合**: LLM理解如何触发和执行此skill

---

### QUICK_START.md（快速卡片）

**包含内容**：
- ✓ 7步流程图（简化版）
- ✓ 核心执行命令
- ✓ 完成标记列表
- ✓ 输出结构图
- ✓ 展示模板
- ✓ 验证清单

**适合**: LLM快速参考核心信息

---

### RUNTIME_GUIDE.md（详细手册）

**包含内容**：
- ✓ 每步骤详细说明
- ✓ 命令格式（正确/错误示例）
- ✓ 进度监控重点
- ✓ 输出展示模板
- ✓ 技术架构详解
- ✓ 性能指标
- ✓ 系统要求
- ✓ 常见问题处理
- ✓ 异常情况处理
- ✓ 执行清单

**适合**: LLM获取完整执行细节和异常处理

---

## 🔍 查找指南

### 想了解...

| 问题 | 查看文档 | 章节 |
|------|---------|------|
| **如何触发这个skill？** | SKILL.md | triggers字段 |
| **基本执行流程？** | QUICK_START.md | 7步执行流程 |
| **核心命令是什么？** | QUICK_START.md | 核心执行命令 |
| **详细步骤说明？** | RUNTIME_GUIDE.md | 完整工作流程 |
| **如何验证环境？** | RUNTIME_GUIDE.md | 系统要求 |
| **输出文件在哪？** | SKILL.md | 输出文件结构 |
| **出现错误怎么办？** | RUNTIME_GUIDE.md | 常见问题处理 |
| **处理时间多久？** | RUNTIME_GUIDE.md | 性能指标 |
| **技术架构是什么？** | SKILLS_README.md | 技术架构 |
| **模型准确率多少？** | SKILL.md | 技术架构 |

---

## 🎓 学习路径

### Level 1: 快速上手（5分钟）

```
阅读顺序：
1. QUICK_START.md（2分钟） - 了解核心流程
2. SKILL.md - triggers和7步骤（3分钟）
```

**能做什么**: 基本执行skill

---

### Level 2: 熟练执行（15分钟）

```
阅读顺序：
1. SKILL.md（完整阅读） - 理解全流程
2. RUNTIME_GUIDE.md - 完整工作流程章节
3. 实际运行一次
```

**能做什么**: 独立完整执行，处理简单问题

---

### Level 3: 专家级（30分钟）

```
阅读顺序：
1. RUNTIME_GUIDE.md（完整阅读） - 掌握所有细节
2. SKILLS_README.md - 了解技术架构
3. 多次实践执行
```

**能做什么**: 完全掌握，能处理复杂情况，优化执行

---

## 📞 文档更新

**更新频率**：
- SKILL.md: 随流程变化更新
- RUNTIME_GUIDE.md: 随技术细节更新
- QUICK_START.md: 保持简洁，极少更新
- 本索引文档: 随新文档添加更新

---

## 💡 使用建议

### 对于LLM开发者

**建议文档集成方式**：
```python
# 在LLM的系统提示中
"""
当用户说"分子识别"相关关键词时：
1. 读取 D:\skills\分子识别skills\SKILL.md
2. 按7步骤交互执行
3. 参考 QUICK_START.md 获取核心命令
4. 遇到问题时查阅 RUNTIME_GUIDE.md
"""
```

### 对于skill维护者

**维护建议**：
- 保持SKILL.md的触发关键词准确
- RUNTIME_GUIDE.md要及时更新技术细节
- QUICK_START.md保持简洁，不要扩充
- 所有路径、命令要实际测试验证

---

## 🗂️ 文件结构

```
D:\skills\分子识别skills\
├── SKILL.md                    # ⭐ Skill定义（LLM入口）
├── QUICK_START.md              # ⭐ 快速参考卡片
├── RUNTIME_GUIDE.md            # ⭐ 详细执行手册
├── SKILLS_README.md            # 技术系统说明
├── README.md                   # 项目介绍
├── INDEX.md                    # 本导航文档
├── scripts/
│   └ simplified_integrated_processor.py  # 主执行脚本
├── models/
│   └ resnet18_classifier/      # ResNet18模型
│   └ yolo/                     # YOLO模型
└── output/                     # 输出目录
```

---

## ✅ 文档完整性检查

**必备文档**（5个）：
- [x] SKILL.md - Skill定义
- [x] QUICK_START.md - 快速卡片
- [x] RUNTIME_GUIDE.md - 详细手册
- [x] SKILLS_README.md - 技术说明
- [x] INDEX.md - 导航文档

**所有文档都已创建并内容完整！✓**

---

**创建日期**: 2026-04-14  
**文档版本**: v1.0  
**适用范围**: 所有LLM模型和用户