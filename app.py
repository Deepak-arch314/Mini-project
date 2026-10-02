"""Flask backend for the Plagiarism Detection mini project.

Run: python app.py      then open http://127.0.0.1:5000
"""
import logging

from flask import Flask, jsonify, render_template, request

import detector
from matchers import MATCHERS

MAX_CHARS = 200_000  # per text

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # reject request bodies > 2 MB
logging.basicConfig(level=logging.INFO)


def error(message: str, status: int):
    return jsonify({"error": message}), status


@app.get("/")
def index():
    return render_template("index.html", algorithms=list(MATCHERS.keys()))


@app.post("/check")
def check():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error("Request must be valid JSON.", 400)

    original, submitted = data.get("original"), data.get("submitted")
    if not isinstance(original, str) or not original.strip():
        return error("Please provide the original/reference text.", 400)
    if not isinstance(submitted, str) or not submitted.strip():
        return error("Please provide the submitted text.", 400)
    if len(original) > MAX_CHARS or len(submitted) > MAX_CHARS:
        return error(f"Each text must be at most {MAX_CHARS:,} characters.", 400)

    algorithm = data.get("algorithm", "ngram")
    try:
        min_words = int(data.get("min_words", 4))
    except (TypeError, ValueError):
        return error("Minimum match length must be a whole number.", 400)
    if not 2 <= min_words <= 20:
        return error("Minimum match length must be between 2 and 20 words.", 400)

    try:
        return jsonify(detector.detect(original, submitted, algorithm, min_words))
    except ValueError as exc:  # bad input / unknown algorithm
        return error(str(exc), 400)
    except Exception:  # unexpected bug
        app.logger.exception("Unexpected error while checking plagiarism")
        return error("Something went wrong on the server. Please try again.", 500)


@app.errorhandler(404)
def not_found(_):
    return error("Resource not found.", 404)


@app.errorhandler(405)
def method_not_allowed(_):
    return error("Method not allowed.", 405)


@app.errorhandler(413)
def too_large(_):
    return error("The submitted data is too large (limit 2 MB).", 413)


if __name__ == "__main__":
    app.run(debug=True)