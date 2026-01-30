def zero_pad(data, block_size=16):
    """
    ZeroBytesPadding填充实现
    :param data: 原始字节数据
    :param block_size: 块大小（字节）
    :return: 填充后的字节数据
    """
    pad_length = block_size - (len(data) % block_size)
    return data + b'\x00' * pad_length

def zero_unpad(padded_data):
    """
    ZeroBytesPadding去除填充实现
    :param padded_data: 填充后的字节数据
    :return: 去除填充后的原始数据
    """
    # 找到最后一个非零字节的位置
    last_non_zero = len(padded_data) - 1
    while last_non_zero >= 0 and padded_data[last_non_zero] == 0:
        last_non_zero -= 1
    if last_non_zero < 0:
        return b''  # 全部是零，返回空
    return padded_data[:last_non_zero + 1]

def pkcs7_pad(data, block_size=16):
    """
    PKCS7填充实现
    :param data: 原始字节数据
    :param block_size: 块大小（字节）
    :return: 填充后的字节数据
    """
    # 计算需要填充的字节数 (1 到 block_size 之间)
    pad_len = block_size - (len(data) % block_size)
    # 如果数据长度是块大小的整数倍，则填充整个块
    if pad_len == 0:
        pad_len = block_size
    
    # 创建填充字节 (每个字节的值等于填充长度)
    padding = bytes([pad_len] * pad_len)
    return data + padding

def pkcs7_unpad(padded_data):
    """
    PKCS7去除填充实现
    :param padded_data: 填充后的字节数据
    :return: 去除填充后的原始数据
    """
    # 检查数据长度是否有效
    if len(padded_data) == 0:
        raise ValueError("Padded data cannot be empty")
    
    # 获取最后一个字节的值（即填充长度）
    pad_len = padded_data[-1]
    
    # 验证填充长度有效性 (1 到 255 之间)
    if pad_len < 1 or pad_len > len(padded_data):
        raise ValueError("Invalid padding length")
    
    # 验证填充字节是否一致
    padding = padded_data[-pad_len:]
    if not all(byte == pad_len for byte in padding):
        raise ValueError("Invalid padding bytes")
    
    # 返回去除填充的数据
    return padded_data[:-pad_len]