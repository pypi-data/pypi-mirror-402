from abc import ABC, abstractmethod

class Evaluator:

    def __init__(self, validator):
        self.validator = validator
        self.evaluation_type = "Default"

    @abstractmethod
    def eval(self, s):
        """Evaluate the given string to validate it."""

    def get_evaluation_type(self):
        return self.evaluation_type