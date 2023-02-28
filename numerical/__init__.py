"""
Positional numeral systems.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Dict, Iterable, Optional, Union, Tuple, cast

from math import isfinite, ceil, floor
from fractions import Fraction
from numbers import Integral
from decimal import Decimal

from functools import cache, wraps
from abc import abstractmethod
from collections import deque
import re

if TYPE_CHECKING:
    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self


__version__ = '0.0.1.dev0'
__all__ = [
    'Numerical',
    'Bengali',
    'Devanagari',
    'Duodecimal',
    'DuodecimalTE',
    'DuodecimalXE',
    'DuodecimalXZ',
    'DuodecimalTurned',
    'Quaternary',
    'Quinary',
    'Senary',
    'Vigesimal',
    'VigesimalJK',
]


ValidInput = Union[str, int, float]  # TODO: Decimal, Fraction


def cached_classproperty(func):
    return classmethod(property(cache(func)))


def abstractclassproperty(func):
    return property(classmethod(abstractmethod(func)))


def convert(method):
    '''Returns ``NotImplemented`` when the conversion of an operand
    fails, thus allowing other classes to define operations with types
    not implemented here.
    '''
    @wraps(method)
    def conversion(self, other):
        try:
            other = self.__class__(other)
        except TypeError:
            return NotImplemented
        return method(self, other)
    return conversion


def convertself(method):
    '''Like ``convert`` but casting the result to own class.
    '''
    @wraps(method)
    def conversion(self, other):
        try:
            other = self.__class__(other)
        except TypeError:
            return NotImplemented
        return self.__class__(method(self, other))
    return conversion


class cidict(dict):
    def __init__(self, mapping):
        super().__init__((k.lower(), v) for k, v in mapping)

    def __getitem__(self, k):
        return super().__getitem__(k.lower())

    def __setitem__(self, k, v):
        super().__setitem__(k.lower(), v)


class OnlyIntegers(TypeError):
    def __init__(self, op: str, values: Tuple[Numerical, ...]):
        self.values = values
        super().__init__(
            f'{op!r} not allowed unless all arguments are integers'
        )


class Meta(type):
    @classmethod
    def __prepare__(*_):
        return {'__slots__': ()}


class Numerical(metaclass=Meta):
    '''Positional numeral system base class.
    '''
    __slots__ = ('value', 'decimal')

    case_sensitive: bool = False
    fractional_separator: str = '.'
    group_separator: Optional[str] = None  # TODO: defaults to _

    value: str
    decimal: Union[int, float]

    def __init__(self, value: ValidInput) -> None:
        if isinstance(value, str):
            self.value = value
            self.decimal = self.__to_dec(value.strip())
        elif isinstance(value, int):
            self.value = self.__from_dec(value)
            self.decimal = value
        elif isinstance(value, float):
            if not isfinite(value):
                raise ValueError(f'cannot convert non-finite {value} to '
                                  '{self.__class__.name}')
            self.value = self.__from_dec(value)
            self.decimal = value
        elif isinstance(value, Numerical):
            if value.digits != self.digits:
                value = self.__class__(value.decimal)
            self.value = value.value
            self.decimal = value.decimal
        elif isinstance(value, Decimal):
            raise NotImplementedError
        elif isinstance(value, Fraction):
            raise NotImplementedError
        else:
            raise TypeError(value)

        # normalize casing
        if not self.case_sensitive:
            self.value = self.__from_dec(self.decimal)

    @abstractclassproperty
    def digits(cls) -> str: ...  # type: ignore

    @cached_classproperty
    def base(cls) -> int:
        return len(cls.digits)

    @cached_classproperty
    def __zero(cls) -> str:
        return cls.digits[0]

    @cached_classproperty
    def __rstrip(cls) -> Callable[[str], str]:
        '''Removes trailing zeros (for fractional parts).'''
        tail = cls.__zero if cls.case_sensitive else cls.__zero.lower() + cls.__zero.upper()
        return lambda string: string.rstrip(tail)

    @cached_classproperty
    def __parse(cls) -> Callable[[str], Tuple[str, str, str]]:
        '''Split number into sign, integer, and fractional parts.
        '''
        if cls.group_separator:
            if cls.group_separator in cls.digits:
                pass  # TODO
            raise NotImplementedError

        if cls.fractional_separator in cls.digits:
            raise RuntimeError(
                f'cannot include the fractional separator {cls.fractional_separator!r} '
                f'within the digits: {cls.digits!r}'
            )

        sep = re.escape(cls.fractional_separator)
        digits = re.escape(cls.digits)
        flags = 0 if cls.case_sensitive else re.IGNORECASE
        pattern = re.compile(fr'^(-)?([{digits}]+)(?:{sep}([{digits}]+))?$', flags)

        def parse(string):
            try:
                return pattern.match(string).groups(default='')
            except AttributeError:
                raise ValueError(string) from None

        return parse

    @cached_classproperty
    def __from_digits(cls) -> Dict[str, int]:
        dictcls = dict if cls.case_sensitive else cidict
        return dictcls((d, i) for i, d in enumerate(cls.digits))

    @cached_classproperty
    def __to_digits(cls) -> Callable[[Iterable[int]], str]:
        digits = {i: d for i, d in enumerate(cls.digits)}
        return lambda integers: ''.join(digits[i] for i in integers)

    @classmethod
    def __from_dec(cls, decimal: Union[int, float]) -> str:
        integer, fractional = divmod(abs(decimal), 1)

        if integer:
            sign = '-' if decimal < 0 else ''
        else:
            sign = f'-{cls.__zero}' if decimal < 0 else cls.__zero

        digits: Iterable = deque()
        quotient = integer
        while quotient:
            quotient, remainder = divmod(quotient, cls.base)
            digits.appendleft(remainder)
        output = f'{sign}{cls.__to_digits(digits)}'

        if fractional:
            digits = deque()
            remainder = fractional
            for i in range(len(str(fractional).split('.')[1]) + 1):
                quotient, remainder = divmod(remainder * cls.base, 1)
                digits.append(quotient)
            if remainder > 0.5:  # TODO: >= ?
                digits.append(1)
            output += (
                f'{cls.fractional_separator}{cls.__rstrip(cls.__to_digits(digits))}'
            )

        return output

    @classmethod
    def __to_dec(cls, string: str) -> Union[int, float]:
        sign, integer, fractional = cls.__parse(string)

        output = 0
        for power, digit in enumerate(integer[::-1]):
            output += cls.__from_digits[digit] * (cls.base ** power)
        for power, digit in enumerate(fractional, 1):
            output += cls.__from_digits[digit] * (cls.base ** -power)

        return (-1 if sign else 1) * output

    # repr
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.value!r})'

    def __hash__(self) -> int:
        return hash(self.decimal)

    # type casting
    def __int__(self) -> int:
        return int(self.decimal)

    def __float__(self) -> float:
        return float(self.decimal)

    def __bool__(self) -> bool:
        return bool(self.value)

    # comparison
    @convert
    def __eq__(self, other) -> bool:
        return self.decimal == other.decimal

    @convert
    def __ne__(self, other) -> bool:
        return self.decimal != other.decimal

    @convert
    def __lt__(self, other) -> bool:
        return self.decimal < other.decimal

    @convert
    def __le__(self, other) -> bool:
        return self.decimal <= other.decimal

    @convert
    def __gt__(self, other) -> bool:
        return self.decimal > other.decimal

    @convert
    def __ge__(self, other) -> bool:
        return self.decimal >= other.decimal

    # unary operations
    def __abs__(self) -> 'Self':
        '''abs(self)'''
        return self.__class__(self.value.lstrip('-'))

    def __neg__(self) -> 'Self':
        '''-self'''
        return self.__class__(-self.decimal)

    def __pos__(self) -> 'Self':
        '''+self'''
        return self

    def __trunc__(self) -> 'Self':  # type: ignore
        '''Truncates self to an integer.'''
        return self.__class__(int(self.decimal))

    def __floor__(self) -> 'Self':  # type: ignore
        '''Finds the greatest integer <= self.'''
        return self.__class__(floor(self.decimal))

    def __ceil__(self) -> 'Self':  # type: ignore
        '''Finds the least integer >= self.'''
        return self.__class__(ceil(self.decimal))

    def __round__(self, ndigits: Optional[int] = None) -> 'Self':  # type: ignore
        '''Rounds self to ndigits decimal places, defaulting to 0.
        If ndigits is omitted or None, returns an integral, otherwise
        returns a real. Rounds half toward even.
        '''
        return self.__class__(round(self.decimal, ndigits))

    def __invert__(self) -> 'Self':
        '''~self'''
        try:
            return self.__class__(~cast(int, self.decimal))
        except TypeError:
            raise OnlyIntegers('invert', (self,)) from None

    # binary operations
    # @convert
    # def __add__(self, other) -> 'Self':
    #     '''self + other'''
    #     return self.__class__(self.decimal + other.decimal)

    @convertself
    def __add__(self, other) -> 'Self':
        '''self + other'''
        return self.decimal + other.decimal

    def __radd__(self, other) -> 'Self':
        '''other + self'''
        return self + other

    @convertself
    def __sub__(self, other) -> 'Self':
        '''self - other'''
        return self.decimal - other.decimal

    @convertself
    def __rsub__(self, other) -> 'Self':  # from Integral
        '''other - self'''
        return other.decimal - self.decimal

    @convertself
    def __mul__(self, other) -> 'Self':
        '''self * other'''
        return self.decimal * other.decimal

    def __rmul__(self, other) -> 'Self':
        '''other * self'''
        return self * other

    @convertself
    def __truediv__(self, other) -> 'Self':
        '''self / other'''
        return self.decimal / other.decimal

    @convertself
    def __rtruediv__(self, other) -> 'Self':
        '''other / self'''
        return other.decimal / self.decimal

    @convertself
    def __floordiv__(self, other) -> 'Self':
        '''self // other'''
        return self.decimal // other.decimal

    @convertself
    def __rfloordiv__(self, other) -> 'Self':
        '''other // self'''
        return other.decimal // self.decimal

    @convertself
    def __mod__(self, other) -> 'Self':
        '''self % other'''
        return self.__class__(self.decimal % other.decimal)

    @convertself
    def __rmod__(self, other) -> 'Self':
        '''other % self'''
        return other.decimal % self.decimal

    def __divmod__(self, other) -> Tuple['Self', 'Self']:
        '''divmod(self, other): The pair (self // other, self % other).'''
        return self // other, self % other

    def __rdivmod__(self, other) -> Tuple['Self', 'Self']:
        '''divmod(other, self): The pair (other // self, other % self).'''
        return other // self, other % self

    @convertself
    def __rpow__(self, other) -> 'Self':
        '''other ** self'''
        return pow(other.decimal, self.decimal)

    # bitwise binary operations
    @convertself
    def __lshift__(self, other) -> 'Self':
        '''self << other'''
        try:
            return self.decimal << other.decimal
        except TypeError:
            raise OnlyIntegers('lshift', (self, other)) from None

    @convertself
    def __rlshift__(self, other) -> 'Self':
        '''other << self'''
        try:
            return other.decimal << self.decimal
        except TypeError:
            raise OnlyIntegers('lshift', (other, self)) from None

    @convertself
    def __rshift__(self, other) -> 'Self':
        '''self >> other'''
        try:
            return self.decimal >> other.decimal
        except TypeError:
            raise OnlyIntegers('rshift', (self, other)) from None

    @convertself
    def __rrshift__(self, other) -> 'Self':
        '''other >> self'''
        try:
            return other.decimal >> self.decimal
        except TypeError:
            raise OnlyIntegers('rshift', (other, self)) from None

    @convertself
    def __and__(self, other) -> 'Self':
        '''self & other'''
        return self.decimal & other.decimal

    @convertself
    def __rand__(self, other) -> 'Self':
        '''other & self'''
        return other.decimal & self.decimal

    @convertself
    def __xor__(self, other) -> 'Self':
        '''self ^ other'''
        return self.decimal ^ other.decimal

    @convertself
    def __rxor__(self, other) -> 'Self':
        '''other ^ self'''
        return other.decimal ^ self.decimal

    @convertself
    def __or__(self, other) -> 'Self':
        '''self | other'''
        return self.decimal | other.decimal

    @convertself
    def __ror__(self, other) -> 'Self':
        '''other | self'''
        return other.decimal | self.decimal

    # binary / ternary operations
    # TODO: check typerrors
    def __pow__(self, exponent, modulus=None) -> 'Self':
        '''self ** exponent % modulus'''
        modulus = None if modulus is None else self.__class__(modulus).decimal
        exponent = self.__class__(exponent).decimal
        return self.__class__(pow(self.decimal, exponent, modulus))


Integral.register(Numerical)


class Duodecimal(Numerical):
    digits = '0123456789ab'


class DuodecimalTE(Numerical):
    digits = '0123456789te'


class DuodecimalXE(Numerical):
    digits = '0123456789xe'


class DuodecimalXZ(Numerical):
    digits = '0123456789xz'


class DuodecimalTurned(Numerical):
    digits = '0123456789↊↋'


class Senary(Numerical):
    digits = '012345'


class Quaternary(Numerical):
    digits = '012345'


class Quinary(Numerical):
    digits = '012345'


class Vigesimal(Numerical):
    digits = '0123456789abcdefghij'


class VigesimalJK(Numerical):
    digits = '0123456789abcdefghjk'


class Bengali(Numerical):
    digits = '০১২৩৪৫৬৭৮৯'
    # group_separator = ','


class Devanagari(Numerical):
    digits = '०१२३४५६७८९'
