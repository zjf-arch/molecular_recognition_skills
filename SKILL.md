---
name: molecular-recognition-skill
description: |
  Extract molecular structures from chemical literature PDFs, intelligently classify and filter, recognize SMILES strings, and output structured Excel data.
  从化学专利PDF文献中自动提取分子结构图，智能分类过滤，识别生成SMILES字符串，输出结构化Excel数据。
  Interactive workflow with 7-step progress tracking.
  交互式7步工作流程，实时进度跟踪。
triggers:
  - "分子识别"
  - "提取分子结构"
  - "识别化学结构"
  - "SMILES识别"
  - "化学结构提取"
  - "处理化学文献"
---

# 分子识别 Skill

## Skill 功能

从化学专利PDF文献中自动：
1. 提取分子结构图（DECIMER Segmentation）
2. 智能分类过滤（ResNet18，准确率98.95%）
3. 识别生成SMILES字符串（DECIMER Transformer）
4. 输出结构化Excel数据

## 执行流程（7步骤）

当用户请求执行此 skill 时，严格按以下流程操作：

### 步骤 1：询问输入文件

**显示提示**：
```
请输入需要处理的文件路径：
- 支持PDF文件（.pdf）
- 支持包含多个PDF文件的目录
示例：
  D:\patents\CN110824838.pdf
  ./papers/paper1.pdf
```

**等待用户输入，然后验证**：
- ��用 `ls -lh "路径"` 验证文件存在
- 如果不存在，提示重新输入
- 如果存在，显示文件大小并确认

### 步骤 2：选择识别引擎

**显示提示**：
```
请选择分子识别引擎：

1. Alchemist API（在线识别）
   ✓ 需要网络
   ✓ 速度快（~500ms/张）
   ✓ 提供置信度
   ✗ 需API额度

2. DECIMER Transformer（离线识别）【推荐】
   ✓ 无需网络
   ✓ 速度更快（~200ms/张）
   ✓ 免费，无限制
   ✓ 数据隐私保护

请选择（输入 1 或 2）：
```

**等待用户选择**：
- 输入 1 → alchemist
- 输入 2 → decimer（推荐）

### 步骤 3-6：运行处理并显示进度

**执行命令**：
```bash
"C:\Users\21600\anaconda3\envs\decimer\python.exe" \
  "D:\skills\分子识别skills\scripts\simplified_integrated_processor.py" \
  --pdf "[用户输入的PDF路径]" \
  --recognizer decimer
```

**关键要求**：
- ✓ 必须使用 decimer conda 环境的 Python
- ✓ 设置超时 ≥ 300秒
- ✓ 使用完整绝对路径
- ✓ 脚本完成后，从输出中提取进度信息并显示

**注意**：由于脚本一次性执行所有步骤（3-6），进度信息将在脚本完成后统一返回。执行完成后，先显示详细进度，再显示总结。

**步骤 3：DECIMER Segmentation - 提取化学结构图**
```
✓ 开始时间: HH:MM:SS
✓ 进度: 正在加载DECIMER模型...正在提取PDF页面...
✓ 完成: 提取完成！
✓ 耗时: 约10��
```

**步骤 4：ResNet18智能分类 - 分类过滤**
```
✓ 开始时间: HH:MM:SS
✓ 进度: 正在加载ResNet18...模型准确率98.95%...
✓ 分类结果:
  - 小分子: XX张 ✓
  - 聚合物: XX张 ✓
  - 废弃: XX张 ✓
✓ 完成: 分类完成！
✓ 耗时: 约5秒
```

**步骤 5：DECIMER Transformer识别 - 生成SMILES**
```
✓ 开始时间: HH:MM:SS
✓ 进度: 正在加载DECIMER Transformer...
✓ 识别:
  - 小分子识别: XX张 ✓
  - 聚合物识别: XX张 ✓
  - 识别成功: XX/XX张 ✓
✓ Ce/Ge替换: XX个聚合物 ✓
✓ RDKit: 可用 ✓
✓ 完成: 识别完成！
✓ 耗时: 约70秒
```

**步骤 6：YOLO处理 + Excel生成**
```
✓ 开始时间: HH:MM:SS
✓ 进度: 正在YOLO处理聚合物...
✓ YOLO处理: XX张聚合物 ✓
✓ Ce填充图片: XX张 ✓
✓ 生成Excel: 完成 ✓
✓ Excel文件: 生成成功 ✓
✓ 完成: Excel生成完成！
✓ 耗时: 约110秒
```

### 步骤 7：显示处理总结（在进度详情之后）

**查找最新输出目录**：
```bash
ls -lt "D:\skills\分子识别skills\output" | head -n 5
```

**读取处理总结JSON**：
```bash
读取: D:\skills\分子识别skills\output\[最新目录]\processing_summary.json
```

