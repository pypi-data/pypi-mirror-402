import re
from .evaluator import Evaluator

class DecimalEvaluator(Evaluator):
    DEC_RE = re.compile(r'^[0-9]+$')

    def __init__(self, validtator):
        super().__init__(validtator)
        self.evaluation_type = "token"

    def eval(self, s):
        spans = []
        offset = 0
        tokens = s.split(" ")

        for tok in tokens:
            start = s.find(tok, offset)
            if start == -1:
                continue
            end = start + len(tok)
            offset = end

            if not DecimalEvaluator.DEC_RE.match(tok):
                continue

            try:
                value = int(tok, 10)
                if 0 <= value <= 255 and self.validator.validate(chr(value)):
                    spans.append([start, end])
            except ValueError:
                continue
        return spans