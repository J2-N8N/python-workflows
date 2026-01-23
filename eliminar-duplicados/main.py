import hashlib
from pathlib import Path
from textwrap import indent
from fastapi import FastAPI
from pydantic import BaseModel
import json
app = FastAPI(title="Duplicate detector API")


class FileItem(BaseModel):
    path: str  # path: /users/jota/...


class HashRequest(BaseModel):
    files: list[FileItem]  # [{path: /users/jota/...}]


# se va a leer el archivo mega x mega
def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    # Garantizamos que el archivo que vamos abrir se cierre si todo sale bien o mal, rb es de lectura de un binario.
    with path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)  # leemos un MB del archivo
            if not chunk:
                # salimos del ciclo
                break
            # actualizamos los nuevos bytes al algoritmo sha256 construye el hash hasta el final.
            hasher.update(chunk)
    # devolvemos el hash final
    return hasher.hexdigest()


@app.post("/duplicates")
def duplicates(payload: HashRequest):
    #print(f"payload: {payload.model_dump()}")
    print(json.dumps(payload.model_dump(),indent=2,ensure_ascii=False))
    results = []
    for item in payload.files:
        #print(f"item: {item}")
        # convertimos el string item.path a un objeto de tipo Path
        path = (
            Path(item.path).expanduser().resolve()
        )  # convertimos y normalizamos las rutas ~/x -> /Users/jota/
        #print(f"path: {path}")
        if not path.exists():
            results.append({"path": item.path, "ok": False, "error": "not_found"})
            continue  # seguimos a la siguiente iteracion
        if not path.is_file():
            results.append({"path": item.path, "ok": False, "error": "not_a_file"})
            continue  # seguimos a la siguiente iteracion

        # en este punto el archivo es valido
        try:
            digest = sha256_file(path)
            results.append(
                {
                    "path": str(path),
                    "ok": True,
                    "sha256": digest,
                    "size": path.stat().st_size,
                    "name": path.name,
                }
            )

        except PermissionError:
            results.append(
                {"path": str(path), "ok": False, "error": "permission_denied"}
            )
        except Exception as e:
            results.append({"path": str(path), "ok": False, "error": str(e)})
    print(f"results: {json.dumps(results,indent=2,ensure_ascii=False)}")
    ok=[result for result in results if result.get("ok")]
    print(f"ok: {json.dumps(ok,indent=2,ensure_ascii=False)}")
    by_hash={}
    for result in ok:
        #!Creamos dinamicamente el diccionario con sus respectivas llaves de acuerdo a cada hash
         #by_hash= {'sdfsdfsfsfsfsdfsdf':['archivo1.txt','archivo2.txt'],
        # 'dtryryfghfrtyrty:['archivo3.txt','archivo4.txt']
        # }
        by_hash.setdefault(result["sha256"],[]).append(result)
        
        dups=[]
        #print(by_hash)
        for hash_key,group in by_hash.items():
            # hash_key, group
            # 'dtryryfghfrtyrty:['archivo3.txt','archivo4.txt']
            if len(group) > 1: # si hay duplicados.
                dups.append({
                    "hash":hash_key,
                    "count":len(group),
                    "keep": group[0]["path"], #mantengo al primer archivo que encuentre
                    "duplicates": [group_item["path"] for group_item in group[1:] ]
                })
        #print(dups)
    print(f"by_hash: {json.dumps(by_hash,indent=2,ensure_ascii=False)}")
    print(f"dups: {json.dumps(dups,indent=2,ensure_ascii=False)}")
    return {
            "scanned":len(results),
            "ok":len(ok),
            "duplicates_count":len(dups),
            "duplicates":dups,
            "results":results
    }