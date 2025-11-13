from flask import Flask, render_template, request
import os
from datetime import datetime

from search_engine import (
    load_documents,
    ContextSearchEngine,
    UserContext
)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "documents.json")

documents = load_documents(DATA_PATH)
engine = ContextSearchEngine(documents)

user_context = UserContext(
    location="Kyiv",
    time_segment="any"
)


@app.route("/", methods=["GET", "POST"])
def index():
    basic_results = []
    context_results = []
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        location = request.form.get("location", "").strip()
        time_segment = request.form.get("time_segment", "").strip()

        if location:
            user_context.location = location

        if time_segment in ["morning", "evening", "any"]:
            user_context.time_segment = time_segment

        if query:
            user_context.add_query(query)
            basic_results = engine.search(query)
            context_results = engine.search_with_context(query, user_context)

    context_info = {
        "location": user_context.location,
        "time_segment": user_context.time_segment,
        "query_history": user_context.query_history[-10:], 
        "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return render_template(
        "index.html",
        query=query,
        basic_results=basic_results,
        context_results=context_results,
        context_info=context_info
    )


if __name__ == "__main__":
    app.run(debug=True)
