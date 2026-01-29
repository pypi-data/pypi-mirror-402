import csv
import os
from dataclasses import dataclass
from typing import List
import ast


# 1. 定义单字条目的数据结构
@dataclass
class HanNomEntry:
    """
    对应 raw_syllable_char_word_table.csv 中的一行数据。
    """
    latin: str  # 国语字音节 (如: a, Á, ác)
    hannom: str  # 汉喃字符 (如: 丫, 惡)
    examples: str  # 词汇示例 (如: 丫鬟 a hoàn...)
    note: str  # Unicode码或备注 (如: U+4E2B, [翻]\nU+963F)

    # def __repr__(self):
    #     return [self.latin, self.hannom, self.examples, self.note]


# 2. 定义读取函数
def load_hannom_table():
    """
    读取 data/raw_syllable_char_word_table.csv 文件。

    Returns:
        List[HanNomCharEntry]: 包含所有字符条目的列表。
    """
    # 获取当前脚本所在的目录
    current_dir = os.path.dirname(__file__)
    # 拼接相对路径: 当前目录/data/文件名
    file_path = os.path.join(current_dir, 'data', 'GungJyuChaJiouZiiHanNanZhuen_new_v1.csv')
    GJCJZHNZ_entries = []
    # newline='' 是 csv 模块要求的，防止不同系统换行符处理不一致
    with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            # 确保这一行至少有4列数据，防止空行报错
            if len(row) >= 4:
                entry = HanNomEntry(
                    latin=row[0].strip(),
                    hannom=row[1].strip(),
                    examples=row[2].strip(),
                    note=row[3].strip()
                )
                GJCJZHNZ_entries.append(entry)

    CVTMPDAT_entries = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接相对路径: 当前目录/data/文件名
    file_path = os.path.join(current_dir, 'data', 'mapping_data.js')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.readlines()
    for each_line in content:
        each_line = each_line.strip()
        if each_line.startswith('['):
            each_line = each_line[:-1]
            each_entry = ast.literal_eval(each_line)
            # print(each_entry)
            CVTMPDAT_entries.append(each_entry)
    # print(CVTMPDAT_entries)

    return (GJCJZHNZ_entries, CVTMPDAT_entries)



# hannom_table = load_hannom_table()
# lookup_table = hannom_table[1]
# for each_lookup_entry in lookup_table:
#     print(each_lookup_entry)
# hannom_table = load_hannom_table()
# print(hannom_table[1])
# --- 测试代码 (你可以直接运行这个文件来测试) ---
# if __name__ == "__main__":
#     # 假设你已经把 csv 放在了正确的位置
#     # 这里为了演示，模拟一下调用
#     data = load_hannom_table()
#
#     if data:
#         print(f"成功加载了 {len(data)} 条数据。")
#         # print("前 3 条数据示例：")
#         for item in data:
#             print(item)

        # # 测试查找包含换行符的特殊条目 (如: 阿)
        # print("\n查找特殊条目 '阿':")
        # for item in data:
        #     if item.hannom == '阿' and item.latin == 'A':
        #         print(f"原始 Code 内容:\n{item.note}")
        #         break