# MemeMorph 全渠道宣发物料与文案包 (Launch Promotion Kit)

本包已为您精细化调优各平台（Reddit、Twitter/X、Hacker News、V2EX、知乎、B站）的宣发文案、标题与配图指引，可直接复制粘贴发布或使用官方免费工具进行全网分发。

---

## 📌 渠道一：Reddit (全球最大开发者与 AI 社区)

### 1. 目标板块
* **`r/LocalLLaMA`** (主打 0 算力本地消费级 GPU 离线跑)
* **`r/StableDiffusion`** (主打 SAM 2 遮罩与防时序闪烁)
* **`r/SideProject`** / **`r/MachineLearning`**

### 2. 帖子标题 (Post Title)
> `I built MemeMorph: An open-source video rotoscoping agent with SAM 2 character tracking, shot splitting, and native Claude/Codex MCP support`

### 3. 正文内容 (Markdown Body)
```markdown
Hey everyone! 👋

I've been working on **MemeMorph (梗影AI)**, an open-source tool and agent workflow designed to make continuous video rotoscoping, character replacement, and stylized motion transfer reliable and production-ready.

### 🛑 Why most AI video tools fail at rotoscoping:
- **Temporal flickering & face morphing**: Generating whole video frames causes background warping and character identity drift.
- **Length limitation**: Most diffusion pipelines max out at 4–10 seconds, breaking full 1–3 minute music videos.
- **Insane API costs**: Iterating on cloud video APIs burns cash rapidly.

### 🛠️ How MemeMorph solves this:
1. **PySceneDetect Shot Splitting**: Decomposes long videos into 3–5s logical shots with a 0.5s sliding overlap.
2. **Meta SAM 2 Temporal Tracking**: Isolates dancing characters so background lighting, stage ambience, and backup dancers remain 100% faithful.
3. **Local Hypit & FastVideo v2**: 6-step distilled pipeline with `lightingMode="source"` running locally on 24GB GPUs (RTX 3090/4090) with zero cloud compute cost and intact audio tracks.
4. **Cloud Gateway Fallback**: Supports ByteDance Seedance 2.5, Kling 1.5, and MiniMax Video-01 via unified SSE streams.
5. **Native Model Context Protocol (MCP)**: Any agent (Claude Desktop, OpenAI Codex, Cursor) can directly call MemeMorph tools (`search_hot_videos`, `split_video_scenes`, `create_rotoscope_task`, `inspect_video_qc`).
6. **Built-in Mock Cluster**: Runs out of the box with zero configuration or API keys needed.

👉 **GitHub Repository**: https://github.com/Jackeyhate9/meme-rotoscope-studio  
Feel free to try it locally (`start_ui.bat` or `python run_mcp.py`)! Star, fork, and feedback are very welcome!
```

### 4. 推荐配图
* `docs/assets/cover_hero.png`
* `docs/assets/cover_studio_workbench.png`

---

## 📌 渠道二：Twitter / X (技术圈病毒式传播 Thread)

### 1. 主推文 (Main Tweet)
```text
🚀 Just open-sourced MemeMorph: an AI video rotoscoping agent built for meme creators and video editors!

✨ PySceneDetect shot splitting (supports full 3-min MVs)
🎯 SAM 2 character tracking (zero background flicker)
⚡ Local Hypit / FastVideo v2 (0 cloud cost on RTX 3090/4090)
🔌 Native Anthropic MCP support for Claude & Codex

GitHub 👇
https://github.com/Jackeyhate9/meme-rotoscope-studio

#AI #GenerativeAI #StableDiffusion #OpenSource #Claude #MCP #ComputerVision
```

### 2. 跟帖 1 (Reply 1 - MCP 特性)
```text
MemeMorph now natively implements the Model Context Protocol (MCP).
You can mount it into Claude Desktop or Cursor with a single json entry:

"mememorph": {
  "command": "python",
  "args": ["d:/meme-rotoscope-studio/run_mcp.py"]
}

Now Claude can search trending dances on Bilibili & Douyin, split shots, and render rotoscopes via natural language!
```

### 3. 跟帖 2 (Reply 2 - 演示与作者)
```text
Includes:
- Infinite node canvas (UpDream / 即梦 style)
- Auto-QC vision inspector with Human-in-the-Loop decision cards
- Pure white modern Vercel/Apple light UI

Built with ❤️ by @Jackeyhate9. Star the repo if you like it! ⭐
```

