import unittest
from midiparse import *

class MidiparseTests(unittest.TestCase):

    def test_find_intervals_of_silence(self):
        test_seq1 = [Note(0, 0, 10, 0), 
                     Note(0, 10, 15, 0),
                     Note(0, 16, 20, 0)]

        test_seq2 = [Note(0, 0, 10, 0), 
                     Note(0, 13, 15, 0),
                     Note(0, 17, 20, 0)]

        test_seq3 = [Note(0, 0, 10, 0), 
                     Note(0, 10, 15, 0),
                     Note(0, 15, 20, 0)]

        exp_silent1 = [(15, 16)]
        exp_non_silent1 = [(0, 15), (16, 20)]

        exp_silent2 = [(10, 13), (15, 17)]
        exp_non_silent2 = [(0, 10), (13, 15), (17, 20)]

        exp_silent3 = []
        exp_non_silent3 = [(0, 20)]
        
        res_silent1, res_non_silent1 = find_intervals_of_silence(test_seq1)
        res_silent2, res_non_silent2 = find_intervals_of_silence(test_seq2)
        res_silent3, res_non_silent3 = find_intervals_of_silence(test_seq3)

        self.assertListEqual(res_silent1, exp_silent1)
        self.assertListEqual(res_silent2, exp_silent2)
        self.assertListEqual(res_silent3, exp_silent3)

        self.assertListEqual(res_non_silent1, exp_non_silent1)
        self.assertListEqual(res_non_silent2, exp_non_silent2)
        self.assertListEqual(res_non_silent3, exp_non_silent3)

