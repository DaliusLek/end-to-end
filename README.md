# end-to-end
# AI Movie Recommender

## Struktūra
- /data/  -> (X,y) pavyzdžiai
- /prompts/ -> testavimo prompt'ai
- /src/ -> Flask API

## Vartojimas
1. python -m venv venv
2. source venv/bin/activate  # Windows: venv\Scripts\activate
3. pip install -r src/requirements.txt
4. python src/app.py
5. POST į http://127.0.0.1:5000/recommend su JSON body
