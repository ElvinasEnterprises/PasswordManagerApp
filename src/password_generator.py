import secrets
import string


class PasswordGenerator:
    """Generates random passwords"""

    LOWER = string.ascii_lowercase
    UPPER = string.ascii_uppercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()-_=+[];:,.?<>"

    def __init__(self, use_lower=True, use_upper=True, use_digits=True, use_symbols=True):
        self._use_lower = use_lower
        self._use_upper = use_upper
        self._use_digits = use_digits
        self._use_symbols = use_symbols

        if not any([self._use_lower, self._use_upper, self._use_digits, self._use_symbols]):
            raise ValueError("at least one character set must be enabled")

    def _alphabet(self) -> str:
        alphabet = ""
        if self._use_lower:
            alphabet += self.LOWER
        if self._use_digits:
            alphabet += self.DIGITS
        if self._use_upper:
            alphabet += self.UPPER
        if self._use_symbols:
            alphabet += self.SYMBOLS
        return alphabet
    
    def generate(self, length: int = 16) -> str:
        if length < 12:
            raise ValueError("length must be at least 12")
        
        alphabet = self._alphabet()

        return "".join(secrets.choice(alphabet) for _ in range(length))

        
        