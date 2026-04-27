# 化学文献分子结构智能提取系统

## 📋 系统概述

这是一个端到端的**化学文献处理Skills系统**，能够自动从PDF专利文献中提取分子结构图，智能分类过滤，识别生成SMILES字符串，并输出结构化数据。

## 🎯 核心功能

### 1. 自动化处理流程
```
PDF输入 → 图像提取 → 智能分类 → 分子识别 → Excel输出
```

### 2. 四大核心技能

| 技能 | 功能 | 技术 |
|------|------|------|
| **图像提取** | 从PDF提取化学结构图 | DECIMER Segmentation |
| **智能分类** | 分类为小分子/聚合物/废弃 | ResNet18 (98.95%准确率) |
| **分子识别** | 生成SMILES字符串 | Alchemist API / DECIMER Transformer |
| **数据输出** | 生成结构化Excel表格 | openpyxl + 图片嵌入 |

---

## 🔄 详细处理流程

### 步骤1：DECIMER图像提取

**输入**：PDF专利文献
**处理**：
- 使用DECIMER Segmentation模型识别化学结构区域
- 提取所有化学结构图
- 保存为PNG格式图片

**输出**：
- 图片数量：通常几百到几千张
- 临时保存路径：`output/[专利名]_[时间戳]/temp_images/`

**关键特性**：
- ✅ 自动识别化学结构边界
- ✅ 支持复杂布局
- ✅ 高准确率提取

---

### 步骤2：ResNet18智能分类

**输入**：提取的化学结构图
**处理**：
- 使用训练好的ResNet18模型分类
- 三分类：小分子、聚合物、废弃

**分类标准**：
| 类别 | 说明 | 后续处理 |
|------|------|---------|
| **小分子** | 有机小分子化合物 | ✅ 识别SMILES |
| **聚合物** | 高分子聚合物结构 | ✅ 识别SMILES |
| **废弃** | 反应式、流程图、表格等 | ❌ 过滤不识别 |

**输出**：
```
images/
├── 小分子/          # small_1.png, small_2.png, ...
├── 聚合物/          # polymer_1.png, polymer_2.png, ...
└── 废弃/            # discarded_1.png, discarded_2.png, ...
```

**模型性能**：
- 验证准确率：**98.95%**
- 推理速度：~50ms/张

---

### 步骤3：分子结构识别

**输入**：小分子和聚合物图片
**处理**：生成SMILES字符串

#### 两种识别引擎

| 特性 | Alchemist API | DECIMER Transformer |
|------|--------------|---------------------|
| **类型** | 在线API | 离线模型 |
| **网络** | ✅ 需要网络 | ❌ 无需网络 |
| **速度** | ~500ms/张 | ~200ms/张 |
| **准确率** | 高 | 高 |
| **成本** | 需API额度 | 免费 |
| **隐私** | 数据上传服务器 | 本地处理 |
| **置信度** | ✅ 提供 | ❌ 不提供 |

**SMILES格式**：
```
小分子示例：C1=CC=CC=C1 (苯环)
聚合物示例：*C(=C)C1=CC=CC=C1* (带端基标记)
```

---

### 步骤4：Excel数据输出

**输入**：识别结果 + 分类图片
**处理**：生成结构化Excel表格

**输出格式**：

| 序号 | 分子结构图 | SMILES | 原文献名称 |
|------|-----------|--------|-----------|
| 1 | [嵌入图片] | C1=CC=CC=C1 | 专利.pdf |
| 2 | [嵌入图片] | CC(C)CC | 专利.pdf |

**特性**：
- ✅ 分子结构图直接嵌入Excel
- ✅ 图片自动缩放（最大高度100像素）
- ✅ 只包含小分子和聚合物
- ✅ 每行一张图、一个SMILES，完全对齐

---

## 📁 输出文件结构

```
output/
└── 专利名称_20260331_120000/           # 时间戳避免冲突
    ├── 专利名称_识别结果.xlsx           # Excel表格
    ├── images/                          # 分类图片
    │   ├── 小分子/                      # 小分子图片
    │   │   ├── small_1.png
    │   │   └── ...
    │   ├── 聚合物/                      # 聚合物图片
    │   │   ├── polymer_1.png
    │   │   └── ...
    │   └── 废弃/                        # 废弃图片
    │       ├── discarded_1.png
    │       └── ...
    └── processing_summary.json          # 处理统计
```

---

## 💻 使用方法

### 快速开始

#### 1. 使用Alchemist识别（在线）
```bash
python scripts\simplified_integrated_processor.py \
  --pdf "专利.pdf" \
  --recognizer alchemist
```

#### 2. 使用DECIMER识别（离线）
```bash
python scripts\simplified_integrated_processor.py \
  --pdf "专利.pdf" \
  --recognizer decimer
```

#### 3. 使用批处理脚本
```bash
run_simplified_processor.bat "专利.pdf" decimer
```

