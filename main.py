from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import requests
from replit import db
import asyncio as aio

app = FastAPI()

EXTENSION_PREFIX = "extension_clicks_"
EXTENSIONS_URL = "https://awesome-arcade-extensions.vercel.app/extensions.json"
REVALIDATION_PERIOD = 60 * 5

@app.get("/")
async def route_root():
    return RedirectResponse("/all/", status_code=308)

@app.get("/all/")
async def route_all():
    extensionCLicks = {}
    
    for key in db.prefix(EXTENSION_PREFIX):
        extensionCLicks[key.replace(EXTENSION_PREFIX, "")] = db[key]
        
    return extensionCLicks

@app.get("/count/")
async def route_click(repo: str):
    key = EXTENSION_PREFIX + repo
    if key not in db:
        raise HTTPException(status_code=404, detail=f"{repo} does not exist.")
        
    return { repo: db[key] }

@app.get("/click/")
async def route_click(repo: str):
    key = EXTENSION_PREFIX + repo
    if key not in db:
        raise HTTPException(status_code=404, detail=f"{repo} does not exist.")
        
    db[key] += 1
    
    return { repo: db[key] }

async def revalidate_extensions_task():
    while True:
        print("Revalidating extensions")
        
        response = requests.get(EXTENSIONS_URL)
        json = response.json()
        
        count = 0
        
        for section in json.values():
            for ext in section:
                repo = EXTENSION_PREFIX + ext["repo"]
                count += 1
                if repo not in db:
                    db[repo] = 0
                    
        print(f"Validated {count} extensions")        
    
        await aio.sleep(REVALIDATION_PERIOD)

@app.on_event("startup")
async def on_startup():
    aio.create_task(revalidate_extensions_task())
