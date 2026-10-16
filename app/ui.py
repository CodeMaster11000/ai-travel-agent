import re

import gradio as gr

from app.agent import plan_trip


def chat(message, history):
    """Generate a trip plan while preserving conversation context."""
    if not message or not message.strip():
        return "Please enter your travel request."

    previous_request = None

    # Find the most recent complete user trip request in the conversation.
    # The agent's parser can reuse its destination, group size, duration and budget.
    user_messages = []
    if history:
        for item in history:
            if isinstance(item, dict):
                if item.get("role") == "user" and item.get("content"):
                    user_messages.append(str(item["content"]))
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                if item[0]:
                    user_messages.append(str(item[0]))

    # Prefer the most recent message that appears to contain all trip fields.
    # If the conversation has only partial follow-ups, fall back to the latest user message.
    required_patterns = (
        re.compile(r"\b(?:trip\s+(?:to|across)|travel\s+to|visit|destination\s+(?:is|to)|in|across)\s+[A-Za-z]", re.I),
        re.compile(r"\b\d+\s*(?:people|persons|travellers|travelers|adults)\b", re.I),
        re.compile(r"\b\d+\s*[- ]?days?\b", re.I),
        re.compile(r"(?:budget|under|within|spend(?:ing)?\s+of)\s*(?:₹|INR\s*|Rs\.?\s*)?[\d,]+", re.I),
    )
    for candidate in reversed(user_messages):
        if all(pattern.search(candidate) for pattern in required_patterns):
            previous_request = candidate
            break
    if previous_request is None and user_messages:
        previous_request = user_messages[-1]

    try:
        # Pass previous context if supported by the agent.
        if previous_request:
            result = plan_trip(
                message.strip(),
                previous_prompt=previous_request,
            )
        else:
            result = plan_trip(message.strip())

        # Handle either a string or a dictionary response.
        if isinstance(result, dict):
            return (
                result.get("response")
                or result.get("itinerary")
                or result.get("plan")
                or str(result)
            )

        return str(result)

    except TypeError as exc:
        # Give a useful error if the agent has a different function signature.
        return (
            f"Could not generate the plan: {exc}\n\n"
            "Check the plan_trip() function signature in app/agent.py."
        )
    except Exception as exc:
        return f"An error occurred while generating your trip plan:\n{exc}"


def launch_ui():
    demo = gr.ChatInterface(
        fn=chat,
        title="AI Travel Planning Agent",
        description=(
            "Plan your trip, estimate costs, check weather, and refine "
            "your itinerary through follow-up messages."
        ),
        examples=[
            "Plan a 3-day trip to Mumbai for 2 people with a budget of ₹15,000.",
            "Plan a 2-day trip to Jaipur for 2 people with a budget of ₹10,000.",
            "Plan a budget-friendly 3-day trip to Goa.",
        ],
        textbox=gr.Textbox(
            placeholder="Describe your destination, budget, and trip duration...",
            container=False,
            scale=7,
        ),
    )

    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    launch_ui()