import re
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from collections import Counter

app = FastAPI(title="N8N + PythoN")

class IncomingData(BaseModel):
    text:str
    source:str  | None

#Palabras que no se van a contabalizar
SPANISH_STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las",
    "por", "un", "para", "con", "no", "una", "su", "al", "lo", "como",
    "más", "mas", "o", "pero", "sus", "le", "ya", "si", "porque", "cuando",
    "muy", "sin", "sobre", "también", "tambien", "me", "hasta", "hay",
    "donde", "han", "quien", "entre", "está", "esta", "ser", "son",
}


def tokenize(text: str) -> List[str]:
    text = text.lower()
    return re.findall(r"[a-záéíóúüñ]+", text, flags=re.IGNORECASE)

@app.post("/analyze")
def analize(data:IncomingData):
    #found_words=data.text.strip().split(" ")
    #print(found_words)
    text=data.text.strip()
    tokens=tokenize(text)
    word_count=len(tokens)
    filtered_tokens=[ token for token in tokens if token not in SPANISH_STOPWORDS]
    counter=Counter(filtered_tokens)
    unique_word_count=len(counter)
    #Creamos dinamicamente una lista de diccionarios con el top 10
    top_words=[{"word":word,"count":count} for word,count in counter.most_common(10)]
    return {
        "received_text":data.text,
        "char_count" : len(data.text),
        "source": data.source,
        "unique_word_count":unique_word_count,
        "words_count":word_count,
        "top_words":top_words
    }
@app.get("/")
def health_check():
    return {"status": "ok", "message": "API funcionando OK :)"}
