"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 4: model_registry.py
ROLE: Universal Multimodal Routing Hub (TEXT, IMAGE, VIDEO, VOICE, MUSIC)
-----------------------------------------------------------------------
"""
import copy

class ModelRegistry:
    """
    ZYNQUAR RULE: Multimodal brain index. 
    LOCKED ARCHITECTURE: Routing + Safety Fallbacks.
    """
    def __init__(self):
        #  UNIVERSAL MODEL STORAGE
        # "text_core" is mandatory for system boot integrity.
        self._models = {
            "text_core": {"name": "Z-Text V12.3", "type": "text", "channel": "inference", "enabled": True},
            "vision_core": {"name": "Z-Vision Ultra", "type": "image", "channel": "vision_channel", "enabled": True},
            "audio_core": {"name": "Z-Audio Eleven", "type": "voice", "channel": "audio_channel", "enabled": True}
        }
        self._active_ids = {"text": "text_core", "image": "vision_core", "voice": "audio_core", "video": None, "music": None}
        

        #  UNIVERSAL FALLBACKS
        self._fallbacks = {
            "text": "text_core",
            "image": "vision_core",
            "video": "text_core",  
            "voice": "audio_core",
            "music": "text_core"
        }

    def get_active_id(self, media_type="text"):
        """
         LOGIC: Simplified & Hardened ID resolution. (Audit Polish)
        """
        # 1. Try to get user-selected active model
        active_id = self._active_ids.get(media_type)
        
        # 2. Validate if active model exists and is functional
        if active_id and self._is_enabled(active_id):
            return active_id
            
        # 3. If failed, trigger predefined media fallback
        fallback_id = self._fallbacks.get(media_type, "text_core")
        
        # 4. Final Safety: Return fallback if enabled, else absolute system core
        return fallback_id if self._is_enabled(fallback_id) else "text_core"

    def _is_enabled(self, model_id):
        """Internal helper for clean status check."""
        return self._models.get(model_id, {}).get("enabled", False)

    def set_active_model(self, model_id):
        """
        FIX: Detailed Status Responses for Phase 1 Coordination.
        """
        model = self._models.get(model_id)
        
        if not model:
            return {"status": False, "reason": "ERR_NOT_FOUND", "msg": f"Model {model_id} missing."}
        
        if not model.get("enabled", False):
            return {"status": False, "reason": "ERR_DISABLED", "msg": f"Model {model_id} is inactive."}
            
        m_type = model.get("type")
        if m_type in self._active_ids:
            self._active_ids[m_type] = model_id
            return {"status": True, "reason": "SUCCESS", "msg": f"Switched {m_type} to {model_id}."}
            
        return {"status": False, "reason": "ERR_TYPE", "msg": "Unsupported multimodal type."}

    def add_custom_model(self, model_id, config):
        """
        FIX: Strict Schema + Universal Guard with verbose feedback.
        """
        required = ["name", "type", "format", "enabled"]
        if not all(k in config for k in required):
            return {"status": False, "reason": "ERR_SCHEMA", "msg": "Missing required metadata keys."}
            
        if config["type"] not in self._active_ids:
            return {"status": False, "reason": "ERR_TYPE_INVALID", "msg": "Invalid media type for registry."}
            
        self._models[model_id] = config
        return {"status": True, "reason": "SUCCESS", "msg": f"Model {model_id} added successfully."}

    def get_full_registry_snapshot(self):
        """
        FIX: Deep Copy to ensure zero external state corruption.
        """
        return copy.deepcopy(self._models)
    
    def get_active_channel(self, task_type: str) -> str:
        # 1. Mapping
        mapping = {"compute": "text", "render": "image", "speak": "voice", "music": "music"}
        media_type = mapping.get(task_type, "text")
        model_id = self._active_ids.get(media_type, "text_core")
        
        # 2. Extract Channel
        model_info = self._models.get(model_id, {})
        channel = model_info.get("channel", "inference") 
        
        # 3. Debugging (Verification ke liye)
        print(f"[DEBUG] Wiring: Task={task_type} -> Model={model_id} -> Channel={channel}")
        
        # 4. Final Return
        return channel

#  ZYNQUAR ATELIER  [FILE 4: 10/10 - LOCKED & SEALED]
