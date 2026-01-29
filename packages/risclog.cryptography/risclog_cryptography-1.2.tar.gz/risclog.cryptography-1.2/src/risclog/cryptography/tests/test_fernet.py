import os
import pytest
from cryptography.fernet import InvalidToken
from risclog.cryptography import CryptographyManager


@pytest.mark.asyncio
async def test_async_cryptography_manager():
    password = b"fSaCbrwrNZt0TYumhzbAOCQl2Trp2siFqXa-rowb4l8="
    message = b"Secret message!"
    salt = os.urandom(16)

    crypto_manager = CryptographyManager(password=password, salt=salt)

    token = await crypto_manager.encrypt(message)
    assert token is not None

    decrypted_message = await crypto_manager.decrypt(token)
    assert decrypted_message == message.decode()


@pytest.mark.asyncio
async def test_async_cryptography_manager_invalid_token():
    salt = os.urandom(16)
    password = b"fSaCbrwrNZt0TYumhzbAOCQl2Trp2siFqXa-rowb4l8="
    invalid_token = b"InvalidToken"
    crypto_manager = CryptographyManager(password=password, salt=salt)

    with pytest.raises(InvalidToken):
        await crypto_manager.decrypt(invalid_token)


@pytest.mark.asyncio
async def test_async_cryptography_manager_with_salt_not_set():
    password = b"fSaCbrwrNZt0TYumhzbAOCQl2Trp2siFqXa-rowb4l8="
    message = b"Secret message!"

    crypto_manager = CryptographyManager(password=password)

    token = await crypto_manager.encrypt(message)
    assert token is not None

    decrypted_message = await crypto_manager.decrypt(token)
    assert decrypted_message == message.decode()


@pytest.mark.asyncio
async def test_async_cryptography_manager_with_salt_not_set_and_second_cryptography_manager_instance():
    password = b"fSaCbrwrNZt0TYumhzbAOCQl2Trp2siFqXa-rowb4l8="
    message = b"Secret message!"

    crypto_manager = CryptographyManager(password=password)
    token = await crypto_manager.encrypt(message)
    assert token is not None

    crypto_manager = CryptographyManager(password=password)
    with pytest.raises(InvalidToken):
        await crypto_manager.decrypt(token)


def test_cryptography_manager():
    password = b"fSaCbrwrNZt0TYumhzbAOCQl2Trp2siFqXa-rowb4l8="
    message = b"Secret message!"
    salt = os.urandom(16)

    crypto_manager = CryptographyManager(password=password, salt=salt)

    token = crypto_manager.encrypt(message)
    assert token is not None

    decrypted_message = crypto_manager.decrypt(token)
    assert decrypted_message == message.decode()


def test_cryptography_manager_invalid_token():
    salt = os.urandom(16)
    password = b"fSaCbrwrNZt0TYumhzbAOCQl2Trp2siFqXa-rowb4l8="
    invalid_token = b"InvalidToken"
    crypto_manager = CryptographyManager(password=password, salt=salt)

    with pytest.raises(InvalidToken):
        crypto_manager.decrypt(invalid_token)
