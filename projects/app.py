# Service projets : créer et lire les projets, stockés dans CouchDB.
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

COUCHDB_URL = os.environ.get("COUCHDB_URL", "http://admin:admin@localhost:5984")
REGION = os.environ.get("REGION", "A")
DB = "projects"

couch = httpx.Client(base_url=COUCHDB_URL)


@asynccontextmanager
async def lifespan(app):
    # Au démarrage : créer la base si elle n'existe pas (412 = existe déjà)
    r = couch.put(f"/{DB}")
    if r.status_code not in (201, 202, 412):
        r.raise_for_status()
    yield


app = FastAPI(title="Service projets", lifespan=lifespan)


class NewProject(BaseModel):
    # L'identifiant sert ensuite dans les URL et dans la table de routage :
    # lettres, chiffres, tirets, et pas de "_" au début (réservé par CouchDB)
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9-]*$")
    name: str


def to_project(doc):
    return {"id": doc["_id"], "name": doc["name"], "region": doc["region"]}


@app.post("/projects", status_code=201)
def create_project(project: NewProject):
    # Le projet vit dans la région du service qui le crée
    doc = {"name": project.name, "region": REGION}
    r = couch.put(f"/{DB}/{project.id}", json=doc)
    if r.status_code == 409:
        raise HTTPException(409, "Ce projet existe déjà")
    if r.status_code not in (201, 202):
        raise HTTPException(502, "CouchDB a refusé l'écriture")
    doc["_id"] = project.id
    return to_project(doc)


@app.get("/projects/{project_id}")
def get_project(project_id: str):
    r = couch.get(f"/{DB}/{project_id}")
    if r.status_code == 404:
        raise HTTPException(404, "Projet introuvable")
    if r.status_code != 200:
        raise HTTPException(502, "CouchDB n'a pas répondu correctement")
    return to_project(r.json())
