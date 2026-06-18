"""
Z-STUDIO V12.3  SYSTEM CORE (SYSTEM GUARD - HARDENED)
Role: Boot Security Gate + Integrity Validator + Safe Mode Controller
"""

import logging


class SystemGuard:

    def __init__(self, state_manager=None, config=None):
        self._safe_mode_active = False
        self._last_error = None
        self._override_allowed = False

        # Optional integrations (SAFE PLUG-IN DESIGN)
        self.state_manager = state_manager
        self.config = config

        #  FIX: internal logger fallback (WIRING SAFETY)
        self._logger = logging.getLogger("SystemGuard")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s | SYSTEM_GUARD | %(levelname)s | %(message)s"
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    # -------------------------
    # INTERNAL SAFE LOGGER
    # -------------------------
    def _log(self, level, message):
        try:
            # FIX: fallback always logs even if state_manager missing
            if self.state_manager and hasattr(self.state_manager, "update_state"):
                self.state_manager.update_state(
                    "last_guard_log",
                    f"{level}:{message}",
                    save_immediate=False
                )
            else:
                getattr(self._logger, level.lower(), self._logger.info)(message)
        except Exception:
            pass

    # -------------------------
    # CORE SAFETY ACTIONS
    # -------------------------
    def trigger_rollback(self, reason=None):
        self._last_error = reason
        self._log("WARN", f"ROLLBACK:{reason}")

    def reset(self):
        self._safe_mode_active = False
        self._last_error = None
        self._log("INFO", "RESET")

    def safe_mode(self):
        self._safe_mode_active = True
        self._log("WARN", "SAFE_MODE_ENABLED")
        return True

    # -------------------------
    # BOOT VALIDATION (HARDENED)
    # -------------------------
    def validate_boot(self, config=None, state=None):
        if config is None or state is None:
            self.trigger_rollback("BOOT_CONTEXT_MISSING")
            return False

        try:
            # FIX: safe dict access compatibility (no logic change)
            cfg_ver = config.get("version") if hasattr(config, "get") else getattr(config, "version", None)
            st_ver = state.get("version") if hasattr(state, "get") else getattr(state, "version", None)

            if cfg_ver and st_ver:
                if cfg_ver != st_ver:
                    self.trigger_rollback("VERSION_MISMATCH")
                    return False
        except Exception:
            self.trigger_rollback("VERSION_CHECK_ERROR")
            return False

        try:
            if hasattr(config, "get") and config.get("integrity_check") == "broken":
                self.trigger_rollback("CONFIG_TAMPER_DETECTED")
                return False
        except Exception:
            self.trigger_rollback("CONFIG_ACCESS_ERROR")
            return False

        self._log("INFO", "BOOT_VALIDATION_PASSED")
        return True

    # -------------------------
    # SECURITY OVERRIDE GATE
    # -------------------------
    def force_override(self, allowed=False):
        self._override_allowed = allowed
        self._log("INFO", f"OVERRIDE_SET:{allowed}")
        return self._override_allowed

    # -------------------------
    # STATE CHECK
    # -------------------------
    def is_safe(self):
        return not self._safe_mode_active