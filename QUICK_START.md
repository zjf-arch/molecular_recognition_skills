# 分子识别 Skill - 快速执行卡片

## 🎯 7步执行流程

```
步骤1 → 询问PDF路径 → 验证文件存在
步骤2 → 选择引擎 → 推荐：DECIMER（离线）
步骤3 → DECIMER Segmentation → 提取化学结构图
步骤4 → ResNet18分类 → 小分子/聚合物/废弃
步骤5 → DECIMER识别 → 生成SMILES
步骤6 → Excel生成 → 嵌入图片+SMILES
步骤7 → 展示总结 → 处理统计+输出文件
```

---

## 🚀 核心执行命令

```bash
"C:\Users\21600\anaconda3\envs\decimer\python.exe" \
  "D:\skills\分子识别skills\scripts\simplified_integrated_processor.py" \
  --pdf "[用户PDF路径]" \
  --recognizer decimer
```

**关键要求**:
- ✓ 必须使用decimer环境Python
- ✓ 超时设置≥300秒
- ✓ 使用完整路径

---

## ✅ 完成标记（监控重点）

| 步骤 | 关键标记 |
|------|---------|
| 3 | "提取完成！" |
| 4 | "验证准确率: 98.95%" |
| 5 | "DECIMER Transformer加载成功" + "识别成功: XX/XX" |
| 6 | "Excel文件生成成功" |
| 7 | "processing_summary.json"读取成功 |

---

## 📊 输出结构

```
output/[文件名]__YYYYMMDD_HHMMSS/
├── [文件名]_识别结果.xlsx
├── processing_summary.json
└── images/
    ├── 小分子/
    ├── 聚合物/
    ├── 废弃/
    └── Ce填充/
```

---

## 🎨 展示模板

**每步骤完成提示**:
```
步骤 X: [名称]
✓ 开始: HH:MM:SS
✓ 状态: [关键信息]
✓ 耗时: XX秒
```

**最终总结**:
```
处理统计: 47张图片 | 14小分子 | 33聚合物 | 0废弃
识别成功: 47/47 (100%) | Ce替换: 31个
输出: Excel + 图片文件夹 + JSON
```

---

## ⚠️ 必须注意

1. **环境**: decimer conda环境（不是base）
2. **路径**: 完整绝对路径（避免相对路径）
3. **超时**: ≥300秒（处理需要3-5分钟）
4. **Python**: 3.8+ in decimer环境
5. **模型**: ResNet18准确率98.95%

---

## 🔍 验证清单

**运行前**:
- decimer环境存在 ✓
- PDF文件路径正确 ✓
- 磁盘空间≥10GB ✓

**运行后**:
- processing_summary.json存在 ✓
- success=true ✓
- Excel文件>0KB ✓
- 图片数量匹配 ✓

---

**详细文档**: RUNTIME_GUIDE.md  
**快速上手**: 本卡片