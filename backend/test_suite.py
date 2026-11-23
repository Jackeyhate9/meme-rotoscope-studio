import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_suite():
    print("=== [1/12] Testing Root Endpoint ===")
    r = client.get("/")
    assert r.status_code == 200, f"Root failed: {r.text}"
    print("✓ Root OK:", r.json()["app"])

    print("\n=== [2/12] Testing Search API & Video Synchronization ===")
    r = client.get("/api/v1/studio/search?keyword=女团&limit=4")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and len(data["items"]) > 0
    first_item = data["items"][0]
    print(f"✓ Search returned {len(data['items'])} items.")
    print(f"  First item: {first_item.get('title')} | 推荐角色: {first_item.get('recommended_character')}")
    assert "recommended_character" in first_item
    assert "suggested_prompt" in first_item

    print("\n=== [3/12] Testing Explore Feed API ===")
    r = client.get("/api/v1/studio/explore")
    assert r.status_code == 200
    explore_data = r.json()
    assert len(explore_data["marquee_news"]) > 0
    assert len(explore_data["top_leaderboard"]) > 0
    print(f"✓ Explore Feed OK: {len(explore_data['templates'])} templates, {len(explore_data['top_leaderboard'])} leaderboard items")

    print("\n=== [4/12] Testing Video Analyze API ===")
    r = client.post("/api/v1/studio/analyze", json={"video_url": "https://www.bilibili.com/video/BV1xx411c7X_KpopDance"})
    assert r.status_code == 200
    analysis = r.json()
    assert analysis["shots_count"] >= 3
    assert len(analysis["recommended_ideas"]) >= 2
    print(f"✓ Video Analyze OK: {analysis['shots_count']} shots detected, {len(analysis['recommended_ideas'])} AI ideas recommended")

    print("\n=== [5/12] Testing User Profile & Credits API ===")
    r = client.get("/api/v1/studio/user/profile")
    assert r.status_code == 200
    initial_credits = r.json()["user"]["credits"]
    print(f"✓ User Credits: {initial_credits}")

    print("\n=== [6/12] Testing Generation Task & Async Render Flow ===")
    r = client.post("/api/v1/studio/generate", json={
        "video_url": "https://www.bilibili.com/video/BV1xx411c7X_KpopDance",
        "target_character": "范德彪",
        "prompt": "反差开原风：范德彪身穿维多利亚西装跳卡点舞",
        "engine": "SEED 2.5",
        "auto_qc": True
    })
    assert r.status_code == 200
    gen_data = r.json()
    task_id = gen_data["task_id"]
    print(f"✓ Task Created: {task_id}, credits deducted: {gen_data['credits_deducted']}, remaining: {gen_data['remaining_credits']}")

    # 轮询任务状态
    r = client.get(f"/api/v1/studio/task/{task_id}")
    assert r.status_code == 200
    task_status = r.json()
    print(f"✓ Task Status Polled: {task_status['status']}, step: {task_status['current_step']}")

    print("\n=== [7/12] Testing Single Shot Reroll (Auto-QC) API ===")
    r = client.post(f"/api/v1/studio/task/{task_id}/reroll-shot", json={"shot_id": 1})
    assert r.status_code == 200
    reroll_data = r.json()
    assert reroll_data["shot_id"] == 1
    assert "9.8" in reroll_data["new_status"]
    print(f"✓ Single-Shot Reroll OK: {reroll_data['new_status']}, remaining credits: {reroll_data['remaining_credits']}")

    print("\n=== [8/12] Testing 30-Day Validity & One-Click Replace Sunset Feature ===")
    # 模拟注入一个 35 天前的老项目
    r = client.post("/api/v1/studio/projects/simulate-expire?days_ago=35")
    assert r.status_code == 200
    simulated_proj = r.json()["project"]
    print(f"✓ Simulated Expired Project created: {simulated_proj['title']}")

    # 获取全部项目，检查有效期及一键替换功能淘汰标志
    r = client.get("/api/v1/studio/projects")
    assert r.status_code == 200
    proj_data = r.json()
    projects = proj_data["projects"]
    print(f"✓ Projects List: Total={proj_data['total']}, Active={proj_data['active_count']}, Expired={proj_data['expired_count']}")

    # 验证有效项目与过期项目的标志
    has_active = False
    has_expired_decommissioned = False
    for p in projects:
        if p["is_expired"]:
            assert p["can_replace"] is False, f"Expired project must have can_replace=False: {p['id']}"
            assert p["remaining_days"] == 0
            has_expired_decommissioned = True
        else:
            assert p["can_replace"] is True, f"Active project must have can_replace=True: {p['id']}"
            assert p["remaining_days"] > 0
            has_active = True

    assert has_active, "Should have active project"
    assert has_expired_decommissioned, "Should have expired project where one-click replace is decommissioned"
    print("✓ Validity contract verified: Active projects allow replacement; >30d projects have one-click replace DECOMMISSIONED!")

    print("\n=== [9/12] Testing One-Click Clean Expired Projects ===")
    r = client.post("/api/v1/studio/projects/clean-expired")
    assert r.status_code == 200
    clean_result = r.json()["data"]
    print(f"✓ Clean Expired OK: Cleaned {clean_result['cleaned_count']} projects, {clean_result['remaining_count']} remaining.")
    assert clean_result["cleaned_count"] >= 1

    # 再次查询，过期项目已被清理，界面不会越积越多
    r = client.get("/api/v1/studio/projects")
    after_clean = r.json()
    assert after_clean["expired_count"] == 0
    print(f"✓ Verified post-cleanup: expired_count is now 0. UI bloat prevented!")

    print("\n=== [10/12] Testing Characters Gene Pool API ===")
    r = client.get("/api/v1/studio/characters")
    assert r.status_code == 200
    chars = r.json()["characters"]
    assert len(chars) >= 4
    print(f"✓ Characters list OK: {len(chars)} characters available")

    # 添加自定义角色
    r = client.post("/api/v1/studio/characters", json={"name": "东北药匣子", "tag": "药匣子", "prompt": "药膳大师手拿药葫芦"})
    assert r.status_code == 200
    print(f"✓ Custom Character added: {r.json()['character']['name']}")

    print("\n=== [11/12] Testing Recharge & Checkout API ===")
    r = client.post("/api/v1/studio/user/recharge", json={"package_name": "爆款创作者包", "credits": 750, "amount": "¥59"})
    assert r.status_code == 200
    print(f"✓ Recharge OK: New balance = {r.json()['total_credits']}")

    print("\n=== [12/12] Testing Admin Ops Console Endpoints ===")
    # 统计大盘
    r = client.get("/api/v1/admin/stats")
    assert r.status_code == 200
    print("✓ Admin Stats OK:", r.json()["metrics"]["today_revenue"])

    # 爬虫审核队列
    r = client.get("/api/v1/admin/crawler-queue")
    assert r.status_code == 200
    queue = r.json()["queue"]
    print(f"✓ Admin Crawler Queue OK: {len(queue)} pending items")

    # 触发爬虫扫描
    r = client.post("/api/v1/admin/crawler/trigger")
    assert r.status_code == 200
    print("✓ Admin Crawler Trigger OK:", r.json()["message"])

    # 审核通过
    first_q_id = queue[0]["id"] if queue else "queue-item-1"
    r = client.post("/api/v1/admin/crawler/approve", json={"queue_id": first_q_id})
    assert r.status_code == 200
    print(f"✓ Admin Approve OK: {r.json()['message']}")

    # 侵权工单
    r = client.get("/api/v1/admin/takedowns")
    assert r.status_code == 200
    takedowns = r.json()["takedowns"]
    print(f"✓ Admin Takedowns OK: {len(takedowns)} tickets")

    print("\n=== [13/14] Testing Agent Reach (B站 & 抖音) Hot & Search Flow ===")
    from app.services.search_service import AgentReachService
    reach_available = AgentReachService.is_available()
    print(f"✓ Agent Reach Engine detected: {reach_available}")
    r = client.get("/api/v1/studio/search?keyword=抖音&category=抖音热歌&limit=4")
    assert r.status_code == 200
    search_data = r.json()
    assert len(search_data["items"]) > 0
    print(f"✓ New Media Platform Search returned {len(search_data['items'])} items (Platform: {search_data['items'][0].get('platform')})")

    print("\n=== [14/14] Testing 一键长视频修改 (Long Video Mode) Pipeline ===")
    r = client.post("/api/v1/studio/analyze", json={
        "video_url": "https://www.bilibili.com/video/BV1xx411c7X_KpopDance",
        "long_video_mode": True
    })
    assert r.status_code == 200
    long_res = r.json()
    assert long_res["long_video_mode"] is True
    assert long_res["video_duration_sec"] >= 60.0
    assert len(long_res["shots"]) >= 8
    print(f"✓ Long Video Analyze OK: {len(long_res['shots'])} continuous shots detected for {long_res['video_duration_sec']}s full MV!")

    # Test Hypit Long Video Generation
    r = client.post("/api/v1/studio/generate", json={
        "video_url": "https://www.bilibili.com/video/BV1xx411c7X_KpopDance",
        "target_character": "范德彪",
        "prompt": "反差开原风：范德彪长视频全片连续转绘",
        "engine": "Local Hypit (FastVideo v2)",
        "long_video_mode": True,
        "auto_qc": True
    })
    assert r.status_code == 200
    long_gen = r.json()
    print(f"✓ Long Video Generation Task OK: {long_gen['task_id']}, engine: {long_gen['engine']}")

    print("\n=== [15/15] Testing MemeMorph MCP Server Tools & Registration ===")
    from app.mcp_server import mcp, search_hot_videos, split_video_scenes, create_rotoscope_task, inspect_video_qc, check_engine_matrix, get_preset_characters, list_projects
    tools = [t.name for t in mcp._tool_manager.list_tools()]
    assert len(tools) >= 7, f"Expected at least 7 MCP tools, got {len(tools)}"
    print(f"✓ MCP Server Registered {len(tools)} tools: {tools}")

    # Test tool 1: search_hot_videos
    search_json = json.loads(search_hot_videos("女团", limit=2))
    assert search_json["status"] == "success"
    assert search_json["count"] > 0
    print(f"✓ MCP search_hot_videos OK: {search_json['count']} videos")

    # Test tool 2: split_video_scenes
    split_json = json.loads(split_video_scenes("test.mp4", long_video_mode=True))
    assert split_json["status"] == "success"
    assert split_json["shots_count"] >= 8
    print(f"✓ MCP split_video_scenes OK: {split_json['shots_count']} shots in long video mode")

    # Test tool 3: check_engine_matrix
    eng_json = json.loads(check_engine_matrix())
    assert eng_json["status"] == "success"
    assert len(eng_json["engines_matrix"]) == 4
    print(f"✓ MCP check_engine_matrix OK: {len(eng_json['engines_matrix'])} engines verified")

    # Test tool 4: inspect_video_qc
    qc_json = json.loads(inspect_video_qc("范德彪"))
    assert qc_json["status"] == "success"
    assert qc_json["qc_report"]["overall_score"] > 0
    print(f"✓ MCP inspect_video_qc OK: score {qc_json['qc_report']['overall_score']}")

    print("\n==================================================")
    print("🎉 ALL 15 API & MCP TEST SUITES PASSED FLAWLESSLY! 🎉")
    print("==================================================")

if __name__ == "__main__":
    test_api_suite()
