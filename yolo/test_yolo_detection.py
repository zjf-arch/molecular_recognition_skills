#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO模型测试脚本
测试化学结构检测功能
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "yolo"))

from yolo_processor import YOLOProcessor
from scripts.logger import logger

def test_yolo_detection():
    """测试YOLO检测功能"""

    # 测试图片路径
    test_image = r"D:\skills\测试文件\[信越]_CN113045465B_Onium salt compound, chemically amplified resist composition, and pattern …_structure_441.png"

    if not Path(test_image).exists():
        logger.error(f"测试图片不存在: {test_image}")
        return False

    logger.info("=" * 80)
    logger.info("YOLO模型测试")
    logger.info("=" * 80)
    logger.info(f"测试图片: {Path(test_image).name}")

    # 输出目录
    output_dir = PROJECT_ROOT / "yolo" / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ==================== 加载YOLO模型 ====================
    logger.info("\n【步骤1】加载YOLO模型...")

    try:
        # 优先使用训练好的化学结构检测模型
        trained_model = PROJECT_ROOT / "yolo" / "detect" / "runs" / "obb" / "train6" / "weights" / "best.pt"
        pretrained_model = PROJECT_ROOT / "yolo" / "detect" / "yolo11n-obb.pt"

        model_path = None
        model_type = None

        if trained_model.exists():
            model_path = trained_model
            model_type = "训练好的化学结构检测模型"
            logger.info(f"✅ 使用训练好的模型: {trained_model.name}")
        elif pretrained_model.exists():
            model_path = pretrained_model
            model_type = "预训练通用模型"
            logger.info(f"✅ 使用预训练模型: {pretrained_model.name}")
        else:
            logger.error("未找到任何YOLO模型")
            logger.info(f"期望路径:")
            logger.info(f"  - 训练模型: {trained_model}")
            logger.info(f"  - 预训练模型: {pretrained_model}")
            return False

        logger.info(f"模型类型: {model_type}")

        # 创建YOLO处理器
        yolo_processor = YOLOProcessor(
            model_path=str(model_path),
            use_smart_placement=False  # 测试时先不使用智能放置
        )
        logger.info("✅ YOLO处理器加载成功")

    except Exception as e:
        logger.error(f"YOLO模型加载失败: {e}")
        return False

    # ==================== 检测化学结构 ====================
    logger.info("\n【步骤2】检测化学结构...")

    try:
        # 读取图片
        image = cv2.imread(test_image)
        if image is None:
            logger.error(f"图片读取失败: {test_image}")
            return False

        logger.info(f"图片尺寸: {image.shape[1]}x{image.shape[0]}")

        # 执行检测
        detections = yolo_processor.detect_structures(
            image_path=test_image,
            conf=0.25,  # 置信度阈值
            iou=0.5,    # IoU阈值
            imgsz=512   # 输入尺寸
        )

        logger.info(f"✅ 检测完成: 发现 {len(detections)} 个结构")

        # 显示检测结果
        for i, det in enumerate(detections):
            logger.info(f"\n  结构 {i+1}:")
            logger.info(f"    置信度: {det['confidence']:.3f}")
            logger.info(f"    边界框: {det['xyxy']}")

            if det.get('xyxyxyxy'):
                logger.info(f"    旋转框: {det['xyxyxyxy']}")

            if det.get('xywhr'):
                logger.info(f"    旋转角度: {det['xywhr'][4]:.2f} rad")

    except Exception as e:
        logger.error(f"检测失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ==================== 可视化检测结果 ====================
    logger.info("\n【步骤3】可视化检测结果...")

    try:
        # 读取原始图片
        vis_image = cv2.imread(test_image)

        # 绘制检测框
        for i, det in enumerate(detections):
            # 绘制边界框
            x1, y1, x2, y2 = det['xyxy']
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # 绿色矩形框
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 标注置信度
            label = f"Struct {i+1}: {det['confidence']:.2f}"
            cv2.putText(vis_image, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # 绘制旋转框（如果有）
            if det.get('xyxyxyxy'):
                points = np.array(det['xyxyxyxy'], dtype=np.int32)
                # 红色旋转框
                cv2.polylines(vis_image, [points], True, (0, 0, 255), 2)

        # 保存可视化结果
        output_path = output_dir / "detection_result.png"
        cv2.imwrite(str(output_path), vis_image)
        logger.info(f"✅ 可视化结果已保存: {output_path}")

    except Exception as e:
        logger.error(f"可视化失败: {e}")
        return False

    # ==================== 用Ce填充检测区域 ====================
    logger.info("\n【步骤4】用Ce元素填充检测区域...")

    try:
        # 扩展检测框边界（让框框变大）
        expansion_factor = 1.00  # 不扩展（可根据需要调整）
        logger.info(f"检测框扩展比例: {expansion_factor*100:.0f}%")

        expanded_detections = []
        for det in detections:
            # 复制检测结果
            expanded_det = det.copy()
            # 不扩展，直接使用原始检测框

            expanded_detections.append(expanded_det)

        # 使用智能Ce放置算法填充扩展后的检测区域
        yolo_processor.use_smart_placement = True  # 启用智能放置
        filled_image = yolo_processor.fill_structures_with_ce(
            image=image,
            detections=expanded_detections,  # 使用扩展后的检测框
            atom_text="Ce",
            offset_along=25.0,         # Ce标记沿切线方向的偏移
            offset_perpendicular=-15.0  # 向右偏移，使化学键向右偏转约30度
        )

        # 保存填充后的图片
        filled_path = output_dir / "filled_with_ce.png"
        cv2.imwrite(str(filled_path), filled_image)
        logger.info(f"✅ Ce填充结果已保存: {filled_path}")

    except Exception as e:
        logger.error(f"Ce填充失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # ==================== 提取化学结构（可选） ====================
    logger.info("\n【步骤5】提取化学结构（可选）...")

    try:
        structures = yolo_processor.extract_structures(
            image_path=test_image,
            conf=0.25,
            padding=10
        )

        logger.info(f"✅ 提取完成: {len(structures)} 个结构")

        # 保存提取的结构
        for i, struct in enumerate(structures):
            struct_path = output_dir / f"structure_{i+1}.png"
            struct['image_pil'].save(str(struct_path))
            logger.info(f"  结构 {i+1}: {struct['width']}x{struct['height']} -> {struct_path}")

    except Exception as e:
        logger.error(f"结构提取失败: {e}")
        return False

    # ==================== 总结 ====================
    logger.info("\n" + "=" * 80)
    logger.info("测试完成")
    logger.info("=" * 80)
    logger.info(f"检测结构数: {len(detections)}")
    logger.info(f"提取结构数: {len(structures)}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"\n输出文件:")
    logger.info(f"  1. detection_result.png (可视化检测结果)")
    logger.info(f"  2. filled_with_ce.png ⭐ (Ce填充后的图片 - 最终结果)")
    for i in range(len(structures)):
        logger.info(f"  3. structure_{i+1}.png (提取的原始结构)")

    logger.info(f"\n💡 最终结果: filled_with_ce.png")
    logger.info(f"   - 检测到的化学结构区域用白色填充")
    logger.info(f"   - 用Ce元素标记替换原有结构")
    logger.info(f"   - 保留原图其他部分不变")

    return True


if __name__ == "__main__":
    success = test_yolo_detection()

    if success:
        logger.info("\n✅ YOLO测试成功！")
    else:
        logger.info("\n❌ YOLO测试失败！")