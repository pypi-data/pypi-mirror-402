from load_syllable_char_table import load_syllable_char_table
from data_store import get_data


def get_chuhannom_from_latin(
    handle,
    input_latin_syllable: str,
    normalize_input_case: bool = True,   # 是否在匹配前统一大小写
    case_insensitive_match: bool = True   # 匹配时是否忽略大小写
):
    result_chars = []
    char_word_table = get_data(handle)
    # char_word_table = load_syllable_char_table('rawCharWordTable.txt')
    input_latin_syllable = input_latin_syllable.strip()
    if normalize_input_case == True:
        input_latin_syllable = input_latin_syllable.lower()
    for each_syllable_char_info_line in char_word_table:
        if case_insensitive_match == True:
            if each_syllable_char_info_line[0].lower() == input_latin_syllable.lower():
                result_chars.append(each_syllable_char_info_line[1])
        else:
            if each_syllable_char_info_line[0] == input_latin_syllable:
                result_chars.append(each_syllable_char_info_line[1])
    return result_chars

def get_chuhannom_unicode_from_latin(
    handle,
    input_latin_syllable: str,
    normalize_input_case: bool = True,   # 是否在匹配前统一大小写
    case_insensitive_match: bool = True   # 匹配时是否忽略大小写
):
    result_chars_unicode = []
    char_word_table = get_data(handle)
    # char_word_table = load_syllable_char_table('rawCharWordTable.txt')
    if normalize_input_case == True:
        input_latin_syllable = input_latin_syllable.lower()
    for each_syllable_char_info_line in char_word_table:
        if case_insensitive_match == True:
            if each_syllable_char_info_line[0].lower() == input_latin_syllable.lower():
                result_chars_unicode.append(each_syllable_char_info_line[3])
        else:
            if each_syllable_char_info_line[0] == input_latin_syllable:
                result_chars_unicode.append(each_syllable_char_info_line[3])
    return result_chars_unicode

