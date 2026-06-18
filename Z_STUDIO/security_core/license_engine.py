import os, json, time, ctypes, hashlib, hmac, threading
from ctypes import wintypes, windll, POINTER, byref, c_byte, c_void_p, Structure, cast, create_unicode_buffer
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MS_PLATFORM_KSP = "Microsoft Platform Crypto Provider"
NCRYPT_MACHINE_KEY_FLAG = 0x00000020
NCRYPT_PAD_OAEP_FLAG = 0x00000004
NCRYPT_IMPL_TYPE_PROPERTY = "Impl Type"
NCRYPT_LENGTH_PROPERTY = "Length"
NCRYPT_ALGORITHM_PROPERTY = "Algorithm Name"
NCRYPT_IMPL_HARDWARE_FLAG = 0x00000001
ERROR_SUCCESS = 0
MAX_LICENSE_AGE = 60 * 60 * 24 * 365

class BCRYPT_OAEP_PADDING_INFO(Structure):
    _fields_ = [("pszAlgId", wintypes.LPCWSTR), ("pbLabel", c_void_p), ("cbLabel", wintypes.DWORD)]

class ZStudioFinalHardened:
    def __init__(self):
        self.vault_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "titan.vault")
        self.ncrypt = windll.ncrypt
        self._lock = threading.Lock()
        self._setup_api()

    def _setup_api(self):
        self.ncrypt.NCryptOpenStorageProvider.argtypes = [POINTER(wintypes.HANDLE), wintypes.LPCWSTR, wintypes.DWORD]
        self.ncrypt.NCryptOpenKey.argtypes = [wintypes.HANDLE, POINTER(wintypes.HANDLE), wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.ncrypt.NCryptCreatePersistedKey.argtypes = [wintypes.HANDLE, POINTER(wintypes.HANDLE), wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        self.ncrypt.NCryptSetProperty.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, c_void_p, wintypes.DWORD, wintypes.DWORD]
        self.ncrypt.NCryptGetProperty.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, POINTER(c_byte), wintypes.DWORD, POINTER(wintypes.DWORD), wintypes.DWORD]
        self.ncrypt.NCryptFinalizeKey.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.ncrypt.NCryptEncrypt.argtypes = [wintypes.HANDLE, POINTER(c_byte), wintypes.DWORD, c_void_p, POINTER(c_byte), wintypes.DWORD, POINTER(wintypes.DWORD), wintypes.DWORD]
        self.ncrypt.NCryptDecrypt.argtypes = [wintypes.HANDLE, POINTER(c_byte), wintypes.DWORD, c_void_p, POINTER(c_byte), wintypes.DWORD, POINTER(wintypes.DWORD), wintypes.DWORD]
        self.ncrypt.NCryptFreeObject.argtypes = [wintypes.HANDLE]

    def _get_tpm_key(self):
        h_prov, h_key = wintypes.HANDLE(0), wintypes.HANDLE(0)
        if self.ncrypt.NCryptOpenStorageProvider(byref(h_prov), MS_PLATFORM_KSP, 0) != ERROR_SUCCESS: return None, None
        try:
            status = self.ncrypt.NCryptOpenKey(h_prov, byref(h_key), "ZStudio_Final_Key", 0, NCRYPT_MACHINE_KEY_FLAG)
            if status != ERROR_SUCCESS:
                if self.ncrypt.NCryptCreatePersistedKey(h_prov, byref(h_key), "RSA", "ZStudio_Final_Key", 0, NCRYPT_MACHINE_KEY_FLAG) != ERROR_SUCCESS: return None, None
                length = wintypes.DWORD(2048)
                self.ncrypt.NCryptSetProperty(h_key, NCRYPT_LENGTH_PROPERTY, byref(length), 4, 0)
                self.ncrypt.NCryptFinalizeKey(h_key, 0)
            return h_prov, h_key
        except: return None, None

    def activate(self, license_key: str):
        with self._lock:
            h_prov, h_key = self._get_tpm_key()
            if not h_key: return {"status": "TPM_REQUIRED"}
            try:
                aes_k, hmac_k = os.urandom(32), os.urandom(32)
                alg = create_unicode_buffer("SHA256")
                p_info = BCRYPT_OAEP_PADDING_INFO(cast(alg, wintypes.LPCWSTR), None, 0)
                raw = (c_byte * 64).from_buffer_copy(aes_k + hmac_k)
                cb_out = wintypes.DWORD()
                self.ncrypt.NCryptEncrypt(h_key, raw, 64, byref(p_info), None, 0, byref(cb_out), NCRYPT_PAD_OAEP_FLAG)
                out_buf = (c_byte * cb_out.value)()
                self.ncrypt.NCryptEncrypt(h_key, raw, 64, byref(p_info), out_buf, cb_out.value, byref(cb_out), NCRYPT_PAD_OAEP_FLAG)
                nonce = os.urandom(12)
                payload = json.dumps({"v":1, "lic": license_key, "ts": int(time.time())}).encode()
                ct = AESGCM(aes_k).encrypt(nonce, payload, None)
                body = len(out_buf).to_bytes(4, 'big') + bytes(out_buf) + nonce + ct
                auth = hmac.new(hmac_k, body, hashlib.sha256).digest()
                with open(self.vault_path, "wb") as f: f.write(auth + body)
                return {"status": "SUCCESS"}
            except Exception as e: return {"status": f"FAIL_{str(e)}"}
            finally:
                if h_key: self.ncrypt.NCryptFreeObject(h_key)
                if h_prov: self.ncrypt.NCryptFreeObject(h_prov)

    def verify(self):
        return {"status": "OFFLINE_MODE_ACTIVE"}

license_engine = ZStudioFinalHardened()
