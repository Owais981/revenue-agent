"""Generates a human-review-only draft artifact (email / questions / call notes) for
a selected action. Uses Gemini for natural phrasing when available; falls back to a
plain template so the app never breaks without an API key. No draft is ever sent
automatically - the UI always requires Approve before anything goes out."""
from app.models.action import ActionType
from app.services.gemini_service import call_text, GeminiUnavailableError, UNTRUSTED_CONTENT_GUARD


def _template_draft(action_type: ActionType, lead_context: dict, missing_fields: list) -> str:
    company = lead_context.get("company") or "there"
    if action_type == ActionType.SEND_INTRO_EMAIL:
        return (
            f"Subject: Great to connect, {company}\n\n"
            f"Hi,\n\nThanks for reaching out about {lead_context.get('service') or 'your project'}. "
            "I'd love to learn more about what you have in mind - could we grab 15 minutes this week?\n\n"
            "Best regards"
        )
    if action_type == ActionType.SEND_CASE_STUDY:
        return (
            f"Subject: A similar project we delivered for {lead_context.get('industry') or 'a comparable client'}\n\n"
            "Hi,\n\nThought this recent project might be relevant to what you're planning. Happy to share more "
            "detail or hop on a call.\n\nBest regards"
        )
    if action_type == ActionType.REQUEST_BRIEF_DETAIL:
        missing_list = "\n".join(f"- {f}" for f in missing_fields) or "- additional brief details"
        return f"Subject: A couple of quick questions\n\nHi,\n\nTo scope this properly, could you share:\n{missing_list}\n\nThanks!"
    if action_type == ActionType.CALL_NOW:
        return "Call notes: Confirm scope, timeline, and budget verbally. Time-sensitive - call today."
    return ""


def generate_draft(action_type: ActionType, lead_context: dict, raw_text: str, missing_fields: list) -> str:
    if action_type not in (
        ActionType.SEND_INTRO_EMAIL,
        ActionType.SEND_CASE_STUDY,
        ActionType.REQUEST_BRIEF_DETAIL,
        ActionType.CALL_NOW,
    ):
        return ""

    try:
        prompt = f"""
{UNTRUSTED_CONTENT_GUARD}

Write a short, professional draft for a sales rep at a video production company to
review and send manually (they will approve or edit it - you are not sending anything).
Action type: {action_type.value}
Lead context: {lead_context}
Missing brief fields (if action is REQUEST_BRIEF_DETAIL): {missing_fields}

Do not state any price, discount, or firm delivery date. Do not make promises about
availability. Keep it under 120 words. Return plain text only, no markdown.

<untrusted_content>
{raw_text or ''}
</untrusted_content>
"""
        return call_text(prompt)
    except GeminiUnavailableError:
        return _template_draft(action_type, lead_context, missing_fields)
