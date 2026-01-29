import re
from .evaluator import Evaluator

class HexadecimalEvaluator(Evaluator):

    HEX_RE = re.compile(r'^[0-9a-fA-F]{2}$')
    HEX_BYTE_CHAR_WIDTH = 2

    def __init__(self, validtator):
        super().__init__(validtator)
        self.evaluation_type = "block"

    def eval(self, s):
        hits = [False] * len(s)
        cleaned = s.replace(" ", "")

        for i in range(len(cleaned) - 1):
            pair = cleaned[i:i+2]

            if not HexadecimalEvaluator.HEX_RE.match(pair):
                continue

            try:
                byte = int(pair, 16)
                char = chr(byte)

                if self.validator.validate(char):
                    hits[i] = True
                    hits[i + 1] = True
            except ValueError:
                continue

        return [hit for hit in hits if hit == True]
