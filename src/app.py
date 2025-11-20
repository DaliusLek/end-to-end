import os
import json
from flask import Flask, request, jsonify
from glob import glob
from pathlib import Path
from dotenv import load_dotenv
import openai

load_dotenv()  # if .env present
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

app = Flask(__name__)

def load_local_movies():
    # Simple local "DB": collect movies from all sample files (for demo)
    movies = []
    for f in glob(str(DATA_DIR / "*.json")):
        try:
            j = json.load(open(f, "r", encoding="utf-8"))
            # try to extract movie list from y.recommended_movies OR full example dataset
            if "y" in j and "recommended_movies" in j["y"]:
                for m in j["y"]["recommended_movies"]:
                    movies.append({
                        "title": m.get("title"),
                        "genres": m.get("genres", []),
                        "duration": m.get("duration", None),
                        "synopsis": m.get("explanation", "")
                    })
        except Exception:
            continue
    # Fallback: small hardcoded list if no data present
    if not movies:
        movies = [
            {"title":"La La Land","genres":["drama","romance"],"duration":128,"synopsis":""},
            {"title":"Edge of Tomorrow","genres":["action","sci-fi"],"duration":113,"synopsis":""},
            {"title":"Superbad","genres":["comedy"],"duration":113,"synopsis":""}
        ]
    return movies

def filter_candidates(movies, prefs):
    mood = prefs.get("mood","").lower()
    genres = [g.lower() for g in prefs.get("genres",[])]
    max_dur = prefs.get("max_duration", None)

    def matches(m):
        # genre match if any genre intersects (simple)
        if genres:
            movie_genres = [g.lower() for g in m.get("genres",[])]
            if not any(g in movie_genres for g in genres):
                return False
        if max_dur and m.get("duration"):
            if m["duration"] > max_dur:
                return False
        return True

    return [m for m in movies if matches(m)]

def call_ai_generate_explanations(candidates, prefs):
    # If OPENAI_KEY not set, return dummy explanations
    if not OPENAI_KEY:
        out = []
        for c in candidates[:3]:
            out.append({
                "title": c["title"],
                "explanation": f"Stubai: {c['title']} sugerina nuotaiką '{prefs.get('mood')}' ir atitinka žanrus {prefs.get('genres')}"
            })
        return out

    # Compose prompt
    prompt = f"""Tu esi filmų rekomendacijų asistentas.
Vartotojo pageidavimai: nuotaika: {prefs.get('mood')}, žanrai: {prefs.get('genres')}, max_duration: {prefs.get('max_duration')}
Duoti kandidatai:
"""
    for c in candidates:
        prompt += f"- {c.get('title')} (genres: {c.get('genres')}, duration: {c.get('duration')})\n"
    prompt += "\nUžduotis: surūšiuok top 3 kandidatus ir trumpai (1-2 sakiniai) paaiškink, kodėl kiekvienas tinka.\n"

    # Call ChatCompletion
    response = openai.ChatCompletion.create(
        model="gpt-4",  # pakeisk pagal savo prieinamumą
        messages=[{"role":"system","content":"You are a helpful movie recommender."},
                  {"role":"user","content":prompt}],
        max_tokens=400,
        temperature=0.7,
    )
    text = response["choices"][0]["message"]["content"]
    # Simple parsing: return the raw text as explanation list
    # For demo, we will wrap the full text under one explanation
    return [{"title":"AI_explanations","explanation": text}]

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json or {}
    prefs = data.get("preferences") or data.get("X") or {}
    # load movies
    movies = load_local_movies()
    candidates = filter_candidates(movies, prefs)
    if not candidates:
        return jsonify({"error":"No candidates found"}), 404

    ai_out = call_ai_generate_explanations(candidates, prefs)
    rec = {
        "movies": candidates[:5],
        "ai": ai_out
    }
    return jsonify(rec)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
