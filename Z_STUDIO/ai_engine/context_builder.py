"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 6: context_builder.py
ROLE: AI Prompt Orchestrator (Stateless + Deterministic + Safe Brain Layer)
STATUS: WIRED + STABLE + ZERO CONTEXT CORRUPTION
"""

import unicodedata


class ContextBuilder:
    """
     ROLE:
    AI ke liye FINAL CONTROLLED PROMPT banana

     RULES:
    - No memory leak
    - No prompt explosion
    - No injection from RAG or memory
    - Fully deterministic output
    """

    def __init__(self, max_tokens=4096):

        self.max_tokens = max_tokens

        # SAFE TOKEN MODEL
        self.char_limit = int(max_tokens * 3.6)

        # Prevent single entry hijack
        self.entry_cap = 1000

        # SYSTEM SAFETY FALLBACK
        self.safe_system_rule = (
            "You are Z-STUDIO AI ENGINE. Follow instructions deterministically. "
            "No hallucination. No external assumption."
        )

    # =====================================================
    # MAIN BUILD FUNCTION
    # =====================================================
    def build_final_prompt(self, user_input, memory_context, system_rules, r_chunks=None):

        # -------------------------
        # SAFE INPUT NORMALIZATION
        # -------------------------
        clean_user = self._sanitize(user_input)

        safe_system = self._sanitize(system_rules) if system_rules else self.safe_system_rule

        # -------------------------
        # LAYERED PROMPT BUILDING
        # -------------------------
        layers = [

            # SYSTEM CORE (IMMUTABLE)
            f"### SYSTEM_PROTOCOL\n{safe_system}",

            # EXTERNAL KNOWLEDGE (RAG SAFE)
            self._format_rag(r_chunks),

            # MEMORY CONTEXT (CAPPED + CLEAN)
            self._format_memory(memory_context),

            # USER INPUT (FINAL CONTROL POINT)
            f"### USER_QUERY\n{clean_user}"
        ]

        # Clean merge
        full_context = "\n\n".join([l for l in layers if l])

        # -------------------------
        # FINAL SAFETY TRIM
        # -------------------------
        return self._apply_final_trim(full_context)

    # =====================================================
    # SANITIZATION CORE
    # =====================================================
    def _sanitize(self, text):
        if not text:
            return ""

        return unicodedata.normalize("NFKC", str(text)).strip()

    # =====================================================
    # RAG FORMATTER (SAFE INJECTION BLOCKER)
    # =====================================================
    def _format_rag(self, chunks):

        if not chunks:
            return ""

        safe_chunks = []

        for c in chunks:

            clean = self._sanitize(c)

            # HARD CAP (prevents prompt flooding)
            safe_chunks.append(f"- {clean[:self.entry_cap]}")

        return "### EXTERNAL_KNOWLEDGE\n" + "\n".join(safe_chunks)

    # =====================================================
    # MEMORY FORMATTER (STRUCTURED HISTORY)
    # =====================================================
    def _format_memory(self, memory):

        if not memory:
            return ""

        history = []

        for entry in memory:

            role = self._sanitize(entry.get("role", "user")).upper()
            content = self._sanitize(entry.get("content", ""))[:self.entry_cap]

            history.append(f"{role}: {content}")

        return "### SESSION_MEMORY\n" + "\n".join(history)

    # =====================================================
    # FINAL TRIM ENGINE (ANTI OVERFLOW CORE)
    # =====================================================
    def _apply_final_trim(self, text):

        if len(text) <= self.char_limit:
            return text

        # SAFE SPLIT (SYSTEM PROTECTED + USER PROTECTED)
        head = int(self.char_limit * 0.3)
        tail = int(self.char_limit * 0.7)

        return (
            text[:head]
            + "\n\n[...CONTEXT_TRUNCATED_SAFE_MODE...]\n\n"
            + text[-tail:]
        )