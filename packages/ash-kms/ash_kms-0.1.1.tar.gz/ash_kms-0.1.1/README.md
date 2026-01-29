# ash-kms
The library provides functionality to handle GCP KMS encryption keys and operations

- The library allows the creation of a new key-ring within GCP KMS.
- The library allows the creation of a new encryption key within GCP KMS.
- The library provides functionality to encrypt secrets using the specified encryption key.
- Users can decrypt secrets using the specified encryption key.

## Installation

```python
pip install ash-kms
```

## Usage
```python
from ash_kms import EncryptionService

key_ring_id = "test_key_ring_id"
key_id = "test_key"
location_id = "global"
plaintext = "asdf1234"

service = EncryptionService(project_id="ash-dev-273120")

key_ring_name = service.create_key_ring(location_id=location_id, key_ring_id=key_ring_id)
print(key_ring_name)

key = service.create_key_symmetric_encrypt_decrypt(location_id=location_id, key_ring_id=key_ring_id, key_id=key_id)
print(key.name)

ciphertext = service.encrypt_symmetric(location_id=location_id, key_ring_id=key_ring_id, key_id=key_id,
                                       plaintext=plaintext)

print(f"{ciphertext=}")
decrypted_plaintext = service.decrypt_symmetric(location_id=location_id, key_ring_id=key_ring_id, key_id=key_id,
                                                ciphertext=ciphertext)

print(f"{plaintext=}")

assert decrypted_plaintext == plaintext

```