import re
import html
import random
import logging
import shutil
import subprocess
import json
import urllib.parse
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from curl_cffi import requests
except ImportError:
    import urllib.request as urllib_req
    requests = None

def clean_html(text: str) -> str:
    if not text:
        return ""
    plain = re.sub(r'<[^>]+>', '', text)
    return html.unescape(plain).strip()

# 精选预置二创舞蹈与爆款模板库 (作为热搜基座与超快兜底池，包含近期现象级爆款 MV)
CURATED_MEME_TEMPLATES = [
    {
        "bvid": "BV1xx411c7X_KpopDance",
        "title": "【女团打歌】aespa - Supernova / Whiplash 标志性魔性卡点直拍",
        "duration": "03:15",
        "author": "SM_Official",
        "play": 1284000,
        "description": "2025-2026 现象级卡点女团舞台，节奏明快，单人C位击剑与跨步手势极具二创张力。",
        "url": "https://www.bilibili.com/video/BV1xx411c7X_KpopDance",
        "pic": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=800&auto=format&fit=crop",
        "category": "K-Pop 卡点舞",
        "shots_count": 4,
        "recommended_character": "范德彪",
        "suggested_prompt": "反差开原风：范德彪身穿维多利亚定制西装，神情霸气跳 K-Pop 卡点女团舞，保留经典鹰爪挠手势",
        "heat_tag": "热度 128.4w",
        "is_curated": True,
        "platform": "B站"
    },
    {
        "bvid": "BV1yy411d8Y_LockDance",
        "title": "【机械锁舞】西装暴徒经典锁步与滑步 Solo · 重低音律动",
        "duration": "02:40",
        "author": "StreetDance_China",
        "play": 941000,
        "description": "开原大舞厅重低音律动，手部高频震感与太空步融合，适合东北喜剧人设。",
        "url": "https://www.bilibili.com/video/BV1yy411d8Y_LockDance",
        "pic": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
        "category": "东北本山宇宙",
        "shots_count": 4,
        "recommended_character": "赵本山",
        "suggested_prompt": "全员复古：身穿经典蓝色中山棉袄、头戴雷锋羊毛帽，雪地舞台光效，配合机械锁步卡点",
        "heat_tag": "热度 94.1w",
        "is_curated": True,
        "platform": "B站"
    },
    {
        "bvid": "BV1Apt2026_RoseBruno",
        "title": "【洗脑神曲】ROSÉ & Bruno Mars - 《APT.》全球爆款打歌卡点 MV",
        "duration": "02:53",
        "author": "Atlantic_Records",
        "play": 2150000,
        "description": "全网刷屏魔性酒桌律动，节奏极度上头，双人互动与高频卡点头部运镜。",
        "url": "https://www.bilibili.com/video/BV1961uYiEhR",
        "pic": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=800&auto=format&fit=crop",
        "category": "流行热歌",
        "shots_count": 4,
        "recommended_character": "范德彪",
        "suggested_prompt": "开原大酒楼风：范德彪与赵本山跳洗脑 APT. 摇摆舞步，双手打节拍，眼神凝重严肃反差拉满",
        "heat_tag": "全球榜 TOP1",
        "is_curated": True,
        "platform": "抖音 / B站"
    },
    {
        "bvid": "BV1NewJeans_HypeBoy",
        "title": "【清爽律动】NewJeans - Hype Boy / How Sweet 青春元气街头齐舞",
        "duration": "02:58",
        "author": "ADOR_Music",
        "play": 1180000,
        "description": "街头自然运镜，Y2K 潮流复古律动，四肢舒展度极高，适合各类次元置换。",
        "url": "https://www.bilibili.com/video/BV1fDqiYNEuf",
        "pic": "https://images.unsplash.com/photo-1524712245354-2c4e5e7121c0?q=80&w=800&auto=format&fit=crop",
        "category": "K-Pop 卡点舞",
        "shots_count": 3,
        "recommended_character": "赛博大花袄",
        "suggested_prompt": "国潮反差风：东北大花袄少女跳 Y2K 街头元气舞，霓虹舞台色调，动作轻盈自然",
        "heat_tag": "热度 118w",
        "is_curated": True,
        "platform": "B站"
    },
    {
        "bvid": "BV1zz411e9Z_LatinDuo",
        "title": "【双人国标】亮剑双雄默契拉丁舞·绝美同步转体名场面",
        "duration": "03:05",
        "author": "DanceGalaxy",
        "play": 729000,
        "description": "双人 SAM 2 独立遮罩跟踪，双人互动张力拉满，正剧人物下场跳舞引发爆笑。",
        "url": "https://www.bilibili.com/video/BV1zz411e9Z_LatinDuo",
        "pic": "https://images.unsplash.com/photo-1547153760-18fc86324498?q=80&w=800&auto=format&fit=crop",
        "category": "影视剧经典",
        "shots_count": 4,
        "recommended_character": "李云龙",
        "suggested_prompt": "亮剑反差风：李云龙与楚云飞身穿军装跳深情双人拉丁舞，眼神充满战友情深与爆笑戏剧反差",
        "heat_tag": "热度 72.9w",
        "is_curated": True,
        "platform": "B站"
    },
    {
        "bvid": "BV1JayChou_HuoYuanJia",
        "title": "【国风电音】周杰伦 - 《霍元甲 / 本草纲目》经典中国风街舞重混",
        "duration": "03:40",
        "author": "JVR_Music",
        "play": 1640000,
        "description": "扇子舞与硬核武术动作融合，节拍铿锵有力，国潮二创天花板基底。",
        "url": "https://www.bilibili.com/video/BV1Njxq67Emc",
        "pic": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
        "category": "国潮与赛博",
        "shots_count": 4,
        "recommended_character": "李云龙",
        "suggested_prompt": "宗师国潮风：手持折扇打出少林五步拳，配合激昂民乐与重低音鼓点，眼神犀利",
        "heat_tag": "热度 164w",
        "is_curated": True,
        "platform": "B站"
    },
    {
        "bvid": "BV1aa411f0W_CyberPopping",
        "title": "【震感街舞】重低音卡点 Popping 震撼全场 · 赛博光影舞台",
        "duration": "01:50",
        "author": "BeatDrop",
        "play": 542000,
        "description": "国潮大红大绿花袄纹理与电子霓虹灯的赛博魔幻融合。",
        "url": "https://www.bilibili.com/video/BV1aa411f0W_CyberPopping",
        "pic": "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?q=80&w=800&auto=format&fit=crop",
        "category": "国潮与赛博",
        "shots_count": 3,
        "recommended_character": "赛博大花袄",
        "suggested_prompt": "赛博国潮风：东北大红艳丽棉花袄高保真纹理，融入赛博朋克面部机械发光纹路，舞台伴随霓虹灯光效律动",
        "heat_tag": "热度 54.2w",
        "is_curated": True,
        "platform": "B站"
    },
    {
        "bvid": "BV1bb411g1V_YaoXiaZiRap",
        "title": "【方言说唱】东北林场药膳自制说唱 MV 卡点节奏",
        "duration": "02:18",
        "author": "NorthEastMeme",
        "play": 415000,
        "description": "东北大剧院风情，金牌药膳调理师的专属快嘴。",
        "url": "https://www.bilibili.com/video/BV1bb411g1V_YaoXiaZiRap",
        "pic": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?q=80&w=800&auto=format&fit=crop",
        "category": "东北本山宇宙",
        "shots_count": 3,
        "recommended_character": "东北药匣子",
        "suggested_prompt": "药膳大师风：手拿银针与药葫芦，身穿老式呢子大衣跳街头说唱步，动作喜感爆棚",
        "heat_tag": "热度 41.5w",
        "is_curated": True,
        "platform": "B站"
    }
]

