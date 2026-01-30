import base64

from Crypto.Cipher import AES
from Crypto.Cipher._mode_gcm import GcmMode
from Crypto.Random import get_random_bytes

from ul_api_utils.encrypt.encrypt_decrypt_abstract import EncryptDecryptAbstract
from ul_api_utils.errors import SimpleValidateApiError


class EncryptDecryptAESXTEA(EncryptDecryptAbstract):

    def __init__(self, aes_key: bytes) -> None:
        self._aes_key = aes_key
        super().__init__()

    @property
    def aes_key(self) -> bytes:
        return self._aes_key

    def encrypt(self, decrypted_key: str) -> str:
        data = base64.b64decode(decrypted_key)
        if len(data) != 32:
            raise SimpleValidateApiError(f'invalid len of key. must be 32, {len(data)} was given')
        nonce = get_random_bytes(12)
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=nonce)
        assert isinstance(cipher, GcmMode), f'GcmMode required, {type(cipher)} was given'
        cipher_text, tag = cipher.encrypt_and_digest(data)
        decoded_key_encrypted = nonce + cipher_text + tag
        if len(decoded_key_encrypted) != 60:
            raise SimpleValidateApiError('len key_encrypted != 60')
        try:
            encrypted_key = base64.standard_b64encode(decoded_key_encrypted)
        except Exception:  # noqa: B902
            raise SimpleValidateApiError('cant encode')
        return encrypted_key.decode('utf-8')

    def decrypt(self, encrypted_key: str) -> str:

        if encrypted_key is None:
            raise SimpleValidateApiError('no key')
        try:
            decoded_key_encrypted = base64.standard_b64decode(encrypted_key.encode('utf-8'))
        except Exception:  # noqa: B902
            raise SimpleValidateApiError('cant encode')

        if len(decoded_key_encrypted) != 60:
            raise SimpleValidateApiError('len key_encrypted != 60')

        nonce = decoded_key_encrypted[:12]
        data = decoded_key_encrypted[12:-16]
        tag = decoded_key_encrypted[-16:]
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=nonce)
        result_key: bytes = cipher.decrypt_and_verify(data, tag)  # type: ignore

        if len(result_key) != 32:
            raise SimpleValidateApiError(f"invalid len of key. must be 32, {len(result_key)} was given")
        decrypted_key = base64.b64encode(result_key)
        return decrypted_key.decode('utf-8')
