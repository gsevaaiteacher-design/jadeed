"""
PROJECT: Z-STUDIO V12.3 (PHASE 2 - AI ENGINE)
SIGNATURE: ZYNQUAR ATELIER
FILE 10: execution_graph.py
ROLE: Brain Controller (Decision & Loop System)
-----------------------------------------------------------------------
"""

class ExecutionGraph:
    """
     ROLE: Pure pipeline ka decision system.
     LOGIC: Decide karta hai ki tool call karna hai, retry karna hai ya output dena hai.
    """

    def __init__(self):
        self.max_loops = 3  # Prevent infinite tool-calling loops
        self._current_loop = 0

    def analyze_and_route(self, response_text, system_state):
        """
         INPUT: response_text (from inference), system_state (current context)
         LOGIC: Parse response for tool calls or direct answers.
         OUTPUT: action_plan: dict
        """
        self._current_loop += 1

        # 1. Check for Tool Calling Pattern (e.g., [TOOL: BROWSER])
        tool_request = self._parse_tool_call(response_text)

        # 2. Decision Logic (Blueprint Rule)
        if tool_request and self._current_loop <= self.max_loops:
            return {
                "action": "CALL_TOOL",
                "tool_name": tool_request['name'],
                "tool_args": tool_request['args'],
                "status": "CONTINUE"
            }
        
        # 3. Final Output Decision
        if self._current_loop > self.max_loops:
            return {
                "action": "FINAL_OUTPUT",
                "data": response_text,
                "status": "LOOP_EXCEEDED_WARNING"
            }

        return {
            "action": "FINAL_OUTPUT",
            "data": response_text,
            "status": "COMPLETE"
        }

    def _parse_tool_call(self, text):
        """
        AI ke response me se tool pattern detect karta hai.
        Example: "I need to check the file. [TOOL: FILE_READ args='config.json']"
        """
        import re
        pattern = r"\[TOOL:\s*(?P<name>\w+)\s*args=['\"](?P<args>.*?)['\"]\]"
        match = re.search(pattern, text)
        
        if match:
            return {
                "name": match.group("name"),
                "args": match.group("args")
            }
        return None

    def reset_graph(self):
        """Loop counter reset for new user input."""
        self._current_loop = 0

#  ZYNQUAR ATELIER  [FILE 10: 10/10 BLUEPRINT ALIGNED]
