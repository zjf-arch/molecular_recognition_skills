# molecular_recognition_skills
自动化解析 PDF、PPT、DOC 及图片格式的专利文档，通过 MineRU 深度学习模型提取全文图片；再应用智能算法，将分子结构图自动划分为小分子、聚合物、废弃三类。随后调用 al-chemist/decimer 工具，将分子结构图像转换为 SMILES 字符串；若为聚合物结构，生成的 SMILES 会再通过 YOLO 模型进一步优化处理。系统最终输出包含序号、分子结构图、SMILES、识别状态、分子在原文献中的位置及原文献名称的结构化表格，支持 Excel、CSV、Markdown 多种格式，并具备批量处理能力与完整的处理日志记录功能。
