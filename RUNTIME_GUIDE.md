# 分子识别 Skills - 运行指南（LLM执行手册）

## 📋 概述

本文档描述了分子识别skills的完整执行流程，旨在让任何LLM模型都能理解并正确执行此skill。

**核心功能**: 从化学专利PDF文献中自动提取分子结构图，智能分类过滤，识别生成SMILES字符串，输出结构化Excel数据。

---

## 🔄 完整工作流程（7步骤）

### 步骤 1：询问输入文件路径

**执行动作**:
```
显示提示信息：
"请输入需要处理的文件路径：
- 支持PDF文件（.pdf）
- 支持包含多个PDF文件的目录
示例：
  D:\patents\CN110824838.pdf
  ./papers/paper1.pdf
  ./patents_folder/"

等待用户输入
```

**输入验证**:
- 使用 `ls -lh "用户输入的路径"` 验证文件存在
- 如果不存在，提示重新输入
- 如果存在，显示文件大小并确认

**关键信息提取**:
- 文件名（用于后续输出文件命名）
- 文件大小（用于预估处理时间）

---

### 步骤 2：选择识别引擎

**执行动作**:
```
显示提示信息：
"请选择分子识别引擎：

1. Alchemist API（在线识别）
   ✓ 需要网络连接
   ✓ 速度快（~500ms/张）
   ✓ 提供置信度评分
   ✗ 数据会上传到服务器
   ✗ 需要API额度

2. DECIMER Transformer（离线识别）【推荐】
   ✓ 无需网络，本地处理
   ✓ 速度更快（~200ms/张）
   ✓ 免费，无限制使用
   ✓ 数据隐私保护
   ✗ 不提供置信度评分

请选择识别引擎（输入 1 或 2）："

等待用户输入
```

**输入验证**:
- 如果输入 "1"，选择 `alchemist`
- 如果输入 "2"，选择 `decimer`（推荐）
- 其他输入提示重新输入

---

### 步骤 3-6：运行处理流程

**执行命令**:
```bash
"C:\Users\21600\anaconda3\envs\decimer\python.exe" \
  "D:\skills\分子识别skills\scripts\simplified_integrated_processor.py" \
  --pdf "用户输入的PDF路径" \
  --recognizer decimer
```

**关键注意事项**:
1. ✓ 必须在 `decimer` conda环境中运行
2. ✓ 使用完整路径（避免相对路径问题）
3. ✓ 设置超时时间 ≥ 300秒（处理可能需要3-5分钟）

**实时监控关键标记**:
监控脚本输出，捕获以下关键完成标记：

| 步骤 | 关键标记 | 含义 |
|------|---------|------|
| 步骤3 | "DECIMER Segmentation加载源码..." | 开始提取化学结构 |
| 步骤3 | "提取完成！" | 提取完成 ✓ |
| 步骤4 | "正在加载ResNet18分类器..." | 开始分类 |
| 步骤4 | "验证准确率: 98.95%" | 模型加载成功 ✓ |
| 步骤4 | "步骤2: ResNet18分类并分别保存..." | 分类完成 ✓ |
| 步骤5 | "DECIMER Transformer加载成功" | 识别模型加载 ✓ |
| 步骤5 | "识别成功: XX/XX 张" | 识别完成 ✓ |
| 步骤6 | "Excel文件生成成功" | Excel生成 ✓ |
| 步骤7 | "处理完成！" | 全流程完成 ✓ |

---

### 步骤 7：读取处理总结并展示

**查找最新输出目录**:
```bash
ls -lt "D:\skills\分子识别skills\output" | head -n 5
```

最新的目录名格式：`[文件名]__YYYYMMDD_HHMMSS`

**读取处理总结**:
```bash
读取: D:\skills\分子识别skills\output\[最新目录]\processing_summary.json
```

**关键数据字段**:
```json
{
  "success": true,                   // 处理是否成功
  "total_images": 47,               // 总提取图片数
  "classification": {
    "小分子": 14,                    // 小分子图片数
    "聚合物": 33,                    // 聚合物图片数  
    "废弃": 0                       // 废弃图片数
  },
  "recognition_success": 47,         // 识别成功数
  "recognition_total": 47,           // 识别总数
  "ce_replacement": {
    "polymers_with_ce_or_ge": 31,   // Ce/Ge替换数
    "rdkit_available": true         // RDKit是否可用
  },
  "yolo_processing": {
    "yolo_processed": 33            // YOLO处理数
  },
  "excel_file": "完整路径",          // Excel文件路径
  "image_folders": {
    "小分子": "完整路径",
    "聚合物": "完整路径",
    "废弃": "完整路径"
  }
}
```

---

## 📊 输出展示模板

### 步骤完成提示（每步完成时显示）

