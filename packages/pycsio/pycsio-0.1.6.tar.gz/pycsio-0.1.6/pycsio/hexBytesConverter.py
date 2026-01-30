from Crypto.Util.number import bytes_to_long as btl
from Crypto.Util.number import long_to_bytes as ltb

class HexBytesConverter:
    def __init__(self):
        pass

    @staticmethod
    def bytes_to_hex(data: bytes) -> str:
        """将 bytes 转为 十六进制字符串"""
        return data.hex()
    
    @staticmethod
    def bytes_to_long(data: bytes) -> str:
        """将 bytes 转为 长整数"""
        return btl(data)
    
    @staticmethod
    def long_to_bytes(data: bytes) -> str:
        """将 长整数 转为 bytes"""
        return ltb(data)

    @staticmethod
    def hex_to_bytes(hex_str: str) -> bytes:
        """将十六进制字符串转为 bytes"""
        return bytes.fromhex(hex_str)

    @staticmethod
    def bytes_to_text(data: bytes) -> str:
        """将 bytes 转为 UTF-8 文本"""
        return data.decode('utf-8')

    @staticmethod
    def text_to_bytes(text: str) -> bytes:
        """将文本转为 bytes"""
        return text.encode('utf-8')

    @staticmethod
    def hex_to_text(hex_str: str) -> str:
        """将十六进制字符串转为 UTF-8 文本"""
        return HexBytesConverter.hex_to_bytes(hex_str).decode('utf-8')

    @staticmethod
    def text_to_hex(text: str) -> str:
        """将文本转为十六进制字符串"""
        return HexBytesConverter.text_to_bytes(text).hex()
