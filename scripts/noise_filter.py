"""
分子结构图像噪声过滤工具
使用预训练分类器过滤非分子结构图像
"""

import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
from pathlib import Path
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MoleculeImageFilter:
    """分子结构图像过滤器"""

    def __init__(self, model_path: str = "D:/skills/噪声去除文件/mole_classifier.pth"):
        """
        初始化过滤器

        Args:
            model_path: 分类器模型路径
        """
        self.model_path = Path(model_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 图像预处理
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])

        # 类别映射
        self.class_names = ['noise', 'polymer', 'small molecule']

        # 加载模型
        self.model = self._load_model()

    def _load_model(self):
        """加载预训练模型"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")

        logger.info(f"加载模型: {self.model_path}")

        # 加载模型（假设是ResNet或其他分类网络）
        model = torch.load(self.model_path, map_location=self.device)
        model.eval()

        logger.info("模型加载成功")
        return model

    def predict_image(self, image_path: str) -> Tuple[str, float]:
        """
        预测单张图像的类别

        Args:
            image_path: 图像路径

        Returns:
            (类别名称, 置信度)
        """
        try:
            # 加载和预处理图像
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)

            # 预测
            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                confidence, predicted_idx = torch.max(probabilities, 0)

                predicted_class = self.class_names[predicted_idx.item()]
                confidence_score = confidence.item()

            return predicted_class, confidence_score

        except Exception as e:
            logger.error(f"预测失败 {image_path}: {e}")
            return 'noise', 0.0  # 出错时默认为噪声

    def filter_images(
        self,
        image_paths: List[str],
        keep_classes: List[str] = ['polymer', 'small molecule'],
        confidence_threshold: float = 0.5
    ) -> List[str]:
        """
        过滤图像，只保留指定类别的图像

        Args:
            image_paths: 图像路径列表
            keep_classes: 保留的类别列表
            confidence_threshold: 置信度阈值

        Returns:
            过滤后的图像路径列表
        """
        logger.info(f"开始过滤 {len(image_paths)} 张图像...")
        logger.info(f"保留类别: {keep_classes}")
        logger.info(f"置信度阈值: {confidence_threshold}")

        filtered_paths = []
        stats = {class_name: 0 for class_name in self.class_names}

        for img_path in image_paths:
            predicted_class, confidence = self.predict_image(img_path)

            stats[predicted_class] += 1

            # 检查是否保留
            if predicted_class in keep_classes and confidence >= confidence_threshold:
                filtered_paths.append(img_path)
                logger.debug(f"保留: {Path(img_path).name} ({predicted_class}, {confidence:.2f})")
            else:
                logger.debug(f"过滤: {Path(img_path).name} ({predicted_class}, {confidence:.2f})")

        # 输出统计
        logger.info("\n分类统计:")
        for class_name, count in stats.items():
            percentage = count / len(image_paths) * 100 if image_paths else 0
            logger.info(f"  {class_name}: {count} ({percentage:.1f}%)")

        logger.info(f"\n过滤结果:")
        logger.info(f"  原始图像: {len(image_paths)}")
        logger.info(f"  保留图像: {len(filtered_paths)}")
        logger.info(f"  过滤图像: {len(image_paths) - len(filtered_paths)}")

        return filtered_paths


def main():
    """测试噪声过滤功能"""
    import argparse

    parser = argparse.ArgumentParser(description='分子结构图像噪声过滤')
    parser.add_argument('input_dir', help='输入图像目录')
    parser.add_argument('--model', default='D:/skills/噪声去除文件/mole_classifier.pth',
                        help='模型路径')
    parser.add_argument('--output', help='输出文件列表（可选）')

    args = parser.parse_args()

    # 收集所有图像
    input_dir = Path(args.input_dir)
    image_paths = list(input_dir.glob('*.png')) + list(input_dir.glob('*.jpg'))

    print(f"\n找到 {len(image_paths)} 张图像")

    # 初始化过滤器
    filter = MoleculeImageFilter(args.model)

    # 过滤图像
    filtered_paths = filter.filter_images(image_paths)

    # 输出结果
    if args.output:
        with open(args.output, 'w') as f:
            for path in filtered_paths:
                f.write(f"{path}\n")
        print(f"\n已保存过滤结果到: {args.output}")

    print(f"\n✓ 过滤完成！保留 {len(filtered_paths)}/{len(image_paths)} 张图像")


if __name__ == "__main__":
    main()