```
步骤 X: [步骤名称]

✓ 开始时间: HH:MM:SS
✓ 进度: [关键进度信息]
✓ 完成状态: [具体完成信息]
✓ 耗时: XX秒
```

### 最终总结展示模板

```
======================================================================
处理统计

| 项目 | 数量/状态 |
|------|----------|
| 输入文件 | [文件名] ([大小]) |
| 识别引擎 | DECIMER Transformer（离线） |
| 总提取图片 | XX 张 |
| 小分子 | XX 张 ✓ |
| 聚合物 | XX 张 ✓ |
| 废弃图片 | XX 张 |
| 有效图片 | XX 张 |
| 识别成功 | XX/XX 张 ✓ |
| 成功率 | XX.X% |
| Ce/Ge替换 | XX 个聚合物 |
| RDKit状态 | 可用 ✓ |
| YOLO处理 | XX 张 ✓ |

======================================================================
输出文件

Excel表格:
- 文件名: [文件��].xlsx
- 路径: [完整路径]

图片文件夹:
- 小分子: XX 张图片 → images\小分子
- 聚合物: XX 张图片 → images\聚合物
- 废弃: XX 张图片 → images\废弃
- Ce填充: XX 张图片 → images\Ce填充

处理总结文件:
- processing_summary.json

======================================================================
✓ 处理成功完成！

- ✓ 成功处理: XX 张图片
- ✓ 识别成功: XX 个SMILES
- ✓ 识别引擎: DECIMER Transformer
- ✓ Ce/Ge替换: XX 个聚合物
- ✓ YOLO处理: XX 张聚合物

总耗时: 约 X 分钟

======================================================================
```

---

## 🔧 技术架构

### 模型组件

| 组件 | 用途 | 模型文件 | 准确率/性能 |
|------|------|---------|-----------|
| **DECIMER Segmentation** | PDF提取化学结构图 | TensorFlow模型 | 90-95%召回率 |
| **ResNet18 Classifier** | 智能分类过滤 | best_model.pth | 98.95%准确率 |
| **DECIMER Transformer** | SMILES字符串识别 | Transformer模型 | 95-98%成功率 |
| **YOLOv8-OBB** | 聚合物Ce原子填充 | yolo11n-ce.pt | 旋转检测 |

### 处理流程数据流

```
PDF文件
  ↓ [DECIMER Segmentation]
提取图片（PNG）
  ↓ [ResNet18分类]
分类结果：小分子、聚合物、废弃
  ↓ [过滤废弃]
有效图片（小分子+聚合物）
  ↓ [DECIMER识别]
SMILES字符串
  ↓ [Ce/Ge替换]
修正后的SMILES
  ↓ [Excel生成]
Excel表格（图片+SMILES）
```

---

## ⚙️ 系统要求

### 软件环境

**必须环境**:
- Python 3.8+
- Conda环境：`decimer`（必须激活）
- DECIMER库已安装

**验证环境**:
```bash
# 验证conda环境
conda env list  # 确认有decimer环境

# 验证Python版本
"C:\Users\21600\anaconda3\envs\decimer\python.exe" --version
```

### 硬件要求

- CPU: 4核以上
- 内存: 8GB以上（推荐16GB）
- 硬盘: 10GB可用空间（临时文件）

---

## ⏱️ 性能指标

### 处理时间参考

| PDF页数 | 图片数量 | 预估时间 |
|---------|---------|---------|
| 1-10页 | 10-50张 | 1-2分钟 |
| 10-50页 | 50-200张 | 3-5分钟 |
| 50-100页 | 200-500张 | 10-15分钟 |
| >100页 | >500张 | >15分钟 |

### 各步骤耗时占比

- 步骤3（提取）：约10%
- 步骤4（分类）：约5%
- 步骤5（识别）：约60%（主要耗时）
- 步骤6（Excel）：约25%

---

## 🐛 常见问题处理

### 问题1：找不到decimer环境

**症状**: `conda env list`中没有decimer环境

**解决方案**:
```bash
# 创建decimer环境
conda create -n decimer python=3.8
conda activate decimer

# 安装依赖
cd D:\skills\分���识别skills
pip install -r requirements.txt

# 安装DECIMER
cd D:\skills\DECIMER-Image_Transformer
pip install -e .
```

### 问题2：PDF提取图片数量为0

**症状**: `total_images: 0`

**可能原因**:
1. PDF为扫描版（无可提取文本）
2. PDF不包含化学结构图
3. DECIMER模型加载失败

**检查方法**:
```bash
# 检查PDF是否为扫描版
python -c "import fitz; doc=fitz.open('PDF路径'); print('可提取文本:', len(doc[0].get_text())>0)"
```

### 问题3：识别成功率低

