"""Fulfillment function for the chatbot"""

# This function handles the fulfillment of the chatbot's intent based on user input.
def handler(event, context):
    genre = None
    slots = event['sessionState']['intent']['slots'] 
    mood = slots.get('mood', {}) \
            .get('value', {}) \
                .get('interpretedValue', '') \
                    .lower()
    if slots["genre"]:
        genre = slots.get('genre', {}) \
                .get('value', {}) \
                    .get('interpretedValue', '') \
                        .lower()

    # Simple hardcoded recommendations
    suggestions = {
        'happy': '🎵 "Happy" by Pharrell Williams',
        'sad': '🎵 "Someone Like You" by Adele',
        'energetic': '🎵 "Eye of the Tiger" by Survivor',
    }

    song = suggestions.get(mood, '🎵 "Here Comes the Sun" by The Beatles')

    response = {
        "sessionState": {
            "dialogAction": {"type": "Close"},
            "intent": {
                "name": event["sessionState"]["intent"]["name"],
                "state": "Fulfilled"
            }
        },
        "messages": [{
            "contentType": "PlainText",
            "content": f"Based on your mood, I recommend: {song}"
        }]
    }

    return response
