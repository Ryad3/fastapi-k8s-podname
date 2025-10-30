import os 
import fastapi

app = fastapi.FastAPI()

@app.get("/get-podname")
async def get_podname():
    pod_name = os.getenv("POD_NAME", "Pod name not set")
    return {"pod_name": pod_name}