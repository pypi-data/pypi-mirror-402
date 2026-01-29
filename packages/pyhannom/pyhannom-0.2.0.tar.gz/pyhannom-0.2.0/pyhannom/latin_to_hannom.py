# from load_hannom_table import load_hannom_table

class latin_to_hannom_result:
    def __init__(self, char_lookup, unicode_lookup, char_entry_lookup,
                 word_lookup, word_entry_lookup,
                 hannom_converter, latin_converter):
        # 这里存储真实的数据，供程序调用
        self.char_lookup = char_lookup
        self.unicode_lookup = unicode_lookup
        self.char_entry_lookup = char_entry_lookup
        self.word_lookup = word_lookup
        self.word_entry_lookup = word_entry_lookup
        self.hannom_converter = hannom_converter
        self.latin_converter = latin_converter

    def __str__(self):
        # 当你调用 print(result) 时，显示你精心设计的排版
        return (
            f"CHAR LEVEL: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.char_lookup}\n"
            f"CHAR LEVEL UNICODE: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.unicode_lookup}\n"
            f"CHAR LEVEL ENTRY: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.char_entry_lookup}\n"
            f"WORD LEVEL: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.word_lookup}\n"
            f"WORD LEVEL ENTRY: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n"
            f"{self.word_entry_lookup}\n"
            f"HANNOM: 工具轉字自𡨸國語𨖅𡨸漢喃 Công cụ chuyển tự từ chữ Quốc ngữ sang chữ Hán Nôm:\n"
            f"{self.hannom_converter}\n"
            f"LATIN: 工具轉字自𡨸國語𨖅𡨸漢喃 Công cụ chuyển tự từ chữ Quốc ngữ sang chữ Hán Nôm:\n"
            f"{self.latin_converter}\n"
        )


def GJCJZHNZ_example_process(input_example):
    if input_example != '':
        hannom_latinnote = input_example.split(' ', 1)
        latinnote = hannom_latinnote[-1]
        latin_note = latinnote.rsplit(' [', 1)
        trans_table = str.maketrans({'-': '- ', '(': '( '})
        latin_part = ' '+latin_note[0].translate(trans_table)
        latin_part = latin_part.replace('\xa0', ' ').replace('...', '... ')
        if len(latin_note) > 1:
            hannom_latin_note = [hannom_latinnote[0], latin_part, '['+latin_note[1]]
        elif len(latin_note) == 1:
            hannom_latin_note = [hannom_latinnote[0], latin_part]
        # print(hannom_latin_note)
        return hannom_latin_note

def match_filter(input_latin, ini_match_hannom_list, ini_match_latin_list, uncased):
    if uncased:
        input_latin = input_latin.lower()
    input_len = len(input_latin.split())
    filter_hannom_list = []
    filter_latin_list = []
    ini_match_list_len = len(ini_match_latin_list)
    for i in range(ini_match_list_len):
        if input_latin == ini_match_latin_list[i]:
            filter_hannom_list.append(ini_match_hannom_list[i])
            filter_latin_list.append(ini_match_latin_list[i])
    return (filter_hannom_list, filter_latin_list)


