from load_word_table import load_word_table
from data_store import get_data


def get_latin_word_from_chuhannom(
    handle,
    input_chuhannom: str,
    normalize_output_case: bool = False
):
    result_latin_words = set()
    # word_entry_list = load_word_table()
    word_entry_list = get_data(handle)
    input_chuhannom = input_chuhannom.strip()
    for each_word_entry in word_entry_list:
        if input_chuhannom in each_word_entry[0]:
            if normalize_output_case == False:
                result_latin_words.add(tuple(each_word_entry))
            if normalize_output_case == True:
                result_latin_words.add(tuple([each_word_entry[0], each_word_entry[1].lower()]))
    return result_latin_words