**提取关键数据并展示**：

```
======================================================================
处理统计

| 项目 | 数量/状态 |
|------|----------|
| 输入文件 | [文件名] ([大小]) |
| 识别引擎 | DECIMER Transformer |
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
- 文件名: [文件名].xlsx
- 路径: [完整路径]

图片文件夹:
- 小分子: XX 张 → images\小分子
- 聚合物: XX 张 → images\聚合物
- 废弃: XX 张 → images\废弃
- Ce填充: XX 张 → images\Ce填充

======================================================================
✓ 处理成功完成！

总耗时: 约 X 分钟

======================================================================
```

## 输出文件结构

```
output/[文件名]__YYYYMMDD_HHMMSS/
├── [文件名]_识别结果.xlsx          # Excel表格（主输出）
├── processing_summary.json         # 处理总结
└── images/
    ├── 小分子/                      # 小分子图片
    ├── 聚合物/                      # 聚合物图片
    ├── 废弃/                        # 废弃图片
    └── Ce填充/                      # Ce原子填充图片
```

## 技术架构

**模型组合**：
- DECIMER Segmentation: 提取化学结构图（召回率90-95%）
- ResNet18 Classifier: 智能分类过滤（准确率98.95%）
- DECIMER Transformer: SMILES识别（成功率95-98%）
- YOLOv8-OBB: 聚合物Ce原子填充

**数据流**：
```
PDF → 提取图片 → 分类 → 过滤废弃 → SMILES识别 → Ce替换 → Excel输出
```

## 性能指标

- 提取速度: ~100ms/页
- 分类速度: ~50ms/张
- 识别速度: ~200ms/张（DECIMER）
- 处理时间: 3-5分钟（50张图片）

## 系统要求

**必须环境**：
- Python 3.8+
- Conda环境: decimer（必须激活）
- DECIMER库已安装

**硬件要求**：
- CPU: 4核+
- 内存: 8GB+（推荐16GB）
- 磁盘: 10GB可用空间

## 常见问题

### Q1: 如何验证decimer环境？

```bash
conda env list  # 确认有decimer环境
"C:\Users\21600\anaconda3\envs\decimer\python.exe" --version  # 验证Python版本
```

### Q2: 提取图片数为0？

可能原因：
- PDF为扫描版（无可提取文本）
- PDF不包含化学结构图
- DECIMER模型加载失败

解决方案：检查PDF是否有可提取文本

### Q3: 识别成功率低？

检查：
- 图片质量是否清晰
- 废弃文件夹是否误分类
- DECIMER模型版本

## 使用场景

- **专利分析**: 批量提取专利中的分子结构
- **文献调研**: 整理论文中的化合物SMILES
- **数据库构建**: 创建分子结构数据库
- **方法对比**: 对比不同文献的合成方法

## 相关文档

- **详细指南**: RUNTIME_GUIDE.md（LLM执行手册）
- **快速卡片**: QUICK_START.md（快速执行参考）
- **系统说明**: SKILLS_README.md（技术文档）

## LLM执行关键要点

**必须遵循**：
1. ✓ 先询问输入 → 等待用户输入
2. ✓ 验证路径 → 确认文件存在
3. ✓ 选择引擎 → 用户选择
4. ✓ 使用decimer环境Python
5. ✓ 设置足够超时（≥300秒）
6. ✓ 监控进度 → 捕获完成标记
7. ✓ 读取总结JSON
8. ✓ 清晰展示结果

**关键命令格式**：
```bash
# ✓ 正确（使用decimer环境Python完整路径）
"C:\Users\21600\anaconda3\envs\decimer\python.exe" "完整脚本路径" --pdf "完整PDF路径" --recognizer decimer

# ✗ 错误（不要使用默认环境或相对路径）
python scripts/...  # 错误：未指定decimer环境
conda run -n decimer ...  # 错误：有编码问题
```

## 示例执行

**用户**: 运行一下分子识别skill吧

**Skill响应**:
```
步骤1: 请输入需要处理的文件路径...
[等待输入]

用户: D:\patents\CN123456.pdf

��骤2: 请选择识别引擎...
[等待选择]

用户: 2

步骤3-6: 开始处理（执行脚本）...
[脚本完成后]

步骤3-6详细进度:
  ✓ 步骤3: DECIMER提取 - 提取完成！
  ✓ 步骤4: ResNet18分类 - 分类完成！
  ✓ 步骤5: DECIMER识别 - 识别完成！
  ✓ 步骤6: YOLO+Excel - 生成完成！

步骤7: 处理总结
[显示完整统计数据和输出文件路径]
```

---

**Skill版本**: v1.0  
**创建日期**: 2026-04-14  
**适用模型**: 所有支持工具调用的LLM