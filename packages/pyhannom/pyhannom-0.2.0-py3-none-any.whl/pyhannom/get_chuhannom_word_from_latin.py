from load_word_table import load_word_table
from data_store import get_data


def get_chuhannom_word_from_latin(
    handle,
    input_latin_syllables: str,
    normalize_input_case: bool = False,   # 是否在匹配前统一大小写
    case_insensitive_match: bool = True   # 匹配时是否忽略大小写
):
    result_word_entry = set()
    # word_entry_list = load_word_table()
    word_entry_list = get_data(handle)
    input_latin_syllables = input_latin_syllables.strip()
    if normalize_input_case == True:
        input_latin_syllables = input_latin_syllables.lower()
    input_latin_syllable_list = input_latin_syllables.split()

    if case_insensitive_match == False:
        for each_word_entry in word_entry_list:
            each_word_entry_check_list = []
            for each_input_latin_syllable in input_latin_syllable_list:
                if each_input_latin_syllable in each_word_entry[1]:
                    each_word_entry_check_list.append(True)
                else:
                    each_word_entry_check_list.append(False)
            if False not in each_word_entry_check_list:
                # print(each_word_entry)
                result_word_entry.add(tuple(each_word_entry))
    if case_insensitive_match == True:
        for each_word_entry in word_entry_list:
            each_word_entry_check_list = []
            for each_input_latin_syllable in input_latin_syllable_list:
                if each_input_latin_syllable.lower() in each_word_entry[1].lower():
                    each_word_entry_check_list.append(True)
                else:
                    each_word_entry_check_list.append(False)
            if False not in each_word_entry_check_list:
                # print(each_word_entry)
                result_word_entry.add(tuple(each_word_entry))
    return result_word_entry

