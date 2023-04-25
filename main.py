from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import requests
from replit import db
import asyncio as aio

EXTENSION_PREFIX = "extension_clicks_"
EXTENSIONS_URL = "https://awesome-arcade-extensions.vercel.app/extensions.json"
REVALIDATION_PERIOD = 60 * 5
RATE_LIMIT = "30/minute"

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
@limiter.limit(RATE_LIMIT)
async def route_root(request: Request):
    return RedirectResponse("/all/", status_code=308)

@app.get("/all/")
@limiter.limit(RATE_LIMIT)
async def route_all(request: Request):
    extensionCLicks = {}
    
    for key in db.prefix(EXTENSION_PREFIX):
        extensionCLicks[key.replace(EXTENSION_PREFIX, "")] = db[key]
        
    return extensionCLicks

@app.get("/count/")
@limiter.limit(RATE_LIMIT)
async def route_count(repo: str, request: Request):
    key = EXTENSION_PREFIX + repo
    if key not in db:
        raise HTTPException(status_code=404, detail=f"{repo} does not exist.")
        
    return { repo: db[key] }

@app.get("/click/")
@limiter.limit(RATE_LIMIT)
async def route_click(repo: str, request: Request):
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80)
