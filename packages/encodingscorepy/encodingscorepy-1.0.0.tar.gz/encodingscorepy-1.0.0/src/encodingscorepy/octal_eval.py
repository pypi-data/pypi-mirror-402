import re
from evaluator import Evaluator

class OctalEvaluator(Evaluator):
    OCT_RE = re.compile(r'^[0-7]+$')

    def __init__(self, validtator):
        super().__init__(validtator)
        self.evaluation_type = "token"

    @staticmethod
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

            if not OctalEvaluator.OCT_RE.match(tok):
                continue

            try:
                value = int(tok, 8)
                if 0 <= value <= 255 and self.validator.validate(chr(value)):
                    spans.append([start, end])
            except ValueError:
                continue

        return spans