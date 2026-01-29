import base64

import crcmod
import six
from google.cloud.kms_v1 import CryptoKey, CryptoKeyVersion, KeyManagementServiceClient

from ash_kms.exceptions import EncryptionServiceError


class EncryptionService:
    def __init__(self, project_id: str):
        self.client = KeyManagementServiceClient()
        self.project_id = project_id

    def encrypt_symmetric(
        self,
        location_id: str,
        key_ring_id: str,
        key_id: str,
        plaintext: str,
    ) -> str:
        """
        Encrypt plaintext using a symmetric key.

        Args:
            location_id (string): Cloud KMS location (e.g. 'us-east1').
            key_ring_id (string): ID of the Cloud KMS key ring (e.g. 'my-key-ring').
            key_id (string): ID of the key to use (e.g. 'my-key').
            plaintext (string): message to encrypt

        Returns:
            Encrypted ciphertext.
        """

        plaintext_bytes = plaintext.encode("utf-8")

        key_name = self.client.crypto_key_path(self.project_id, location_id, key_ring_id, key_id)

        encrypt_response = self.client.encrypt(
            request={
                "name": key_name,
                "plaintext": plaintext_bytes,
                "plaintext_crc32c": self._crc32c(plaintext_bytes),
            },
        )

        if not encrypt_response.verified_plaintext_crc32c:
            raise EncryptionServiceError("The request sent to the server was corrupted in-transit.")
        if encrypt_response.ciphertext_crc32c != self._crc32c(encrypt_response.ciphertext):
            raise EncryptionServiceError("The response received from the server was corrupted in-transit.")

        return base64.b64encode(encrypt_response.ciphertext).decode("utf-8")

    def decrypt_symmetric(
        self,
        location_id: str,
        key_ring_id: str,
        key_id: str,
        ciphertext: str,
    ) -> str:
        """
        Decrypt the ciphertext using the symmetric key

        Args:
            location_id (string): Cloud KMS location (e.g. 'us-east1').
            key_ring_id (string): ID of the Cloud KMS key ring (e.g. 'my-key-ring').
            key_id (string): ID of the key to use (e.g. 'my-key').
            ciphertext (str): Encrypted str to decrypt.

        Returns:
            DecryptResponse: Response including plaintext.

        """

        ciphertext_bytes = base64.b64decode(ciphertext.encode("utf-8"))

        key_name = self.client.crypto_key_path(self.project_id, location_id, key_ring_id, key_id)

        decrypt_response = self.client.decrypt(
            request={
                "name": key_name,
                "ciphertext": ciphertext,
                "ciphertext_crc32c": self._crc32c(ciphertext_bytes),
            },
        )

        if decrypt_response.plaintext_crc32c != self._crc32c(decrypt_response.plaintext):
            raise EncryptionServiceError("The response received from the server was corrupted in-transit.")

        return decrypt_response.plaintext.decode("utf-8")

    def create_key_ring(self, location_id: str, key_ring_id: str) -> str:
        """
        Creates a new key ring in Cloud KMS

        Args:
            location_id: Cloud KMS location (e.g. 'us-east1').
            key_ring_id: ID of the key ring to create (e.g. 'my-key-ring').

        Returns:
            key_ring_name: Cloud KMS key ring name.

        """
        location_name = f"projects/{self.project_id}/locations/{location_id}"

        created_key_ring = self.client.create_key_ring(
            request={
                "parent": location_name,
                "key_ring_id": key_ring_id,
                "key_ring": {},
            },
        )

        return created_key_ring.name

    def create_key_symmetric_encrypt_decrypt(self, location_id: str, key_ring_id: str, key_id: str) -> CryptoKey:
        """
        Creates a new key in Cloud KMS.

        Args:
            project_id: Google Cloud project ID (e.g. 'my-project').
            location_id: Cloud KMS location (e.g. 'us-east1').
            key_ring_id: ID of the Cloud KMS key ring (e.g. 'my-key-ring').
            key_id: ID of the key to create (e.g. 'my-symmetric-key').

        Returns:
            Cloud KMS key.
        """
        key_ring_name = self.client.key_ring_path(self.project_id, location_id, key_ring_id)

        key = {
            "purpose": CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT,
            "version_template": {
                "algorithm": CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION,
            },
        }

        return self.client.create_crypto_key(
            request={"parent": key_ring_name, "crypto_key_id": key_id, "crypto_key": key},
        )

    def _crc32c(self, data: bytes) -> int:
        """
        Calculates the CRC32C checksum of the provided data.

        Args:
            data: the bytes over which the checksum should be calculated.

        Returns:
            An int representing the CRC32C checksum of the provided bytes.
        """
        crc32c_fun = crcmod.predefined.mkPredefinedCrcFun("crc-32c")
        return crc32c_fun(six.ensure_binary(data))
