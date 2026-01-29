import csv
import ast
import os
from dataclasses import dataclass
from typing import List


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
def load_extend_hannom_table():
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
            #print(each_entry)
            CVTMPDAT_entries.append(each_entry)
    print(CVTMPDAT_entries)
    return CVTMPDAT_entries


result = load_extend_hannom_table()
# print(result)