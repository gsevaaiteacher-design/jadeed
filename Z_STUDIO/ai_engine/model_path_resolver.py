"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 1: model_path_resolver.py
ROLE: Model ka exact location final karna (ENTRY GATE)
-----------------------------------------------------------------------
"""

import os

class ModelPathResolver:
    """
    ZYNQUAR RULE: Ye file sirf rasta batayegi, model load nahi karega.
    """
    def __init__(self, project_root=None):
        # FIX: Dynamic Root Detection (Production Grade)
        if project_root is None:
            self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.project_root = project_root

        self.base_dir = os.path.join(self.project_root, "model_storage")
        
        # FIX: Storage Clusters (Defined for Priority Order)
        self.paths = {
            "internal": os.path.join(self.base_dir, "default_models"),
            "user": os.path.join(self.base_dir, "user_loaded_models"),
            "fallback": os.path.join(self.base_dir, "fallback_models")
        }

    def resolve_model_path(self, model_id, registry_data=None):
        """
        Input: model_id | Output: absolute_path
        Logic: Registry -> Internal -> User -> Fallback
        """
        # 1. FIX: Registry path validation with type safety (Audit Issue 1)
        if isinstance(registry_data, dict):
            ext_path = registry_data.get(model_id)
            if isinstance(ext_path, str) and self._validate(ext_path):
                return os.path.abspath(ext_path)

        # 2. FIX: Guaranteed Priority Order search (Audit Issue 2)
        priority_keys = ["internal", "user", "fallback"]
        for key in priority_keys:
            target = os.path.join(self.paths[key], model_id)
            if self._validate(target):
                return os.path.abspath(target)

        # 3. Final Fail Signal
        raise FileNotFoundError(f"[ZYNQUAR_ERROR] Model ID '{model_id}' not found in any cluster.")

    def _validate(self, path):
        """
        FIX: Hardened integrity check (Audit Issue 3)
        Check: Path exists, is a FILE (not dir), and has data.
        """
        try:
            return (
                path and 
                os.path.exists(path) and 
                os.path.isfile(path) and 
                os.path.getsize(path) > 0
            )
        except OSError:
            return False

#  ZYNQUAR ATELIER  [FILE 1: LOCKED & FINAL]
