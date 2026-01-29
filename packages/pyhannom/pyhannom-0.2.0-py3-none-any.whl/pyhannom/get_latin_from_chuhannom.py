from load_syllable_char_table import load_syllable_char_table
from data_store import get_data

def get_latin_from_chuhannom(handle, input_chuhannom: str, normalize_output_case: bool = False):
    result_latin_syllables = []
    # char_word_table = load_syllable_char_table('rawCharWordTable.txt')
    char_word_table = get_data(handle)
    input_chuhannom = input_chuhannom.strip()
    for each_syllable_char_info_line in char_word_table:
        if input_chuhannom in each_syllable_char_info_line[1]:
            if normalize_output_case == False:
                result_latin_syllables.append(each_syllable_char_info_line[0])
            else:
                result_latin_syllables.append(each_syllable_char_info_line[0].lower())
    return result_latin_syllables
