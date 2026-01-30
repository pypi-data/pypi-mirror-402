import hashlib
   
class Hasher:
    """
    一个支持多种哈希算法的工具类。
    支持的算法包括：
    - sha1, sha256, sha512, sha224, sha384
    - sha3_256, sha3_512, blake2b, blake2s
    - shake_128, shake_256
    """

    def __init__(self, algorithm='sha256'):
        self.algorithm = algorithm.lower()

    def set_algorithm(self, algorithm):
        """
        设置哈希算法
        """
        self.algorithm = algorithm

    def hash(self, pwd, length=32):
        """
        对密码进行哈希处理并返回十六进制字符串
        :param pwd: 密码，可以是字符串或 bytes
        :param length: 仅对 shake_128/shake_256 有效，指定输出长度
        :return: 哈希值（十六进制字符串）
        """
        if isinstance(pwd, str):
            pwd = pwd.encode()
        elif not isinstance(pwd, bytes):
            raise TypeError("pwd must be string or bytes")

        if self.algorithm in ['sha1', 'sha256', 'sha512', 'sha224', 'sha384', 'sha3_256', 'sha3_512', 'blake2b', 'blake2s']:
            # 用于标准哈希算法
            hash_func = getattr(hashlib, self.algorithm)
            return hash_func(pwd).hexdigest()
        elif self.algorithm == 'shake_128' or self.algorithm == 'shake_256':
            # 用于可变长度哈希（Shake）
            shake_func = getattr(hashlib, self.algorithm)
            return shake_func(pwd).hexdigest(length)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")