# Numerical

This library provides a base class to easily create [**positional numeral systems**][1]
that include all of the mathematical operations defined in Python for complex, real,
rational, and integral numbers.

You only need to provide a string with the chosen digits (the base of the numeral
system is deduced from the number of digits, i.e. the length of the string). E.g.

```python
from numerical import Numerical

class Dudodecimal(Numerical):
    digits = '0123456789AB'

num = Duodecimal('a')
print(repr(num))
#> Duodecimal('A')
```` 

Numerical can handle integer or float operands and will attempt to convert any
string to the defined numeral system.

```python
from numerical import Duodecimal

assert 10 == Duodecimal(10) == 0b1010 == Duodecimal('a') == 10.0 == DuodecimalXZ('A')
```


If you include letters among the symbols, they are treated by default as case
insensitive (and normalized to the defined case). You can modify this behavior
by setting the attribute `case_insensitive` to `False`.

```python
from numerical import Numerical

class Dudodecimal(Numerical):
    digits = '0123456789ab'
    case_insensitive = False
```

## Included numeral systems

| Base | Class              | Symbols                |
| ---- | ------------------ | ---------------------- |
| 4    | `Quaternary`       | `0123`                 |
| 5    | `Quinary`          | `01234`                |
| 6    | `Senary`           | `012345`               |
| 10   | `Bengali`          | `০১২৩৪৫৬৭৮৯`         |
| 10   | `Devanagari`       | `०१२३४५६७८९`           |
| 11   | `Undecimal`        | `0123456789a`          |
| 12   | `Duodecimal`       | `0123456789ab`         |
| 12   | `DuodecimalTE`     | `0123456789te`         |
| 12   | `DuodecimalXE`     | `0123456789xe`         |
| 12   | `DuodecimalXZ`     | `0123456789xz`         |
| 12   | `DuodecimalTurned` | <code>0123456789&#x218a;&#x218b;</code> |
| 20   | `Vigesimal`        | `0123456789abcdefghij` |
| 20   | `VigesimalJK`      | `0123456789abcdefghjk` |

[1]: https://en.wikipedia.org/wiki/Positional_notation
