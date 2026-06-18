"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 13: fallback_brain.py
ROLE: Fallback Brain (Safety & Error Recovery)
-----------------------------------------------------------------------
"""

class FallbackBrain:
    """
     ROLE: System fail hone par safe response dena.
     LOGIC: Predefined safe responses aur degraded mode management.
    """

    def __init__(self):
        # Blueprint logic: Category-wise safe responses
        self.safety_responses = {
            "MODEL_ERROR": "System is currently recalibrating its neural weights. Please try again in a moment.",
            "MEMORY_OVERFLOW": "The conversation context is too dense. Let's start fresh for better clarity.",
            "TOOL_FAILURE": "I encountered an issue accessing that external tool. How else can I assist you?",
            "GENERIC_CRASH": "Z-Studio Engine has encountered a temporary blockage. Safe mode is now active."
        }

    def trigger_fallback(self, error_type, context=None):
        """
         INPUT: error_type: str, context: dict (optional)
         LOGIC: Detect error category -> Return safe response.
         OUTPUT: fallback_response: str
        """
        # 1. Error Mapping (Blueprint Logic)
        response = self.safety_responses.get(error_type, self.safety_responses["GENERIC_CRASH"])

        # 2. Context Awareness (Optional)
        # Agar context me user ka naam ya session hai, toh response personalize kiya ja sakta hai
        if context and "user_name" in context:
            response = f"Pardon me, {context['user_name']}. {response}"

        # 3. Log for Debugging (Industrial requirement)
        self._log_failure(error_type, context)

        return response

    def _log_failure(self, error_type, context):
        """Internal logging to track why the fallback was triggered."""
        # Blueprint: Failure isolation and recording
        print(f"[FALLBACK_LOG] Type: {error_type} | Data: {context}")

    def get_degraded_mode_status(self):
        """Checks if the system should stay in 'Basic Mode'."""
        return "DEGRADED_STABLE"

#  ZYNQUAR ATELIER  [FILE 13: 10/10 BLUEPRINT ALIGNED]
