from load_hannom_table import load_hannom_table
from latin_to_hannom import latin_to_hannom
from hannom_to_latin import hannom_to_latin
from load_parallel_corpus import load_parallel_corpus

hannom_table = load_hannom_table()

lt2hn_result = latin_to_hannom(hannom_table, 'ách', uncased=True, precise_match=True)
print(lt2hn_result.unicode_lookup)

hn2lt_result = hannom_to_latin(hannom_table, '心', uncased=True, precise_match=True)
print(hn2lt_result)

parallel_corpus = load_parallel_corpus()
print(parallel_corpus)