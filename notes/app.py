# Service notes : ajouter et lire les notes d'un projet, stockées dans CouchDB.
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

COUCHDB_URL = os.environ.get("COUCHDB_URL", "http://admin:admin@localhost:5984")
DB = "notes"

couch = httpx.Client(base_url=COUCHDB_URL)


@asynccontextmanager
async def lifespan(app):
    # Au démarrage : créer la base si elle n'existe pas (412 = existe déjà)
    r = couch.put(f"/{DB}")
    if r.status_code not in (201, 202, 412):
        r.raise_for_status()
    # Index pour retrouver vite les notes d'un projet, triées par date
    couch.post(f"/{DB}/_index", json={
        "index": {"fields": ["project", "created_at"]},
        "name": "par-projet",
    }).raise_for_status()
    yield


app = FastAPI(title="Service notes", lifespan=lifespan)


class NewNote(BaseModel):
    author: str
    text: str


def to_note(doc):
    return {
        "id": doc["_id"],
        "project": doc["project"],
        "author": doc["author"],
        "text": doc["text"],
        "created_at": doc["created_at"],
    }


@app.post("/projects/{project_id}/notes", status_code=201)
def add_note(project_id: str, note: NewNote):
    doc = {
        "project": project_id,
        "author": note.author,
        "text": note.text,
        # Format fixe en UTC : le tri de CouchDB compare les dates comme du texte
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    r = couch.post(f"/{DB}", json=doc)
    if r.status_code not in (201, 202):
        raise HTTPException(502, "CouchDB a refusé l'écriture")
    doc["_id"] = r.json()["id"]
    return to_note(doc)


@app.get("/projects/{project_id}/notes")
def list_notes(project_id: str):
    r = couch.post(f"/{DB}/_find", json={
        "selector": {"project": project_id},
        "sort": [{"project": "asc"}, {"created_at": "asc"}],
        "limit": 100000,  # par défaut CouchDB n'en renvoie que 25
    })
    if r.status_code != 200:
        raise HTTPException(502, "CouchDB n'a pas répondu correctement")
    return [to_note(d) for d in r.json()["docs"]]
