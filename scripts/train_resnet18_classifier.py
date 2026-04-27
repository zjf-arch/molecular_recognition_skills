#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ResNet18分子图像分类训练脚本
训练三分类模型：小分子、聚合物、废弃
"""

import sys
import os
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models
import time
import json
from datetime import datetime

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.logger import logger


class MoleculeClassifier:
    """分子图像分类器"""

    def __init__(self, data_dir: str, model_save_dir: str):
        """
        初始化分类器

        Args:
            data_dir: 训练数据目录（包含小分子、聚合物、废弃三个子文件夹）
            model_save_dir: 模型保存目录
        """
        self.data_dir = Path(data_dir)
        self.model_save_dir = Path(model_save_dir)
        self.model_save_dir.mkdir(parents=True, exist_ok=True)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"使用设备: {self.device}")

        # 数据预处理
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),           # ResNet18标准输入
            transforms.RandomHorizontalFlip(),        # 数据增强：水平翻转
            transforms.RandomRotation(10),            # 数据增强：旋转±10度
            transforms.ColorJitter(brightness=0.2, contrast=0.2),  # 数据增强：亮度对比度
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],           # ImageNet标准化
                std=[0.229, 0.224, 0.225]
            )
        ])

        self.val_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def prepare_data(self, train_ratio=0.8, batch_size=32):
        """
        准备训练数据

        Args:
            train_ratio: 训练集比例（默认80%）
            batch_size: 批大小

        Returns:
            train_loader, val_loader, class_names
        """
        logger.info("=" * 80)
        logger.info("准备训练数据")
        logger.info("=" * 80)

        # 加载完整数据集
        full_dataset = datasets.ImageFolder(
            root=str(self.data_dir),
            transform=self.transform
        )

        class_names = full_dataset.classes
        logger.info(f"类别: {class_names}")
        logger.info(f"类别索引: {full_dataset.class_to_idx}")

        # 统计每个类别的样本数
        class_counts = {}
        for _, label in full_dataset.samples:
            class_name = class_names[label]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        logger.info("\n各类别样本数:")
        for class_name, count in class_counts.items():
            logger.info(f"  {class_name}: {count}张")

        # 划分训练集和验证集
        total_size = len(full_dataset)
        train_size = int(train_ratio * total_size)
        val_size = total_size - train_size

        logger.info(f"\n划分数据集:")
        logger.info(f"  总样本数: {total_size}")
        logger.info(f"  训练集: {train_size}张 ({train_ratio*100:.0f}%)")
        logger.info(f"  验证集: {val_size}张 ({(1-train_ratio)*100:.0f}%)")

        train_dataset, val_dataset = random_split(
            full_dataset,
            [train_size, val_size],
            generator=torch.Generator().manual_seed(42)  # 固定随机种子
        )

        # 验证集使用不同的transform（不增强）
        val_dataset.dataset.transform = self.val_transform

        # 创建数据加载器
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True if torch.cuda.is_available() else False
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=4,
            pin_memory=True if torch.cuda.is_available() else False
        )

        logger.info(f"✅ 数据准备完成")

        return train_loader, val_loader, class_names, class_counts

    def build_model(self, num_classes=3, pretrained=True):
        """
        构建ResNet18模型

        Args:
            num_classes: 分类数量（默认3类）
            pretrained: 是否使用预训练权重

        Returns:
            model
        """
        logger.info("=" * 80)
        logger.info("构建ResNet18模型")
        logger.info("=" * 80)

        # 加载ResNet18
        if pretrained:
            model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
            logger.info("✅ 使用ImageNet预训练权重")
        else:
            model = models.resnet18(weights=None)
            logger.info("⚠️ 不使用预训练权重")

        # 修改最后一层（全连接层）
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, num_classes)

        logger.info(f"修改输出层: {num_features} -> {num_classes}")
        logger.info(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")

        # 移动到设备
        model = model.to(self.device)

        logger.info(f"✅ 模型构建完成")

        return model

    def train_model(
        self,
        model,
        train_loader,
        val_loader,
        num_epochs=20,
        learning_rate=0.001,
        save_best=True
    ):
        """
        训练模型

        Args:
            model: 模型
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            num_epochs: 训练轮数
            learning_rate: 学习率
            save_best: 是否保存最佳模型

        Returns:
            training_history
        """
        logger.info("=" * 80)
        logger.info("开始训练")
        logger.info("=" * 80)
        logger.info(f"训练参数:")
        logger.info(f"  训练轮数: {num_epochs}")
        logger.info(f"  学习率: {learning_rate}")
        logger.info(f"  设备: {self.device}")

        # 定义损失函数和优化器
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        # 学习率衰减
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)

        # 训练历史
        history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
            'learning_rates': []
        }

        best_val_acc = 0.0
        best_epoch = 0

        start_time = time.time()

        for epoch in range(num_epochs):
            logger.info(f"\n{'='*60}")
            logger.info(f"Epoch {epoch+1}/{num_epochs}")
            logger.info(f"{'='*60}")

            # 训练阶段
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            for batch_idx, (images, labels) in enumerate(train_loader):
                images = images.to(self.device)
                labels = labels.to(self.device)

                # 前向传播
                outputs = model(images)
                loss = criterion(outputs, labels)

                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                # 统计
                train_loss += loss.item()
                _, predicted = outputs.max(1)
                train_total += labels.size(0)
                train_correct += predicted.eq(labels).sum().item()

                # 打印进度
                if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == len(train_loader):
                    logger.info(
                        f"  Batch [{batch_idx+1}/{len(train_loader)}] "
                        f"Loss: {loss.item():.4f} "
                        f"Acc: {100.*train_correct/train_total:.2f}%"
                    )

            train_loss = train_loss / len(train_loader)
            train_acc = 100. * train_correct / train_total

            # 验证阶段
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for images, labels in val_loader:
                    images = images.to(self.device)
                    labels = labels.to(self.device)

                    outputs = model(images)
                    loss = criterion(outputs, labels)

                    val_loss += loss.item()
                    _, predicted = outputs.max(1)
                    val_total += labels.size(0)
                    val_correct += predicted.eq(labels).sum().item()

            val_loss = val_loss / len(val_loader)
            val_acc = 100. * val_correct / val_total

            # 更新学习率
            scheduler.step()
            current_lr = optimizer.param_groups[0]['lr']

            # 记录历史
            history['train_loss'].append(train_loss)
            history['train_acc'].append(train_acc)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)
            history['learning_rates'].append(current_lr)

            logger.info(f"\nEpoch {epoch+1} 结果:")
            logger.info(f"  训练 - Loss: {train_loss:.4f}, Acc: {train_acc:.2f}%")
            logger.info(f"  验证 - Loss: {val_loss:.4f}, Acc: {val_acc:.2f}%")
            logger.info(f"  学习率: {current_lr:.6f}")

            # 保存最佳模型
            if save_best and val_acc > best_val_acc:
                best_val_acc = val_acc
                best_epoch = epoch + 1

                best_model_path = self.model_save_dir / "best_model.pth"
                torch.save({
                    'epoch': epoch + 1,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_acc': val_acc,
                    'val_loss': val_loss,
                }, best_model_path)

                logger.info(f"  ✅ 保��最佳模型 (Epoch {best_epoch}, Acc {best_val_acc:.2f}%)")

        # 训练完成
        elapsed_time = time.time() - start_time
        logger.info(f"\n{'='*80}")
        logger.info("训练完成")
        logger.info(f"{'='*80}")
        logger.info(f"总耗时: {elapsed_time:.2f}秒")
        logger.info(f"最佳验证准确率: {best_val_acc:.2f}% (Epoch {best_epoch})")

        # 保存最终模型
        final_model_path = self.model_save_dir / "final_model.pth"
        torch.save({
            'epoch': num_epochs,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_acc': val_acc,
            'val_loss': val_loss,
        }, final_model_path)

        logger.info(f"✅ 最终模型已保存: {final_model_path}")

        # 保存训练历史
        history_path = self.model_save_dir / "training_history.json"
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ 训练历史已保存: {history_path}")

        return history

    def evaluate_model(self, model, val_loader, class_names):
        """
        评估模型性能

        Args:
            model: 模型
            val_loader: 验证数据加载器
            class_names: 类别名称
        """
        logger.info("=" * 80)
        logger.info("模型评估")
        logger.info("=" * 80)

        model.eval()

        # 统计每个类别的准确率
        class_correct = [0] * len(class_names)
        class_total = [0] * len(class_names)

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(self.device)
                labels = labels.to(self.device)

                outputs = model(images)
                _, predicted = outputs.max(1)

                for i in range(len(labels)):
                    label = labels[i]
                    pred = predicted[i]
                    class_total[label] += 1
                    if pred == label:
                        class_correct[label] += 1

        logger.info("\n各类别准确率:")
        for i, class_name in enumerate(class_names):
            acc = 100. * class_correct[i] / class_total[i] if class_total[i] > 0 else 0
            logger.info(f"  {class_name}: {acc:.2f}% ({class_correct[i]}/{class_total[i]})")

        logger.info(f"\n总体准确率: {100.*sum(class_correct)/sum(class_total):.2f}%")

    def predict_test_set(self, test_dir: str, model_path: str, output_csv: str):
        """
        对测试集进行预测

        Args:
            test_dir: 测试集目录
            model_path: 模型文件路径
            output_csv: 输出CSV文件路径
        """
        logger.info("=" * 80)
        logger.info("测试集预测")
        logger.info("=" * 80)

        test_dir = Path(test_dir)

        if not test_dir.exists():
            logger.error(f"测试集目录不存在: {test_dir}")
            return

        # 加载模型
        checkpoint = torch.load(model_path, map_location=self.device)
        model = self.build_model(num_classes=3, pretrained=False)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()

        logger.info(f"✅ 加载模型: {model_path}")
        logger.info(f"   验证准确率: {checkpoint['val_acc']:.2f}%")

        # 获取所有测试图片
        image_files = list(test_dir.glob("*.png")) + \
                     list(test_dir.glob("*.jpg")) + \
                     list(test_dir.glob("*.jpeg"))

        logger.info(f"\n测试集图片数: {len(image_files)}")

        if len(image_files) == 0:
            logger.warning("没有找到测试图片")
            return

        # 预测
        predictions = []

        logger.info("\n开始预测...")
        start_time = time.time()

        for i, image_file in enumerate(image_files, 1):
            if i % 100 == 0 or i == len(image_files):
                logger.info(f"  处理进度: {i}/{len(image_files)}")

            try:
                # 加载图片
                from PIL import Image
                image = Image.open(image_file).convert('RGB')
                image = self.val_transform(image)
                image = image.unsqueeze(0).to(self.device)

                # 预测
                with torch.no_grad():
                    outputs = model(image)
                    probs = torch.nn.functional.softmax(outputs, dim=1)
                    _, predicted = outputs.max(1)

                    pred_class = predicted.item()
                    confidence = probs[0][pred_class].item()

                predictions.append({
                    'filename': image_file.name,
                    'filepath': str(image_file),
                    'predicted_class': ['小分子', '废弃', '聚合物'][pred_class],  # 正确的class_to_idx顺序
                    'confidence': confidence,
                    'probabilities': {
                        '小分子': probs[0][0].item(),
                        '废弃': probs[0][1].item(),
                        '聚合物': probs[0][2].item()
                    }
                })

            except Exception as e:
                logger.warning(f"处理失败 {image_file.name}: {e}")
                predictions.append({
                    'filename': image_file.name,
                    'filepath': str(image_file),
                    'predicted_class': 'ERROR',
                    'confidence': 0.0,
                    'error': str(e)
                })

        elapsed_time = time.time() - start_time
        logger.info(f"\n✅ 预测完成")
        logger.info(f"   耗时: {elapsed_time:.2f}秒")
        logger.info(f"   平均速度: {elapsed_time*1000/len(image_files):.1f}ms/张")

        # 统计预测结果
        logger.info("\n预测统计:")
        class_counts = {}
        for pred in predictions:
            class_name = pred['predicted_class']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        for class_name, count in class_counts.items():
            logger.info(f"  {class_name}: {count}张 ({100.*count/len(predictions):.2f}%)")

        # 保存结果到CSV
        import pandas as pd

        df = pd.DataFrame(predictions)
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')

        logger.info(f"\n✅ 结果已保存: {output_csv}")

        # 移动图片到对应文件夹（可选）
        logger.info("\n是否将图片移动到对应类别文件夹？")
        output_class_dir = test_dir.parent / "测试集_分类结果"
        output_class_dir.mkdir(exist_ok=True)

        for class_name in ['小分子', '聚合物', '废弃']:
            class_dir = output_class_dir / class_name
            class_dir.mkdir(exist_ok=True)

        import shutil

        moved_count = 0
        for pred in predictions:
            if pred['predicted_class'] != 'ERROR':
                src = Path(pred['filepath'])
                dst = output_class_dir / pred['predicted_class'] / src.name
                shutil.copy2(src, dst)  # 复制而不是移动，保留原文件
                moved_count += 1

        logger.info(f"✅ 已复制 {moved_count} 张图片到分类文件夹: {output_class_dir}")

        return predictions


def main():
    """主训练流程"""

    logger.info("=" * 80)
    logger.info("ResNet18分子图像分类训练")
    logger.info("=" * 80)

    # 数据目录 - 只使用三个训练文件夹
    data_dir = PROJECT_ROOT / "训练集"

    # 创建临时训练目录（只包含小分子、聚合物、废弃）
    temp_train_dir = PROJECT_ROOT / "temp_train_data"
    temp_train_dir.mkdir(exist_ok=True)

    import shutil
    for class_name in ['小分子', '聚合物', '废弃']:
        src_dir = data_dir / class_name
        dst_dir = temp_train_dir / class_name
        if src_dir.exists():
            if not dst_dir.exists():
                shutil.copytree(src_dir, dst_dir)
                logger.info(f"复制训练数据: {class_name} -> {dst_dir}")

    model_save_dir = PROJECT_ROOT / "models" / "resnet18_classifier"

    # 测试集目录
    test_dir = data_dir / "测试集"

    # 创建分类器
    classifier = MoleculeClassifier(
        data_dir=str(temp_train_dir),
        model_save_dir=str(model_save_dir)
    )

    # 1. 准备数据
    train_loader, val_loader, class_names, class_counts = classifier.prepare_data(
        train_ratio=0.8,
        batch_size=32
    )

    # 2. 构建模型
    model = classifier.build_model(num_classes=3, pretrained=True)

    # 3. 训练模型
    history = classifier.train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=20,
        learning_rate=0.001,
        save_best=True
    )

    # 4. 评估模型
    classifier.evaluate_model(model, val_loader, class_names)

    # 5. 预测测试集（如果有）
    if test_dir.exists():
        logger.info("\n" + "=" * 80)
        logger.info("预测测试集")
        logger.info("=" * 80)

        best_model_path = model_save_dir / "best_model.pth"
        output_csv = model_save_dir / "test_predictions.csv"

        predictions = classifier.predict_test_set(
            test_dir=str(test_dir),
            model_path=str(best_model_path),
            output_csv=str(output_csv)
        )

    logger.info("\n✅ 所有任务完成")


if __name__ == "__main__":
    main()