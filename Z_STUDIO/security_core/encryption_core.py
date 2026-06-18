"""
ROLE: 3/9 - ENCRYPTION LAYER
DESCRIPTION: Handles model/config protection and key management.
STRICT DOMAIN: Encrypt/Decrypt ONLY. No hardware binding, no sandbox.
-----------------------------------------------------------------------
"""
import os, time, hmac, hashlib, struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

class ZStudioEncryptionCore:
    def __init__(self):
        self.VER = b'\x08'  # Blueprint V8 Compliance
        self.ITER = 400000  # High-security iterations
        self.salt_size = 16
        self.nonce_size = 12

    def _derive_runtime_key(self, master_key: str, salt: bytes) -> bytes:
        """Derives a high-entropy key for AES-GCM."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.ITER
        )
        return kdf.derive(master_key.encode())

    def protect_data(self, data: bytes, master_key: str) -> bytes:
        """
        Encrypts models or configs.
        Output: [SIG(32)][VER(1)][SALT(16)][NONCE(12)][CT(N)]
        """
        salt = os.urandom(self.salt_size)
        nonce = os.urandom(self.nonce_size)
        key = self._derive_runtime_key(master_key, salt)
        
        # Adding timestamp for temporal integrity
        timestamp = struct.pack(">Q", int(time.time()))
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, timestamp + data, None)
        
        # Build payload for signing
        payload = self.VER + salt + nonce + ciphertext
        
        # HMAC-SHA256 Signature (Integrity Layer)
        sig = hmac.new(key, payload, hashlib.sha256).digest()
        
        return sig + payload

    def unprotect_data(self, bundle: bytes, master_key: str) -> bytes:
        """
        Decrypts models or configs with strict integrity check.
        """
        if len(bundle) < 61: # 32(sig)+1(ver)+16(salt)+12(nonce)
            raise ValueError("E_PAYLOAD_INVALID")

        # Split bundle
        sig_stored = bundle[:32]
        payload = bundle[32:]
        ver = payload[0:1]
        salt = payload[1:17]
        nonce = payload[17:29]
        ciphertext = payload[29:]

        if ver != self.VER:
            raise PermissionError("E_VERSION_MISMATCH")

        # Derive same key to verify signature
        key = self._derive_runtime_key(master_key, salt)
        
        # Verify Integrity BEFORE Decryption
        sig_check = hmac.new(key, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig_stored, sig_check):
            raise PermissionError("E_INTEGRITY_FAIL")

        # Decrypt
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        
        # Remove timestamp (8 bytes) and return raw data
        return decrypted[8:]

# Instance
encryption_core = ZStudioEncryptionCore()