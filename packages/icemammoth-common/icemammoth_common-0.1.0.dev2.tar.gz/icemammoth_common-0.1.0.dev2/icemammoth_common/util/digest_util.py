
import hashlib

def md5(str) -> str:
    hash_object = hashlib.md5(str.encode())  # 将字符串编码并进行 MD5 加密
    return hash_object.hexdigest().upper()