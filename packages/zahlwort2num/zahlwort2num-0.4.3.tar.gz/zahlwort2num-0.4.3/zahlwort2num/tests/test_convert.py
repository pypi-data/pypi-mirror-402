from unittest import TestCase
import zahlwort2num as w2n

class TestConverter(TestCase):

    def test_hardcoded_values_upto_100(self):
        test_cases = {
            'eins': 1, 'zwei': 2, 'zwo': 2, 'drei': 3, 'vier': 4, 'fünf': 5, 'sechs': 6,
            'sieben': 7, 'acht': 8, 'neun': 9, 'zehn': 10, 'elf': 11, 'zwölf': 12,
            'dreizehn': 13, 'vierzehn': 14, 'fünfzehn': 15, 'sechzehn': 16,
            'siebzehn': 17, 'achtzehn': 18, 'neunzehn': 19, 'zwanzig': 20,
            'einundzwanzig': 21, 'zweiundzwanzig': 22, 'dreiundzwanzig': 23,
            'vierundzwanzig': 24, 'fünfundzwanzig': 25, 'sechsundzwanzig': 26,
            'siebenundzwanzig': 27, 'achtundzwanzig': 28, 'neunundzwanzig': 29,
            'dreißig': 30, 'einunddreißig': 31, 'zweiunddreißig': 32, 'dreiunddreißig': 33,
            'vierunddreißig': 34, 'fünfunddreißig': 35, 'sechsunddreißig': 36,
            'siebenunddreißig': 37, 'achtunddreißig': 38, 'neununddreißig': 39,
            'vierzig': 40, 'einundvierzig': 41, 'zweiundvierzig': 42, 'dreiundvierzig': 43,
            'vierundvierzig': 44, 'fünfundvierzig': 45, 'sechsundvierzig': 46,
            'siebenundvierzig': 47, 'achtundvierzig': 48, 'neunundvierzig': 49,
            'fünfzig': 50, 'einundfünfzig': 51, 'zweiundfünfzig': 52, 'dreiundfünfzig': 53,
            'vierundfünfzig': 54, 'fünfundfünfzig': 55, 'sechsundfünfzig': 56,
            'siebenundfünfzig': 57, 'achtundfünfzig': 58, 'neunundfünfzig': 59,
            'sechzig': 60, 'einundsechzig': 61, 'zweiundsechzig': 62, 'dreiundsechzig': 63,
            'vierundsechzig': 64, 'fünfundsechzig': 65, 'sechsundsechzig': 66,
            'siebenundsechzig': 67, 'achtundsechzig': 68, 'neunundsechzig': 69,
            'siebzig': 70, 'einundsiebzig': 71, 'zweiundsiebzig': 72, 'dreiundsiebzig': 73,
            'vierundsiebzig': 74, 'fünfundsiebzig': 75, 'sechsundsiebzig': 76,
            'siebenundsiebzig': 77, 'achtundsiebzig': 78, 'neunundsiebzig': 79,
            'achtzig': 80, 'einundachtzig': 81, 'zweiundachtzig': 82, 'dreiundachtzig': 83,
            'vierundachtzig': 84, 'fünfundachtzig': 85, 'sechsundachtzig': 86,
            'siebenundachtzig': 87, 'achtundachtzig': 88, 'neunundachtzig': 89,
            'neunzig': 90, 'einundneunzig': 91, 'zweiundneunzig': 92, 'dreiundneunzig': 93,
            'vierundneunzig': 94, 'fünfundneunzig': 95, 'sechsundneunzig': 96,
            'siebenundneunzig': 97, 'achtundneunzig': 98, 'einhundert': 100
        }
        self.compare_sets(test_cases)

    def test_bugs_found_by_users(self):
        test_cases = {
            'hundertdreiundzwanzig': 123,
            'hundert': 100,
            'tausend': 1000
        }
        self.compare_sets(test_cases)

    def test_more_specific(self):
        words = [
            'sieben', 'neunundneunzig', 'eintausend', 'zweihunderttausend',
            'fünfundvierzighundertvier', 'fünfundvierzighundertelf',
            'zweihundertfünfundzwanzig', 'dreitausendsechshundertfünfundzwanzig',
            'zwölftausendachthundertvierundfünfzig',
            'sechshundertdreiundfünfzigtausendfünfhunderteinundzwanzig',
            'neunundneunzig', 'fünfhunderttausendzwei', 'eine million viertausend',
            'siebenhundert trillion neun milliarde eine million neuntausendeins',
            'neun quadrilliarde elf', 'zwei milliarden', 'eintausend', 'null',
            'neunundvierzig', 'zwohundertzwoundzwanzig', 'zwotausend'
        ]
        numbers = [
            7, 99, 1000, 200000, 4504, 4511, 225, 3625, 12854, 653521, 99, 500002,
            1004000, 700000000009001009001, 9000000000000000000000000011, 2000000000,
            1000, 0, 49, 222, 2000
        ]
        self.compare_sets(dict(zip(words, numbers)))

    def test_ordinal_numbers(self):
        words = ['vierundzwanzigstem', 'siebzigste', 'siebte', 'neunte', 'erste', 'zwanzigste']
        numbers = ['24.', '70.', '7.', '9.', '1.', '20.']
        self.compare_sets(dict(zip(words, numbers)))

    def test_negative_values(self):
        words = [
            'minus eine million', 'minus dreizehn',
            'minus siebenhundert millionen achtundsiebzig', 'minus elf'
        ]
        numbers = [-1000000, -13, -700000078, -11]
        self.compare_sets(dict(zip(words, numbers)))

    def test_negative_with_ordinal(self):
        words = ['minus erste', 'minus zweiundneunzigstem']
        numbers = ['-1.', '-92.']
        self.compare_sets(dict(zip(words, numbers)))

    def test_swiss_variant(self):
        test_cases = {'dreissig': 30}
        self.compare_sets(test_cases)

    def test_yet_another_ordinal_edge_case(self):
        words = ['sieben', 'siebte', 'siebten']
        numbers = [7, '7.', '7.']
        self.compare_sets(dict(zip(words, numbers)))

    def test_fractions(self):
        test_cases = {
            'ein und zwei': 0.5,  # Example fraction handling
        }
        self.compare_sets(test_cases)

    def compare_sets(self, test_cases):
        for word, expected in test_cases.items():
            self.assertEqual(w2n.convert(word), expected)