---

## 📌 渠道三：V2EX (国内高质量技术社区)

### 1. 目标节点
* `/go/create` (自做作品) 或 `/go/share` (分享发现)

### 2. 标题
> `[开源推荐] 开源了 MemeMorph：基于 SAM 2 + 本地 Hypit / 字节可灵的短视频二创转绘 Agent，原生支持 Claude / Codex MCP 接入`

### 3. 正文内容
```markdown
各位 V 友大家好！

做短视频二创或者 AI 视频转绘的老哥们经常遇到几个让人抓狂的问题：
1. 画面背景疯狂闪烁，人脸几秒钟就漂移变形；
2. 工具只能出 4~15 秒短片，根本无法处理 1~3 分钟的完整打歌舞和 MV；
3. 云端视频 API 算力极贵，调试几次几百块就没了。

针对这些痛点，我开发并开源了 **MemeMorph (梗影AI)**。

### 核心亮点：
- **PySceneDetect 镜头切分**：自动把长视频拆分为 3~5 秒连续镜头，支持一键长视频修改与无缝回流缝合；
- **Meta SAM 2 伴舞背景高保真**：精准抠出动作主体，原片舞台灯光与伴舞完全保留；
- **本地工业级 Hypit 引擎适配**：针对本地 RTX 3090/4090 (24G 显存) 用户，支持 6 步蒸馏 FastVideo v2 与 `lightingMode="source"`，0 云端算力开销；
- **多模型底座矩阵**：除了本地 GPU，还支持字节跳动 Seedance 2.5、快手可灵 1.5、MiniMax 统一调度；
- **原生接入 Anthropic MCP 协议**：已内置完整的 MCP Server，可在 Claude Desktop、Cursor、Codex 中以工具箱形式直接调用；
- **零门槛即开即用**：内置完整的高保真智能 Mock 集群，不需要配置任何付费 Key，双击 `start_ui.bat` 即可跑通全套纯白现代 UI。

- 项目地址：https://github.com/Jackeyhate9/meme-rotoscope-studio
- License：Apache 2.0

欢迎大家试用、提 Issue 和 PR，如果对你有帮助，欢迎点个 Star 支持一下！
有深度合作或技术交流需求的 V 友也可以在 README 文末扫码加我微信（坐标北京朝阳）。
```

---

## 📌 渠道四：知乎 / 掘金 (技术深度长文)

* **文章标题**：《从 0 到 1 开源一个 AI 视频二创 Agent：解决时序闪烁、长视频镜头切分与 Claude MCP 协议接入》
* **文章重点**：
  1. 架构总览：FastAPI + AG-UI 全双工流式推送 + SAM 2 + 本地 Hypit；
  2. 算法痛点与解决：为什么单纯做 Video-to-Video 会闪烁？如何用 SAM 2 锁定人物遮罩并保留真实光影？
  3. 长视频切分策略：PySceneDetect 镜头边缘判定 + 0.5 秒滑动重叠窗口；
  4. 为什么 Agent 需要接入 MCP？通过 Model Context Protocol 让外部大模型具备视频理解与转绘控制能力；
  5. 完整开源代码展示与实操指引。

---

## 📌 渠道五：B站 / 抖音 / 视频号 (视频自引流)

* **视频类型**：15 秒分屏对比视频 (Split Wipe)
* **画面布局**：
  - 左侧：原版热门舞步（aespa Whiplash / ROSÉ《APT.》）；
  - 右侧：MemeMorph 实时转绘结果（范德彪霸气歪嘴鹰爪挠）；
  - 中间：动态划屏光条与原声高保真卡点。
* **文案与标题**：
  > “当范德彪去跳女团卡点舞是什么体验？基于 SAM 2 + 本地 GPU 的长视频二创 Agent 已全量开源！0 算力成本，代码已托管 GitHub！”
* **评论区置顶**：
  > “源码与一键启动包已开源在 GitHub: `Jackeyhate9/meme-rotoscope-studio`，支持 Claude MCP 工具接入。作者微信在 README 文末，欢迎二创老哥与算法大佬交流！”
