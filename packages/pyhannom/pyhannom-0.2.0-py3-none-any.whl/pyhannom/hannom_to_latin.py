# from load_hannom_table import load_hannom_table

class hannom_to_latin_result:
    def __init__(self, char_lookup, char_entry_lookup,
                 word_lookup, word_entry_lookup,
                 latin_converter, hannom_converter):
        # 这里存储真实的数据，供程序调用
        self.char_lookup = char_lookup
        self.char_entry_lookup = char_entry_lookup
        self.word_lookup = word_lookup
        self.word_entry_lookup = word_entry_lookup
        self.latin_converter = latin_converter
        self.hannom_converter = hannom_converter

    def __str__(self):
        # 当你调用 print(result) 时，显示你精心设计的排版
        return (
            f"CHAR LEVEL: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.char_lookup}\n"
            f"CHAR LEVEL ENTRY: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.char_entry_lookup}\n"
            f"WORD LEVEL: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.word_lookup}\n"
            f"WORD LEVEL ENTRY: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.word_entry_lookup}\n"
            f"LATIN: 工具轉字自𡨸國語𨖅𡨸漢喃 Công cụ chuyển tự từ chữ Quốc ngữ sang chữ Hán Nôm:\n"
            f"{self.latin_converter}\n"
            f"HANNOM: 工具轉字自𡨸國語𨖅𡨸漢喃 Công cụ chuyển tự từ chữ Quốc ngữ sang chữ Hán Nôm:\n"
            f"{self.hannom_converter}\n"
        )


def GJCJZHNZ_example_process(input_example):
    if input_example != '':
        hannom_latinnote = input_example.split(' ', 1)
        latinnote = hannom_latinnote[-1]
        latin_note = latinnote.rsplit(' [', 1)
        trans_table = str.maketrans({'-': '- ', '(': '( '})
        latin_part = ' '+latin_note[0].translate(trans_table)
        latin_part = latin_part.replace('\xa0', ' ').replace('...', '... ')
        latin_part_for_return = latin_note[0].replace('\xa0', ' ')
        if len(latin_note) > 1:
            hannom_latin_note = [hannom_latinnote[0], latin_part_for_return, '['+latin_note[1]]
        elif len(latin_note) == 1:
            hannom_latin_note = [hannom_latinnote[0], latin_part_for_return]
        # print(hannom_latin_note)
        return hannom_latin_note

def match_filter(input_hannom, ini_match_latin_list, ini_match_hannom_list):
    input_len = len(input_hannom)
    filter_latin_list = []
    filter_hannom_list = []
    ini_match_list_len = len(ini_match_hannom_list)
    for i in range(ini_match_list_len):
        if len(ini_match_hannom_list[i]) == input_len:
            filter_latin_list.append(ini_match_latin_list[i])
            filter_hannom_list.append(ini_match_hannom_list[i])
    return (filter_latin_list, filter_hannom_list)


def hannom_to_latin(combined_handle, hannom,
                    uncased=True, precise_match = True):
    GJCJZHNZ_handle = combined_handle[0]
    CVTMPDAT_handle = combined_handle[1]
    hannom = hannom.strip()

    # GungJyuChaJiouZiiHanNanZhuen_SyllableChar_Part
    only_chars_list = []
    entries_list = []
    for each_item in GJCJZHNZ_handle:
        if hannom in each_item.hannom:
            if uncased:
                only_chars_list.append(each_item.latin.lower())
            else:
                only_chars_list.append(each_item.latin)
            entries_list.append(each_item)
            #print(each_item)
    #return (only_chars_list, entries_list)
    # GungJyuChaJiouZiiHanNanZhuen_SyllableChar_Part

    # GungJyuChaJiouZiiHanNanZhuen_Word_Part
    only_words_list = []
    word_lv_entries_list = []
    for each_item in GJCJZHNZ_handle:
        examples = each_item.examples.split(' · ')
        for each_example_pair in examples:
            each_example_pair = each_example_pair.strip()
            if each_example_pair == '':
                continue
            hannom_part = GJCJZHNZ_example_process(each_example_pair)[0]
            if hannom in hannom_part and len(hannom) > 1:
                #print(each_example_pair)
                correspd_latin_pair = GJCJZHNZ_example_process(each_example_pair)[1]
                if uncased:
                    only_words_list.append(correspd_latin_pair.lower())
                else:
                    only_words_list.append(correspd_latin_pair)
                word_lv_entries_list.append(each_item)
        #return (only_words_list, entries_list)
    # GungJyuChaJiouZiiHanNanZhuen_Word_Part

    # Converter_mapping_data.JS_SyllableChar_Part
    cvtmpdat_only_chars_list = []
    cvtmpdat_only_chars_hannom_list = []
    for each_item in CVTMPDAT_handle:
        each_item_hannom_lists = each_item[1].replace('【', '').replace('】', '').split('/')
        # print(each_item_hannom_lists)
        for each_item_each_hannom in each_item_hannom_lists:
        #all(hannom in each_item_each_hannom for each_item_each_hannom in each_item_hannom_lists)
            if hannom in each_item_each_hannom:
                correspd_latin = each_item[0]
                if uncased:
                    cvtmpdat_only_chars_list.append(correspd_latin.lower())
                    cvtmpdat_only_chars_hannom_list.append(each_item_each_hannom)
                else:
                    cvtmpdat_only_chars_list.append(correspd_latin)
                    cvtmpdat_only_chars_hannom_list.append(each_item_each_hannom)
                # print(cvtmpdat_only_chars_list)
    # Converter_mapping_data.JS_SyllableChar_Part
    # print(len(cvtmpdat_only_chars_list))
    # print(len(cvtmpdat_only_chars_hannom_list))
    if precise_match == True:
        cvtmpdat_only_chars_list, cvtmpdat_only_chars_hannom_list = match_filter(hannom, cvtmpdat_only_chars_list, cvtmpdat_only_chars_hannom_list)

    return hannom_to_latin_result(
        only_chars_list,
        entries_list,
        only_words_list,
        word_lv_entries_list,
        cvtmpdat_only_chars_list,
        cvtmpdat_only_chars_hannom_list
    )
    #return (only_chars_list, entries_list, only_words_list, word_lv_entries_list, cvtmpdat_only_chars_list, cvtmpdat_only_chars_hannom_list)

# hannom_table = load_hannom_table()
# result = hannom_to_latin(hannom_table, '洲亞', precise_match=True)
# print(result.latin_converter)
#
# my_lookup_char = result.char_lookup
# my_converter_result = result.hannom_converter
#
# print(my_lookup_char)
# print(my_converter_result)
# hannom_table = load_hannom_table()
# result = hannom_to_latin(hannom_table, '人', precise_match = True)
#
# print('GJCJZHNZ char level list:')
# print(result[0])
# print('GJCJZHNZ char level entries:')
# print(result[1])
#
# print('GJCJZHNZ word level list:')
# print(result[2])
# print('GJCJZHNZ word level entries:')
# print(result[3])
#
# print('CVTMPDAT latin list:')
# print(result[4])
# print('CVTMPDAT hannom list:')
# print(result[5])