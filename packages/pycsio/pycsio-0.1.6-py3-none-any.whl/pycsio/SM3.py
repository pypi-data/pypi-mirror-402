from numba import njit, uint32, int64
import numpy as np
import os

# numba int64类型转为uint32
@njit(uint32(int64), nogil=True, cache=True)
def i8_u4(x):
    return x


Tj_rl = np.empty((64, ), np.uint32)
Tj_rl[:16] = [i8_u4(0x79cc4519 << j | 0x79cc4519 >> 32-j) for j in range(16)]
Tj_rl[16:] = [i8_u4(0x7a879d8a << (j & 31) | 0x7a879d8a >> (32 - j & 31)) for j in range(16, 64)]
V0 = np.asarray([0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600, 0xa96f30bc, 0x163138aa, 0xe38dee4d, 0xb0fb0e4e], np.uint32)


@njit(uint32[::1](uint32[::1], uint32[::1]), nogil=True, cache=True)
def CF(V, B_):
    W = np.empty((68,), np.uint32)
    for i in range(0, len(B_), 16):
        W[:16] = B_[i:i+16]
        A, B, C, D, E, F, G, H = V
        for j in range(64):
            if j >= 12:
                X = i8_u4(W[j - 12] ^ W[j - 5] ^ (W[j + 1] << 15 | W[j + 1] >> 17))
                W[j + 4] = X ^ (X << 15 | X >> 17) ^ (X << 23 | X >> 9) ^ (W[j - 9] << 7 | W[j - 9] >> 25) ^ W[j - 2]
            A_rl12 = A << 12 | A >> 20
            tmp = i8_u4(A_rl12 + E + Tj_rl[j])
            SS1 = (tmp << 7 | tmp >> 25)
            SS2 = SS1 ^ A_rl12
            if j & 0x30:  # 16 <= j
                FF, GG = A & B | A & C | B & C, E & F | ~E & G
            else:
                FF, GG = A ^ B ^ C, E ^ F ^ G
            TT1, TT2 = i8_u4(FF + D + SS2 + (W[j] ^ W[j + 4])), i8_u4(GG + H + SS1 + W[j])
            C, D, G, H = B << 9 | B >> 23, C, F << 19 | F >> 13, G
            A, B, E, F = TT1, A, i8_u4(TT2 ^ (TT2 << 9 | TT2 >> 23) ^ (TT2 << 17 | TT2 >> 15)), E
        V[:] = V[0] ^ A, V[1] ^ B, V[2] ^ C, V[3] ^ D, V[4] ^ E, V[5] ^ F, V[6] ^ G, V[7] ^ H
    return V


def digest(data):
    # 填充
    pad_num = 64 - (len(data) + 1 & 0x3f)
    data += b'\x80' + (len(data) << 3).to_bytes(pad_num if pad_num >= 8 else pad_num + 64, 'big')
    # 迭代压缩
    return CF(np.copy(V0), np.frombuffer(data, np.uint32).byteswap()).byteswap().tobytes()

def update_digest(current_v, block_data):
    return CF(np.copy(current_v), np.frombuffer(block_data, dtype=np.uint32).byteswap())
def digest_file(file_path, buffer_size=1024*1024*10):  # 默认缓冲区大小为10MB
    V = V0.copy()
    total_length = os.path.getsize(file_path)
    
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(buffer_size)
            if not chunk: 
                break
            V = update_digest(V, chunk)
        
        # 最后添加填充
        file_position = f.tell()
        pad_num = 64 - ((file_position + 1) & 0x3f)
        padding = b'\x80' + (total_length * 8).to_bytes(pad_num if pad_num >= 8 else pad_num + 64, 'big')
        V = update_digest(V, padding)
    
    return V.byteswap().tobytes()