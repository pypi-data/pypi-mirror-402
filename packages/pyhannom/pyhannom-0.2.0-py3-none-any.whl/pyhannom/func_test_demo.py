from load_syllable_char_table import load_syllable_char_table
from get_chuhannom_from_latin import get_chuhannom_from_latin
from get_chuhannom_from_latin import get_chuhannom_unicode_from_latin
from get_latin_from_chuhannom import get_latin_from_chuhannom

from load_word_table import load_word_table
from get_chuhannom_word_from_latin import get_chuhannom_word_from_latin
from get_latin_word_from_chuhannom import get_latin_word_from_chuhannom


hannom_syllable_char_table = load_syllable_char_table()
got_hannom_char = get_chuhannom_from_latin(hannom_syllable_char_table, 'bàn')
got_hannom_unicode = get_chuhannom_unicode_from_latin(hannom_syllable_char_table, 'buộc')
got_latin_syllable = get_latin_from_chuhannom(hannom_syllable_char_table, '心')

hannom_word_table = load_word_table(hannom_syllable_char_table)
got_hannom_word = get_chuhannom_word_from_latin(hannom_word_table, 'hưng hửng')
got_latin_word = get_latin_word_from_chuhannom(hannom_word_table, '汴𠲅')


print(hannom_syllable_char_table)
print(got_hannom_char)
print(got_hannom_unicode)
print(got_latin_syllable)

print(hannom_word_table)
print(got_hannom_word)
print(got_latin_word)