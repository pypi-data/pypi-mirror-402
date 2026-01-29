from data_store import store_data
from data_store import get_data
# from load_syllable_char_table_base_20250917 import load_syllable_char_table
import unicodedata
import re
import os

def to_ascii(s):
    # NFD 分解 -> 去掉音符 -> 转回 str
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('ascii')

def is_latin_or_digit(s):
    ascii_str = to_ascii(s)
    # 如果全是数字
    if ascii_str.isdigit():
        return True
    # 如果包含至少一个英文字母
    if re.search(r'[A-Za-z]', ascii_str):
        return True
    return False

def load_word_table(handle):
    word_entry_list = []
    province_name_entry = []
    country_name_entry = []  # 用来存储处理后的行
    full_final_word_entry_list = []
    base_dir = os.path.dirname(__file__)  # pyhannom 包所在目录
    data_path = os.path.join(base_dir, "data", "country_name.txt")
    with open(data_path, "r", encoding="utf-8") as country_name_f:
        for line in country_name_f:
            # 去掉行尾换行符
            stripped_line = line.strip('\n')
            # 按制表符分割成列表
            parts = stripped_line.split('\t')
            each_country_entry = [parts[1].strip(), parts[0].strip()]
            # 添加到结果列表
            country_name_entry.append(each_country_entry)
    # print(country_name_entry)

    base_dir = os.path.dirname(__file__)  # pyhannom 包所在目录
    data_path = os.path.join(base_dir, "data", "vietnam_province_name.txt")
    with open(data_path, "r", encoding="utf-8") as province_name_f:
        for line in province_name_f:
            stripped_line = line.strip('\n')
            stripped_line_list = stripped_line.split(' ')
            # print(stripped_line_list)
            result = []
            for item in stripped_line_list:
                if is_latin_or_digit(item) and result and is_latin_or_digit(result[-1]):
                    result[-1] += ' ' + item
                else:
                    result.append(item)
            # print(result)
            for ele_num in range(len(result)):
                if ele_num % 2 == 0:
                    province_name_entry.append([result[ele_num].strip(), result[ele_num + 1].strip()])
    # print(province_name_entry)

    # char_word_table = load_syllable_char_table('rawCharWordTable.txt')
    char_word_table = get_data(handle)
    for each_syllable_char_info_line in char_word_table:
        word_list_in_each_line = each_syllable_char_info_line[2].split(' · ')
        for each_word in word_list_in_each_line:
            if len(each_word) > 0:
                word_entry = each_word.split(" ", 1)
                non_cjkv_part = word_entry[1].split('[')
                if len(non_cjkv_part) > 1:
                    non_cjkv_part = [non_cjkv_part[0].strip(), ('[' + non_cjkv_part[1]).strip()]
                cjkv_part = word_entry[0].strip()
                word_entry = [cjkv_part] + non_cjkv_part
                # print(word_entry)
                word_entry_list.append(word_entry)
    full_final_word_entry_list = word_entry_list + country_name_entry + province_name_entry
    return store_data(full_final_word_entry_list)

