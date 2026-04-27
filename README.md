# 分子识别 Skills (Molecular Recognition Skills)

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Internal-green)]()

自动化提取专利文档中的分子结构，并识别生成 SMILES 字符串。集成 DECIMER 和 YOLO 技术实现高精度分子结构识别。

## 📋 核心功能

- **DECIMER 处理**: 使用 DECIMER-Image_Transformer 和 DECIMER-Image-Segmentation 技术提取和分割分子结构图
- **YOLO 检测**: 基于 YOLO 模型检测分子结构区域
- **智能分类**: ResNet18 分类器过滤非分子结构图片
- **SMILES 生成**: 调用 al-chemist API 识别分子结构生成 SMILES
- **批量处理**: 支持批量处理多个文档，自动生成结果报告
- **人工审核**: 可选人工筛选流程，确保结果准确性

## 🗂️ 项目结构

```
molecular_recognition_skills/
├── scripts/                  # 核心处理脚本
│   ├── simplified_integrated_processor.py   # 主处理脚本
│   ├── decimer_processor.py                 # DECIMER 处理模块
│   ├── molecule_classifier.py               # 分子分类器
│   ├── alchemist_api.py                     # al-chemist API
│   └── table_generator.py                   # 结果表格生成
├── yolo/                     # YOLO 模型相关
│   ├── detect/               # YOLO 检测模块
│   │   ├── dataset/          # 训练数据集
│   │   ├── predict.py        # 预测脚本
│   │   └── train.py          # 训练脚本
│   └── yolo_processor.py     # YOLO 处理脚本
├── DECIMER-Image_Transformer/    # DECIMER Transformer (可选)
├── DECIMER-Image-Segmentation/   # DECIMER Segmentation (可选)
├── models/                   # 模型文件目录 (不上传)
├── config.json               # 配置文件
├── requirements.txt          # Python 依赖包
├── .gitignore                # Git 忽略规则
└── 文档/
    ├── README.md             # 本文档
    ├── SKILL.md              # Skill 定义文档
    ├── QUICK_START.md        # 快速开始指南
    ├── RUNTIME_GUIDE.md      # 详细执行手册
    └── INDEX.md              # 文档导航
```

## 🚀 快速开始

### 1. 克隆仓库

```bash
# 克隆主仓库
git clone https://github.com/zjf-arch/molecular_recognition_skills.git

# 进入项目目录
cd molecular_recognition_skills

# 克隆 DECIMER 项目（可选）
git clone https://github.com/Kohulan/DECIMER-Image_Transformer.git
git clone https://github.com/Kohulan/DECIMER-Image-Segmentation.git
```

### 2. 系统要求

- Python 3.7 或更高版本
- Conda 环境 (推荐)
- Windows / macOS / Linux

### 3. 安装依赖

```bash
# 创建 conda 环境
conda create -n decimer python=3.8
conda activate decimer

# 安装主项目依赖
pip install -r requirements.txt

# 安装 DECIMER 项目（可选，根据需要）
# 方式1: 克隆到项目目录
git clone https://github.com/Kohulan/DECIMER-Image_Transformer.git
git clone https://github.com/Kohulan/DECIMER-Image-Segmentation.git

cd DECIMER-Image_Transformer
pip install -e .
cd ..

cd DECIMER-Image-Segmentation
pip install -e .
cd ..

# 方式2: 直接安装（不需要本地克隆）
pip install decimer
pip install decimer-segmentation
```

### 4. 下载模型文件

⚠️ **重要**: 模型文件较大，不包含在 Git 仓库中。请单独下载：

- `mole_classifier.pth` (43MB) - ResNet18 分类器
- YOLO 模型权重
- DECIMER 模型权重

