#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分子图像分类器模块
使用训练好的ResNet18模型自动分类分子图像
"""

import sys
from pathlib import Path
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.logger import logger


class MoleculeImageClassifier:
    """分子图像分类器（使用训练好的ResNet18）"""

    def __init__(self, model_path: str = None):
        """
        初始化分类器

        Args:
            model_path: 模型文件路径，默认使用训练好的最佳模型
        """
        if model_path is None:
            model_path = PROJECT_ROOT / "models" / "resnet18_classifier" / "best_model.pth"

        self.model_path = Path(model_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 类别名称（按训练时的顺序）
        self.class_names = ['小分子', '废弃', '聚合物']

        # 图像预处理
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        # 加载模型
        self.model = self._load_model()

    def _load_model(self) -> nn.Module:
        """加载训练好的模型"""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"模型文件不存在: {self.model_path}\n"
                "请先运行训练脚本: python scripts/train_resnet18_classifier.py"
            )

        # 构建ResNet18模型
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(512, 3)  # 3个类别

        # 加载训练好的权重
        checkpoint = torch.load(self.model_path, map_location=self.device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        model.eval()

        logger.info(f"✅ 加载分类模型: {self.model_path}")
        logger.info(f"   验证准确率: {checkpoint['val_acc']:.2f}%")

        return model

    def classify_image(self, image_path: str) -> Dict:
        """
        分类单张图片

        Args:
            image_path: 图片路径

        Returns:
            {
                'class': 类别名称,
                'confidence': 置信���,
                'probabilities': 各类别概率
            }
        """
        try:
            # 加载图片
            image = Image.open(image_path).convert('RGB')
            image = self.transform(image).unsqueeze(0).to(self.device)

            # 预测
            with torch.no_grad():
                outputs = self.model(image)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                _, predicted = outputs.max(1)

                pred_class_idx = predicted.item()
                confidence = probs[0][pred_class_idx].item()

            return {
                'class': self.class_names[pred_class_idx],
                'confidence': confidence,
                'probabilities': {
                    self.class_names[i]: probs[0][i].item()
                    for i in range(len(self.class_names))
                }
            }

        except Exception as e:
            logger.warning(f"分类失败 {image_path}: {e}")
            return {
                'class': 'ERROR',
                'confidence': 0.0,
                'error': str(e)
            }

    def classify_batch(
        self,
        image_paths: List[str],
        keep_classes: List[str] = ['小分子', '聚合物'],
        confidence_threshold: float = 0.5
    ) -> Tuple[List[str], List[Dict]]:
        """
        批量分类并过滤图片

        Args:
            image_paths: 图片路径列表
            keep_classes: 保留的类别（默认只保留小分子和聚合物）
            confidence_threshold: 置信度阈值

        Returns:
            (过滤后的图片路径列表, 分类结果列表)
        """
        logger.info(f"开始分类 {len(image_paths)} 张图片...")
        logger.info(f"保留类别: {keep_classes}")
        logger.info(f"置信度阈值: {confidence_threshold}")

        filtered_paths = []
        results = []

        class_counts = {name: 0 for name in self.class_names}
        class_counts['ERROR'] = 0

        for i, image_path in enumerate(image_paths, 1):
            if i % 100 == 0 or i == len(image_paths):
                logger.info(f"  处理进度: {i}/{len(image_paths)}")

            result = self.classify_image(image_path)
            results.append(result)

            pred_class = result['class']
            class_counts[pred_class] += 1

            # 过滤逻辑
            if pred_class in keep_classes and result['confidence'] >= confidence_threshold:
                filtered_paths.append(image_path)

        # 统计结果
        logger.info(f"\n分类统计:")
        for class_name, count in class_counts.items():
            if count > 0:
                logger.info(f"  {class_name}: {count}张 ({100.*count/len(image_paths):.2f}%)")

        filter_rate = 1.0 - len(filtered_paths) / len(image_paths)
        logger.info(f"\n过滤结果:")
        logger.info(f"  原始图片: {len(image_paths)}张")
        logger.info(f"  保留图片: {len(filtered_paths)}张")
        logger.info(f"  过滤率: {filter_rate:.2%}")
        logger.info(f"  预计节省API调用: {filter_rate:.2%}")

        return filtered_paths, results

    def filter_images(
        self,
        image_paths: List[str],
        keep_classes: List[str] = ['小分子', '聚合物'],
        confidence_threshold: float = 0.5
    ) -> List[str]:
        """
        过滤图片（只返回过滤后的路径，不返回详细信息）

        Args:
            image_paths: 图片路径列表
            keep_classes: 保留的类别
            confidence_threshold: 置信度阈值

        Returns:
            过滤后的图片路径列表
        """
        filtered_paths, _ = self.classify_batch(
            image_paths,
            keep_classes,
            confidence_threshold
        )
        return filtered_paths


def test_classifier():
    """测试分类器"""

    logger.info("=" * 80)
    logger.info("分子图像分类器测试")
    logger.info("=" * 80)

    # 创建分类器
    classifier = MoleculeImageClassifier()

    # 测试图片
    test_images_dir = PROJECT_ROOT / "训练集" / "测试集_分类结果_修正"

    if not test_images_dir.exists():
        logger.warning(f"测试目录不存在: {test_images_dir}")
        return

    # 测试每个类别
    for class_name in ['小分子', '废弃', '聚合物']:
        class_dir = test_images_dir / class_name
        if not class_dir.exists():
            continue

        image_files = list(class_dir.glob("*.png"))[:5]  # 每个类别测试5张

        logger.info(f"\n测试类别: {class_name}")
        correct = 0

        for image_file in image_files:
            result = classifier.classify_image(str(image_file))
            is_correct = result['class'] == class_name

            if is_correct:
                correct += 1
                logger.info(f"  ✅ {image_file.name}: {result['class']} ({result['confidence']:.2%})")
            else:
                logger.warning(f"  ❌ {image_file.name}: 预测={result['class']}, 实际={class_name} ({result['confidence']:.2%})")

        accuracy = correct / len(image_files) if image_files else 0
        logger.info(f"  准确率: {accuracy:.2%} ({correct}/{len(image_files)})")

    logger.info("\n✅ 测试完成")


if __name__ == "__main__":
    test_classifier()