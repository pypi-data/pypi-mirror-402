import os
import base64
import asyncio
from typing import Union, Optional, cast, Coroutine, Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


class CryptographyManager:
    def __init__(
        self,
        password: Union[str, bytes],
        salt: Optional[Union[str, bytes]] = None,
        iterations: int = 400000,
    ):
        """
        Initialize the CryptographyManager with the given parameters.

        :param password: The password used for key derivation.
        :param salt: The salt to use for PBKDF2. If None, a new salt is generated.
        :param iterations: The number of iterations for PBKDF2.
        """
        self.password = (
            password if isinstance(password, bytes) else str.encode(password)
        )
        if salt:
            self.salt: bytes = (
                salt
                if isinstance(salt, bytes)
                else str.encode(salt).decode("unicode_escape").encode()
            )
        else:
            self.salt = os.urandom(16)

        self.iterations = iterations
        self.key_length = 32  # Length of the derived key in bytes (for Fernet)

        # Create PBKDF2HMAC instance
        self.kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=self.salt,
            iterations=self.iterations,
            backend=default_backend(),
        )

        # Derive a key from the password
        self.key = self.kdf.derive(self.password)

        # Encode the key in Base64 for Fernet
        self.encoded_key = base64.urlsafe_b64encode(self.key)

        # Create Fernet instance with the derived key
        self.fernet = Fernet(self.encoded_key)

    async def __aencrypt(self, message: Union[str, bytes]) -> bytes:
        """
        Encrypt the given message using Fernet asynchronously.

        :param message: The message to encrypt.
        :return: The encrypted message.
        """
        message = message if isinstance(message, bytes) else str.encode(message)
        return cast(bytes, await asyncio.to_thread(self.fernet.encrypt, message))

    async def __adecrypt(self, token: bytes) -> str:
        """
        Decrypt the given token using Fernet asynchronously.

        :param token: The encrypted message to decrypt.
        :return: The decrypted message.
        """
        message = cast(bytes, await asyncio.to_thread(self.fernet.decrypt, token))
        return message.decode()

    def encrypt(
        self, message: Union[str, bytes]
    ) -> Union[bytes, Coroutine[Any, Any, bytes]]:
        """
        Encrypt the given message using Fernet.

        When called from within a running event loop, returns a coroutine that must be awaited.
        When called outside an event loop, returns the encrypted bytes directly.

        :param message: The message to encrypt.
        :return: Encrypted bytes, or a coroutine yielding encrypted bytes if called from a running loop.
        """
        try:
            loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return self.__aencrypt(message=message)
        else:
            return asyncio.run(self.__aencrypt(message=message))

    def decrypt(self, token: bytes) -> Union[str, Coroutine[Any, Any, str]]:
        """
        Decrypt the given token using Fernet.

        When called from within a running event loop, returns a coroutine that must be awaited.
        When called outside an event loop, returns the decrypted string directly.

        :param token: The encrypted message to decrypt.
        :return: Decrypted string, or a coroutine yielding decrypted string if called from a running loop.
        """
        try:
            loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return self.__adecrypt(token=token)
        else:
            return asyncio.run(self.__adecrypt(token=token))
