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

    def test_austrian_variants(self):
        """Test Austrian German variants"""
        test_cases = {
            'zwoa': 2,
            'zwoahundert': 200,  # Austrian compound
            'zwoatausend': 2000,  # Austrian compound
        }
        self.compare_sets(test_cases)

    def test_yet_another_ordinal_edge_case(self):
        words = ['sieben', 'siebte', 'siebten']
        numbers = [7, '7.', '7.']
        self.compare_sets(dict(zip(words, numbers)))

    def test_fractions(self):
        test_cases = {
            'ein und zwei': 0.5,  # Example fraction handling
            'ein und drei': 1/3,
            'zwei und drei': 2/3,
            'ein und vier': 0.25,
            'drei und vier': 0.75,
            'ein und fünf': 0.2,
            'vier und fünf': 0.8,
        }
        self.compare_sets(test_cases)

    def test_extended_fractions(self):
        """Test extended fraction support like 'drei viertel'"""
        test_cases = {
            'ein halb': 0.5,
            'eine halbe': 0.5,
            'ein viertel': 0.25,
            'zwei viertel': 0.5,
            'drei viertel': 0.75,
            'vier viertel': 1.0,
            'ein drittel': 1/3,
            'zwei drittel': 2/3,
            'ein fünftel': 0.2,
            'drei fünftel': 0.6,
            'ein sechstel': 1/6,
            'fünf sechstel': 5/6,
        }
        self.compare_sets(test_cases)

    def test_decimal_numbers(self):
        """Test decimal number support like 'zwei komma fünf'"""
        test_cases = {
            'zwei komma fünf': 2.5,
            'eins komma zwei': 1.2,
            'drei komma null': 3.0,
            'vier komma sieben': 4.7,
            'null komma fünf': 0.5,
            'zehn komma eins': 10.1,
            'hundert komma zwei': 100.2,
            'eintausend komma drei': 1000.3,
        }
        self.compare_sets(test_cases)

    def test_large_scale_numbers(self):
        """Test very large numbers with multiple scales"""
        test_cases = {
            'eine million': 1000000,
            'zwei millionen': 2000000,
            'eine milliarde': 1000000000,
            'zwei milliarden': 2000000000,
            'eine billion': 1000000000000,
            'zwei billionen': 2000000000000,
            'eine billiarde': 1000000000000000,
            'zwei billiarden': 2000000000000000,
            'eine trillion': 1000000000000000000,
            'zwei trillionen': 2000000000000000000,
        }
        self.compare_sets(test_cases)

    def test_complex_combinations(self):
        """Test complex number combinations"""
        test_cases = {
            'einhunderttausend': 100000,
            'zweihunderttausend': 200000,
            'dreihunderttausend': 300000,
            'fünfhunderttausend': 500000,
        }
        self.compare_sets(test_cases)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        test_cases = {
            'null': 0,
            'eins': 1,
            'ein': 1,
            'eine': 1,
            'er': 1,
            'zwei': 2,
            'zwo': 2,
            'hundert': 100,
            'tausend': 1000,
            'einhundert': 100,
            'eintausend': 1000,
            'zehntausend': 10000,
            'einhunderttausend': 100000,
        }
        self.compare_sets(test_cases)

    def test_ordinal_variations(self):
        """Test various ordinal number forms"""
        test_cases = {
            'erste': '1.',
            'zweite': '2.',
            'dritte': '3.',
            'vierte': '4.',
            'fünfte': '5.',
            'siebte': '7.',
            'achte': '8.',
            'neunte': '9.',
            'zehnte': '10.',
            'zwanzigste': '20.',
            'dreißigste': '30.',
            'hundertste': '100.',
        }
        self.compare_sets(test_cases)

    def test_case_insensitivity(self):
        """Test that the converter handles different cases"""
        test_cases = {
            'EIN': 1,
            'Zwei': 2,
            'DREI': 3,
            'Vier': 4,
            'Fünf': 5,
            'ZWEIHUNDERT': 200,
            'tausend': 1000,
        }
        self.compare_sets(test_cases)

    def test_compound_scales(self):
        """Test numbers with multiple scale multipliers"""
        test_cases = {
            'zwei millionen fünfhunderttausend': 2500000,
            'eine milliarde zweihundert millionen': 1200000000,
            'drei billionen vierhundertfünfzig milliarden': 3450000000000,
        }
        self.compare_sets(test_cases)

    def test_whitespace_handling(self):
        """Test handling of extra whitespace"""
        test_cases = {
            '  eins  ': 1,
            'zweiundzwanzig': 22,  # "zwei und zwanzig" without space
            'hundert   ': 100,
            '  tausend': 1000,
        }
        self.compare_sets(test_cases)

    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        invalid_inputs = [
            'invalid',
            'notanumber',
            'xyz123',
        ]
        for invalid_input in invalid_inputs:
            with self.assertRaises(ValueError):
                w2n.convert(invalid_input)

    def compare_sets(self, test_cases):
        for word, expected in test_cases.items():
            self.assertEqual(w2n.convert(word), expected)
