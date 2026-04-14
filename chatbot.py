import json
import random
import re

with open("intents.json") as file:
    data = json.load(file)


def clean_text(text):
    return re.findall(r'\b\w+\b', text.lower())


def similarity(user_words, pattern_words):
    return len(set(user_words) & set(pattern_words))


def get_response(user_input):
    user_words = clean_text(user_input)

    best_score = 0
    best_intent = None

    for intent in data["intents"]:
        for pattern in intent["patterns"]:
            pattern_words = clean_text(pattern)

            score = similarity(user_words, pattern_words)

            if score > best_score:
                best_score = score
                best_intent = intent

    if best_intent and best_score > 0:
        return random.choice(best_intent["responses"])

    return "Sorry, I didn’t understand that. Can you rephrase?"
