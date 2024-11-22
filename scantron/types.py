import re
from dataclasses import dataclass
from enum import Enum
from typing import Final, List, Pattern

SID_REGEX: Final[Pattern] = re.compile(r"^\d{8}$")


class Student:
    _name: str
    _sid: str

    def __init__(self, name: str, sid: str):
        self._name = " ".join(name.strip().split())
        self._sid = sid.strip() # remove leading/trailing whitespace

    @property
    def name(self):
        return self._name

    @property
    def sid(self):
        return self._sid

    @property
    def is_valid(self) -> bool:
        return len(self.name) > 0 and SID_REGEX.match(self.sid) is not None

    def __eq__(self, other):
        return self.name == other.name and self.sid == other.sid

    def __str__(self):
        return f"{self.name} [{self.sid}]"

    def __repr__(self):
        return f"Student(\"{self.name}\", \"{self.sid}\")"


class Bubble(Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'

    @classmethod
    def parse(cls, value: str):
        try:
            if value.isdigit():
                return Bubble(chr(ord('A') + (int(value) - 1)))
        except ValueError:
            error_msg = f"Invalid bubble value: {value}"
            raise ValueError(error_msg)
        return Bubble(value)


BUBBLES = [Bubble.A, Bubble.B, Bubble.C, Bubble.D, Bubble.E]


class Response:
    _bubbles: List[Bubble]

    def __init__(self, choices: List[Bubble]):
        self._bubbles = sorted(choices, key=lambda b: b.value)

    @classmethod
    def parse(cls, value: str):
        return Response(
            choices=list(set([
                Bubble.parse(num)
                for num in re.sub(r'[^\dA-E]', '', value)
            ]))
        )

    @property
    def bubbles(self):
        return self._bubbles

    @property
    def bubble_set(self):
        return set(self.bubbles)

    def __eq__(self, other):
        return self.bubbles == other.bubbles

    def __str__(self):
        return ', '.join(map(str, self.bubbles))

    def __repr__(self):
        return f"Response({self})"


class Scantron:
    _student: Student
    _form: Bubble
    _responses: List[Response]

    def __init__(self, student: Student, form: Bubble, responses: List[Response]):
        self._student = student
        self._form = form
        self._responses = responses

    @classmethod
    def parse(cls, row: List[str]):
        """BNF: scantron ::= form student_id student_name num_questions [responses] """
        num_questions = int(row[3])
        return Scantron(
            student=Student(
                name=row[1],
                sid=row[2],
            ),
            form=Bubble.parse(row[0]),
            responses=[
                Response.parse(bbl_tpl)
                for bbl_tpl in row[4:4 + num_questions]
            ]
        )

    @property
    def student(self):
        return self._student

    @property
    def form(self):
        return self._form

    @property
    def responses(self):
        return self._responses

    def __eq__(self, other):
        print(self.student == other.student)
        return (self.student == other.student
                and self.form == other.form
                and self.responses == other.responses)

    def __str__(self):
        response_lines = "\n".join(map(lambda e: f"Q{1 + e[1]} {e[0]}", enumerate(self.responses)))
        return f"{str(self._student)}:\n{response_lines}"

    def __repr__(self):
        return f"Scantron(\"{self._student}\", {self._responses})"


class RubricItem:
    _correct_response: Response
    _partial_credit: bool

    def __init__(self, correct_response: Response, partial_credit: bool = False):
        self._correct_response = correct_response
        self._partial_credit = partial_credit

    @classmethod
    def parse(cls, value: str):
        """BNF: rubric_item ::= ['P'] response """
        is_partial = value.startswith('P')
        response_str = value[1:] if is_partial else value

        return RubricItem(
            correct_response=Response.parse(response_str),
            partial_credit=is_partial
        )

    @property
    def correct_response(self):
        return self._correct_response

    @property
    def partial_credit(self):
        return self._partial_credit

    def grade(self, response: Response) -> float:
        """For partial credit, use Canvas scoring = clamp((SELECTED_CORRECT - SELECTED_WRONG) / |CORRECT|, [0, 1])"""
        correct_bubbles = self.correct_response.bubble_set
        response_bubbles = response.bubble_set

        if self.partial_credit:
            num_correct = len(correct_bubbles & response_bubbles)
            num_wrong = len(response_bubbles - correct_bubbles)

            score = float(num_correct - num_wrong) / len(correct_bubbles)
            return max(0, score)

        # exact match
        return int(correct_bubbles == response_bubbles)

    def __eq__(self, other):
        return (self.correct_response == other.correct_response
                and self.partial_credit == other.partial_credit)

    def __str__(self):
        return f"{'P' if self.partial_credit else ''}{self.correct_response}"

    def __repr__(self):
        return f"RubricItem({self})"


class Rubric:
    _items: List[RubricItem]
    _points: float
    _extra_credit: bool

    def __init__(self, rubric_items: List[RubricItem], points: float = 1., extra_credit: bool = False):
        self._items = rubric_items
        self._points = points
        self._extra_credit = extra_credit

    @classmethod
    def parse(cls, value: str):
        """
        Examples:
            'A' for 1 point, full credit for A,
            'PAB' for 1 point, partial credit for AB,
            'A E' for 1 point, full credit for A, extra credit,
            '1.5 ABC' for 1.5 point, full credit for ABC,
            '0.5 BCD' for 0.5 points, full credit for BCD,
            '1 PBAC' for 1 point, full credit for ABC with partial credit
            '1 PABC|ABD' for 1 point, ABC with partial credit OR ABD with full credit (whichever yields higher score)

        Grammar:
            rubric_sequence ::= rubric_item ['|' rubric_sequence]
            rubric ::= [points SPACE] rubric_sequence [SPACE 'E']
        """
        parts = value.split()

        extra_credit = parts[-1] == 'E'
        is_points_first = len(parts) == 3 or len(parts) == 2 and not extra_credit
        points = float(parts[0]) if is_points_first else 1.

        items = [RubricItem.parse(item)
                 for item in parts[1 if is_points_first else 0].split('|')]

        return Rubric(
            rubric_items=items,
            points=points,
            extra_credit=extra_credit
        )

    def grade(self, response: Response) -> (float, float):
        """Max score for all items.
        :returns: (points, out_of)"""
        points_earned = self.points * max([item.grade(response) for item in self.items])
        out_of = self.points if not self.extra_credit else 0

        return points_earned, out_of

    @property
    def items(self):
        return self._items

    @property
    def points(self):
        return self._points

    @property
    def extra_credit(self):
        return self._extra_credit

    def __eq__(self, other):
        return (self.items == other.items
                and self.points == other.points
                and self.extra_credit == other.extra_credit)

    def __str__(self):
        return f"({self.points}{'E' if self.extra_credit else ''} pts) {'|'.join(map(str, self.items))}"

    def __repr__(self):
        return f"Rubric({self.points}, {'|'.join(map(str, self.items))}, {self.extra_credit})"


class Key:
    _form: Bubble
    _questions: List[Rubric]

    def __init__(self, form: Bubble, questions: List[Rubric]):
        self._form = form
        self._questions = questions

    @classmethod
    def parse(cls, row: List[str]):
        """BNF: key ::= form 'KEY' '' num_questions [rubrics] """
        num_questions = int(row[3])
        return Key(
            form=Bubble.parse(row[0]),
            questions=[Rubric.parse(rubric) for rubric in row[4:4 + num_questions]]
        )

    def grade(self, scantron: Scantron) -> (float, float):
        """:returns (points, out_of)"""
        assert scantron.form == self.form, \
            f"Cannot grade a Scantron with form {scantron.form} using Key with form {self.form}"
        assert len(scantron.responses) == len(self.questions), \
            f"Cannot grade a Scantron with {len(scantron.responses)} responses using Key with {len(self.questions)} questions"

        scorings = [rubric.grade(response)
                    for rubric, response in zip(self.questions, scantron.responses)]

        # reduce: (p1, o1), (p2, o2) -> (p1 + p2, o1 + o2)
        return tuple(map(sum, zip(*scorings)))

    @property
    def form(self):
        return self._form

    @property
    def questions(self):
        return self._questions

    def __eq__(self, other):
        return (self.form == other.form
                and self.questions == other.questions)

    def __str__(self):
        return (f"==> Key [Form {self.form}]\n"
                "\n".join(map(lambda e: f"\t[Q{e[1]}] {e[0]}", enumerate(self.questions))))

    def __repr__(self):
        return f"Key({self.form}, {len(self.questions)} questions)"


@dataclass
class ScantronGrade:
    student: Student
    form: Bubble
    points: float
    out_of: float

    def __str__(self):
        return f"{self.student} [{self.form}]: {self.points}/{self.out_of}"

    def __repr__(self):
        return f"ScantronGrade({self.points}/{self.out_of})"


class Grader:
    _keys: List[Key] = []

    def __init__(self, keys: List[Key]):
        def add_key(self, key: Key):
            assert key.form not in [k.form for k in self.keys], \
                f"Cannot have multiple keys for form {key.form}"
            self._keys.append(key)

        for key in keys:
            add_key(self, key)

    @property
    def keys(self):
        return self._keys

    def _find_key(self, form: Bubble) -> Key:
        for key in self.keys:
            if key.form == form:
                return key
        assert False, f"Key for form {form} not found"

    def grade(self, scantron: Scantron) -> ScantronGrade:
        """Grades a scantron with the key matching their form"""
        points, out_of = self._find_key(scantron.form).grade(scantron)
        return ScantronGrade(
            student=scantron.student,
            form=scantron.form,
            points=points,
            out_of=out_of
        )

    def grade_all(self, scantrons: List[Scantron]) -> List[ScantronGrade]:
        return [self.grade(scantron) for scantron in scantrons]