CATEGORY_SEARCH_MAP = {
    "K-Pop 卡点舞": "K-Pop 卡点舞 MV 直拍 现场",
    "流行热歌": "2025 2026 热门 MV 官方打歌",
    "抖音热歌": "抖音 热门 舞蹈 MV 洗脑神曲",
    "东北本山宇宙": "范德彪 赵本山 经典名场面 舞蹈",
    "影视剧经典": "经典影视名场面 舞蹈 亮剑",
    "国潮与赛博": "国潮 街舞 卡点 MV 现场",
    "全部": "近期热门 MV 卡点 舞蹈"
}

class AgentReachService:
    """
    基于 Agent Reach 的新媒体全网热点与视频检索感知引擎
    支持直连 B站 (bilibili) 与 抖音 (douyin) 实时热榜与热门 MV 检索
    """
    
    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("agent-reach") is not None

    @classmethod
    def run_reach(cls, channel: str, action: str, args: Optional[List[str]] = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
        cmd = ["agent-reach", channel, action]
        if args:
            cmd.extend(args)
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8"
            )
            if res.returncode == 0 and res.stdout:
                data = json.loads(res.stdout)
                if data.get("ok"):
                    return data
        except Exception as e:
            logger.info("Agent reach %s %s failed: %s", channel, action, e)
        return None

    @classmethod
    def get_bilibili_hot(cls, limit: int = 6) -> List[Dict[str, Any]]:
        """获取 B站 实时热榜与热舞/MV"""
        data = cls.run_reach("bilibili", "hot", ["--limit", str(limit)])
        if not data:
            return []
        items = []
        for item in data.get("items", []):
            raw = item.get("raw") or {}
            bvid = raw.get("bvid") or (item.get("url", "").split("/")[-1] if item.get("url") else "")
            if not bvid:
                continue
            title = clean_html(item.get("title", ""))
            author = clean_html(item.get("author", "UP主"))
            desc = clean_html(raw.get("description", "") or item.get("text", ""))
            views = raw.get("stats", {}).get("view", 500000)
            heat = f"Agent Reach热榜 {round(views/10000, 1)}w" if isinstance(views, (int, float)) and views >= 10000 else "Agent Reach实时热点"
            
            rec_char, prompt = cls._recommend_meme(title, desc)
            items.append({
                "bvid": bvid,
                "title": title,
                "duration": raw.get("duration", "03:15"),
                "author": author,
                "play": views,
                "description": desc or f"Agent Reach 实时直通 B站 热榜二创源：《{title}》",
                "url": item.get("url") or f"https://www.bilibili.com/video/{bvid}",
                "pic": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=800&auto=format&fit=crop",
                "category": "K-Pop 卡点舞" if any(k in title.lower() for k in ["舞", "kpop", "dance", "女团"]) else "流行热歌",
                "shots_count": 4,
                "recommended_character": rec_char,
                "suggested_prompt": prompt,
                "heat_tag": heat,
                "is_curated": False,
                "platform": "Bilibili (Agent Reach 实时直通)"
            })
        return items

    @classmethod
    def search_bilibili(cls, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        """在 B站 实时搜索视频"""
        data = cls.run_reach("bilibili", "search", [query, "--limit", str(limit)])
        if not data:
            return []
        items = []
        for item in data.get("items", []):
            raw = item.get("raw") or {}
            bvid = raw.get("bvid") or ((item.get("url") or "").split("/")[-1])
            if not bvid:
                continue
            title = clean_html(item.get("title", ""))
            author = clean_html(item.get("author", "UP主"))
            rec_char, prompt = cls._recommend_meme(title, "")
            items.append({
                "bvid": bvid,
                "title": title,
                "duration": raw.get("duration", "03:00"),
                "author": author,
                "play": raw.get("play", 100000),
                "description": f"Agent Reach 搜索发现：《{title}》",
                "url": item.get("url") or f"https://www.bilibili.com/video/{bvid}",
                "pic": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop",
                "category": "流行热歌",
                "shots_count": 4,
                "recommended_character": rec_char,
                "suggested_prompt": prompt,
                "heat_tag": "Agent Reach 直连",
                "is_curated": False,
                "platform": "B站 (Agent Reach)"
            })
        return items

    @classmethod
    def search_douyin_hot(cls, query: str = "抖音 热门舞蹈 MV", limit: int = 4) -> List[Dict[str, Any]]:
        """通过 Agent Reach 检索抖音爆款舞蹈与新媒体神曲"""
        data = cls.run_reach("web", "search", [query, "--limit", str(limit)])
        if not data:
            return []
        items = []
        for idx, item in enumerate(data.get("items", [])):
            title = clean_html(item.get("title", ""))
            text = clean_html(item.get("text", ""))
            url = item.get("url", "")
            rec_char, prompt = cls._recommend_meme(title, text)
            vid = f"DY_{abs(hash(url or title)) % 100000000}"
            items.append({
                "bvid": vid,
                "title": title[:50] + ("..." if len(title) > 50 else ""),
                "duration": "01:30",
                "author": item.get("author") or "抖音热度榜",
                "play": 1580000,
                "description": (text[:120] + "...") if text else f"抖音爆款二创风向标：《{title}》",
                "url": url or f"https://www.douyin.com/video/{vid}",
                "pic": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=800&auto=format&fit=crop",
                "category": "抖音热歌",
                "shots_count": 4,
                "recommended_character": rec_char,
                "suggested_prompt": prompt,
                "heat_tag": "抖音热榜 TOP",
                "is_curated": False,
                "platform": "抖音 (Agent Reach 实时直通)"
            })
        return items

    @staticmethod
    def _recommend_meme(title: str, desc: str) -> (str, str):
        content = (title + " " + desc).lower()
        if any(k in content for k in ["机械", "太空", "本山", "东北", "小品", "锁步", "大叔"]):
            return "赵本山", "反差复古风：身穿经典蓝色中山棉袄跳太空机械锁步，表情严肃喜感"
        elif any(k in content for k in ["双人", "军", "正剧", "亮剑", "李云龙", "国风", "武术"]):
            return "李云龙", "反差亮剑风：李云龙身穿经典军装跳节奏卡点舞台，气势如虹动作极具反差"
        elif any(k in content for k in ["国潮", "大花袄", "朋克", "赛博", "唢呐", "魔性"]):
            return "赛博大花袄", "赛博国潮风：东北艳丽大花袄纹理搭配赛博朋克面部微光发光纹路，动作轻快灵动"
        elif any(k in content for k in ["说唱", "rap", "林场", "药膳"]):
            return "东北药匣子", "药膳大师风：手持药葫芦身穿毛呢大衣跳街头说唱步，喜感爆棚"
        return "范德彪", "反差开原风：范德彪身穿维多利亚西装跳卡点打歌舞，招牌鹰爪挠手势"


class SearchService:
    """
    负责新媒体视频素材检索，支持 Agent Reach (B站 & 抖音)、B站原生爬虫与本地精选二创素材池对齐。
    """

    @classmethod
    def search_bilibili_live(cls, keyword: str, page: int = 1, page_size: int = 6) -> List[Dict[str, Any]]:
        """
        调用 B站 原生接口搜索视频片段
        """
        results = []
        try:
            if requests:
                session = requests.Session(impersonate="chrome120")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://www.bilibili.com",
                    "Origin": "https://www.bilibili.com"
                }
                resp = session.get(
                    "https://api.bilibili.com/x/web-interface/search/all/v2",
                    params={"keyword": keyword, "page": page},
                    headers=headers,
                    timeout=5
                )
                data = resp.json()
            else:
                encoded = urllib.parse.quote(keyword)
                url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={encoded}&page={page}"
                req = urllib_req.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com"})
                with urllib_req.urlopen(req, timeout=5) as r:
                    data = json.loads(r.read().decode("utf-8"))

            if data.get("code") == 0:
                raw_items = data.get("data", {}).get("result", [])
                for item in raw_items:
                    if item.get("result_type") == "video":
                        for v in item.get("data", [])[:page_size]:
                            bvid = v.get("bvid")
                            if not bvid:
                                continue
                            title = clean_html(v.get("title", ""))
                            duration = v.get("duration", "02:30")
                            author = clean_html(v.get("author", "B站UP主"))
                            play = v.get("play", 10000)
                            desc = clean_html(v.get("description", ""))
                            pic = v.get("pic", "")
                            if pic.startswith("//"):
                                pic = f"https:{pic}"
                            
                            rec_char, prompt = AgentReachService._recommend_meme(title, desc)
                            play_str = f"播放 {round(play/10000, 1)}w" if isinstance(play, (int, float)) and play >= 10000 else "火爆推荐"

                            results.append({
                                "bvid": bvid,
                                "title": title,
                                "duration": duration,
                                "author": author,
                                "play": play,
                                "description": desc or f"近期热门二创源：《{title}》",
                                "url": f"https://www.bilibili.com/video/{bvid}",
                                "pic": pic or "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=800&auto=format&fit=crop",
                                "category": "K-Pop 卡点舞" if any(k in title.lower() for k in ["舞", "kpop", "k-pop", "dance"]) else "流行热歌",
                                "shots_count": 4,
                                "recommended_character": rec_char,
                                "suggested_prompt": prompt,
                                "heat_tag": play_str,
                                "is_curated": False,
                                "platform": "B站"
                            })
        except Exception as e:
            logger.info("Bilibili live search temporarily unavailable (%s), falling back to curated library", str(e))
        return results

    @classmethod
    def search_videos(cls, keyword: str = "", category: str = "全部", limit: int = 8) -> List[Dict[str, Any]]:
        """
        统一搜索入口：整合 Agent Reach (B站/抖音实时)、B站爬虫与精选库
        """
        results = []
        kw = keyword.strip()

        # 1. 优先尝试通过 Agent Reach 检索 B站 与 抖音 实时热门与新媒体爆款
        if AgentReachService.is_available():
            try:
                if "抖音" in kw or category == "抖音热歌":
                    dy_items = AgentReachService.search_douyin_hot(kw or "抖音 热门舞蹈 MV", limit=limit)
                    results.extend(dy_items)
                elif kw:
                    reach_bili = AgentReachService.search_bilibili(kw, limit=limit)
                    results.extend(reach_bili)
                else:
                    hot_bili = AgentReachService.get_bilibili_hot(limit=limit // 2 + 1)
                    results.extend(hot_bili)
                    hot_douyin = AgentReachService.search_douyin_hot("抖音 热门舞蹈 MV", limit=limit // 2)
                    results.extend(hot_douyin)
            except Exception as e:
                logger.info("AgentReach query error: %s", e)

        # 2. 若 Agent Reach 无结果，尝试从 B站 原生爬虫接口查询
        if len(results) < limit:
            live_query = kw or CATEGORY_SEARCH_MAP.get(category, "近期热门MV 卡点 舞蹈")
            live_results = cls.search_bilibili_live(live_query, page=1, page_size=limit)
            for item in live_results:
                if not any(r.get("bvid") == item["bvid"] for r in results):
                    results.append(item)

        # 3. 匹配并混合本地精选库（保证卡片视觉高品质与稳固兜底）
        for item in CURATED_MEME_TEMPLATES:
            if category != "全部" and item.get("category") != category:
                continue
            if kw:
                match_text = f"{item['title']} {item['description']} {item['recommended_character']} {item['category']}"
                if kw.lower() not in match_text.lower():
                    continue
            if not any(r.get("bvid") == item["bvid"] for r in results):
                results.append(item)

        # 4. 兜底返回全部精选，确保前端永远有高质量视觉卡片
        if not results:
            results = CURATED_MEME_TEMPLATES

        return results[:limit]
