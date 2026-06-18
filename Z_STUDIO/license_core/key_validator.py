import hashlib
import platform
import subprocess
import os
import json
import uuid
import hmac

class ZStudioSecurity:
    def __init__(self):
        self.root = os.getcwd()
        self.license_dir = os.path.join(self.root, "license_core")
        self.token_store = os.path.join(self.license_dir, "activation_token.store")

        self._INTERNAL_IV = b"Z-STUDIO-V8-X99-HARDENING-CORE-2026"

        #  DNA TAG (REQUIRED)
        self._DNA_TAG = "ZYNQUAR2026"

        if not os.path.exists(self.license_dir):
            os.makedirs(self.license_dir)

    def get_hwid(self):
        identifiers = []

        cpu = None
        try:
            output = subprocess.check_output(
                'wmic cpu get processorid',
                shell=True,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            ).decode(errors="ignore").splitlines()

            if len(output) > 1:
                cpu = output[1].strip()
        except:
            cpu = None

        if not cpu or "processorid" in str(cpu).lower():
            cpu = platform.processor() or "UNKNOWN_CPU"

        identifiers.append(cpu)
        identifiers.append(str(uuid.getnode()))
        identifiers.append(platform.machine())
        identifiers.append(platform.node())

        raw_id = "-".join(identifiers)
        return hashlib.sha512(raw_id.encode()).hexdigest()[:32].upper()

    # =========================
    #  DNA LOGIC (FINAL FIX)
    # =========================
    def _dna_check(self, license_key):
        tag = self._DNA_TAG

        # 1. MUST exist in some form
        if not any(c in license_key for c in tag):
            return False

        # 2. MUST NOT exist as full continuous block
        if tag in license_key:
            return False

        # 3. MUST be fully represented (all chars exist somewhere)
        for c in tag:
            if c not in license_key:
                return False

        return True

    # =========================
    # PAYLOAD (UNCHANGED LOGIC)
    # =========================
    def _get_payload(self, license_key, hwid):
        parts = license_key.split("-")

        if len(parts) < 3:
            return None

        core_key = "-".join(parts[:-1])
        return f"{hwid}:{core_key}"

    def _get_dynamic_salt(self, hwid):
        combined = f"{hwid}:{self._INTERNAL_IV.decode()}".encode()
        return hashlib.sha256(combined).digest()

    def _generate_signature(self, hwid, license_key):

        #  DNA MUST PASS HERE TOO
        if not self._dna_check(license_key):
            return None

        dynamic_salt = self._get_dynamic_salt(hwid)

        payload = self._get_payload(license_key, hwid)
        if payload is None:
            return None

        return hmac.new(
            dynamic_salt,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def validate_key_format(self, key):
        if not key or not isinstance(key, str):
            return False

        return key.startswith("ZST-") and len(key.split('-')) >= 4

    def activate_machine(self, license_key):

        if not self.validate_key_format(license_key):
            return False, "INVALID_FORMAT"

        #  DNA HARD CHECK
        if not self._dna_check(license_key):
            return False, "DNA_INVALID_OR_MISSING"

        current_hwid = self.get_hwid()

        signature = self._generate_signature(current_hwid, license_key)

        if not signature:
            return False, "SIGNATURE_BUILD_FAILED"

        payload = {
            "hwid_lock": current_hwid,
            "license_key": license_key,
            "signature": signature,
            "activation_meta": {
                "ts": "2026-04-20",
                "core": "V8-HARDENED"
            }
        }

        temp_file = self.token_store + ".tmp"

        try:
            with open(temp_file, 'w') as f:
                json.dump(payload, f, indent=4)

            if os.path.exists(self.token_store):
                os.remove(self.token_store)

            os.rename(temp_file, self.token_store)
            return True, "SUCCESS"

        except Exception:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False, "IO_ERROR"

    def check_license(self):
        current_hwid = self.get_hwid()

        if not os.path.exists(self.token_store):
            return {"status": "AWAITING_ACTIVATION", "hwid": current_hwid}

        try:
            with open(self.token_store, 'r') as f:
                data = json.load(f)
        except:
            return {"status": "CORRUPTED_TOKEN", "hwid": current_hwid}

        #  DNA CHECK ON STORED KEY
        if not self._dna_check(data.get("license_key", "")):
            return {"status": "DNA_REJECTED", "hwid": current_hwid}

        if data.get("hwid_lock") != current_hwid:
            return {"status": "INVALID_HARDWARE", "hwid": current_hwid}

        expected_sig = self._generate_signature(
            current_hwid,
            data.get("license_key")
        )

        if not expected_sig or data.get("signature") != expected_sig:
            return {"status": "TAMPERED_LICENSE", "hwid": current_hwid}

        return {"status": "AUTHORIZED", "hwid": current_hwid}

    def verify_integrity(self, config):
        return True


if __name__ == "__main__":
    guard = ZStudioSecurity()
    print("--- Z-STUDIO SECURITY CORE [LOCKED] ---")
    status = guard.check_license()
    print(f"STATUS: {status['status']} | HWID: {status['hwid']}")