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

    def __init__(
        self, 
        choices: List[str],
        is_blacklist: bool = False,
        allow_empty: bool = False,
        case_sensitive: bool = True,
        invalid_message: str = "The choice you have input is invalid."
    ):
        self.choices = choices
        self.is_blacklist = is_blacklist
        self.case_sensitive = case_sensitive
        self.invalid_message = invalid_message

        if allow_empty:
            self.choices.remove("") if is_blacklist else self.choices.append("")

        if not case_sensitive:
            self.choices = [c.lower() for c in self.choices]

    def validate(self, document: Document):
        choice = document.text if self.case_sensitive else document.text.lower() # input as a string
        valid = choice not in self.choices if self.is_blacklist else choice in self.choices
        if not valid:
            raise ValidationError(
                message = self.invalid_message,
                cursor_position = len(document.text)
            )

