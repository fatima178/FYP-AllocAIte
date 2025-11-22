from fastapi import APIRouter, HTTPException

from processing.nlp.chatbot_processing import handle_chatbot_query

router = APIRouter(tags=["Chatbot"])


# -----------------------------------------------------
# MAIN ENDPOINT
# -----------------------------------------------------
@router.post("/chatbot")
def chatbot(data: dict):
    message = data.get("message", "").strip()
    user_id = data.get("user_id")
    if not message:
        raise HTTPException(400, "Missing message")
    if not user_id:
        raise HTTPException(400, "Missing user_id")

    try:
        return handle_chatbot_query(message, int(user_id))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
