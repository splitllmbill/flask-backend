from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import os


aes_key = os.getenv('ENC_KEY')
aes_iv = os.getenv('ENC_IV')

def decrypt(ciphertext):
    key = aes_key.encode('utf-8')
    iv = aes_iv.encode('utf-8')
    ciphertext_decode = base64.b64decode(ciphertext)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ciphertext_decode), AES.block_size)
    return decrypted.decode('utf-8')