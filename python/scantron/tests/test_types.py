import unittest

from scantron.types import Student, Bubble, BUBBLES, Response, Scantron


class TestStudent(unittest.TestCase):
    def test_constructor(self):
        """Test constructor of Student"""
        student = Student(name="WANG        AY", sid="12345678")

        self.assertEqual(student.name, "WANG AY", "Duplicate whitespaces should be removed")
        self.assertEqual(student.sid, "12345678", "SID should be set")

    def test_validity(self):
        """Test is_valid property of Student"""
        valid_student = Student(name="WANG        AY", sid="12345678")
        invalid_students = [Student(name="", sid="12345678"),
                            Student(name="WANG        AY", sid="1245678"),
                            Student(name="WANG        AY", sid=""),
                            Student(name="WANG        AY", sid="123456789"),
                            Student(name='', sid='')]

        self.assertTrue(valid_student.is_valid, f"{valid_student} should be valid")
        for invalid_student in invalid_students:
            self.assertFalse(invalid_student.is_valid, f"{invalid_student} should be invalid.")

    # def test_keys(self):
    #     """Test is_key property of Student"""
    #     key = Student(name='', sid='')
    #     not_key = Student(name='WANG        AY', sid='12345678')
    #
    #     self.assertTrue(key.is_key, f"{key} should be a key")
    #     self.assertFalse(not_key.is_key, f"{not_key} should not be a key")


class TestBubble(unittest.TestCase):
    def test_parse_letter(self):
        """Test parsing of single capital letters"""
        letters = ['A', 'B', 'C', 'D', 'E']

        for letter, bubble in zip(letters, BUBBLES):
            self.assertEqual(Bubble.parse(letter), bubble,
                             f"'{letter}' should be parsed as {bubble}")

    def test_parse_digit(self):
        """Test parsing of single digits"""
        digits = ['1', '2', '3', '4', '5']

        for digit, bubble in zip(digits, BUBBLES):
            self.assertEqual(Bubble.parse(digit), bubble,
                             f"'{digit}' should be parsed as {bubble}")


class TestResponse(unittest.TestCase):
    def test_parse_multiple(self):
        """Test parsing of multiple bubbles)"""
        multiples = ['(2,4,5)', '(1,2,3,5)', '(3,4)', '12', 'ABC', ]
        multiples_responses = [Response(choices=[Bubble.B, Bubble.D, Bubble.E]),
                               Response(choices=[Bubble.A, Bubble.B, Bubble.C, Bubble.E]),
                               Response(choices=[Bubble.C, Bubble.D]),
                               Response(choices=[Bubble.A, Bubble.B]),
                               Response(choices=[Bubble.A, Bubble.B, Bubble.C])]

        for multiple, response in zip(multiples, multiples_responses):
            self.assertEqual(Response.parse(multiple), response, f"'{multiple}' should be parsed as {response}")

    def test_parse_sorting(self):
        """Test parsing of non-sorted bubbles (of digits)"""
        full_multiples = ['(5,1,4,2,3)', '(1,5,3,2,4)', '53214', 'CABDE']

        for multiple in full_multiples:
            self.assertEqual(Response.parse(multiple).bubbles,
                             Response(choices=BUBBLES).bubbles,
                             "Should sort bubbles")


class TestScantron(unittest.TestCase):
    def test_parse(self):
        row = ['B', "WANG        AY", '12345678', '9',
               '1', '2', '3', '4', '5',
               '(5,4,3,2,1)', '(1,2,3,4,5)', 'ABCDE', '12345']

        actual = Scantron.parse(row)
        self.assertEqual(actual,
                         Scantron(
                             student=Student(name="WANG        AY", sid="12345678"),
                             form=Bubble.B,
                             responses=[
                                 Response(choices=[Bubble.A]),
                                 Response(choices=[Bubble.B]),
                                 Response(choices=[Bubble.C]),
                                 Response(choices=[Bubble.D]),
                                 Response(choices=[Bubble.E]),

                                 Response(choices=BUBBLES),
                                 Response(choices=BUBBLES),
                                 Response(choices=BUBBLES),
                                 Response(choices=BUBBLES),
                             ]
                         ),
                         "Should parse row correctly")


if __name__ == '__main__':
    unittest.main()
