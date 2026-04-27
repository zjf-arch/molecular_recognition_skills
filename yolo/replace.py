import pandas as pd
from rdkit import Chem
from rdkit import RDLogger

# 关闭 RDKit 警告（可选）
RDLogger.DisableLog('rdApp.*')

def replace_ce_with_allyl(smiles):
    """
    将 SMILES 中的 'Ce' 或 '[Ge]' 替换为异丙烯基 (isopropenyl group: C=C(C))
    注意：'Ce' 或 '[Ge]' 被视为连接点，替换为 * 后用 RDKit 正确连接异丙烯基
    """
    has_ce = 'Ce' in smiles
    has_ge = '[Ge]' in smiles

    if not (has_ce or has_ge):
        return smiles  # 如果没有 Ce 或 Ge，直接返回原 SMILES

    # 将 Ce 或 [Ge] 替换为连接点 *
    smiles_with_star = smiles.replace('Ce', '*').replace('[Ge]', '*')
    
    # 解析含连接点的分子
    mol = Chem.MolFromSmiles(smiles_with_star)
    if mol is None:
        raise ValueError(f"无法解析 SMILES: {smiles_with_star}")

    # 创建可编辑分子
    rwmol = Chem.RWMol(mol)
    
    # 找到所有连接点 * 的索引（支持多个 Ce，但通常只有一个）
    star_indices = []
    for atom in rwmol.GetAtoms():
        if atom.GetSymbol() == '*':
            star_indices.append(atom.GetIdx())
    
    if not star_indices:
        return Chem.MolToSmiles(mol)  # 没有连接点，直接返回

    # 异丙烯基：CH2=C(CH3)-，连接点在第一个C（即CH2=的碳）
    # 构建异丙烯基片段：C=C(C)，其中第一个C（索引0）用于连接
    allyl_smiles = "C=C(C)"
    allyl_mol = Chem.MolFromSmiles(allyl_smiles)
    if allyl_mol is None:
        raise RuntimeError("无法构建异丙烯基片段")

    # 从右到左处理连接点（避免索引偏移）
    for star_idx in sorted(star_indices, reverse=True):
        # 获取连接点的邻居（应该只有一个，因为是单键连接）
        neighbors = rwmol.GetAtomWithIdx(star_idx).GetNeighbors()
        if len(neighbors) != 1:
            raise ValueError(f"连接点 * 必须只连接一个原子，但在 {smiles} 中有 {len(neighbors)} 个")

        neighbor_idx = neighbors[0].GetIdx()

        # 删除连接点 *
        rwmol.RemoveAtom(star_idx)

        # 调整 neighbor_idx（如果 star_idx < neighbor_idx，则 neighbor_idx 自动减1）
        if star_idx < neighbor_idx:
            neighbor_idx -= 1

        # 添加异丙烯基的所有原子
        atom_map = {}  # 映射旧索引到新索引
        for atom in allyl_mol.GetAtoms():
            new_atom = Chem.Atom(atom.GetSymbol())
            new_idx = rwmol.AddAtom(new_atom)
            atom_map[atom.GetIdx()] = new_idx

        # 添加异丙烯基内部的键
        for bond in allyl_mol.GetBonds():
            a1 = atom_map[bond.GetBeginAtomIdx()]
            a2 = atom_map[bond.GetEndAtomIdx()]
            rwmol.AddBond(a1, a2, bond.GetBondType())

        # 将原分子的 neighbor 与异丙烯基的连接点（第一个C，索引0）连接
        allyl_connection_idx = atom_map[1]  # 连接点是异丙烯基的标号1的C
        rwmol.AddBond(neighbor_idx, allyl_connection_idx, Chem.BondType.SINGLE)

    # 生成新的 SMILES（使用Kekulize避免自动芳香化）
    new_mol = rwmol.GetMol()
    # Kekulize：保持双键形式，不自动芳香化环结构
    Chem.Kekulize(new_mol, clearAromaticFlags=True)
    new_smiles = Chem.MolToSmiles(new_mol, isomericSmiles=True, kekuleSmiles=True)
    return new_smiles


# -----------------------------
# 主程序：读取 Excel，处理，保存
# -----------------------------

def main():
    input_file = "before_rpl.xlsx"      # 输入文件名
    output_file = "after_rpl.xlsx"      # 输出文件名

    # 读取 Excel 文件（默认读取第一个 sheet）
    df = pd.read_excel(input_file, header=None, engine='openpyxl')

    # 确保至少有一列
    if df.shape[1] < 1:
        raise ValueError("Excel 文件至少需要一列 SMILES 数据")

    # 提取第一列（SMILES）
    smiles_col = df.iloc[:, 0].astype(str)

    # 处理每一行 SMILES
    new_smiles_list = []
    for i, smi in enumerate(smiles_col):
        try:
            if pd.isna(smi) or smi.strip() == "":
                new_smiles_list.append("")
            else:
                new_smi = replace_ce_with_allyl(smi)
                new_smiles_list.append(new_smi)
        except Exception as e:
            print(f"第 {i+1} 行处理出错: {smi} | 错误: {e}")
            new_smiles_list.append(f"ERROR: {e}")

    # 将结果写入第二列
    df[1] = new_smiles_list  # 自动创建第二列（索引为1）

    # 保存到新 Excel 文件
    df.to_excel(output_file, index=False, header=False, engine='openpyxl')
    print(f"处理完成！结果已保存到 {output_file}")


if __name__ == "__main__":
    main()