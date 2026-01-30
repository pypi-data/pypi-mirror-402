class BaseConverter:
    def __init__(self):
        self.supported_bases = list(range(2, 37))  # 支持的进制范围是 2 到 36

    def is_valid_base(self, base):
        return base in self.supported_bases

    def is_valid_number(self, number, base):
        if not isinstance(number, str):
            return False
        for ch in number:
            if ch.isdigit():
                if int(ch) >= base:
                    return False
            else:
                if ch.upper() not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    return False
        return True

    def to_decimal(self, number, base):
        """
        将任意进制的字符串转换为十进制整数
        """
        if not self.is_valid_number(number, base):
            raise ValueError(f"Invalid number for base {base}")

        decimal = 0
        for ch in number:
            if ch.isdigit():
                digit = int(ch)
            else:
                digit = ord(ch.upper()) - ord('A') + 10
            decimal = decimal * base + digit
        return decimal

    def from_decimal(self, decimal, base):
        """
        将十进制整数转换为任意进制的字符串
        """
        if decimal == 0:
            return '0'
        digits = []
        while decimal > 0:
            remainder = decimal % base
            if remainder < 10:
                digits.append(str(remainder))
            else:
                digits.append(chr(ord('A') + remainder - 10))
            decimal //= base
        return ''.join(reversed(digits))

    def convert(self, number, from_base, to_base):
        """
        将一个数从 from_base 进制转换为 to_base 进制
        """
        if not self.is_valid_base(from_base) or not self.is_valid_base(to_base):
            raise ValueError("Unsupported base. Supported bases are 2 to 36")

        if not self.is_valid_number(number, from_base):
            raise ValueError(f"Invalid number for base {from_base}")

        decimal = self.to_decimal(number, from_base)
        result = self.from_decimal(decimal, to_base)
        return result