**症状**: `recognition_success/recognition_total < 0.9`

**可能原因**:
1. 图片质量差
2. 图片为复杂聚合物
3. DECIMER模型版本问题

**建议**: 检查`images\废弃`文件夹，确认是否误分类

### 问题4：Excel文件未生成

**症状**: 输出目录中没有.xlsx文件

**检查方法**:
```bash
# 查看错误日志
grep "ERROR\|Exception" processing_summary.json
```

---

## 📁 输出文件结构

### 标准输出目录结构

```
output/
└── [文件名]__YYYYMMDD_HHMMSS/
    ├── [文件名]_识别结果.xlsx          # Excel表格（主输出）
    ├── processing_summary.json         # 处理总结JSON
    └── images/
        ├── 小分子/                      # 小分子图片（14张）
        │   ├── small_1.png
        │   └── ...
        ├── 聚合物/                      # 聚合物图片（33张）
        │   ├── polymer_1.png
        │   └── ...
        ├── 废弃/                        # 废弃图片（通常为空）
        └── Ce填充/                      # Ce原子填充的聚合物图片（33张）
            ├── ce_filled_1.png
            └── ...
```

---

## 🎯 LLM执行关键要点

### 必须遵循的执行顺序

1. ✓ **先询问** → 等待用户输入
2. ✓ **验证路径** → 确认文件存在
3. ✓ **选择引擎** → 用户选择1或2
4. ✓ **激活环境** → 使用decimer环境Python
5. ✓ **运行脚本** → 设置足够超时时间
6. ✓ **监控进度** → 捕获关键完成标记
7. ✓ **读取总结** → 从JSON提取关键数据
8. ✓ **清晰展示** → 按模板格式化输出

### 关键命令格式

**正确示例**:
```bash
# 使用decimer环境的Python
"C:\Users\21600\anaconda3\envs\decimer\python.exe" \
  "D:\skills\分子识别skills\scripts\simplified_integrated_processor.py" \
  --pdf "完整路径" \
  --recognizer decimer
```

**错误示例（不要这样做）**:
```bash
# ✗ 使用默认Python环境
python scripts/simplified_integrated_processor.py

# ✗ 使用conda run（有编��问题）
conda run -n decimer python scripts/...

# ✗ 使用相对路径
python ./scripts/simplified_integrated_processor.py
```

### 进度监控重点

**必须捕获的关键信息**:
- ✓ DECIMER加载成功
- ✓ ResNet18准确率98.95%
- ✓ 提取图片数量
- ✓ 分类结果（小分子、聚合物、废弃）
- ✓ 识别成功率
- ✓ Ce/Ge替换数量
- ✓ YOLO处理数量
- ✓ Excel生成路径

---

## 📝 执行清单（Checklist）

**运行前检查**:
- [ ] decimer环境存在
- [ ] PDF文件路径正确
- [ ] Python版本≥3.8
- [ ] 硬盘空间≥10GB

**运行中监控**:
- [ ] 步骤3完成标记捕获
- [ ] 步骤4完成标记捕获
- [ ] 步骤5完成标记捕获
- [ ] 步骤6完成标记捕获
- [ ] 无ERROR或Exception

**运行后验证**:
- [ ] processing_summary.json存在
- [ ] success字段为true
- [ ] Excel文件存在且大小>0
- [ ] 图片文件夹数量匹配

---

## 🔗 相关文件路径

| 类型 | 路径 |
|------|------|
| 主脚本 | `D:\skills\分子识别skills\scripts\simplified_integrated_processor.py` |
| 模型目录 | `D:\skills\分子识别skills\models\` |
| 输出目录 | `D:\skills\分子识别skills\output\` |
| 测试文件 | `D:\skills\分子识别skills\测试文件\` |
| 系统文档 | `D:\skills\分子识别skills\SKILLS_README.md` |

---

## 💡 最佳实践建议

1. **优先选择DECIMER离线引擎**（隐私好、无限制）
2. **处理大批量时分批执行**（避免内存溢出）
3. **保留原始输出目录**（方便后续查看）
4. **检查废弃文件夹**（确认分类准确性）
5. **定期清理output目录**（避免硬盘空间不足）

---

## 📞 异常情况处理

### 如果处理失败

**步骤**:
1. 读取processing_summary.json
2. 检查success字段（应为false）
3. 查找ERROR标记
4. 根据错误类型提供解决方案：
   - 模型加载失败 → 检查环境
   - PDF读取失败 → 检查文件格式
   - 识别失败 → 检查图片质量
   - Excel生成失败 → 检查openpyxl库

---

**文档版本**: v1.0  
**创建日期**: 2026-04-14  
**适用范围**: 所有LLM模型执行分子识别skill  
**更新频率**: 随skill版本更新