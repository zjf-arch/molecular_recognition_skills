"""
DECIMER Segmentation 分子结构提取工具
替代 MineRU，使用专业的化学结构分割模型
"""

import sys
import io
from pathlib import Path
import logging
from typing import List, Dict, Any
from datetime import datetime
import numpy as np

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加脚本目录到路径
sys.path.append(str(Path(__file__).parent))

from alchemist_api import AlchemistAPI
from table_generator import TableGenerator

# 尝试导入进度条
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("提示: 安装 tqdm 可以获得更好的进度显示 (pip install tqdm)")

# 尝试导入 DECIMER Segmentation
try:
    from decimer_segmentation import segment_chemical_structures_from_file, segment_chemical_structures
    DECIMER_AVAILABLE = True
except ImportError:
    DECIMER_AVAILABLE = False
    print("警告: DECIMER Segmentation 未安装")
    print("安装方法: pip install decimer-segmentation")
    print("或: cd D:\\skills\\DECIMER-Image-Segmentation && pip install -e .")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('D:\\skills\\logs\\decimer_processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DECIMERSegmentationProcessor:
    """DECIMER Segmentation 处理器"""

    def __init__(self, output_dir: str = "D:/skills/molecular_images"):
        """
        初始化处理器

        Args:
            output_dir: 输出目录
        """
        if not DECIMER_AVAILABLE:
            raise ImportError(
                "DECIMER Segmentation 未安装。"
                "请运行: pip install decimer-segmentation"
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_structures_from_pdf(
        self,
        pdf_path: str,
        expand: bool = True,
        save_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        从PDF提取化学结构图

        Args:
            pdf_path: PDF文件路径
            expand: 是否扩展不完整的遮罩
            save_images: 是否保存图像到磁盘

        Returns:
            提取的结构信息列表
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"文件不存在: {pdf_path}")

        logger.info(f"使用 DECIMER Segmentation 处理: {pdf_path.name}")
        print(f"\n{'='*60}")
        print(f"DECIMER Segmentation - 化学结构提取")
        print(f"{'='*60}")
        print(f"文件: {pdf_path.name}")
        print(f"{'='*60}\n")

        try:
            # 使用 DECIMER Segmentation 提取化学结构
            logger.info("正在分割化学结构...")
            print("正在识别和分割化学结构...")

            segments = segment_chemical_structures_from_file(
                str(pdf_path),
                expand=expand
            )

            if not segments:
                logger.warning("未找到化学结构")
                print("\n未找到化学结构")
                return []

            logger.info(f"找到 {len(segments)} 个化学结构")
            print(f"\n✓ 找到 {len(segments)} 个化学结构")

            # 准备输出目录 - 直接保存，不创建额外子目录避免路径过长
            # 输出目录已经是 output/images，确保目录存在
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # 处理每个结构
            structures = []

            iterator = tqdm(enumerate(segments, 1), desc="保存图像") if HAS_TQDM else enumerate(segments, 1)

            for idx, segment in iterator:
                if not isinstance(segment, np.ndarray):
                    logger.warning(f"跳过无效结构 {idx}: 类型 {type(segment)}")
                    continue

                # 保存图像 - 使用简短的文件名避免路径过长
                image_filename = f"struct_{idx}.png"  # 简化文件名
                image_path = self.output_dir / image_filename  # 直接保存到output_dir

                if save_images:
                    try:
                        # 使用PIL保存图像，更可靠
                        from PIL import Image
                        # DECIMER返回的是numpy数组，可能有RGB或BGR格式
                        # 检查通道数并转换
                        if len(segment.shape) == 3:
                            # 如果是3通道，假设是RGB
                            pil_image = Image.fromarray(segment)
                        elif len(segment.shape) == 2:
                            # 如果是灰度图
                            pil_image = Image.fromarray(segment)
                        else:
                            logger.warning(f"未知图像格式 {idx}: shape={segment.shape}")
                            pil_image = Image.fromarray(segment)

                        pil_image.save(str(image_path))
                        logger.info(f"保存结构 {idx}: {image_filename}")
                    except Exception as e:
                        logger.error(f"保存图像失败 {idx}: {e}")
                        continue

                structures.append({
                    'index': idx,
                    'image': segment,
                    'image_path': str(image_path),
                    'filename': image_filename,
                    'shape': segment.shape
                })

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

    def process_patent(
        self,
        pdf_path: str,
        manual_review: bool = False,
        api_url: str = "https://api-ocsr.alchemist.iresearch.net.cn/ocsr/",
        api_headers: Dict[str, str] = None,
        output_format: str = 'xlsx',
        include_images: bool = True
    ) -> Dict[str, Any]:
        """
        完整处理流程：提取 → 识别 → 生成表格

        Args:
            pdf_path: PDF文件路径
            manual_review: 是否人工审核
            api_url: al-chemist API地址
            api_headers: API请求头
            output_format: 输出格式
            include_images: 是否在表格中包含图片

        Returns:
            处理结果
        """
        pdf_path = Path(pdf_path)

        # 1. 提取化学结构
        structures = self.extract_structures_from_pdf(pdf_path)

        if not structures:
            return {
                'success': False,
                'error': '未找到化学结构',
                'patent_name': pdf_path.name
            }

        # 2. 人工审核（可选）
        if manual_review:
            structures = self._manual_review_structures(structures)
            if not structures:
                return {
                    'success': False,
                    'error': '用户取消了所有结构',
                    'patent_name': pdf_path.name
                }

        # 3. 调用API识别
        logger.info("调用 API 识别分子结构...")
        print(f"\n{'='*60}")
        print("调用 API 识别分子结构...")
        print(f"{'='*60}\n")

        if api_headers is None:
            api_headers = {
                "X-API-Version": "1.0",
                "Content-Type": "application/json"
            }

        api_client = AlchemistAPI(api_url, api_headers)
        image_paths = [s['image_path'] for s in structures]

        # 批量识别
        if HAS_TQDM:
            results = []
            for idx, image_path in enumerate(tqdm(image_paths, desc="识别分子"), 1):
                result = api_client.recognize_molecule(image_path)
                result['image_path'] = image_path
                result['index'] = idx
                results.append(result)
                if idx < len(image_paths):
                    import time
                    time.sleep(0.5)
        else:
            results = api_client.batch_recognize(image_paths, delay=0.5)

        # 4. 生成表格
        logger.info("生成结果表格...")
        print(f"\n{'='*60}")
        print("生成结果表格...")
        print(f"{'='*60}\n")

        table_generator = TableGenerator("D:/skills/results")
        table_path = table_generator.create_result_table(
            results,
            pdf_path.name,
            include_images=include_images,
            format=output_format
        )

        # 5. 输出结果
        logger.info("处理完成")
        print(f"\n{'='*60}")
        print("✓ 处理完成！")
        print(f"{'='*60}")
        print(f"化学结构: {len(structures)} 个")
        print(f"成功识别: {sum(1 for r in results if r['success'])}/{len(results)}")
        print(f"表格位置: {table_path}")
        print(f"{'='*60}\n")

        return {
            'success': True,
            'patent_name': pdf_path.name,
            'total_structures': len(structures),
            'successful_recognitions': sum(1 for r in results if r['success']),
            'table_path': table_path,
            'results': results
        }

    def _manual_review_structures(self, structures: List[Dict]) -> List[Dict]:
        """
        人工审核化学结构

        Args:
            structures: 结构列表

        Returns:
            用户确认的结构列表
        """
        logger.info("进入人工审核阶段")
        print(f"\n{'='*60}")
        print("人工审核阶段")
        print(f"{'='*60}")
        print(f"找到 {len(structures)} 个化学结构")
        print("\n操作说明:")
        print("  y - 确认是化学结构")
        print("  n - 不是，跳过")
        print("  o - 打开查看")
        print("  s - 跳过剩余")
        print("  q - 退出")
        print(f"{'='*60}")

        approved = []

        for idx, structure in enumerate(structures, 1):
            print(f"\n[{idx}/{len(structures)}]")
            print(f"  大小: {structure['shape'][1]}x{structure['shape'][0]} px")
            print(f"  文件: {structure['filename']}")

            while True:
                response = input("\n是否为化学结构？(y/n/o/s/q): ").strip().lower()

                if response == 'y':
                    approved.append(structure)
                    print("✓ 已确认")
                    break
                elif response == 'n':
                    print("- 已跳过")
                    break
                elif response == 'o':
                    try:
                        import cv2
                        cv2.imshow("Chemical Structure", structure['image'])
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    except Exception as e:
                        print(f"无法显示图像: {e}")
                elif response == 's':
                    logger.info("用户跳过剩余结构")
                    print(f"\n已确认 {len(approved)} 个结构")
                    return approved
                elif response == 'q':
                    logger.info("用户取消处理")
                    print("\n用户取消")
                    return []
                else:
                    print("无效输入，请输入 y/n/o/s/q")

        print(f"\n{'='*60}")
        print(f"审核完成！确认 {len(approved)} 个结构")
        print(f"{'='*60}\n")

        return approved


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='DECIMER Segmentation 化学结构提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基本用法
  python decimer_processor.py patent.pdf

  # 批量处理
  python decimer_processor.py patent1.pdf patent2.pdf

  # 带人工审核
  python decimer_processor.py patent.pdf --manual-review

  # 输出CSV格式
  python decimer_processor.py patent.pdf --format csv

  # 仅提取图像（不识别）
  python decimer_processor.py patent.pdf --extract-only
        """
    )

    parser.add_argument('patents', nargs='+', help='专利文件路径（PDF格式）')
    parser.add_argument('--manual-review', action='store_true',
                        help='启用人工审核')
    parser.add_argument('--format', choices=['xlsx', 'csv', 'md'],
                        default='xlsx', help='输出表格格式')
    parser.add_argument('--no-images', action='store_true',
                        help='表格中不包含图片')
    parser.add_argument('--extract-only', action='store_true',
                        help='仅提取图像，不调用API识别')
    parser.add_argument('--no-expand', action='store_true',
                        help='不扩展不完整的遮罩')

    args = parser.parse_args()

    # 检查 DECIMER 是否可用
    if not DECIMER_AVAILABLE:
        print("\n错误: DECIMER Segmentation 未安装")
        print("\n安装方法:")
        print("  pip install decimer-segmentation")
        print("或:")
        print("  cd D:\\skills\\DECIMER-Image-Segmentation")
        print("  pip install -e .")
        sys.exit(1)

    # 创建处理器
    processor = DECIMERSegmentationProcessor()

    # 处理文件
    results_list = []

    for pdf_file in args.patents:
        try:
            if args.extract_only:
                # 仅提取图像
                structures = processor.extract_structures_from_pdf(
                    pdf_file,
                    expand=not args.no_expand
                )
                result = {
                    'success': len(structures) > 0,
                    'patent_name': Path(pdf_file).name,
                    'total_structures': len(structures)
                }
            else:
                # 完整处理
                result = processor.process_patent(
                    pdf_file,
                    manual_review=args.manual_review,
                    output_format=args.format,
                    include_images=not args.no_images
                )

            results_list.append(result)

        except Exception as e:
            logger.error(f"处理失败 {pdf_file}: {e}")
            print(f"\n错误: 处理失败 - {pdf_file}")
            print(f"原因: {e}")
            results_list.append({
                'success': False,
                'patent_name': Path(pdf_file).name,
                'error': str(e)
            })

    # 输出汇总
    if len(results_list) > 1:
        print(f"\n{'='*60}")
        print("批量处理完成！")
        print(f"{'='*60}")
        print(f"处理文件数: {len(results_list)}")
        success_count = sum(1 for r in results_list if r['success'])
        print(f"成功: {success_count}/{len(results_list)}")
        print(f"{'='*60}\n")

    # 返回退出码
    sys.exit(0 if all(r['success'] for r in results_list) else 1)


if __name__ == "__main__":
    main()