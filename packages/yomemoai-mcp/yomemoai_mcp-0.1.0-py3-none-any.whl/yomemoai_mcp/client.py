import base64
import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os


class MemoClient:
    """
    Client for yomemoai API
    It's a wrapper for the yomemoai API.
    """

    def __init__(self, api_key: str, private_key_pem: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.private_key = serialization.load_pem_private_key(
            self._normalize_pem(private_key_pem),
            password=None,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        self.session = requests.Session()
        self.session.headers.update(
            {"X-Memo-API-Key": self.api_key, "Content-Type": "application/json"})

    def _normalize_pem(self, pem_str: str) -> bytes:
        pem_str = pem_str.strip()
        if "-----BEGIN" not in pem_str:
            return f"-----BEGIN PRIVATE KEY-----\n{pem_str}\n-----END PRIVATE KEY-----".encode()
        return pem_str.encode()

    def pack_data(self, raw_data: bytes) -> str:
        aes_key = os.urandom(32)
        nonce = os.urandom(12)

        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(
            nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(raw_data) + encryptor.finalize()

        combined_data = base64.b64encode(
            nonce + ciphertext + encryptor.tag).decode('utf-8')

        encrypted_key = self.public_key.encrypt(
            aes_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                         algorithm=hashes.SHA256(), label=None)
        )
        key_base64 = base64.b64encode(encrypted_key).decode('utf-8')

        signature = self.private_key.sign(
            combined_data.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        sig_base64 = base64.b64encode(signature).decode('utf-8')

        pkg = {
            "data": combined_data,
            "key": key_base64,
            "signature": sig_base64
        }
        return base64.b64encode(json.dumps(pkg).encode()).decode()

    def unpack_and_decrypt(self, encrypted_pkg_base64: str) -> bytes:
        pkg_json = base64.b64decode(encrypted_pkg_base64)
        pkg = json.loads(pkg_json)

        if "key" in pkg and pkg["key"]:
            encrypted_key = base64.b64decode(pkg["key"])
            aes_key = self.private_key.decrypt(
                encrypted_key,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                             algorithm=hashes.SHA256(), label=None)
            )

            combined_data = base64.b64decode(pkg["data"])
            nonce = combined_data[:12]
            tag = combined_data[-16:]
            ciphertext = combined_data[12:-16]

            cipher = Cipher(algorithms.AES(aes_key), modes.GCM(
                nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return decryptor.update(ciphertext) + decryptor.finalize()
        else:
            data = base64.b64decode(pkg["data"])
            return self.private_key.decrypt(
                data,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                             algorithm=hashes.SHA256(), label=None)
            )

    def add_memory(self, content: str, handle: str = "", description: str = "", metadata: Dict = None):
        token_size = len(content)

        packed = self.pack_data(content.encode('utf-8'))
        payload = {
            "ciphertext": packed,
            "description": description,
            "handle": handle,
            "metadata": metadata or {
                "token_size": token_size,
                "from": "yomemoai-mcp",
            }
        }
        resp = self.session.post(
            f"{self.base_url}/api/v1/memory", json=payload)
        resp.raise_for_status()
        return resp.json()

    def get_memories(self, handle: Optional[str] = None) -> List[Dict]:
        url = f"{self.base_url}/api/v1/memory"
        params = {"handle": handle} if handle else {}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()

        memories = resp.json().get("data", [])
        for m in memories:
            try:
                decrypted = self.unpack_and_decrypt(m["content"])
                m["content"] = decrypted.decode('utf-8')
            except Exception as e:
                print(f"Decryption failed for {m.get('id')}: {e}")
        return memories
