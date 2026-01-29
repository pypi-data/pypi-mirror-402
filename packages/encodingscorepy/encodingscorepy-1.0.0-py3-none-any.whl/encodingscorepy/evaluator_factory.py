from base64_eval import Base64Evaluator
from hexadecimal_eval import HexadecimalEvaluator
from octal_eval import OctalEvaluator
from decimal_eval import DecimalEvaluator

class EvaluatorFactory:

    @staticmethod
    def get_evaluator(encoding, validator):
            if encoding == "base64":
                return Base64Evaluator(validator)
            elif encoding == "hexadecimal":
                return HexadecimalEvaluator(validator)
            elif encoding == "octal":
                return OctalEvaluator(validator)
            elif encoding == "decimal":
                return DecimalEvaluator(validator)
            else:
                raise Exception(f"Unsupported encoding: {encoding}")