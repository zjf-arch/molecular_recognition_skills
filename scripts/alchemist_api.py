"""
al-chemist API 接口调用模块
用于识别分子结构图并生成 SMILES
"""

import base64
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AlchemistAPI:
    """al-chemist API 客户端"""

    def __init__(self, api_url: str, headers: Dict[str, str]):
        """
        初始化 API 客户端

        Args:
            api_url: API 地址
            headers: 请求头
        """
        self.api_url = api_url
        self.headers = headers

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片编码为 base64

        Args:
            image_path: 图片路径

        Returns:
            base64 编码的字符串
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')

    def recognize_molecule(self, image_path: str) -> Dict[str, Any]:
        """
        识别分子结构并返回 SMILES（已转换为 Kekule 形式，避免芳香化）

        Args:
            image_path: 分子结构图路径

        Returns:
            包含识别结果的字典，格式：
            {
                'success': bool,
                'smiles': str,  # 识别成功时（Kekule 形式）
                'error': str,   # 识别失败时
                'raw_response': dict  # 原始响应
            }
        """
        try:
            # 编码图片
            image_base64 = self.encode_image_to_base64(image_path)

            # 构造请求数据（API 不支持 kekulize 参数）
            payload = {
                "imageBase64": image_base64
            }

            # 发送请求（禁用 SSL 验证，因为证书可能过期）
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=False  # 禁用 SSL 验证
            )

            # 检查响应状态
            if response.status_code == 200:
                result = response.json()

                # 解析响应（需要根据实际 API 响应格式调整）
                # API 返回格式: {"data": {"smiles": "...", "molblock": "..."}}
                smiles = result.get('smiles') or result.get('data', {}).get('smiles')
                molblock = result.get('molblock') or result.get('data', {}).get('molblock')

                # 如果有 molblock 但没有 smiles，转换 molblock
                if molblock and not smiles:
                    try:
                        from rdkit import Chem
                        mol = Chem.MolFromMolBlock(molblock)
                        if mol is not None:
                            # 使用 kekuleSmiles=True 参数，避免芳香化
                            smiles = Chem.MolToSmiles(mol, kekuleSmiles=True)
                            logger.info("从 molblock 转换得到 SMILES (kekuleSmiles=True)")
                    except Exception as e:
                        logger.warning(f"molblock 转换失败: {e}")

                # 如果 API 直接返回 SMILES，转换为 Kekule 形式
                if smiles:
                    try:
                        from rdkit import Chem
                        mol = Chem.MolFromSmiles(smiles)
                        if mol is not None:
                            # 检查是否包含芳香原子
                            has_aromatic = any(atom.GetIsAromatic() for atom in mol.GetAtoms())
                            if has_aromatic:
                                logger.info(f"检测到芳香原子，转换为 Kekule 形式")
                                try:
                                    # 先调用 Kekulize() 来去芳香化分子对象
                                    Chem.Kekulize(mol, clearAromaticFlags=True)
                                    smiles = Chem.MolToSmiles(mol, kekuleSmiles=True)
                                    logger.info(f"成功转换为 Kekule SMILES")
                                except Exception as kekulize_error:
                                    logger.warning(f"Kekulize with clearAromaticFlags 失败: {kekulize_error}")
                                    try:
                                        Chem.Kekulize(mol, clearAromaticFlags=False)
                                        smiles = Chem.MolToSmiles(mol, kekuleSmiles=True)
                                        logger.info(f"使用 Kekulize (不清理标志) 转换成功")
                                    except Exception as e2:
                                        logger.warning(f"Kekulize 失败: {e2}，仅使用 kekuleSmiles 参数")
                                        smiles = Chem.MolToSmiles(mol, kekuleSmiles=True)
                    except Exception as e:
                        logger.warning(f"RDKit 转换失败: {e}，使用原始 SMILES")

                if smiles:
                    return {
                        'success': True,
                        'smiles': smiles,
                        'raw_response': result
                    }
                else:
                    return {
                        'success': False,
                        'error': '响应中未找到 SMILES',
                        'raw_response': result
                    }
            else:
                return {
                    'success': False,
                    'error': f'API 请求失败，状态码: {response.status_code}',
                    'raw_response': {'status_code': response.status_code, 'text': response.text}
                }

        except requests.exceptions.Timeout:
            logger.error(f"请求超时: {image_path}")
            return {
                'success': False,
                'error': '请求超时',
                'raw_response': {}
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return {
                'success': False,
                'error': f'请求异常: {str(e)}',
                'raw_response': {}
            }
        except Exception as e:
            logger.error(f"处理图片时出错: {e}")
            return {
                'success': False,
                'error': f'处理出错: {str(e)}',
                'raw_response': {}
            }

    def batch_recognize(self, image_paths: list, delay: float = 0.5) -> list:
        """
        批量识别分子结构图

        Args:
            image_paths: 图片路径列表
            delay: 请求间隔（秒），避免过快��求

        Returns:
            结果列表，每个元素为 recognize_molecule 的返回值
        """
        import time

        results = []
        total = len(image_paths)

        for idx, image_path in enumerate(image_paths, 1):
            logger.info(f"正在处理 [{idx}/{total}]: {image_path}")
            result = self.recognize_molecule(image_path)
            result['image_path'] = image_path
            result['index'] = idx
            results.append(result)

            # 添加延迟，避免请求过快
            if idx < total:
                time.sleep(delay)

        return results


def test_api_connection(api_url: str, headers: Dict[str, str], test_image_path: Optional[str] = None) -> bool:
    """
    测试 API 连接是否正常

    Args:
        api_url: API 地址
        headers: 请求头
        test_image_path: 测试图片路径（可选）

    Returns:
        是否连接成功
    """
    try:
        client = AlchemistAPI(api_url, headers)

        # 如果有测试图片，尝试识别
        if test_image_path and Path(test_image_path).exists():
            result = client.recognize_molecule(test_image_path)
            return result['success']
        else:
            # 尝试简单的连接测试
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(api_url, timeout=5, verify=False)
            return response.status_code < 500
    except Exception as e:
        logger.error(f"API 连接测试失败: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # API 配置
    api_url = "https://api-ocsr.alchemist.iresearch.net.cn/ocsr/"
    headers = {
        "X-API-Version": "1.0",
        "Content-Type": "application/json"
    }

    # 测试连接
    print("测试 API 连接...")
    if test_api_connection(api_url, headers):
        print("[OK] API 连接成功")
    else:
        print("[ERROR] API 连接失败")

    # 如果提供了测试图片，尝试识别
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        print(f"\n测试识别图片: {test_image}")

        client = AlchemistAPI(api_url, headers)
        result = client.recognize_molecule(test_image)

        if result['success']:
            print(f"[OK] 识别成功")
            print(f"SMILES: {result['smiles']}")
        else:
            print(f"[ERROR] 识别失败: {result['error']}")

        print(f"\n原始响应: {result['raw_response']}")