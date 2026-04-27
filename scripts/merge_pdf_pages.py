#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF页面拼接工具
将指定PDF的特定页面拼接到另一个PDF的末尾
"""

import sys
import os
from pathlib import Path
import fitz  # PyMuPDF
from datetime import datetime

def merge_pdf_pages(
    pdf1_path: str,
    pdf2_path: str,
    page_num: int,
    output_path: str = None
):
    """
    将pdf2的指定页面拼接到pdf1的末尾

    Args:
        pdf1_path: 第一个PDF文件路径（目标PDF）
        pdf2_path: 第二个PDF文件路径（源PDF）
        page_num: 要提取的页码（从1开始）
        output_path: 输出文件路径（可选）

    Returns:
        输出文件路径
    """
    pdf1_path = Path(pdf1_path)
    pdf2_path = Path(pdf2_path)

    # 检查文件是否存在
    if not pdf1_path.exists():
        raise FileNotFoundError(f"PDF文件不存在: {pdf1_path}")

    if not pdf2_path.exists():
        raise FileNotFoundError(f"PDF文件不存在: {pdf2_path}")

    # 生成输出文件名
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = pdf1_path.parent / f"{pdf1_path.stem}_merged_{timestamp}.pdf"

    output_path = Path(output_path)

    print("=" * 80)
    print("PDF页面拼接工具")
    print("=" * 80)
    print(f"目标PDF: {pdf1_path.name}")
    print(f"源PDF: {pdf2_path.name}")
    print(f"提取页码: 第{page_num}页")
    print(f"输出文件: {output_path.name}")
    print("=" * 80)

    try:
        # 打开第一个PDF
        print(f"\n【步骤1】读取目标PDF: {pdf1_path.name}")
        pdf1 = fitz.open(str(pdf1_path))
        pdf1_pages = pdf1.page_count
        print(f"  页数: {pdf1_pages}")

        # 打开第二个PDF
        print(f"\n【步骤2】读取源PDF: {pdf2_path.name}")
        pdf2 = fitz.open(str(pdf2_path))
        pdf2_pages = pdf2.page_count
        print(f"  页数: {pdf2_pages}")

        # 检查页码是否有效
        if page_num < 1 or page_num > pdf2_pages:
            raise ValueError(f"页码 {page_num} 无效，PDF2只有 {pdf2_pages} 页")

        # 创建新的PDF
        print(f"\n【步骤3】创建新PDF...")
        new_pdf = fitz.open()

        # 复制第一个PDF的所有页面
        print(f"  复制 {pdf1_pages} 页从 {pdf1_path.name}")
        new_pdf.insert_pdf(pdf1, from_page=0, to_page=pdf1_pages-1)

        # 提取并插入第二个PDF的指定页面
        print(f"  提取第 {page_num} 页从 {pdf2_path.name}")
        # PyMuPDF页码从0开始
        page_index = page_num - 1
        new_pdf.insert_pdf(pdf2, from_page=page_index, to_page=page_index)

        # 保存新PDF
        print(f"\n【步骤4】保存新PDF...")
        new_pdf.save(str(output_path))

        # 关闭文件
        pdf1.close()
        pdf2.close()
        new_pdf.close()

        print(f"\n[OK] 拼接完成！")
        print(f"\n输出文件: {output_path}")
        print(f"  总页数: {pdf1_pages + 1} 页")
        print(f"  - 前 {pdf1_pages} 页: 来自 {pdf1_path.name}")
        print(f"  - 第 {pdf1_pages + 1} 页: 来自 {pdf2_path.name} 的第 {page_num} 页")

        return str(output_path)

    except Exception as e:
        print(f"\n❌ 拼接失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='PDF页面拼接工具 - 将指定PDF的特定页面拼接到另一个PDF的末尾',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 将pdf2的第70页拼接到pdf1的末尾
  python merge_pdf_pages.py --pdf1 "D:\\skills\\测试文件\\文件1.pdf" --pdf2 "D:\\skills\\测试文件\\文件2.pdf" --page 70

  # 指定输出文件
  python merge_pdf_pages.py --pdf1 "文件1.pdf" --pdf2 "文件2.pdf" --page 70 --output "merged.pdf"
        '''
    )

    parser.add_argument('--pdf1', type=str, required=True, help='目标PDF文件路径（将被追加）')
    parser.add_argument('--pdf2', type=str, required=True, help='源PDF文件路径（提取页面）')
    parser.add_argument('--page', type=int, required=True, help='要提取的页码（从1开始）')
    parser.add_argument('--output', type=str, help='输出文件路径（可选）')

    args = parser.parse_args()

    # 执行拼接
    result = merge_pdf_pages(
        pdf1_path=args.pdf1,
        pdf2_path=args.pdf2,
        page_num=args.page,
        output_path=args.output
    )

    print(f"\n✅ 成功生成: {result}")


if __name__ == "__main__":
    main()