详见 [模型下载说明](#模型下载)

### 5. 使用方法

#### 基本用法

```bash
# 激活环境
conda activate decimer

# 处理单个文档
python scripts/simplified_integrated_processor.py input.pdf

# 批量处理
python scripts/simplified_integrated_processor.py *.pdf

# 自动模式（无人工审核）
python scripts/simplified_integrated_processor.py input.pdf --no-manual
```

#### YOLO 模型

```bash
# YOLO 检测
python yolo/yolo_processor.py input.png

# 批量检测
python yolo/detect/predict.py yolo/detect/dataset/images/val/
```

#### 更多使用方法

参见详细文档：
- [QUICK_START.md](QUICK_START.md) - 快速参考卡片
- [RUNTIME_GUIDE.md](RUNTIME_GUIDE.md) - 详细执行手册
- [SKILL.md](SKILL.md) - Skill 定义与触发条件

#### 方式一：统一入口工具（推荐）

最简单的方式，自动选择最佳处理方法：

```bash
# 处理单个专利（自动模式，推荐）
python D:\skills\scripts\unified_patent_tool.py patent.pdf

# 批量处理多个专利
python D:\skills\scripts\unified_patent_tool.py patent1.pdf patent2.pdf

# 自动处理（无人工审核）
python D:\skills\scripts\unified_patent_tool.py patent.pdf --no-manual

# 输出CSV格式
python D:\skills\scripts\unified_patent_tool.py patent.pdf --format csv
```

**特点**：
- 自动检测MineRU可用性
- MineRU不可用时自动切换到手动提取模式
- 支持批量处理
- 清晰的进度显示

#### 方式二：手动PDF提取工具（当前推荐）

由于MineRU模型问题，当前推荐使用手动提取方式：

```bash
# 基本用法（带人工审核）
python D:\skills\scripts\manual_pdf_processor.py patent.pdf

# 自动处理所有图片（无人工审核）
python D:\skills\scripts\manual_pdf_processor.py patent.pdf --no-manual

# 调整智能筛选参数
python D:\skills\scripts\manual_pdf_processor.py patent.pdf --min-width 200 --min-height 200 --min-size 20

# 禁用智能筛选（提取所有图片）
python D:\skills\scripts\manual_pdf_processor.py patent.pdf --no-filter

# 批量处理多个PDF
python D:\skills\scripts\manual_pdf_processor.py patent1.pdf patent2.pdf

# 输出CSV格式
python D:\skills\scripts\manual_pdf_processor.py patent.pdf --format csv
```

**功能特点**：
- ✓ 图片智能筛选（过滤小图标、logo等）
- ✓ 进度条显示（需要tqdm）
- ✓ 支持人工审核（可选打开图片查看）
- ✓ 批量处理多个PDF
- ✓ 支持多种输出格式

#### 方式三：使用批处理脚本（Windows）

1. 将专利文件放入 `D:\skills\patents\` 目录
2. 双击运行 `extract_patents.bat`
3. 按提示操作

## 📥 模型下载

由于模型文件较大，不包含在 Git 仓库中。请从以下位置下载：

| 模型 | 大小 | 下载地址 |
|------|------|----------|
| `mole_classifier.pth` | 43MB | [下载链接] |
| YOLO 权重 | ~10MB | [下载链接] |
| DECIMER 模型 | 自动下载 | DECIMER 初始化时自动下载 |

下载后放置在以下目录：
```
models/
  └ resnet18_classifier/  # ResNet18 模型
yolo/detect/weights/       # YOLO 模型
mole_classifier.pth        # 分类器模型
```

## 🔧 技术架构

### 核心技术栈

- **DECIMER-Image_Transformer**: 化学结构图像转换和识别
- **DECIMER-Image-Segmentation**: 分子结构图像分割
- **YOLOv8**: 分子结构区域检测
- **ResNet18**: 分子/非分子图像分类
- **al-chemist API**: SMILES 字符串生成

### 工作流程

```
输入文档 (PDF/图片)
    ↓
DECIMER 提取图像
    ↓
YOLO 检测分子区域
    ↓
ResNet18 分类过滤
    ↓
al-chemist API 识别
    ↓
生成 SMILES + 表格输出
```

## 📊 输出格式

生成的表格包含以下列：

| 序号 | 分子结构图 | SMILES | 识别状态 | 原文献名称 |
|------|-----------|--------|---------|-----------|
| 1    | [图片]    | CCO    | 成功    | patent_001.pdf |
| 2    | [图片]    | CC(=O)O | 成功   | patent_001.pdf |
| 3    | [图片]    | -      | 失败    | patent_001.pdf |

支持的输出格式：
- **Excel (.xlsx)** - 默认格式，可嵌入图片
- **CSV (.csv)** - 纯文本格式
- **Markdown (.md)** - 文档格式

输出文件位置：
- 表格文件: `output/results.xlsx`
- 图片文件夹: `output/images/`
- JSON 总结: `output/summary.json`

## 📖 文档导航

本项目包含完整的文档体系：

| 文档 | 用途 | 适用对象 |
|------|------|---------|
| [README.md](README.md) | 项目介绍 | 用户/开发者 |
| [SKILL.md](SKILL.md) | Skill 定义 | LLM 模型 |
| [QUICK_START.md](QUICK_START.md) | 快速参考 | LLM/用户 |
| [RUNTIME_GUIDE.md](RUNTIME_GUIDE.md) | 详细手册 | LLM/开发者 |
| [INDEX.md](INDEX.md) | 文档导航 | 所有用户 |

## ⚙️ 高级配置

### MineRU 方法选择

- **ocr**: 使用 OCR 技术，适用于扫描件或图片型 PDF
- **txt**: 适用于文本型 PDF，速度快
- **auto**: 自动选择最佳方法（默认）

### al-chemist API 配置

在 `config.json` 中修改：

```json
"alchemist": {
  "api_url": "https://api-ocsr.alchemist.iresearch.net.cn/ocsr/",
  "headers": {
    "X-API-Version": "1.0",
    "Content-Type": "application/json"
  },
  "kekulize": true
}
```

**kekulize 参数说明**：
- `true`（默认）: 将芳香环转换为凯库勒结构，显式表示单双键
- `false`: 保持芳香表示，使用小写字母表示芳香原子
- 详细说明请查看: [KEKULIZE_CONFIG.md](D:\skills\KEKULIZE_CONFIG.md)

### 输出配置

```json
"output": {
  "table_format": "xlsx",          // 输出格式: xlsx, csv, md
  "include_images_in_table": true  // 是否在表格中嵌入图片
}
```

## 🔧 故障排除

### 问题 1：MineRU 处理失败

**可能原因**：
- 文件格式不支持
- 模型文件缺失
- 内存不足

**解决方法**：
1. 检查文件格式（支持 PDF, PPT, PPTX, DOC, DOCX, PNG, JPG）
2. 确认 `models` 目录完整
3. 尝试使用 `-m ocr` 方法

### 问题 2：al-chemist API 调用失败

**可能原因**：
- 网络连接问题
- API 服务不可用
- 图片格式不支持

**解决方法**：
1. 检查网络连接
2. 使用测试脚本验证 API：
   ```bash
   python D:\skills\scripts\alchemist_api.py test_image.png
   ```

### 问题 3：提取不到分子结构图

**可能原因**：
- MineRU 未识别出图片
- 图片筛选条件过严

**解决方法**：
1. 检查 `molecular_images` 目录下是否有输出
2. 查看 MineRU 日志
3. 手动检查专利中是否包含分子结构图

## 📝 日志查看

日志文件位于：`D:\skills\logs\patent_processor.log`

## 🔄 工作流程图

```
专利文档 (PDF)
    ↓
MineRU 处理
    ↓
提取图片
    ↓
人工审核 (可选)
    ↓
al-chemist API 识别
    ↓
生成表格 (Excel/CSV/MD)
```

## 📞 技术支持

如遇问题，请检查：

1. 日志文件：`D:\skills\logs\patent_processor.log`
2. 配置文件：`D:\skills\config.json`
3. 环境依赖���`conda list -n mineru`

## 📄 许可证

本项目仅供内部研究使用。

---

**版本**: 1.0.0
**更新日期**: 2026-04-27
**维护者**: Molecular Recognition Team

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 使用 Python 3.7+ 特性
- 遵循 PEP 8 代码规范
- 添加必要的文档和注释
- 测试新增功能

## 🙏 致谢

- [DECIMER-Image_Transformer](https://github.com/Kohulan/DECIMER-Image_Transformer)
- [DECIMER-Image-Segmentation](https://github.com/Kohulan/DECIMER-Image-Segmentation)
- [al-chemist API](https://api-ocsr.alchemist.iresearch.net.cn/)
- [YOLOv8](https://github.com/ultralytics/ultralytics)

## 📞 技术支持

遇到问题？请：

1. 查看详细文档: [RUNTIME_GUIDE.md](RUNTIME_GUIDE.md)
2. 检查配置文件: `config.json`
3. 查看日志文件: `logs/` 目录
4. 提交 Issue: [GitHub Issues](https://github.com/zjf-arch/molecular_recognition_skills/issues)