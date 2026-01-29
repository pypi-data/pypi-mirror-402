import re

class Validator:

    def __init__(self, pattern):
        self.pattern = pattern

        try:
            self.regexp = re.compile(self.pattern)
        except Exception:
            raise Exception(f"The provided character_set_regex {pattern} could not be parsed as a regex pattern.")

    def validate(self, s):
        try:
            return re.match(self.pattern, s) is not None
        except Exception:
            return False
