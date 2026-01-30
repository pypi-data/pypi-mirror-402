import base64
import hashlib
import json
import logging
import os
from enum import Enum
from functools import lru_cache
from typing import Literal, NamedTuple

from recurvedata.client.client import Client
from recurvedata.utils.imports import MockModule
from recurvedata.utils.registry import register_func

try:
    from cryptography.hazmat.primitives import hashes, padding, serialization
    from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    mock_module = MockModule("cryptography")
    hashes = mock_module
    padding = mock_module
    serialization = mock_module
    asymmetric_padding = mock_module
    Cipher = mock_module
    algorithms = mock_module
    modes = mock_module

logger = logging.getLogger(__name__)


class CryptoMethod(str, Enum):
    AES_128 = "AES-128"
    AES_256 = "AES-256"
    RSA_2048 = "RSA-2048"
    RSA_4096 = "RSA-4096"


class RSAKeyPair(NamedTuple):
    public_key: bytes
    private_key: bytes


class CryptoUtil:
    """Utility class for encryption operations"""

    @staticmethod
    @lru_cache
    def fetch_key_data(key_name: str) -> tuple[str, str]:
        """Fetch key data from server using key name"""
        client = Client()
        response = client.request("GET", f"/api/executor/keys/{key_name}")
        key_data = response["key_data"]
        encryption_method = response["encryption_method"]
        return key_data, encryption_method

    @staticmethod
    @lru_cache
    def get_key_data(key_name: str) -> bytes | RSAKeyPair:
        """Get and process key data from server using key name

        Args:
            key_name: Name of the key to fetch

        Returns:
            Processed key data based on encryption method from server
        """
        key_data, encryption_method = CryptoUtil.fetch_key_data(key_name)
        return CryptoUtil._decode_key_data(key_data, encryption_method)

    @staticmethod
    def _decode_key_data(key_data: str, encryption_method: str) -> bytes | RSAKeyPair:
        if encryption_method in (CryptoMethod.AES_128, CryptoMethod.AES_256):
            try:
                key = base64.urlsafe_b64decode(key_data)
            except Exception as e:
                raise ValueError("Invalid base64 encoding") from e
            if len(key) not in (16, 24, 32):
                raise ValueError("AES key must be 16, 24, or 32 bytes long")
            return key
        elif encryption_method in (CryptoMethod.RSA_2048, CryptoMethod.RSA_4096):
            try:
                key_dict = json.loads(key_data)
            except Exception as e:
                raise ValueError("Invalid RSA key data") from e
            if not isinstance(key_dict, dict):
                raise ValueError("Invalid RSA key data")
            if "public_key" not in key_dict or "private_key" not in key_dict:
                raise ValueError("Public key or private key is missing")
            return RSAKeyPair(
                public_key=key_dict["public_key"].encode("utf-8"),
                private_key=key_dict["private_key"].encode("utf-8"),
            )
        else:
            raise ValueError(f"Unsupported encryption method: {encryption_method}")

    @staticmethod
    def aes_encrypt_with_key(
        key: bytes, data: str | bytes | None, mode: Literal["ECB", "CBC"] = "ECB", iv: str | bytes | None = None
    ) -> bytes | None:
        """Encrypt data using AES with provided key

        Args:
            key: AES key bytes
            data: Data to encrypt
            mode: AES mode ('ECB' or 'CBC')
            iv: Initialization vector for CBC mode

        Returns:
            Encrypted bytes (with IV prepended for CBC mode)
        """
        if data is None:
            return None

        if isinstance(data, str):
            data = data.encode("utf-8")

        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data) + padder.finalize()

        if mode.upper() == "ECB":
            cipher = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
            return cipher.update(padded_data) + cipher.finalize()
        elif mode.upper() == "CBC":
            if iv is None:
                processed_iv = os.urandom(16)
            else:
                if isinstance(iv, str):
                    iv = iv.encode("utf-8")
                # Hash the IV to get exactly 16 bytes
                processed_iv = hashlib.md5(iv).digest()

            cipher = Cipher(algorithms.AES(key), modes.CBC(processed_iv)).encryptor()
            return processed_iv + cipher.update(padded_data) + cipher.finalize()
        else:
            raise ValueError(f"Unsupported AES mode: {mode}")

    @staticmethod
    def aes_decrypt_with_key(key: bytes, data: bytes | None, mode: Literal["ECB", "CBC"] = "ECB") -> bytes | None:
        """Decrypt data using AES with provided key"""
        if data is None:
            return None

        if mode.upper() == "ECB":
            cipher = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
            padded_data = cipher.update(data) + cipher.finalize()
        elif mode.upper() == "CBC":
            iv = data[:16]
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
            padded_data = cipher.update(data[16:]) + cipher.finalize()
        else:
            raise ValueError(f"Unsupported AES mode: {mode}")

        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        return unpadder.update(padded_data) + unpadder.finalize()

    @staticmethod
    def aes_encrypt(
        key_name: str, data: str | bytes | None, mode: Literal["ECB", "CBC"] = "ECB", iv: str | bytes | None = None
    ) -> bytes | None:
        """Encrypt data using AES with key from key store"""
        key: bytes = CryptoUtil.get_key_data(key_name)
        return CryptoUtil.aes_encrypt_with_key(key, data, mode, iv)

    @staticmethod
    def aes_decrypt(key_name: str, data: bytes | None, mode: Literal["ECB", "CBC"] = "ECB") -> bytes | None:
        """Decrypt data using AES with key from key store"""
        key: bytes = CryptoUtil.get_key_data(key_name)
        return CryptoUtil.aes_decrypt_with_key(key, data, mode)

    @staticmethod
    def rsa_encrypt_with_key(public_key: bytes, data: str | bytes) -> bytes:
        """Encrypt data using RSA with provided public key"""
        public_key_obj = serialization.load_pem_public_key(public_key)
        if isinstance(data, str):
            data = data.encode("utf-8")

        return public_key_obj.encrypt(
            data,
            asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    @staticmethod
    def rsa_decrypt_with_key(private_key: bytes, data: bytes) -> bytes:
        """Decrypt data using RSA with provided private key"""
        private_key_obj = serialization.load_pem_private_key(private_key, password=None)
        return private_key_obj.decrypt(
            data,
            asymmetric_padding.OAEP(
                mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    @staticmethod
    def rsa_encrypt(key_name: str, data: str | bytes | None) -> bytes | None:
        """Encrypt data using RSA with key from key store"""
        if data is None:
            return None
        key_pair: RSAKeyPair = CryptoUtil.get_key_data(key_name)
        return CryptoUtil.rsa_encrypt_with_key(key_pair.public_key, data)

    @staticmethod
    def rsa_decrypt(key_name: str, data: bytes | None) -> bytes | None:
        """Decrypt data using RSA with key from key store"""
        if data is None:
            return None
        key_pair: RSAKeyPair = CryptoUtil.get_key_data(key_name)
        return CryptoUtil.rsa_decrypt_with_key(key_pair.private_key, data)

    @staticmethod
    def base64_encode(data: bytes | None) -> str | None:
        """Convert bytes data to base64 encoded string.

        Args:
            data: The bytes data to encode. Can be None.

        Returns:
            Base64 encoded string if input is not None, otherwise None.
        """
        if data is None:
            return None
        return base64.b64encode(data).decode("utf-8")

    @staticmethod
    def base64_decode(data: str | None) -> bytes | None:
        """Convert base64 encoded encrypted data back to bytes

        Args:
            data: Base64 encoded encrypted data string. Can be None.

        Returns:
            Decoded bytes data if input is not None, otherwise None.
        """
        if data is None:
            return None
        return base64.b64decode(data.encode("utf-8"))

    @staticmethod
    def md5(data: str | bytes | None) -> str | None:
        """Calculate MD5 hash of data

        Args:
            data: Input data as string or bytes

        Returns:
            MD5 hash as hex string
        """
        return CryptoUtil._hash(data, "md5")

    @staticmethod
    def sha1(data: str | bytes | None) -> str | None:
        """Calculate SHA1 hash of data

        Args:
            data: Input data as string or bytes

        Returns:
            SHA1 hash as hex string
        """
        return CryptoUtil._hash(data, "sha1")

    @staticmethod
    def sha256(data: str | bytes | None) -> str | None:
        """Calculate SHA256 hash of data

        Args:
            data: Input data as string or bytes

        Returns:
            SHA256 hash as hex string
        """
        return CryptoUtil._hash(data, "sha256")

    @staticmethod
    def _hash(data: str | bytes | None, algorithm: Literal["md5", "sha1", "sha256"]) -> str | None:
        if data is None:
            return None
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.new(algorithm, data).hexdigest()


@register_func
def secret(key_name: str) -> str:
    """Get secret from server using key name"""
    try:
        key_data, _ = CryptoUtil.fetch_key_data(key_name)
        return key_data
    except Exception as e:
        logger.warning(f"Failed to get secret for key {key_name}: {e}")

        return key_name


aes_encrypt = CryptoUtil.aes_encrypt
aes_decrypt = CryptoUtil.aes_decrypt
rsa_encrypt = CryptoUtil.rsa_encrypt
rsa_decrypt = CryptoUtil.rsa_decrypt
base64_encode = CryptoUtil.base64_encode
base64_decode = CryptoUtil.base64_decode