### 命令行参数

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--pdf` | ✅ | PDF文件路径 | `"专利.pdf"` |
| `--recognizer` | ❌ | 识别引擎 | `alchemist` / `decimer` |
| `--output` | ❌ | 自定义输出目录 | `"D:\output"` |

---

## 🔧 高级功能

### 1. Excel清理工具

**用途**：删除没有分子结构图的行

```bash
python scripts\clean_excel_right.py "Excel文件.xlsx"
```

**效果**：
- 自动检测每行是否有图片
- 删除没有图片的行
- 确保每行一张图、一个SMILES

### 2. 批量处理

```bash
# Windows批处理
for %%f in (D:\patents\*.pdf) do (
  python scripts\simplified_integrated_processor.py --pdf "%%f" --recognizer decimer
)

# Linux/Mac
for pdf in patents/*.pdf; do
  python scripts/simplified_integrated_processor.py --pdf "$pdf" --recognizer decimer
done
```

### 3. Python API调用

```python
from scripts.simplified_integrated_processor import SimplifiedIntegratedProcessor

# 创建处理器
processor = SimplifiedIntegratedProcessor(recognizer_type='decimer')

# 处理PDF
result = processor.process_pdf('专利.pdf')

# 查看结果
print(f"提取图片: {result['total_images']} 张")
print(f"小分子: {result['classification']['小分子']} 张")
print(f"聚合物: {result['classification']['聚合物']} 张")
print(f"识别成功: {result['recognition_success']} 个")
print(f"输出文件: {result['excel_file']}")
```

---

## 📊 性能指标

### 处理速度

| 阶段 | 速度 | 1000张图片耗时 |
|------|------|---------------|
| 图像提取 | ~100ms/页 | ~10分钟 |
| 智能分类 | ~50ms/张 | ~1分钟 |
| Alchemist识别 | ~500ms/张 | ~8分钟 |
| DECIMER识别 | ~200ms/张 | ~3分钟 |

### 准确率

| 指标 | 数值 |
|------|------|
| 分类准确率 | 98.95% |
| SMILES识别成功率 | 95-98% |
| 图片提取召回率 | 90-95% |

---

## ⚙️ 系统要求

### 硬件要求
- CPU：4核以上
- 内存：8GB以上
- 硬盘：10GB可用空间（临时文件）

### 软件要求
- Python 3.8+
- Conda环境：`decimer`
- 依赖包：见`requirements.txt`

### 安装依赖

```bash
# 创建conda环境
conda create -n decimer python=3.8
conda activate decimer

# 安装依赖
pip install -r requirements.txt

# 安装DECIMER（如使用离线识别）
cd D:\skills\DECIMER-Image_Transformer
pip install -e .
```

---

## 🎓 技术架构

### 模型组合

```
Skills Pipeline:
  ├─ DECIMER Segmentation (图像提取)
  ├─ ResNet18 Classifier (智能分类)
  ├─ Alchemist API / DECIMER Transformer (分子识别)
  └─ openpyxl Engine (数据输出)
```

### 数据流向

```
PDF (输入)
  ↓
DECIMER → 图片列表
  ↓
ResNet18 → 分类结果
  ↓ (过滤废弃)
识别引擎 → SMILES
  ↓
Excel生成器 → Excel + 图片 (输出)
```

---

## 🐛 常见问题

### Q1: DECIMER加载失败？
```bash
# 检查安装
python -c "from DECIMER import predict_SMILES; print('OK')"

# 重新安装
cd D:\skills\DECIMER-Image_Transformer
pip install -e .
```

### Q2: Alchemist API连接失败？
- 检查网络连接
- 验证API地址和密钥
- 查看API额度

### Q3: 图片提取数量少？
- 检查PDF质量
- 调整DECIMER参数
- 尝试不同的PDF阅读器

### Q4: 内存不足？
- 减小批量处理大小
- 使用更小的模型
- 增加系统内存

---

## 📈 未来扩展

### 计划功能
- [ ] 支持更多识别引��
- [ ] 添加化合物属性预测
- [ ] 支持批量对比分析
- [ ] 集成分子可视化
- [ ] Web界面支持

### 自定义扩展
```python
# 添加新的识别引擎
class CustomRecognizer:
    def recognize(self, image_path):
        # 自定义识别逻辑
        return {
            'success': True,
            'smiles': '...',
            'confidence': 0.95
        }
```

---

## 📞 相关文档

- **使用指南**：[SIMPLIFIED_PROCESSING_GUIDE.md](SIMPLIFIED_PROCESSING_GUIDE.md)
- **训练指南**：[RESNET18_TRAINING_GUIDE.md](RESNET18_TRAINING_GUIDE.md)
- **双引擎对比**：[DUAL_ENGINE_RECOGNITION_GUIDE.md](DUAL_ENGINE_RECOGNITION_GUIDE.md)

---

## 📄 许可证

本项目仅供学术研究使用。

---

**创建日期**：2026-03-31
**版本**：1.0
**维护者**：Chemical AI Research Team