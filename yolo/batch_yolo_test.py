#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO批量测试脚本
批量处理指定目录下的所有图片，生成Ce填充结果
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np
from datetime import datetime
import pandas as pd

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "yolo"))

from yolo_processor import YOLOProcessor
from scripts.logger import logger

def batch_process_images(
    input_dir: str,
    output_dir: str = None,
    expansion_factor: float = 1.00,
    conf: float = 0.25
):
    """
    批量处理图片

    Args:
        input_dir: 输入图片目录
        output_dir: 输出目录（可选，默认自动生成）
        expansion_factor: 检测框扩展比例（默认1.00，不扩展）
        conf: YOLO检测置信度阈值（默认0.25）

    Returns:
        处理统计信息
    """
    input_dir = Path(input_dir)
    if not input_dir.exists():
        logger.error(f"输入目录不存在: {input_dir}")
        return None

    # 输出目录
    if output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = PROJECT_ROOT / "yolo" / "batch_output" / f"batch_{timestamp}"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 子目录
    detection_dir = output_dir / "detection_results"  # 可视化检测结果
    filled_dir = output_dir / "filled_results"        # Ce填充结果
    original_dir = output_dir / "original_structures" # 提取的原始结构

    detection_dir.mkdir(parents=True, exist_ok=True)
    filled_dir.mkdir(parents=True, exist_ok=True)
    original_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 80)
    logger.info("YOLO批量处理")
    logger.info("=" * 80)
    logger.info(f"输入目录: {input_dir}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"扩展比例: {expansion_factor*100:.0f}%")
    logger.info(f"置信度阈值: {conf}")

    # ==================== 加载YOLO模型 ====================
    logger.info("\n【步骤1】加载YOLO模型...")

    try:
        # 使用训练好的化学结构检测模型
        model_path = PROJECT_ROOT / "yolo" / "detect" / "runs" / "obb" / "train6" / "weights" / "best.pt"

        if not model_path.exists():
            logger.error(f"模型不存在: {model_path}")
            return None

        yolo_processor = YOLOProcessor(
            model_path=str(model_path),
            use_smart_placement=True  # 启用智能Ce放置
        )
        logger.info("✅ YOLO模型加载成功")

    except Exception as e:
        logger.error(f"YOLO模型加载失败: {e}")
        return None

    # ==================== 批量处理图片 ====================
    logger.info("\n【步骤2】批量处理图片...")

    # 扫描所有PNG图片
    image_files = sorted(input_dir.glob("*.png"))
    logger.info(f"发现 {len(image_files)} 张PNG图片")

    # 处理统计
    results = []
    stats = {
        'total': len(image_files),
        'processed': 0,
        'success': 0,
        'failed': 0,
        'no_detection': 0
    }

    for i, image_file in enumerate(image_files, 1):
        logger.info(f"\n处理图片 [{i}/{len(image_files)}]: {image_file.name}")

        try:
            # 读取图片
            image = cv2.imread(str(image_file))
            if image is None:
                logger.warning(f"  图片读取失败: {image_file.name}")
                stats['failed'] += 1
                continue

            logger.info(f"  图片尺寸: {image.shape[1]}x{image.shape[0]}")

            # ==================== YOLO检测 ====================
            detections = yolo_processor.detect_structures(
                image_path=str(image_file),
                conf=conf,
                iou=0.5,
                imgsz=512
            )

            logger.info(f"  检测结果: {len(detections)} 个结构")

            if len(detections) == 0:
                logger.warning(f"  ⚠️ 未检测到化学结构")
                stats['no_detection'] += 1

                # 保存未检测到结构的记录
                results.append({
                    'filename': image_file.name,
                    'status': 'no_detection',
                    'detections': 0,
                    'confidence': None,
                    'image_size': f"{image.shape[1]}x{image.shape[0]}"
                })
                continue

            # ==================== 扩展检测框 ====================
            expanded_detections = []
            for det in detections:
                expanded_det = det.copy()

                # 扩展轴对齐边界框
                if det.get('xyxy'):
                    x1, y1, x2, y2 = det['xyxy']
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    w = (x2 - x1) * expansion_factor
                    h = (y2 - y1) * expansion_factor
                    expanded_det['xyxy'] = [cx - w/2, cy - h/2, cx + w/2, cy + h/2]

                # 扩展旋转边界框
                if det.get('xyxyxyxy'):
                    points = np.array(det['xyxyxyxy'], dtype=np.float32)
                    center = points.mean(axis=0)
                    expanded_points = center + (points - center) * expansion_factor
                    expanded_det['xyxyxyxy'] = expanded_points.tolist()

                # 扩展xywhr格式
                if det.get('xywhr'):
                    cx, cy, w, h, r = det['xywhr']
                    expanded_det['xywhr'] = [cx, cy, w * expansion_factor, h * expansion_factor, r]

                expanded_detections.append(expanded_det)

            # ==================== 可视化检测结果 ====================
            vis_image = image.copy()
            for det in detections:
                # 绘制轴对齐边界框（绿色）
                x1, y1, x2, y2 = det['xyxy']
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # 标注置信度
                label = f"{det['confidence']:.2f}"
                cv2.putText(vis_image, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 绘制旋转边界框（红色）
                if det.get('xyxyxyxy'):
                    points = np.array(det['xyxyxyxy'], dtype=np.int32)
                    cv2.polylines(vis_image, [points], True, (0, 0, 255), 2)

            detection_path = detection_dir / f"{image_file.stem}_detection.png"
            cv2.imwrite(str(detection_path), vis_image)
            logger.info(f"  ✅ 检测可视化已保存")

            # ==================== Ce填充处理 ====================
            filled_image = yolo_processor.fill_structures_with_ce(
                image=image,
                detections=expanded_detections,
                atom_text="Ce",
                offset_along=25.0,
                offset_perpendicular=-15.0  # 向右偏移，使化学键向右偏转约30度
            )

            filled_path = filled_dir / f"{image_file.stem}_filled.png"
            cv2.imwrite(str(filled_path), filled_image)
            logger.info(f"  ✅ Ce填充已保存")

            # ==================== 提取原始结构 ====================
            structures = yolo_processor.extract_structures(
                image_path=str(image_file),
                conf=conf,
                padding=10
            )

            # 保存提取的结构
            for j, struct in enumerate(structures):
                struct_path = original_dir / f"{image_file.stem}_struct_{j+1}.png"
                struct['image_pil'].save(str(struct_path))

            logger.info(f"  ✅ 提取结构已保存: {len(structures)} 个")

            # ==================== 记录结果 ====================
            best_detection = max(detections, key=lambda d: d['confidence'])

            results.append({
                'filename': image_file.name,
                'status': 'success',
                'detections': len(detections),
                'confidence': best_detection['confidence'],
                'image_size': f"{image.shape[1]}x{image.shape[0]}",
                'detection_path': str(detection_path),
                'filled_path': str(filled_path),
                'structures_extracted': len(structures)
            })

            stats['success'] += 1
            stats['processed'] += 1

        except Exception as e:
            logger.error(f"  ❌ 处理失败: {e}")
            stats['failed'] += 1
            stats['processed'] += 1

            results.append({
                'filename': image_file.name,
                'status': 'failed',
                'detections': 0,
                'confidence': None,
                'image_size': 'N/A',
                'error': str(e)
            })

    # ==================== 生成处理报告 ====================
    logger.info("\n【步骤3】生成处理报告...")

    # Excel报告
    excel_path = output_dir / "batch_processing_report.xlsx"
    df = pd.DataFrame(results)
    df.to_excel(str(excel_path), index=False)
    logger.info(f"✅ Excel报告已保存: {excel_path}")

    # 文本摘要
    summary_path = output_dir / "processing_summary.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("YOLO批量处理报告\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"输入目录: {input_dir}\n")
        f.write(f"输出目录: {output_dir}\n")
        f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("统计信息:\n")
        f.write(f"  - 图片总数: {stats['total']}\n")
        f.write(f"  - 已处理: {stats['processed']}\n")
        f.write(f"  - 成功: {stats['success']}\n")
        f.write(f"  - 失败: {stats['failed']}\n")
        f.write(f"  - 未检测到结构: {stats['no_detection']}\n\n")
        f.write(f"成功率: {stats['success']/stats['total']*100:.1f}%\n\n")
        f.write("输出目录结构:\n")
        f.write(f"  - detection_results/  ({len([f for f in results if f['status']=='success'])} 张检测可视化)\n")
        f.write(f"  - filled_results/      ({len([f for f in results if f['status']=='success'])} 张Ce填充结果) ⭐ 最终结果\n")
        f.write(f"  - original_structures/ (提取的原始结构图)\n")
        f.write(f"  - batch_processing_report.xlsx (详细报告)\n")

    logger.info(f"✅ 文本摘要已保存: {summary_path}")

    # ==================== 打印总结 ====================
    logger.info("\n" + "=" * 80)
    logger.info("批量处理完成")
    logger.info("=" * 80)
    logger.info(f"图片总数: {stats['total']}")
    logger.info(f"处理成功: {stats['success']}")
    logger.info(f"处理失败: {stats['failed']}")
    logger.info(f"未检测到结构: {stats['no_detection']}")
    logger.info(f"成功率: {stats['success']/stats['total']*100:.1f}%")
    logger.info(f"\n输出目录: {output_dir}")
    logger.info(f"  - detection_results/ (检测可视化)")
    logger.info(f"  - filled_results/ ⭐ (Ce填充结果 - 最终结果)")
    logger.info(f"  - original_structures/ (原始结构)")
    logger.info(f"  - batch_processing_report.xlsx (详细报告)")
    logger.info(f"  - processing_summary.txt (文本摘要)")

    return {
        'stats': stats,
        'results': results,
        'output_dir': str(output_dir),
        'excel_path': str(excel_path)
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='YOLO批量处理脚本 - 批量处理图片生成Ce填充结果',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 基本用法（默认不扩展）
  python batch_yolo_test.py --input "D:\\skills\\测试文件\\测试图片"

  # 指定扩展比例（扩展5%）
  python batch_yolo_test.py --input "D:\\skills\\测试文件\\测试图片" --expansion 1.05

  # 指定输出目录和置信度
  python batch_yolo_test.py --input "D:\\skills\\测试文件\\测试图片" --output "D:\\output" --conf 0.30
        '''
    )

    parser.add_argument('--input', type=str, required=True, help='输入图片目录路径')
    parser.add_argument('--output', type=str, help='输出目录路径（可选）')
    parser.add_argument('--expansion', type=float, default=1.00, help='检测框扩展比例（默认1.00，不扩展）')
    parser.add_argument('--conf', type=float, default=0.25, help='YOLO检测置信度阈值（默认0.25）')

    args = parser.parse_args()

    # 执行批量处理
    result = batch_process_images(
        input_dir=args.input,
        output_dir=args.output,
        expansion_factor=args.expansion,
        conf=args.conf
    )

    if result and result['stats']['success'] > 0:
        logger.info(f"\n✅ 批量处理成功！共处理 {result['stats']['success']} 张图片")
        logger.info(f"查看结果: {result['output_dir']}")
    else:
        logger.info("\n❌ 批量处理失败或未检测到任何结构")


if __name__ == "__main__":
    main()