import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

class AESHelper:
    def __init__(self, key_size=16):
        self.key_size = key_size  # 16, 24, or 32 bytes (AES-128, AES-192, AES-256)
        self.block_size = 16  # AES block size is always 16 bytes

    def generate_key(self):
        """生成 AES 密钥"""
        return get_random_bytes(self.key_size)

    def encrypt(self, data: bytes, key: bytes) -> bytes:
        """加密数据"""
        if len(key) != self.key_size:
            raise ValueError(f"Key size must be {self.key_size} bytes")
        cipher = AES.new(key, AES.MODE_CBC)
        padded_data = pad(data, self.block_size)
        ciphertext = cipher.encrypt(padded_data)
        return cipher.iv + ciphertext  # 返回 IV + 密文

    def decrypt(self, encrypted_data: bytes, key: bytes) -> bytes:
        """解密数据"""
        if len(key) != self.key_size:
            raise ValueError(f"Key size must be {self.key_size} bytes")
        iv = encrypted_data[:self.block_size]
        ciphertext = encrypted_data[self.block_size:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(ciphertext), self.block_size)
        return decrypted_data

    def encrypt_string(self, text: str, key: bytes) -> str:
        """加密字符串"""
        return self.encrypt(text.encode('utf-8'), key).hex()

    def decrypt_string(self, encrypted_str: str, key: bytes) -> str:
        """解密字符串"""
        encrypted_data = bytes.fromhex(encrypted_str)
        return self.decrypt(encrypted_data, key).decode('utf-8')

    def encrypt_file(self, file_path: str, key: bytes, output_path: str = None):
        """加密文件"""
        with open(file_path, 'rb') as f:
            data = f.read()
        encrypted = self.encrypt(data, key)
        if output_path is None:
            output_path = file_path + '.enc'
        with open(output_path, 'wb') as f:
            f.write(encrypted)

    def decrypt_file(self, file_path: str, key: bytes, output_path: str = None):
        """解密文件"""
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted = self.decrypt(encrypted_data, key)
        if output_path is None:
            output_path = file_path[:-4]  # 去掉 .enc 后缀
        with open(output_path, 'wb') as f:
            f.write(decrypted)
