#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO化学结构检测处理器
使用YOLOv11模型检测和提取化学结构
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ Ultralytics YOLO not available. YOLO processing disabled.")


class YOLOProcessor:
    """YOLO化学结构检测处理器"""

    def __init__(self, model_path: str = None, use_smart_placement: bool = True):
        """
        初始化YOLO处理器

        Args:
            model_path: YOLO模型路径，默认使用detect/yolo11n-obb.pt
            use_smart_placement: 是否使用智能Ce放置算法（来自fill.py）
        """
        if not YOLO_AVAILABLE:
            raise ImportError("Ultralytics YOLO is not installed. Please install it with: pip install ultralytics")

        self.use_smart_placement = use_smart_placement
        
        # 设置默认模型路径 - 使用训练好的化学结构检测模型
        if model_path is None:
            # 尝试多个可能的路径（优先使用训练好的模型）
            possible_paths = [
                "/root/net-disk/test1/长鑫1103/detect/runs/obb/train6/weights/best.pt",
                "/root/net-disk/test1/detect/runs/obb/train6/weights/best.pt",
                "detect/runs/obb/train6/weights/best.pt",
                "../detect/runs/obb/train6/weights/best.pt",
                # 备用：通用模型（不推荐用于化学结构检测）
                "/root/net-disk/test1/长鑫1103/detect/yolo11n-obb.pt",
                "/root/net-disk/test1/detect/yolo11n-obb.pt",
                "detect/yolo11n-obb.pt",
                "../detect/yolo11n-obb.pt"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path is None:
                raise FileNotFoundError(f"YOLO model not found in any of these paths: {possible_paths}")
        
        self.model_path = model_path
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """加载YOLO模型"""
        try:
            print(f"🔄 Loading YOLO model from: {self.model_path}")
            self.model = YOLO(self.model_path)
            print(f"✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            raise

    # ==================== 智能Ce放置算法（来自fill.py）====================

    @staticmethod
    def _poly_mask(h: int, w: int, pts_px: np.ndarray) -> np.ndarray:
        """创建多边形掩码"""
        m = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(m, [pts_px.astype(np.int32)], 255)
        return m

    @staticmethod
    def _nearest_edge_point_outside(gray: np.ndarray, poly_px: np.ndarray, ring: int = 60) -> Optional[np.ndarray]:
        """
        找到多边形外部最近的边缘点

        Args:
            gray: 灰度图像
            poly_px: 多边形顶点坐标 [N, 2]
            ring: 搜索环的半径

        Returns:
            最近的边缘点坐标 [x, y]，如果没找到返回None
        """
        h, w = gray.shape
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # 创建多边形内部掩码
        mask_in = YOLOProcessor._poly_mask(h, w, poly_px)

        # 移除多边形内部的边缘
        edges[mask_in == 255] = 0

        # 创建搜索环：多边形周围ring像素范围内
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*ring+1, 2*ring+1))
        near = cv2.dilate(mask_in, kernel)

        # 只保留搜索环内的边缘
        edges[near == 0] = 0

        # 找到所有边缘点
        ys, xs = np.where(edges > 0)
        if len(xs) == 0:
            return None

        # 计算多边形中心
        C = poly_px.mean(axis=0).astype(np.float32)

        # 找到距离中心最近的边缘点
        pts = np.stack([xs.astype(np.float32), ys.astype(np.float32)], axis=1)
        k = np.argmin(np.sum((pts - C[None, :])**2, axis=1))

        return pts[k]

    @staticmethod
    def _fit_tangent_at(gray: np.ndarray, P: np.ndarray, win: int = 27, min_pts: int = 8) -> Optional[np.ndarray]:
        """
        在给定点拟合切线方向

        Args:
            gray: 灰度图像
            P: 点坐标 [x, y]
            win: 窗口大小
            min_pts: 最小点数

        Returns:
            切线方向向量 [dx, dy]，如果失败返回None
        """
        h, w = gray.shape

        # 提取窗口
        x0 = max(0, int(P[0] - win//2))
        x1 = min(w, int(P[0] + win//2) + 1)
        y0 = max(0, int(P[1] - win//2))
        y1 = min(h, int(P[1] + win//2) + 1)

        roi = gray[y0:y1, x0:x1]

        # 边缘检测
        edges = cv2.Canny(roi, 40, 120, apertureSize=3)
        ys, xs = np.where(edges > 0)

        if len(xs) < min_pts:
            return None

        # PCA拟合主方向
        pts = np.stack([xs, ys], axis=1).astype(np.float32)
        mean = pts.mean(axis=0, keepdims=True)
        cov = np.cov((pts - mean).T)

        eigvals, eigvecs = np.linalg.eig(cov)
        t = eigvecs[:, np.argmax(eigvals)].astype(np.float32)
        t /= (np.linalg.norm(t) + 1e-12)

        return t

    @staticmethod
    def _choose_inside_end(poly_px: np.ndarray, P: np.ndarray, t: np.ndarray,
                          offset: float, min_offset: float = 2.0,
                          offset_perpendicular: float = 0.0) -> np.ndarray:
        """
        沿着切线方向选择多边形内部的端点，并支持垂直方向的偏移

        Args:
            poly_px: 多边形顶点坐标 [N, 2]
            P: 起始点 [x, y]
            t: 切线方向 [dx, dy]
            offset: 沿切线方向的偏移距离
            min_offset: 最小偏移距离
            offset_perpendicular: 垂直于切线方向的偏移距离（正值向左，负值向右）

        Returns:
            选择的端点坐标 [x, y]
        """
        poly = poly_px.reshape(-1, 1, 2).astype(np.float32)
        cur = float(offset)

        # 计算垂直于切线的方向向量（逆时针旋转90度）
        # t = [dx, dy] -> perpendicular = [-dy, dx]
        t_perp = np.array([-t[1], t[0]], dtype=np.float32)

        while cur >= min_offset:
            # 沿着切线方向的两个候选点
            c1 = (P + t * cur).astype(np.float32)
            c2 = (P - t * cur).astype(np.float32)

            # 添加垂直方向的偏移
            c1 = (c1 + t_perp * offset_perpendicular).astype(np.float32)
            c2 = (c2 + t_perp * offset_perpendicular).astype(np.float32)

            # 检查哪个点在多边形内部
            d1 = cv2.pointPolygonTest(poly, (float(c1[0]), float(c1[1])), True)  # inside > 0
            d2 = cv2.pointPolygonTest(poly, (float(c2[0]), float(c2[1])), True)

            if d1 > 0 and d2 > 0:
                return c1 if d1 >= d2 else c2
            if d1 > 0:
                return c1
            if d2 > 0:
                return c2

            # 缩小偏移距离重试
            cur *= 0.7

        # 如果都失败，返回多边形中心（也添加垂直偏移）
        center = poly_px.mean(axis=0).astype(np.float32)
        return (center + t_perp * offset_perpendicular).astype(np.float32)

    @staticmethod
    def _draw_bond(img: np.ndarray, P: np.ndarray, Q: np.ndarray,
                   min_len: float = 22.0, thickness: int = 8) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        在图像上绘制化学键（从P指向Q的直线）
        如果 |PQ| < min_len，则自动延长Q使得 |PQ| = min_len

        Args:
            img: 输入图像
            P: 起始点 [x, y]
            Q: 结束点 [x, y]
            min_len: 化学键最小长度（默认22.0）
            thickness: 线条粗细（默认8）

        Returns:
            (P_int, Q_int) - 绘制的起始点和结束点（整数坐标）
        """
        P = np.asarray(P, dtype=np.float32)
        Q = np.asarray(Q, dtype=np.float32)

        # 计算向量和长度
        v = Q - P
        L = float(np.linalg.norm(v) + 1e-12)

        # 如果长度小于最小值，延长Q
        if L < min_len:
            v = v / L
            Q = P + v * min_len

        # 边界裁剪
        h, w = img.shape[:2]
        Q[0] = np.clip(Q[0], 0, w - 1)
        Q[1] = np.clip(Q[1], 0, h - 1)
        P[0] = np.clip(P[0], 0, w - 1)
        P[1] = np.clip(P[1], 0, h - 1)

        # 转换为整数坐标
        P_int = (int(round(P[0])), int(round(P[1])))
        Q_int = (int(round(Q[0])), int(round(Q[1])))

        # 绘制黑色线条
        cv2.line(img, P_int, Q_int, (0, 0, 0), thickness=thickness, lineType=cv2.LINE_AA)

        return P_int, Q_int

    @staticmethod
    def _draw_atom_with_shift(img: np.ndarray, place: np.ndarray, P: np.ndarray,
                              Q2: Tuple[int, int], poly_px: np.ndarray,
                              atom_text: str = "Ce", atom_shift: float = 10.0,
                              font_scale: float = 1.15, thickness: int = 2) -> np.ndarray:
        """
        绘制元素标记（Ce），并根据化学键方向调整位置

        Args:
            img: 输入图像
            place: 初始放置位置 [x, y]
            P: 化学键起始点 [x, y]
            Q2: 化学键结束点 (x, y)（整数坐标）
            poly_px: 多边形顶点坐标 [N, 2]
            atom_text: 元素文本（默认"Ce"）
            atom_shift: 沿化学键方向的偏移距离（默认10.0）
            font_scale: 字体大小（默认1.15）
            thickness: 字体粗细（默认2）

        Returns:
            修改后的图像
        """
        h, w = img.shape[:2]

        # 计算Ce标记的最终位置
        ce_pt = place.copy()

        if P is not None and Q2 is not None:
            # 使用化学键的方向（从P指向Q2）
            dir_vec = (np.array(Q2, dtype=np.float32) - np.array(P, dtype=np.float32))
            norm = float(np.linalg.norm(dir_vec) + 1e-12)
            u = dir_vec / norm

            # 候选位置：沿化学键方向偏移
            candidate = place + u * float(atom_shift)

            # 检查候选位置是否在多边形内部，如果不在则逐步缩小偏移
            poly_cv = poly_px.reshape(-1, 1, 2).astype(np.float32)
            shift = float(atom_shift)

            while shift > 1.0:
                d = cv2.pointPolygonTest(poly_cv, (float(candidate[0]), float(candidate[1])), True)
                if d > 0:
                    break
                shift *= 0.7
                candidate = place + u * shift

            # 边界裁剪
            candidate[0] = np.clip(candidate[0], 0, w - 1)
            candidate[1] = np.clip(candidate[1], 0, h - 1)
            ce_pt = candidate.astype(np.float32)

        # 绘制元素标记
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_w, text_h), baseline = cv2.getTextSize(atom_text, font, font_scale, thickness)

        # 计算文本位置（居中）
        text_x = int(ce_pt[0]) - text_w // 2
        text_y = int(ce_pt[1]) + text_h // 2

        # 绘制白色轮廓
        cv2.putText(img, atom_text, (text_x, text_y), font,
                   font_scale, (255, 255, 255), thickness + 2, cv2.LINE_AA)
        # 绘制黑色文字
        cv2.putText(img, atom_text, (text_x, text_y), font,
                   font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

        return img

    # ==================== 原有方法 ====================

    def pad_image_to_size(self, image: np.ndarray, target_size: int = 512) -> Tuple[np.ndarray, Dict]:
        """
        将图像填充到目标尺寸（而不是缩放）

        Args:
            image: 输入图像
            target_size: 目标尺寸（默认512）

        Returns:
            填充后的图像和填充信息字典
        """
        h, w = image.shape[:2]

        # 如果图像已经足够大，不需要填充
        if h >= target_size and w >= target_size:
            return image, {'padded': False, 'original_size': (w, h)}

        # 计算需要填充的尺寸
        new_h = max(h, target_size)
        new_w = max(w, target_size)

        # 计算填充量（居中填充）
        pad_top = (new_h - h) // 2
        pad_bottom = new_h - h - pad_top
        pad_left = (new_w - w) // 2
        pad_right = new_w - w - pad_left

        # 使用白色填充（255, 255, 255）
        padded_image = cv2.copyMakeBorder(
            image,
            pad_top, pad_bottom, pad_left, pad_right,
            cv2.BORDER_CONSTANT,
            value=(255, 255, 255)  # 白色填充
        )

        print(f"📏 Image padded from {w}x{h} to {new_w}x{new_h}")

        return padded_image, {
            'padded': True,
            'original_size': (w, h),
            'padded_size': (new_w, new_h),
            'padding': {
                'top': pad_top,
                'bottom': pad_bottom,
                'left': pad_left,
                'right': pad_right
            }
        }

    def detect_structures(self, image_path: str = None, image_array: np.ndarray = None,
                         conf: float = 0.25, iou: float = 0.5, imgsz: int = 512) -> List[Dict]:
        """
        检测图像中的化学结构

        Args:
            image_path: 图像文件路径
            image_array: 图像数组（numpy array）
            conf: 置信度阈值
            iou: IoU阈值
            imgsz: 输入图像大小

        Returns:
            检测结果列表，每个结果包含坐标、置信度等信息
        """
        if self.model is None:
            raise RuntimeError("YOLO model not loaded")

        # 确定输入源
        if image_path is not None:
            source = image_path
        elif image_array is not None:
            source = image_array
        else:
            raise ValueError("Either image_path or image_array must be provided")

        try:
            print(f"🔍 YOLO detection parameters: conf={conf}, iou={iou}, imgsz={imgsz}")
            if image_array is not None:
                print(f"📊 Input image shape: {image_array.shape}, dtype: {image_array.dtype}")

            # 执行检测
            results = self.model.predict(
                source=source,
                imgsz=imgsz,
                conf=conf,
                iou=iou,
                verbose=True  # 改为True以查看详细输出
            )

            print(f"📊 YOLO results type: {type(results)}, length: {len(results)}")

            # 解析结果
            detections = []
            for idx, result in enumerate(results):
                print(f"📊 Result {idx}: has obb={hasattr(result, 'obb')}, obb is None={result.obb is None if hasattr(result, 'obb') else 'N/A'}")

                # 检查是否有OBB结果
                if hasattr(result, 'obb') and result.obb is not None:
                    boxes = result.obb
                    print(f"📊 OBB boxes count: {len(boxes)}")

                    for i, box in enumerate(boxes):
                        print(f"\n🔍 === Inspecting box {i} ===")
                        print(f"   Box type: {type(box)}")
                        print(f"   Box attributes: {[attr for attr in dir(box) if not attr.startswith('_')]}")

                        # 检查data属性
                        if hasattr(box, 'data'):
                            print(f"   📦 box.data:")
                            print(f"      - type: {type(box.data)}")
                            print(f"      - shape: {box.data.shape if hasattr(box.data, 'shape') else 'N/A'}")
                            print(f"      - value: {box.data}")

                        # 提取旋转框的完整信息
                        xyxy = box.xyxy[0].cpu().numpy().tolist() if hasattr(box.xyxy[0], 'cpu') else box.xyxy[0].tolist()
                        print(f"   ✅ box.xyxy[0]: {xyxy}")

                        # 提取旋转框的四个角点 (xyxyxyxy格式)
                        xyxyxyxy = None
                        if hasattr(box, 'xyxyxyxy'):
                            print(f"   ✅ Has xyxyxyxy attribute")
                            if box.xyxyxyxy is not None:
                                print(f"      - type: {type(box.xyxyxyxy)}")
                                print(f"      - shape: {box.xyxyxyxy.shape if hasattr(box.xyxyxyxy, 'shape') else 'N/A'}")
                                print(f"      - value: {box.xyxyxyxy}")
                                xyxyxyxy = box.xyxyxyxy[0].cpu().numpy().tolist() if hasattr(box.xyxyxyxy[0], 'cpu') else box.xyxyxyxy[0].tolist()
                            else:
                                print(f"      - xyxyxyxy is None")
                        else:
                            print(f"   ❌ No xyxyxyxy attribute")

                        # 提取旋转框的中心点、宽高和角度 (xywhr格式)
                        xywhr = None
                        if hasattr(box, 'xywhr'):
                            print(f"   ✅ Has xywhr attribute")
                            if box.xywhr is not None:
                                print(f"      - type: {type(box.xywhr)}")
                                print(f"      - shape: {box.xywhr.shape if hasattr(box.xywhr, 'shape') else 'N/A'}")
                                print(f"      - value: {box.xywhr}")
                                xywhr = box.xywhr[0].cpu().numpy().tolist() if hasattr(box.xywhr[0], 'cpu') else box.xywhr[0].tolist()
                            else:
                                print(f"      - xywhr is None")
                        else:
                            print(f"   ❌ No xywhr attribute")

                        detection = {
                            'index': i,
                            'xyxy': xyxy,  # 轴对齐边界框
                            'xyxyxyxy': xyxyxyxy,  # 旋转框的四个角点
                            'xywhr': xywhr,  # 中心点、宽高、旋转角度
                            'confidence': float(box.conf[0]) if hasattr(box.conf[0], 'cpu') else float(box.conf[0]),
                            'class': int(box.cls[0]) if hasattr(box.cls[0], 'cpu') else int(box.cls[0])
                        }
                        detections.append(detection)

                        # 打印最终提取的信息
                        print(f"\n  ✅ Detection {i} extracted:")
                        print(f"     - confidence: {detection['confidence']:.3f}")
                        print(f"     - xyxy (axis-aligned): {xyxy}")
                        if xyxyxyxy:
                            print(f"     - xyxyxyxy (rotated corners): {xyxyxyxy}")
                        if xywhr:
                            print(f"     - xywhr (cx,cy,w,h,r): {xywhr}")
                else:
                    # 尝试检查是否有普通的boxes
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        print(f"⚠️ No OBB results, but found {len(result.boxes)} regular boxes")

            print(f"✅ YOLO detected {len(detections)} structures")
            return detections

        except Exception as e:
            print(f"❌ YOLO detection failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def fill_structures_with_ce(self, image: np.ndarray, detections: List[Dict],
                                atom_text: str = "Ce", offset_along: float = 25.0,
                                ring: int = 60, win: int = 27,
                                bond_thick: int = 2, min_bond: float = 2.0,
                                atom_shift: float = 10.0,
                                offset_perpendicular: float = -5.0) -> np.ndarray:
        """
        用白色填充检测到的化学结构区域，并用Ce元素替换

        使用智能算法（来自fill.py）：
        1. 找到检测区域外部最近的边缘点（化学键连接点）
        2. 在该点拟合切线方向（化学键方向）
        3. 沿着切线方向，在检测区域内部放置Ce标记

        Args:
            image: 输入图像
            detections: YOLO检测结果列表
            atom_text: 要添加的元素文本（默认"Ce"）
            offset_along: 沿切线方向的偏移距离（默认19.0，用于调整Ce标记位置）
            ring: 搜索边缘点的环半径（默认60，与fill.py一致）
            win: 拟合切线的窗口大小（默认27，与fill.py一致）
            bond_thick: 化学键线条粗细（默认8，与fill.py一致，用于绘制化学键）
            min_bond: 化学键最小长度（默认22.0，与fill.py一致，短于此值会自动延长）
            atom_shift: Ce标记沿化学键方向的偏移距离（默认10.0，与fill.py一致，用于微调Ce位置）
            offset_perpendicular: 垂直于切线方向的偏移距离（默认-5.0）
                                 正值：向左偏移
                                 负值：向右偏移

        Returns:
            填充后的图像
        """
        if len(detections) == 0:
            print("⚠️ No detections to fill")
            return image

        h, w = image.shape[:2]
        filled_image = image.copy()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        mode = "smart" if self.use_smart_placement else "simple"
        print(f"🎨 Filling {len(detections)} detected structures with '{atom_text}' (mode: {mode})")

        for i, detection in enumerate(detections):
            # 优先使用旋转框的四个角点
            if detection.get('xyxyxyxy') is not None:
                # 使用旋转框的四个角点
                xyxyxyxy = detection['xyxyxyxy']
                # xyxyxyxy格式: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                # 已经是4个点的列表,直接转换为numpy数组
                points = np.array(xyxyxyxy, dtype=np.float32)

                print(f"  🔷 Using rotated bounding box (OBB)")
                print(f"     Points: {points}")

                # 将旋转框内部用白色填充
                points_int = points.astype(np.int32)
                fill_color = (255, 255, 255)  # BGR格式：白色
                cv2.fillPoly(filled_image, [points_int], color=fill_color)

                # 绘制白色边框(可选,增强视觉效果)
                border_thickness = 2
                border_color = (255, 255, 255)  # BGR格式：白色
                cv2.polylines(filled_image, [points_int], isClosed=True, color=border_color, thickness=border_thickness)

                # 计算旋转框的中心点(用于放置Ce)
                center_x = int(np.mean(points[:, 0]))
                center_y = int(np.mean(points[:, 1]))

                # 计算旋转框的宽度和高度(用于日志)
                # 使用边长计算
                box_width = np.linalg.norm(points[1] - points[0])
                box_height = np.linalg.norm(points[2] - points[1])

                # 用于智能放置的多边形
                poly_px = points.astype(np.float32)

                # 获取旋转角度信息(如果有)
                if detection.get('xywhr') is not None:
                    xywhr = detection['xywhr']
                    rotation_rad = xywhr[4]
                    rotation_deg = np.degrees(rotation_rad)
                    print(f"     Rotation: {rotation_rad:.4f} rad ({rotation_deg:.2f}°)")

            else:
                # 回退到轴对齐边界框
                print(f"  ⬜ Using axis-aligned bounding box (fallback)")
                x1, y1, x2, y2 = detection['xyxy']
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # 确保坐标在图像范围内
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)

                # 计算检测框的宽度和高度
                box_width = x2 - x1
                box_height = y2 - y1

                # 用白色填充矩形内部
                fill_color = (255, 255, 255)  # BGR格式：白色
                cv2.rectangle(filled_image, (x1, y1), (x2, y2), fill_color, -1)  # -1表示填充

                # 绘制白色边框(可选)
                border_thickness = 2
                border_color = (255, 255, 255)  # BGR格式：白色
                cv2.rectangle(filled_image, (x1, y1), (x2, y2), border_color, border_thickness)

                # 计算中心点
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                # 用于智能放置的多边形
                poly_px = np.array([
                    [x1, y1],
                    [x2, y1],
                    [x2, y2],
                    [x1, y2]
                ], dtype=np.float32)

            # 计算Ce标记的位置
            P = None
            t = None
            place = None
            Q2 = None

            if self.use_smart_placement:
                # 智能算法：找到化学键连接点
                # poly_px已经在上面定义好了(旋转框或矩形框)

                # 1. 找到多边形外部最近的边缘点
                P = self._nearest_edge_point_outside(gray, poly_px, ring=ring)

                # 2. 拟合切线方向
                t = self._fit_tangent_at(gray, P, win=win) if P is not None else None

                # 3. 选择内部端点
                if P is not None and t is not None:
                    place = self._choose_inside_end(poly_px, P, t, offset_along,
                                                    offset_perpendicular=offset_perpendicular)
                    print(f"  🎯 Smart placement: edge_point=({P[0]:.1f},{P[1]:.1f}), tangent=({t[0]:.2f},{t[1]:.2f}), perp_offset={offset_perpendicular:.1f}")

                    # 4. 绘制化学键（从P指向place）
                    P_int, Q2 = self._draw_bond(filled_image, P, place, min_len=min_bond, thickness=bond_thick)
                    print(f"     🔗 Bond drawn: {P_int} -> {Q2} (thickness={bond_thick}, min_len={min_bond})")
                else:
                    # 如果智能算法失败，回退到中心点
                    place = poly_px.mean(axis=0).astype(np.float32)
                    print(f"  ⚠️ Smart placement failed, using center")
            else:
                # 简单模式：使用中心点
                place = poly_px.mean(axis=0).astype(np.float32)

            # 5. 绘制元素标记（Ce），并根据化学键方向调整位置
            if place is not None:
                self._draw_atom_with_shift(filled_image, place, P, Q2, poly_px,
                                          atom_text=atom_text, atom_shift=atom_shift,
                                          font_scale=0.8, thickness=1)
                print(f"  ✅ Filled structure {i+1} [size: {box_width:.1f}x{box_height:.1f}]")
                print(f"     🧪 Atom '{atom_text}' placed with shift={atom_shift}")

        return filled_image

    def extract_structures(self, image_path: str = None, image_array: np.ndarray = None,
                          conf: float = 0.01, iou: float = 0.5, imgsz: int = 320,
                          padding: int = 10) -> List[Dict]:
        """
        检测并提取化学结构图像
        
        Args:
            image_path: 图像文件路径
            image_array: 图像数组
            conf: 置信度阈值
            iou: IoU阈值
            imgsz: 输入图像大小
            padding: 裁剪时的边距
            
        Returns:
            提取的结构列表，每个包含图像数据和元数据
        """
        # 读取图像
        if image_path is not None:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image: {image_path}")
        elif image_array is not None:
            image = image_array
        else:
            raise ValueError("Either image_path or image_array must be provided")

        # 获取原始图像尺寸
        original_h, original_w = image.shape[:2]
        print(f"🔍 Original image size: {original_w}x{original_h}")

        # 使用填充而不是缩放（填充到至少512x512）
        min_size = 512
        padded_image, pad_info = self.pad_image_to_size(image, target_size=min_size)

        # 检测结构（使用填充后的图像）
        detections = self.detect_structures(
            image_array=padded_image,
            conf=conf,
            iou=iou,
            imgsz=imgsz
        )

        # 提取每个检测到的结构（从填充后的图像中提取）
        structures = []
        h, w = padded_image.shape[:2]
        
        for detection in detections:
            # 获取边界框坐标
            x1, y1, x2, y2 = detection['xyxy']
            
            # 添加边距并确保在图像范围内
            x1 = max(0, int(x1) - padding)
            y1 = max(0, int(y1) - padding)
            x2 = min(w, int(x2) + padding)
            y2 = min(h, int(y2) + padding)
            
            # 裁剪结构（从填充后的图像中裁剪）
            structure_img = padded_image[y1:y2, x1:x2]
            
            # 转换为PIL Image
            structure_pil = Image.fromarray(cv2.cvtColor(structure_img, cv2.COLOR_BGR2RGB))
            
            # 转换为base64
            buffered = BytesIO()
            structure_pil.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            structures.append({
                'index': detection['index'],
                'confidence': detection['confidence'],
                'bbox': [x1, y1, x2, y2],
                'image_array': structure_img,
                'image_pil': structure_pil,
                'image_base64': img_base64,
                'width': x2 - x1,
                'height': y2 - y1
            })
        
        print(f"✅ Extracted {len(structures)} structures")
        return structures
    
    def process_from_file_id(self, file_id: str, db_manager, fill_with_ce: bool = True,
                            offset_perpendicular: float = -5.0) -> Dict:
        """
        从数据库中的file_id处理图像

        Args:
            file_id: 文件ID
            db_manager: 数据库管理器
            fill_with_ce: 是否用白色填充检测区域并添加Ce标记（默认True）
            offset_perpendicular: 垂直于切线方向的偏移距离（默认0.0）
                                 正值：向左偏移
                                 负值：向右偏移

        Returns:
            处理结果，包含填充后的图像或提取的结构
        """
        # offset_perpendicular参数已经从函数参数传入，不需要硬编码
        try:
            # 使用DatabaseManager的get_image_by_id方法获取图像数据
            image_data = db_manager.get_image_by_id(file_id)

            if not image_data:
                return {
                    'success': False,
                    'error': f'Image not found: {file_id}'
                }

            # 解码图像
            import io
            from PIL import Image
            image_pil = Image.open(io.BytesIO(image_data))
            image_array = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

            print(f"📊 Original image shape: {image_array.shape}")

            # 填充图像到至少512x512
            padded_image, pad_info = self.pad_image_to_size(image_array, target_size=512)

            # 检测化学结构
            # 使用标准参数：imgsz=512, conf=0.25（与原始命令行一致）
            print(f"🔍 YOLO detection with conf=0.25, iou=0.5, imgsz=512")
            detections = self.detect_structures(
                image_array=padded_image,
                conf=0.25,
                iou=0.5,
                imgsz=512
            )

            print(f"✅ YOLO detected {len(detections)} structures")

            if len(detections) == 0:
                print(f"⚠️ WARNING: No structures detected by YOLO!")
                print(f"   This means NO Ce markers will be added to the image.")
                print(f"   The saved image will be identical to the padded image.")
                print(f"   Possible reasons:")
                print(f"   1. The image does not contain recognizable chemical structures")
                print(f"   2. The confidence threshold (0.25) is too high")
                print(f"   3. The YOLO model is not properly loaded")
                print(f"   4. The image size (512) is not suitable for this image")

            if fill_with_ce:
                # 用白色填充检测区域并添加Ce标记
                filled_image = self.fill_structures_with_ce(padded_image, detections, atom_text="Ce",
                                                           offset_perpendicular=offset_perpendicular)

                # 转换为PIL Image
                filled_pil = Image.fromarray(cv2.cvtColor(filled_image, cv2.COLOR_BGR2RGB))

                # 保存YOLO处理过的图像到指定文件夹
                try:
                    import os
                    from datetime import datetime

                    # 目标文件夹
                    output_dir = "/root/net-disk/test1/长鑫1103/检查"

                    # 确保文件夹存在
                    os.makedirs(output_dir, exist_ok=True)

                    # 生成文件名：file_id_timestamp.png
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{file_id}_{timestamp}_yolo_processed.png"
                    filepath = os.path.join(output_dir, filename)

                    # 保存原始填充图像（用于对比）
                    padded_pil = Image.fromarray(cv2.cvtColor(padded_image, cv2.COLOR_BGR2RGB))
                    padded_filename = f"{file_id}_{timestamp}_padded.png"
                    padded_filepath = os.path.join(output_dir, padded_filename)
                    padded_pil.save(padded_filepath)

                    # 保存YOLO处理后的图像
                    filled_pil.save(filepath)

                    print(f"💾 Saved YOLO processed images to {output_dir}:")
                    print(f"   - Padded image: {padded_filename}")
                    print(f"   - Filled image: {filename}")

                except Exception as e:
                    print(f"⚠️ Failed to save YOLO processed image: {e}")
                    import traceback
                    traceback.print_exc()

                # 转换为base64
                buffered = BytesIO()
                filled_pil.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

                return {
                    'success': True,
                    'filled_image': filled_image,
                    'filled_image_pil': filled_pil,
                    'filled_image_base64': img_base64,
                    'detections': detections,
                    'count': len(detections),
                    'pad_info': pad_info,
                    'saved_filepath': filepath if 'filepath' in locals() else None
                }
            else:
                # 提取检测到的结构
                structures = self.extract_structures(image_array=padded_image)

                return {
                    'success': True,
                    'structures': structures,
                    'count': len(structures),
                    'pad_info': pad_info
                }

        except Exception as e:
            print(f"❌ Error processing file_id {file_id}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


# 全局YOLO处理器实例
_yolo_processor = None

def get_yolo_processor(force_reload: bool = False) -> YOLOProcessor:
    """
    获取YOLO处理器实例（单例模式）

    Args:
        force_reload: 是否强制重新加载处理器
    """
    global _yolo_processor
    if _yolo_processor is None or force_reload:
        try:
            _yolo_processor = YOLOProcessor()
            print("✅ YOLO processor initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize YOLO processor: {e}")
            raise
    return _yolo_processor

def reset_yolo_processor():
    """重置YOLO处理器（用于重新加载配置）"""
    global _yolo_processor
    _yolo_processor = None
    print("🔄 YOLO processor reset")

