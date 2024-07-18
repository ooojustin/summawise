
import pygments
from typing import Optional
from whats_that_code.election import guess_language_all_methods
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.lexers import guess_lexer as pygments_guess_lexer
from pygments.lexer import Lexer
from pygments.formatter import Formatter
from pygments.formatters import  Terminal256Formatter
from pygments.util import ClassNotFound

def guess_lexer(code: str) -> Optional[Lexer]:
    language_name = guess_language_all_methods(code)
    if language_name:
        try:
            return get_lexer_by_name(language_name)
        except ClassNotFound:
            pass
    try:
        return pygments_guess_lexer(code)
    except Exception:
        pass

def highlight_code(code: str, lexer: Optional[Lexer] = None, formatter: Optional[Formatter] = None):
    if lexer is None:
        lexer = guess_lexer(code) or TextLexer()
    if formatter is None:
        formatter = Terminal256Formatter()
    highlighted_code = pygments.highlight(code, lexer, formatter)
    return highlighted_code
