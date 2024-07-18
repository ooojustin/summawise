from typing import List
from prompt_toolkit.document import Document
from prompt_toolkit.validation import Validator, ValidationError

class NumericChoiceValidator(Validator):

    def __init__(self, valid_choices: List[int]):
        self.valid_choices = valid_choices

    def validate(self, document: Document):
        try:
            value = int(document.text)
            if value not in self.valid_choices:
                raise ValidationError(
                    message="That number isn't a valid choice.",
                    cursor_position=len(document.text)
                )
        except ValueError:
            raise ValidationError(
                message="Input the number corresponding with your choice.",
                cursor_position=len(document.text)
            )

class ChoiceValidator(Validator):

    def __init__(self, valid_choices: List[str], allow_empty: bool = False):
        self.valid_choices = valid_choices
        if allow_empty:
            self.valid_choices.append("")

    def validate(self, document: Document):
        choice = document.text # input as a string
        if choice not in self.valid_choices:
            raise ValidationError(
                message = "The choice you have input is invalid.",
                cursor_position = len(document.text)
            )

