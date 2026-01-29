import keyring
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

def encrypt(message, key):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(message) + padder.finalize()

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return ciphertext

def decrypt(ciphertext, key):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)

    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    message = unpadder.update(padded_data) + unpadder.finalize()

    return message

def get_password(id: str, username: str) -> str:
    """从 Windows Credential Manager 获取密码，如果没有就提示输入并保存"""
    password = keyring.get_password(id, username)
    if password is None:
        password = input(f"请输入 {username} 的密码: ")
        keyring.set_password(id, username, password)
    return password