def latin_to_hannom(combined_handle, latin, uncased=True,
                    precise_match = True):
    GJCJZHNZ_handle = combined_handle[0]
    CVTMPDAT_handle = combined_handle[1]
    latin = latin.strip()
    #print(latin.split())

    # Converter_mapping_data.JS_SyllableChar_Part
    cvtmpdat_only_chars_list = []
    cvtmpdat_only_chars_latin_list = []
    if uncased:
        for each_item in CVTMPDAT_handle:
            if latin.lower() in each_item[0].lower():
                mapDataChars = each_item[1]
                current_map_char_list = mapDataChars.replace('【','').replace('】','').split('/')
                cvtmpdat_only_chars_list = cvtmpdat_only_chars_list + current_map_char_list
                for k in range(len(current_map_char_list)):
                    cvtmpdat_only_chars_latin_list.append(each_item[0].lower())
                #print(cvtmpdat_only_chars_list)
    else:
        for each_item in CVTMPDAT_handle:
            if latin in each_item[0]:
                mapDataChars = each_item[1]
                current_map_char_list = mapDataChars.replace('【', '').replace('】', '').split('/')
                cvtmpdat_only_chars_list = cvtmpdat_only_chars_list + current_map_char_list
                for k in range(len(current_map_char_list)):
                    cvtmpdat_only_chars_latin_list.append(each_item[0])
                #print(cvtmpdat_only_chars_list)
    # Converter_mapping_data.JS_SyllableChar_Part

    # GungJyuChaJiouZiiHanNanZhuen_Word_Part
    only_words_list = []
    word_lv_entries_list = []
    if uncased:
        latins = latin.lower().split()
        space_latins = []
        for each_syllable in latins:
            space_latins.append(' ' + each_syllable)
        for each_item in GJCJZHNZ_handle:
            for each_example in each_item.examples.split(' · '):
                each_example = each_example.strip()
                if each_example == '':
                    continue
                each_example = each_example.lower()
                processed_splitted_example = GJCJZHNZ_example_process(each_example)
                #print(processed_splitted_example)
                example_hannom_part = processed_splitted_example[0]
                example_latin_part = processed_splitted_example[1]
                #example_note_part = processed_splitted_example[2]
                if all(sub in example_latin_part for sub in space_latins) and len(space_latins)>1:
                    #print(example_hannom_part)
                    only_words_list.append(example_hannom_part)
                    word_lv_entries_list.append(each_item)
                    #print(example_note_part)
    else:
        latins = latin.split()
        space_latins = []
        for each_syllable in latins:
            space_latins.append(' ' + each_syllable)
        for each_item in GJCJZHNZ_handle:
            for each_example in each_item.examples.split(' · '):
                each_example = each_example.strip()
                if each_example == '':
                    continue
                processed_splitted_example = GJCJZHNZ_example_process(each_example)
                #print(processed_splitted_example)
                example_hannom_part = processed_splitted_example[0]
                example_latin_part = processed_splitted_example[1]
                #example_note_part = processed_splitted_example[2]
                if all(sub in example_latin_part for sub in space_latins) and len(space_latins)>1:
                    #print(example_hannom_part)
                    only_words_list.append(example_hannom_part)
                    word_lv_entries_list.append(each_item)
                    #print(example_note_part)
    # GungJyuChaJiouZiiHanNanZhuen_Word_Part

    # GungJyuChaJiouZiiHanNanZhuen_SyllableChar_Part
    only_chars_list = []
    chars_unicode_list = []
    entries_list = []
    if uncased:
        for each_item in GJCJZHNZ_handle:
            if latin.lower() == each_item.latin.lower():
                only_chars_list.append(each_item.hannom)
                entries_list.append(each_item)
                chars_unicode_list.append('U+' + each_item.note.split('U+', 1)[-1])
                #print(each_item)
    else:
        for each_item in GJCJZHNZ_handle:
            if latin == each_item.latin:
                only_chars_list.append(each_item.hannom)
                entries_list.append(each_item)
                chars_unicode_list.append('U+' + each_item.note.split('U+', 1)[-1])
                #print(each_item)
        # only_chars_list.append('🀁☯👘🖌🐉🏯')
        # only_chars_list = only_chars_list + cvtmpdat_only_chars_list
        # return (only_chars_list, entries_list)
    # GungJyuChaJiouZiiHanNanZhuen_SyllableChar_Part
    # print(len(cvtmpdat_only_chars_list))
    # print(len(cvtmpdat_only_chars_latin_list))
    if precise_match == True:
        cvtmpdat_only_chars_list, cvtmpdat_only_chars_latin_list = match_filter(latin, cvtmpdat_only_chars_list, cvtmpdat_only_chars_latin_list, uncased)

    return latin_to_hannom_result(
        only_chars_list,
        chars_unicode_list,
        entries_list,
        only_words_list,
        word_lv_entries_list,
        cvtmpdat_only_chars_list,
        cvtmpdat_only_chars_latin_list
    )
    # print('GJCJZHNZ char level list:')
    # print(only_chars_list)
    # print('GJCJZHNZ char level entries:')
    # print(entries_list)
    #
    # print('GJCJZHNZ word level list:')
    # print(only_words_list)
    # print('GJCJZHNZ word level entries:')
    # print(word_lv_entries_list)
    #
    # print('CVTMPDAT list:')
    # print(cvtmpdat_only_chars_list)


    # return f"CHAR LEVEL: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n" \
    #        f"{only_chars_list}\n" \
    #        f"CHAR LEVEL UNICODE: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n" \
    #        f"{chars_unicode_list}\n" \
    #        f"CHAR LEVEL METADATA: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n" \
    #        f"{entries_list}\n" \
    #        f"WORD LEVEL: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n" \
    #        f"{only_words_list}\n" \
    #        f"WORD LEVEL METADATA: 工具查究𡨸漢喃準 Công Cụ Tra Cứu Chữ Hán Nôm Chuẩn:\n" \
    #        f"{word_lv_entries_list}\n" \
    #        f"HANNOM: 工具轉字自𡨸國語𨖅𡨸漢喃 Công cụ chuyển tự từ chữ Quốc ngữ sang chữ Hán Nôm:\n" \
    #        f"{cvtmpdat_only_chars_list}\n" \
    #        f"LATIN: 工具轉字自𡨸國語𨖅𡨸漢喃 Công cụ chuyển tự từ chữ Quốc ngữ sang chữ Hán Nôm:\n" \
    #        f"{cvtmpdat_only_chars_latin_list}\n" \

    # return (only_chars_list, chars_unicode_list, entries_list, only_words_list, word_lv_entries_list, cvtmpdat_only_chars_list, cvtmpdat_only_chars_latin_list)


    # if syllablechar_word == 1:
    #     only_words_list = []
    #     entries_list = []
    #     if uncased:
    #         latin = latin.lower()
    #         latins = latin.split()
    #         for each_item in GJCJZHNZ_handle:
    #             str_lower_examples = each_item.examples.lower()
    #             examples = str_lower_examples.split(' · ')
    #             for each_example_pair in examples:
    #                 if all(sub in each_example_pair for sub in latins):
    #                     #print(each_example_pair)
    #                     only_words_list.append(each_example_pair)
    #                     entries_list.append(each_item)
    #     else:
    #         latins = latin.split()
    #         for each_item in GJCJZHNZ_handle:
    #             examples = each_item.examples.split(' · ')
    #             for each_example_pair in examples:
    #                 if all(sub in each_example_pair for sub in latins):
    #                     #print(each_example_pair)
    #                     only_words_list.append(each_example_pair)
    #                     entries_list.append(each_item)
    #     return (only_words_list, entries_list)


# hannom_table = load_hannom_table()
# result = latin_to_hannom(hannom_table, 'châu á', uncased=True, precise_match=True)
# print(result)
#
# my_chars = result.char_lookup
# my_unicodes = result.unicode_lookup
#
# print(my_chars)
# print(my_unicodes)
#
# print('GJCJZHNZ char level list:')
# print(result[0])
# print('GJCJZHNZ char unicode list:')
# print(result[1])
# print('GJCJZHNZ char level entries:')
# print(result[2])
#
# print('GJCJZHNZ word level list:')
# print(result[3])
# print('GJCJZHNZ word level entries:')
# print(result[4])
#
# print('CVTMPDAT hannom list:')
# print(result[5])
# print('CVTMPDAT latin list:')
# print(result[6])
