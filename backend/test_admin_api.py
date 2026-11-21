import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
base = "/api/v1"

print('--- 1. Testing /admin/stats ---')
r = client.get(f'{base}/admin/stats')
assert r.status_code == 200
stats = r.json()
print('Metrics:', stats['metrics'])

print('\n--- 2. Testing /admin/crawler-queue ---')
r = client.get(f'{base}/admin/crawler-queue')
assert r.status_code == 200
queue = r.json()
print(f'Queue items: {len(queue["queue"])}')

print('\n--- 3. Testing /admin/crawler/trigger ---')
r = client.post(f'{base}/admin/crawler/trigger', json={})
assert r.status_code == 200
trigger_res = r.json()
print('Trigger result:', trigger_res.get('message'))

print('\n--- 4. Testing /admin/takedowns ---')
r = client.get(f'{base}/admin/takedowns')
assert r.status_code == 200
takedowns = r.json()
print(f'Takedowns count: {len(takedowns["takedowns"])}')

print('\n--- 5. Testing /studio/projects (validity & age) ---')
r = client.get(f'{base}/studio/projects')
assert r.status_code == 200
projects = r.json()
print(f'Projects count: {len(projects["projects"])}')
for p in projects['projects']:
    print(f"Project {p['id']}: age={p.get('age_days')}d, expired={p.get('is_expired')}, can_replace={p.get('can_replace')}, badge={p.get('validity_badge')}")

print('\n--- 6. Testing /studio/projects/simulate-expire ---')
r = client.post(f'{base}/studio/projects/simulate-expire', json={})
assert r.status_code == 200
sim_res = r.json()
print('Simulate expire result:', sim_res.get('message'))

# Re-check projects after simulate expire
r = client.get(f'{base}/studio/projects')
assert r.status_code == 200
projects_after_sim = r.json()
expired_list = [p for p in projects_after_sim['projects'] if p.get('is_expired')]
print(f'Expired projects found: {len(expired_list)}')

print('\n--- 7. Testing /studio/projects/clean-expired ---')
r = client.post(f'{base}/studio/projects/clean-expired', json={})
assert r.status_code == 200
clean_res = r.json()
print('Clean result:', clean_res)

r = client.get(f'{base}/studio/projects')
assert r.status_code == 200
projects_final = r.json()
print(f'Remaining projects count: {len(projects_final["projects"])}')
assert all(not p.get('is_expired') for p in projects_final['projects'])
print('All expired projects successfully cleaned up!')
