"""AskUserQuestion tool - Interactive user prompts with multiple choice"""

from cosmux.tools.base import BaseTool, ToolOutput


class AskUserQuestionTool(BaseTool):
    """
    Ask the user interactive questions with multiple choice options.

    This tool sends questions to the UI and waits for user responses.
    The actual response handling is done by the AgentOrchestrator.
    """

    name = "AskUserQuestion"
    description = """Ask the user questions during execution. Use this to:
1. Gather user preferences or requirements
2. Clarify ambiguous instructions
3. Get decisions on implementation choices
4. Offer choices about what direction to take

Users can always select 'Other' to provide custom text input."""

    async def execute(self, input_data: dict, workspace_path: str) -> ToolOutput:
        """
        This tool doesn't execute directly - it signals to the orchestrator
        that we need to wait for user input. The actual execution is handled
        by the AgentOrchestrator which yields the question_prompt event.
        """
        questions = input_data.get("questions", [])

        # Validate questions
        if not questions:
            return ToolOutput(
                success=False,
                error="No questions provided"
            )

        if len(questions) > 4:
            return ToolOutput(
                success=False,
                error="Maximum 4 questions allowed"
            )

        for i, q in enumerate(questions):
            if "question" not in q:
                return ToolOutput(
                    success=False,
                    error=f"Question {i} missing 'question' field"
                )
            if "options" not in q:
                return ToolOutput(
                    success=False,
                    error=f"Question {i} missing 'options' field"
                )

            options = q.get("options", [])
            if len(options) < 2:
                return ToolOutput(
                    success=False,
                    error=f"Question {i} must have at least 2 options"
                )
            if len(options) > 4:
                return ToolOutput(
                    success=False,
                    error=f"Question {i} can have at most 4 options"
                )

            for j, opt in enumerate(options):
                if "label" not in opt:
                    return ToolOutput(
                        success=False,
                        error=f"Question {i}, option {j} missing 'label'"
                    )
                if "description" not in opt:
                    return ToolOutput(
                        success=False,
                        error=f"Question {i}, option {j} missing 'description'"
                    )

        # Return success - actual waiting for response is handled by orchestrator
        return ToolOutput(
            success=True,
            result="Questions validated - awaiting user response"
        )

    def get_schema(self) -> dict:
        """Return the tool schema for Claude API"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "description": "Questions to ask the user (1-4 questions)",
                        "minItems": 1,
                        "maxItems": 4,
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "The complete question to ask. Should be clear and end with a question mark."
                                },
                                "header": {
                                    "type": "string",
                                    "description": "Very short label (max 12 chars). Examples: 'Framework', 'Auth method'",
                                    "maxLength": 12
                                },
                                "options": {
                                    "type": "array",
                                    "description": "Available choices (2-4 options). User can always select 'Other' for custom input.",
                                    "minItems": 2,
                                    "maxItems": 4,
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "label": {
                                                "type": "string",
                                                "description": "Display text for this option (1-5 words). Add '(Recommended)' if this is the recommended choice."
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "Explanation of what this option means or what happens if chosen."
                                            }
                                        },
                                        "required": ["label", "description"]
                                    }
                                },
                                "multiSelect": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "If true, user can select multiple options."
                                }
                            },
                            "required": ["question", "header", "options", "multiSelect"]
                        }
                    }
                },
                "required": ["questions"]
            }
        }
