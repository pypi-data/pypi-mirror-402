import re
from .validation import Validator
from .evaluator_factory import EvaluatorFactory

SUPPORTED_ENCODINGS = [
    "base64",
    "hexadecimal",
    "octal",
    "decimal"
]

class EncodingScorer:

    def __init__(self, encoding, character_set_regex="[A-Za-z0-9\s.,!?]"):
        self.encoding = encoding
        self.character_set_regex = character_set_regex

        if not self.is_valid_encoding():
            raise Exception(f"Invalid encoding provided: {encoding}. Must be one of: {SUPPORTED_ENCODINGS}")

        self.validator = Validator(character_set_regex)

    def is_valid_encoding(self):
        return self.encoding in SUPPORTED_ENCODINGS

    def score(self, s):
        evaluator = EvaluatorFactory.get_evaluator(self.encoding, self.validator)
        return self._score_counter(s, evaluator)

    def _score_counter(self, s, evaluator):
        hits = evaluator.eval(s)
        total = len(s.split(" ")) if evaluator.get_evaluation_type() == "token" else len(s)
        print(len(hits))
        return len(hits) / total