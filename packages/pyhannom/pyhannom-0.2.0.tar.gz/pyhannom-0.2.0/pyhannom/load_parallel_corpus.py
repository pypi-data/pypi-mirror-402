import json
import os
from dataclasses import dataclass
from typing import List, Optional


# 1. 定义数据结构：使用 dataclass 更加 Pythonic 且内存高效
@dataclass
class HanNomSentence:
    """
    代表一个汉喃-国语字平行句对的数据结构。
    """
    hannom: str  # 汉喃句子
    latin: str  # 对应的国语字句子
    note: str = ""  # 备注（如：格式说明、特殊词汇标记等）
    source_url: str = ""  # 数据来源 URL

    def __repr__(self):
        # 打印时只显示前几个字，保持整洁
        return f"\nHanNom: {self.hannom}\nLatin: {self.latin}\nnote: {self.note}\nSource URL: {self.source_url}\n"


# 2. 定义加载函数
def load_parallel_corpus() -> List[HanNomSentence]:
    """
    加载内置的汉喃-国语字平行语料库。

    Returns:
        List[HanNomSentence]: 包含所有句对对象的列表。
    """
    # 假设 json 文件和这个 python 文件在同一个目录下
    # 如果你的结构不同，请相应调整路径
    base_dir = os.path.dirname(os.path.abspath(__file__)) + '\data'
    # print(base_dir)
    data_path = os.path.join(base_dir, 'parallel_corpus.json')

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 将字典转换为 HanNomSentence 对象列表
        corpus = [
            HanNomSentence(
                hannom=item.get("hannom", ""),
                latin=item.get("latin", ""),
                note=item.get("note", ""),
                source_url=item.get("source_url", "")
            )
            for item in data
        ]
        return corpus

    except FileNotFoundError:
        print(f"Error: The corpus file was not found at {data_path}")
        return []



# corpus = load_parallel_corpus()
# print(corpus)
#
#
# target_pair = corpus[1]
# print("THE TARGET PAIR:")
# print(target_pair)
# target_hannom = target_pair.hannom
# print("THE HAN-NOM IN TARGET PAIR:")
# print(target_hannom)
# target_latin = target_pair.latin
# print("THE LATIN IN TARGET PAIR:")
# print(target_latin)
# target_note = target_pair.note
# print("THE NOTE IN TARGET PAIR:")
# print(target_note)
# target_source = target_pair.source_url
# print("THE SOURCE URL IN TARGET PAIR:")
# print(target_source)
#
# print(len(corpus))