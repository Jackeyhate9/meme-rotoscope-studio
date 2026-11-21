import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
base = "/api/v1/studio"

print("=== 1. Test GET /workflows/github ===")
r = client.get(f"{base}/workflows/github")
assert r.status_code == 200
res = r.json()
print("Total GitHub presets:", res["count"])
for w in res["workflows"]:
    print(f" * {w['name']}: {w['stars']} stars, repo: {w['repo']}")

print("\n=== 2. Test GET /canvas/state ===")
r = client.get(f"{base}/canvas/state")
assert r.status_code == 200
state = r.json()
print("Canvas nodes count:", len(state["state"]["nodes"]))
print("Canvas links count:", len(state["state"]["links"]))

print("\n=== 3. Test POST /canvas/fork-branch ===")
r = client.post(f"{base}/canvas/fork-branch", json={"character_name": "赵本山", "engine": "MiniMax 海螺 H3"})
assert r.status_code == 200
fork = r.json()
print("Fork message:", fork["message"])
print("New nodes count:", len(fork["state"]["nodes"]))

print("\n=== 4. Test POST /canvas/save ===")
r = client.post(f"{base}/canvas/save", json={"zoom": 0.95})
assert r.status_code == 200
save_res = r.json()
print("Save result:", save_res["message"])

print("\nALL CANVAS & GITHUB WORKFLOW ENDPOINTS WORKING PERFECTLY!")
