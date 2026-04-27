#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
带页码溯源功能的DECIMER处理器
使用PyMuPDF逐页提取，记录页码信息
"""

import sys
import io
from pathlib import Path
import logging
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
import fitz  # PyMuPDF

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加脚本目录到路径
sys.path.append(str(Path(__file__).parent))

from scripts.logger import logger

# 尝试导入进度条
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# 尝试导入 DECIMER Segmentation
try:
    from decimer_segmentation import segment_chemical_structures
    DECIMER_AVAILABLE = True
except ImportError:
    DECIMER_AVAILABLE = False
    print("警告: DECIMER Segmentation 未安装")


class DECIMERProcessorWithPageTracking:
    """带页码溯源的DECIMER处理器"""

    def __init__(self, output_dir: str = "D:/skills/molecular_images"):
        """
        初始化处理器

        Args:
            output_dir: 输出目录
        """
        if not DECIMER_AVAILABLE:
            raise ImportError("DECIMER Segmentation 未安装")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_structures_from_pdf(
        self,
        pdf_path: str,
        expand: bool = True,
        save_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        从PDF提取化学结构图（带页码信息）

        Args:
            pdf_path: PDF文件路径
            expand: 是否扩展不完整的遮罩
            save_images: 是否保存图像到磁盘

        Returns:
            提取的结构信息列表，每个元素包含：
            - index: 结构索引
            - image: numpy数组
            - image_path: 图片保存路径
            - filename: 文件名
            - page_number: 页码（从1开始）
            - shape: 图片尺寸
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"文件不存在: {pdf_path}")

        logger.info(f"使用 DECIMER Segmentation 处理: {pdf_path.name}")
        print(f"\n{'='*60}")
        print(f"DECIMER Segmentation - 化学结构提取（带页码溯源）")
        print(f"{'='*60}")
        print(f"文件: {pdf_path.name}")
        print(f"{'='*60}\n")

        try:
            # 打开PDF
            pdf_doc = fitz.open(str(pdf_path))
            total_pages = pdf_doc.page_count

            logger.info(f"PDF总页数: {total_pages}")
            print(f"PDF总页数: {total_pages}\n")

            structures = []
            global_idx = 0

            # 逐页处理
            iterator = tqdm(range(total_pages), desc="处理页面") if HAS_TQDM else range(total_pages)

            for page_num in iterator:
                # 获取页面
                page = pdf_doc[page_num]

                # 将页面渲染为图片
                mat = fitz.Matrix(3.0, 3.0)  # 3倍放大提高质量（原为2.0）
                pix = page.get_pixmap(matrix=mat)

                # 转换为numpy数组
                img_data = pix.tobytes("png")
                import cv2
                img_array = np.frombuffer(img_data, dtype=np.uint8)
                page_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                # 使用DECIMER提取这一页的化学结构
                try:
                    segments = segment_chemical_structures(page_image, expand=expand)

                    if segments:
                        logger.info(f"  第{page_num + 1}页: 找到 {len(segments)} 个结构")

                        # 保存每个结构
                        for seg_idx, segment in enumerate(segments):
                            if not isinstance(segment, np.ndarray):
                                continue

                            global_idx += 1

                            # 保存图像
                            image_filename = f"struct_page{page_num + 1}_{seg_idx + 1}.png"
                            # 确保输出目录存在
                            self.output_dir.mkdir(parents=True, exist_ok=True)

                            image_path = self.output_dir / image_filename

                            if save_images:
                                try:
                                    from PIL import Image
                                    if len(segment.shape) == 3:
                                        pil_image = Image.fromarray(segment)
                                    elif len(segment.shape) == 2:
                                        pil_image = Image.fromarray(segment)
                                    else:
                                        pil_image = Image.fromarray(segment)

                                    # 保存高质量PNG图片
                                    pil_image.save(str(image_path), format='PNG', optimize=False)

                                except Exception as e:
                                    logger.error(f"保存图像失败: {e}")
                                    continue

                            structures.append({
                                'index': global_idx,
                                'image': segment,
                                'image_path': str(image_path),
                                'filename': image_filename,
                                'page_number': page_num + 1,  # 页码从1开始
                                'shape': segment.shape
                            })

                except Exception as e:
                    logger.warning(f"处理第{page_num + 1}页时出错: {e}")
                    continue

            pdf_doc.close()

            print(f"\n{'='*60}")
            print(f"提取完成！")
            print(f"化学结构数量: {len(structures)}")
            print(f"保存位置: {self.output_dir}")
            print(f"{'='*60}\n")

            return structures

        except Exception as e:
            logger.error(f"DECIMER 处理失败: {e}")
            print(f"\n错误: {e}")
            raise


# 测试代码
if __name__ == "__main__":
    processor = DECIMERProcessorWithPageTracking()

    # 测试文件
    test_pdf = r"D:\skills\测试文件\[信越]_CN110824838B_测试文件_仅1和49页.pdf"

    structures = processor.extract_structures_from_pdf(test_pdf)

    print(f"\n提取结果:")
    for i, struct in enumerate(structures[:10], 1):
        print(f"  {i}. 页码{struct['page_number']}: {struct['filename']}")