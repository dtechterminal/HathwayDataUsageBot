from Crypto.Cipher import AES
import base64

def decrypt_string(cipher_b64: str) -> str:
    # 1) Base64 → raw ciphertext
    ct = base64.b64decode(cipher_b64)

    # 2) Prepare key & IV
    key = b"EXTRACT THE KEY FROM HATHWAY APP WITH APKTOOL"  # 32 bytes
    iv  = b"1110010011001111"                 # 16 bytes

    # 3) Decrypt AES-256-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ct)

    # 4) Strip PKCS#7 padding
    pad_len = padded[-1]
    plain   = padded[:-pad_len]

    # 5) Decode UTF-8
    return plain.decode('utf-8')


# Encryption function
def encrypt_string(plain_text: str) -> str:
    # 1) Prepare key & IV
    key = b"EXTRACT THE KEY FROM HATHWAY APP WITH APKTOOL"  # 32 bytes
    iv  = b"1110010011001111"                 # 16 bytes

    # 2) PKCS#7 padding
    pad_len = 16 - (len(plain_text) % 16)
    padded = plain_text.encode('utf-8') + bytes([pad_len] * pad_len)

    # 3) Encrypt AES-256-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(padded)

    # 4) Base64 encode
    return base64.b64encode(ct).decode('utf-8')