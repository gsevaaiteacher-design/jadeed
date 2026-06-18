"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 7: memory_engine.py
ROLE: Session Memory Manager (READ/WRITE/TRUNCATE)
-----------------------------------------------------------------------
"""

class MemoryEngine:
    """
     ROLE: Session memory manage karna (READ/WRITE).
     LOGIC: History append karna aur long-term context ko stable rakhna.
    """

    def __init__(self, history_limit=20):
        # Industrial standard: 20 turns (User + Assistant) for stable context.
        self.history_limit = history_limit
        # Volatile storage simulation (Production me Redis ya DB handler yahan connect hoga).
        self._session_db = {}

    def get_memory(self, session_id):
        """
         INPUT (READ): session_id: str
         OUTPUT (READ): memory_context: list
        """
        # Blueprint logic: Session ID se memory context nikalna.
        # Agar naya session hai, toh empty list return karna.
        return self._session_db.get(session_id, [])

    def commit_to_memory(self, session_id, user_input, response_text):
        """
         INPUT (WRITE): session_id, user_input, response_text
         LOGIC: Append fresh turn and enforce truncation (FIFO).
        """
        if not session_id:
            return False

        if session_id not in self._session_db:
            self._session_db[session_id] = []

        # 1. Append User Input
        self._session_db[session_id].append({
            "role": "user", 
            "content": str(user_input).strip()
        })

        # 2. Append Assistant Response
        self._session_db[session_id].append({
            "role": "assistant", 
            "content": str(response_text).strip()
        })

        # 3. Truncate (FIFO): Purani memory hatana taaki bloat na ho.
        self._truncate_session(session_id)
        return True

    def _truncate_session(self, session_id):
        """Latest 'history_limit' turns ko preserve karta hai."""
        # 1 Turn = 2 Entries (User + Assistant). Limit calculation: limit * 2.
        full_limit = self.history_limit * 2
        if len(self._session_db[session_id]) > full_limit:
            # Slicing from the end to keep the most recent history.
            self._session_db[session_id] = self._session_db[session_id][-full_limit:]

    def reset_session(self, session_id):
        """Session wipe out logic (Clear memory)."""
        if session_id in self._session_db:
            del self._session_db[session_id]

#  ZYNQUAR ATELIER  [FILE 7: 10/10 BLUEPRINT ALIGNED]
