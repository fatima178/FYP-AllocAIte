from fastapi import APIRouter, HTTPException

from processing.nlp.chatbot_processing import get_chatbot_suggestions, handle_chatbot_query

router = APIRouter(tags=["Chatbot"])


# -----------------------------------------------------
# MAIN ENDPOINT
# -----------------------------------------------------
@router.post("/chatbot")
def chatbot(data: dict):
    # receive a chat message and pass it into the chatbot processing layer
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


@router.get("/chatbot/suggestions")
def chatbot_suggestions(user_id: int):
    # suggestions are based on the manager's current uploaded data
    if not user_id:
        raise HTTPException(400, "Missing user_id")

    try:
        return {"suggestions": get_chatbot_suggestions(int(user_id))}
    except ValueError as exc:
        raise HTTPException(400, str(exc))
