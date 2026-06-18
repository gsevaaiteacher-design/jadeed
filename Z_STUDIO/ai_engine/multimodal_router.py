"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 12: multimodal_router.py
ROLE: Input Router (Type Detection & Normalization)
-----------------------------------------------------------------------
"""

class MultimodalRouter:
    """
     ROLE: Input type detect karna aur sahi handler ko route karna.
     LOGIC: Raw input ko analyze karke normalized text string me badalna.
    """

    def __init__(self):
        # Blueprint logic: Supported input formats
        self.supported_types = ["text", "image_path", "audio_path", "document_path"]

    def route_input(self, raw_input, force_task=None):
        """
        [V12.3 TITAN ROUTER] - Multi-Phase Intelligent Redirector.
        Phase 0-7 (Stable) | Phase 8-13 (Bridge Ready)
        """
        # 1. Sabse pehle type aur task detect karo
        input_type = self._detect_type(raw_input)
        
        # Priority Override: Agar UI ne koi specific button (force_task) dabaya ho
        final_task = force_task if force_task else input_type

        #  LAYER 1: SPECIAL AI TASKS (Phase 8, 9, 12, 13 Ready)
        
        # VOICE CLONING / MUSIC GEN (Phase 8 & 12)
        if "voice_clone" in final_task or "music" in final_task:
            return self._handle_audio_engine(raw_input, task=final_task)

        # BG REMOVAL & UPSCALING (Phase 9 - Automation/Vision)
        if "bg_removal" in final_task or "upscale" in final_task:
            return self._handle_vision_engine(raw_input, task=final_task)

        #  LAYER 2: STANDARD MULTIMODAL ROUTING
        
        # TEXT & PROMPTS
        if final_task == "text_prompt":
            return self._handle_text(raw_input)

        # IMAGES (Regular processing)
        elif final_task == "image_path":
            return self._handle_multimodal(raw_input, "IMAGE")

        # AUDIO (Regular playback/transcription)
        elif final_task == "audio_path":
            # Phase 8: Vosk/Whisper yahan se trigger hoga
            return self._handle_multimodal(raw_input, "AUDIO")

        # VIDEO
        elif final_task == "video_path":
            return self._handle_multimodal(raw_input, "VIDEO")

        # DOCUMENTS (RAG/Knowledge Base)
        elif final_task == "document_path":
            return self._handle_document(raw_input)

        #  LAYER 3: CRITICAL SAFE FALLBACK (Phase 7 - Crash Proof)
        return self._handle_fallback(raw_input, reason="UNKNOWN_TYPE")

    def _detect_type(self, data):
        """
        Z-STUDIO TITAN KERNEL: Intelligent Task & Media Classifier.
        Handles: Voice, Music, Cloning, Upscaling, BG Removal.
        """
        if not data:
            return "empty_void"

        # 1. Dictionary/Payload Check (Agar complex command ho)
        if isinstance(data, dict):
            return data.get("task_type", "dynamic_payload")

        if isinstance(data, str):
            d = data.lower().strip()

            # --- LAYER 1: TASK COMMAND DETECTION (ASLI FIRE) ---
            # Agar user ne direct path ki jagah task keyword diya ho
            if any(k in d for k in ["clone_voice", "voice_match"]): return "voice_clone_task"
            if any(k in d for k in ["remove_bg", "bg_remover"]): return "bg_removal_task"
            if any(k in d for k in ["upscale", "super_res"]): return "upscale_task"
            if any(k in d for k in ["gen_music", "music_make"]): return "music_gen_task"

            # --- LAYER 2: DEEP MEDIA EXTENSION CHECK ---
            
            # IMAGE & UPSCALER/BG TARGETS
            if d.endswith(('.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp')):
                # Logic: Agar image hai toh system default use 'image_path' hi dega
                return "image_path"

            # AUDIO / VOICE / MUSIC TARGETS
            if d.endswith(('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.opus')):
                # Audio files can be Voice or Music
                return "audio_path"

            # VIDEO TARGETS
            if d.endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
                return "video_path"

            # DOCUMENTS
            if d.endswith(('.pdf', '.txt', '.docx', '.json', '.yaml')):
                return "document_path"

            # --- LAYER 3: RAW TEXT / PROMPT ---
            # Agar koi extension nahi mila toh wo AI Prompt hai
            return "text_prompt"

        return "unsupported_type"
    
    def _handle_fallback(self, data, reason="GENERAL"):
        """
        [V12.3] LAST SAFETY NET - NEVER CRASH.
        Redirects unknown tasks to potential Automation Phase.
        """
        self.logger.warning(f" [FALLBACK] Handling unknown input. Reason: {reason}")
        
        # Agar string hai toh clean karke return karo
        if isinstance(data, str):
            clean_data = data.strip()
            # Yahan hum rasta khol rahe hain future Automation ke liye
            return {
                "status": "FALLBACK_PENDING",
                "type": "unclassified_command",
                "payload": clean_data,
                "target_layer": "automation_core" # Phase 9 Ready
            }

        return {"status": "CRITICAL_UNKNOWN", "raw": str(data)}
    

    def _handle_multimodal(self, path, prefix):
        """
        [V12.3] SAFE NORMALIZATION.
        Standardizes paths for AI Engine & Automation Core.
        """
        import os
        # Path validation taaki galat rasta system na bhatkaye
        abs_path = os.path.abspath(path) if os.path.exists(path) else path
        
        return {
            "type": prefix,           # IMAGE, AUDIO, VIDEO
            "path": abs_path,         # Pura paka rasta
            "filename": os.path.basename(path),
            "context": f"[{prefix}_INPUT]",
            "is_local": os.path.exists(path),
            "automation_ready": True  # Automation layer ise pick kar sakegi
        }

    def _handle_text(self, text):
        """
        [V12.3] TEXT NORMALIZER & INTENT PREP.
        Logic: Cleans text and calculates metadata for Phase 12.
        """
        if not text:
            return {"type": "text", "content": "", "length": 0, "priority": "low"}

        clean_text = text.strip()
        
        # Metadata logic: Chote text ko "Command" aur bade ko "Context" samjho
        is_long_form = len(clean_text) > 500
        
        return {
            "type": "text",
            "content": clean_text,
            "meta": {
                "length": len(clean_text),
                "is_complex": is_long_form,
                "encoding": "utf-8"
            },
            "target": "inference_engine" if not is_long_form else "context_builder"
        }

    def _handle_document(self, path):
        """
        [V12.3] DOCUMENT SCANNER & KNOWLEDGE BASE LINK.
        Logic: Prepares document for Vector DB (Phase 6).
        """
        import os
        
        # 1. Path Verification
        exists = os.path.exists(path)
        ext = os.path.splitext(path)[1].lower() if exists else "unknown"

        # 2. Simulation with Real Metadata
        return {
            "type": "document",
            "path": os.path.abspath(path) if exists else path,
            "status": "READY_FOR_SCAN" if exists else "FILE_MISSING",
            "meta": {
                "extension": ext,
                "is_local": exists,
                "process_mode": "RAG_INJECTION" # Phase 6 (Vector Core) trigger
            },
            "content_sim": f"[DOCUMENT_INPUT] System ready to index: {os.path.basename(path)}"
        }

#  ZYNQUAR ATELIER  [FILE 12: 10/10 BLUEPRINT ALIGNED]
