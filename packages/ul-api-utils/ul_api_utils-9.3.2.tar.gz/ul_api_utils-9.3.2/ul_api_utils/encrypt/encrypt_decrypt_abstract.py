import abc


class EncryptDecryptAbstract(abc.ABC):

    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def encrypt(self, decrypted_key: str) -> str:
        raise NotImplementedError('Error')

    @abc.abstractmethod
    def decrypt(self, encrypted_key: str) -> str:
        raise NotImplementedError('Error')
