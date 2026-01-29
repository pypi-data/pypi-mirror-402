import base64
import re
from .evaluator import Evaluator

class Base64Evaluator(Evaluator):

    B64_RE = re.compile(r'^[A-Za-z0-9+/]{4}$')

    def __init__(self, validtator):
        super().__init__(validtator)
        self.evaluation_type = "block"

    def eval(self, s):
        hits = [False] * len(s)

        for i in range(len(s) - 3):
            quad = s[i:i+4]

            if not Base64Evaluator.B64_RE.match(quad):
                continue

            try:
                bin_bytes = base64.b64decode(quad, validate=True)

                if len(bin_bytes) != 3:
                    continue

                ok = True
                for b in bin_bytes:
                    char = bytes([b]).decode("latin-1")
                    if not self.validator.validate(char):
                        ok = False
                        break
                if ok == True:
                    for j in range(i, i + 4):
                        hits[j] = True

            except (ValueError, base64.binascii.Error):
                continue

        return [hit for hit in hits if hit == True]