from baseConverter import BaseConverter
class BaseConverterDecimal(BaseConverter):
    def to_decimal(self, number, base):
        """
        支持小数的进制转换
        """
        if '.' in number:
            integer_part, fractional_part = number.split('.')
        else:
            integer_part = number
            fractional_part = ''

        decimal = 0
        for ch in integer_part:
            if ch.isdigit():
                digit = int(ch)
            else:
                digit = ord(ch.upper()) - ord('A') + 10
            decimal = decimal * base + digit

        for ch in fractional_part:
            if ch.isdigit():
                digit = int(ch)
            else:
                digit = ord(ch.upper()) - ord('A') + 10
            decimal = decimal + digit / (base ** (len(fractional_part) - 1))

        return decimal

    def from_decimal(self, decimal, base, precision=10):
        """
        将十进制浮点数转换为任意进制
        """
        if decimal == 0:
            return '0'

        integer_part = int(decimal)
        fractional_part = decimal - integer_part

        digits = []
        # 整数部分
        while integer_part > 0:
            remainder = integer_part % base
            if remainder < 10:
                digits.append(str(remainder))
            else:
                digits.append(chr(ord('A') + remainder - 10))
            integer_part //= base

        # 小数部分
        fractional_digits = []
        for _ in range(precision):
            fractional_part *= base
            digit = int(fractional_part)
            if digit < 10:
                fractional_digits.append(str(digit))
            else:
                fractional_digits.append(chr(ord('A') + digit - 10))
            fractional_part -= digit
            if fractional_part == 0:
                break

        return ''.join(reversed(digits)) + '.' + ''.join(fractional_digits)
