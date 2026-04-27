"""
PDF 页面提取工具
从 PDF 中提取指定页面并保存为新文件
"""

import fitz  # PyMuPDF
from pathlib import Path


def extract_pdf_pages(input_path: str, output_path: str, pages: list):
    """
    从 PDF 中提取指定页面

    Args:
        input_path: 输入 PDF 路径
        output_path: 输出 PDF 路径
        pages: 要保留的页码列表（从1开始计数）
    """
    # 打开 PDF
    doc = fitz.open(input_path)

    print(f"原始 PDF 共 {len(doc)} 页")
    print(f"将保留第 {pages} 页")

    # 创建新文档
    new_doc = fitz.open()

    # 提取指定页面（注意：PyMuPDF 页码从 0 开始）
    for page_num in pages:
        if 1 <= page_num <= len(doc):
            # 页码从1开始，转换为从0开始的索引
            page_index = page_num - 1
            new_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)
            print(f"[OK] 已提取第 {page_num} 页")
        else:
            print(f"[跳过] 第 {page_num} 页不存在（总页数：{len(doc)}）")

    # 保存新文档
    new_doc.save(output_path)
    print(f"\n新 PDF 已保存: {output_path}")
    print(f"新 PDF 共 {len(new_doc)} 页")

    # 关闭文档
    doc.close()
    new_doc.close()


def main():
    # 输入文件路径
    input_file = r"D:\skills\测试文件\[信越]_CN110824838B_Resist composition and patterning method.pdf"

    # 输出文件路径
    output_file = r"D:\skills\测试文件\[信越]_CN110824838B_测试文件_仅1和49页.pdf"

    # 要保留的页码（从1开始计数）
    pages_to_keep = [1, 49]

    print("=" * 60)
    print("PDF 页面提取工具")
    print("=" * 60)

    # 检查输入文件
    if not Path(input_file).exists():
        print(f"错误：文件不存在 - {input_file}")
        return

    # 执行提取
    extract_pdf_pages(input_file, output_file, pages_to_keep)

    print("=" * 60)
    print("处理完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()