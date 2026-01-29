import re
import os
from data_store import store_data


def load_syllable_char_table():
    """
    解析 rawCharWordTable.txt，将需要的行合并并拆分出 Unicode 部分和前置内容。

    参数:
        file_path (str): 输入文件路径

    返回:
        list[list[str]]: 处理后的二维列表，每行格式为：
                         [原行的前几列..., Unicode部分, 前置内容]
    """
    # 读取文件并按行拆分为列表
    base_dir = os.path.dirname(__file__)  # pyhannom 包所在目录
    data_path = os.path.join(base_dir, "data", "raw_char_word_table.txt")
    with open(data_path, "r", encoding="utf-8") as f:
        table_rows = [line.strip('\n').split('\t') for line in f]

    processed_rows = []
    row_index = 1  # 跳过表头

    while row_index < len(table_rows):
        current_row = table_rows[row_index]

        # 如果最后一列不包含 'U+'，需要和后续行合并
        if 'U+' not in current_row[-1]:
            merge_index = row_index + 1
            while merge_index < len(table_rows):
                next_row = table_rows[merge_index]
                current_row[-1] += '\n' + next_row[0]
                if 'U+' in next_row[0]:
                    break
                merge_index += 1
            row_index = merge_index + 1
        else:
            row_index += 1

        # 拆分 Unicode 部分
        last_column = current_row[-1]
        unicode_pos = last_column.find("U+")
        if unicode_pos != -1:
            before_unicode = last_column[:unicode_pos].strip().replace('\n', ' ')
            unicode_part = last_column[unicode_pos:].strip()
            processed_row = current_row[:-1] + [unicode_part] + [before_unicode]
            processed_rows.append(processed_row)
        else:
            print("U+ NOT FOUND")
            return ["U+ NOT FOUND"]
    return store_data(processed_rows)
