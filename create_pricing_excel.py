# -*- coding: utf-8 -*-
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

# Define Color Palette
HEADER_FILL = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Slate
HEADER_FONT = Font(name="微软雅黑", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="微软雅黑", size=14, bold=True, color="1E293B")
SUBTITLE_FONT = Font(name="微软雅黑", size=9, italic=True, color="64748B")
DATA_FONT = Font(name="微软雅黑", size=10)
BOLD_DATA_FONT = Font(name="微软雅黑", size=10, bold=True)
HIGHLIGHT_FILL = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # Light Amber
RECOMMEND_FILL = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Light Green
ACCENT_FONT = Font(name="微软雅黑", size=10, bold=True, color="15803D") # Green text
GRAY_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

thin_border = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)

# ---------------------------------------------------------------------------------------------------
# Sheet 1: 竞品与主流AI视频平台会员对照
# ---------------------------------------------------------------------------------------------------
ws1 = wb.active
ws1.title = "竞品平台会员与算力对照"

ws1.append(["市面主流 AI 视频 / 动作迁移与转绘平台会员定价全景对照表 (2025-2026 最新调研)"])
ws1.append(["涵盖国内顶流（快手可灵、字节即梦）、海外垂直赛道龙头（Viggle 动作迁移、DomoAI 风格转绘、Runway 等）"])
ws1.append([])

headers1 = [
    "平台名称", "核心赛道/定位", "免费额度政策", "月会员标价(元)", 
    "连续包月/首月(元)", "年会员总价(元)", "年卡折合月价(元)", "年卡折扣力度", 
    "每月赠送算力/积分", "单条5s视频消耗", "每月成片预估(条)", "单条成片折算成本(元)", 
    "排队与并发权益", "画质与去水印权益", "商业模式核心启示"
]
ws1.append(headers1)

competitor_data = [
    ["快手可灵 (Kling AI)", "通用视频生成/运镜", "每日免费少量灵感值(每日清零)", 66, 19, 396, 33.0, "5.0折 (限时大促)", "660 灵感值", "10 灵感值/5s", 66, 0.50, "标准排队队列 / 1并发", "去水印 / 720P~1080P", "高门槛流量漏斗，通过首月19元低价锁定自动续费"],
    ["快手可灵 (Kling AI)", "铂金会员 (Pro)", "无额外免费", 266, 198, 1980, 165.0, "6.2折", "3,000 灵感值", "10 灵感值/5s", 300, 0.55, "快速专属通道 / 3并发", "1080P高表现 / 运镜控制 / 视频延长", "针对中度短剧与自媒体创作者的主力生产力卡"],
    ["快手可灵 (Kling AI)", "钻石会员 (Premier)", "无额外免费", 666, 498, 4980, 415.0, "6.2折", "8,000 灵感值", "10 灵感值/5s", 800, 0.52, "极速VIP通道 / 5并发", "全特权解锁 / 优先测试新模型", "针对小工作室/MCN的月度算力包销"],
    ["Viggle AI (核心直接竞品)", "动作迁移/角色重绘 (Pro)", "每日少量免费/带水印/单并发", 72, 58, 690, 57.5, "8.0折 (年付$95.9)", "80 积分", "1 积分/次混合", 80, 0.72, "4 并发并行生成", "无水印 / 720P / 最长10分钟上传", "垂直动作迁移标杆，按任务次扣点，轻量易上手"],
    ["Viggle AI (核心直接竞品)", "Live 计划 (动态/实时)", "无额外免费", 160, 145, 1380, 115.0, "8.0折 (年付$191.9)", "200 积分", "1 积分/次混合", 200, 0.58, "6 并发并行生成", "支持 Seedance 模型 / 实时摄像头换脸", "绑定顶尖动作底模，提供高阶动捕重定向能力"],
    ["Viggle AI (核心直接竞品)", "Max 计划 (重度量产)", "无额外免费", 580, 520, 4600, 383.3, "8.0折 (年付$639.9)", "800 积分", "1 积分/次混合", 800, 0.48, "10 并发并行生成", "全模型解锁 / 资产无限期云端存储", "为矩阵号创作者提供工业化生产能力"],
    ["DomoAI (核心直接竞品)", "视频风格转绘/动漫风 (Basic)", "注册送15-30积分试用", 72, 72, 600, 50.0, "7.0折 (年付$6.99/mo)", "500 积分", "约15 积分/5s", 33, 1.52, "标准队列 / 无 Relax 模式", "无水印 / 720P基础画质", "不设无限慢速生成，迫使用户向标准版升级"],
    ["DomoAI (核心直接竞品)", "Standard (含无限慢速)", "注册送15-30积分试用", 200, 200, 1680, 140.0, "7.0折 (年付$19.59/mo)", "1,500 积分", "约15 积分/5s", "100+ (含无限)", 1.40, "Fast高速点数 + 无限 Relax 慢速通道", "1080P超清 / 风格模型全选", "【最强订阅心智】：送无限慢速通道，用户黏性与留存极高"],
    ["DomoAI (核心直接竞品)", "Pro 计划 (专业转绘)", "无额外免费", 500, 500, 4200, 350.0, "7.0折 (年付$48.99/mo)", "5,000 积分", "约15 积分/5s", "330+ (含无限)", 1.06, "极速队列 + 无限 Relax 慢速通道", "20s 超长连续生成 / AI放大高清化", "高ARPU值捕获高阶付费创作者"],
    ["字节即梦 (Dreamina)", "进阶会员 (标准版)", "每日免费赠少量日常积分(当日清零)", 39, 29, 348, 29.0, "7.4折", "1,200 积分", "约15 积分/5s", 80, 0.36, "标准排队队列 / 1并发", "去水印 / 720P-1080P / 与剪映联动", "生态联动：与剪映会员打通，形成从生成到剪辑的闭环"],
    ["字节即梦 (Dreamina)", "高级会员 (专业版)", "每日免费赠少量日常积分(当日清零)", 99, 79, 888, 74.0, "7.5折", "4,000 积分", "约15 积分/5s", 260, 0.28, "免排队极速通道 / 3并发", "支持 Seedance 2.5 旗舰模型 / 4K放大", "面向 AI 短剧、商业短视频的刚需生产力工具"],
    ["Runway Gen-3", "Standard 标准版", "注册赠 125 积分一次性体验", 108, 108, 1030, 85.8, "8.0折 (年付$12/mo)", "625 积分", "5 积分/秒 (25点/5s)", 25, 3.43, "标准通道 / 无法使用无限模式", "4K 导出 / 关键帧画笔控制", "国际一线品牌溢价高，单秒生成成本居高不下"],
    ["Runway Gen-3", "Unlimited 无限版", "无额外免费", 680, 680, 6500, 541.7, "8.0折 (年付$76/mo)", "2,250 积分", "点数耗尽后转无限 Relax", "无限 Relax 条", 0.50, "高速额度 + 无限 Relax 慢速通道", "全特权 / 团队协作权限", "高端创作者的终极选择，靠无限闲时算力锁定年费"]
]

for row in competitor_data:
    ws1.append(row)

# ---------------------------------------------------------------------------------------------------
# Sheet 2: 底层算力与API成本对照
# ---------------------------------------------------------------------------------------------------
ws2 = wb.create_sheet(title="底层算力与API成本对照")

ws2.append(["AI 视频生成大模型官方 API 与 GPU 算力云租赁成本精算表 (2025-2026 实测)"])
ws2.append(["用于评估 MemeMorph 平台在【纯API调用】与【自建/租用显卡私有化部署】的边际成本与技术选型"])
ws2.append([])

headers2 = [
    "算力提供方 / 方案", "技术与模型规格", "计费类型", "采购单价", 
    "单镜(5s)耗时", "单镜(5s)直接成本(元)", "15s成片(3镜)基础成本(元)", 
    "质检重抽(+20%冗余)", "单条成片综合成本(元)", "并发/吞吐弹性", "优缺点与平台建议"
]
ws2.append(headers2)

compute_data = [
    ["火山引擎 (字节跳动)", "SEED 2.5 视频大模型 (720P)", "API 按次调用", "¥0.25 / 5秒", "12~18 秒", 0.25, 0.75, 0.15, 0.90, "近乎无限弹性并发", "【首选主力引擎】：面部一致性强，角色动作保真度极高，适合冷启动期零闲置成本"],
    ["火山引擎 (字节跳动)", "SEED 2.5 视频大模型 (1080P)", "API 按次调用", "¥0.45 / 5秒", "20~30 秒", 0.45, 1.35, 0.27, 1.62, "弹性并发支持", "用于 VIP 高清导出模式，画质细腻但单片成本高，可作为高阶付费特权"],
    ["快手可灵官方", "可灵 1.5 视频模型 (标准模式)", "API 按次调用", "¥0.22 / 5秒", "15~25 秒", 0.22, 0.66, 0.13, 0.79, "高并发支持 (需提工单)", "【备选引擎】：大动态舞蹈连贯度好，成本亲民，适合大批量背景人物替换"],
    ["快手可灵官方", "可灵 1.5 视频模型 (高表现模式)", "API 按次调用", "¥0.60 / 5秒", "30~45 秒", 0.60, 1.80, 0.36, 2.16, "受配额限制", "表现力好但成本偏高，适合单次Re-roll关键镜头时使用"],
    ["MiniMax 海螺 AI", "Hailuo H3 视频模型 (720P)", "API 按次调用", "¥0.35 / 5秒", "18~28 秒", 0.35, 1.05, 0.21, 1.26, "弹性调用", "运镜平滑，肢体变形率低，适合作为熔断备用路线"],
    ["AutoDL 算力云", "RTX 4090 24GB (按量计费)", "GPU 按时出租", "¥1.88 / 小时", "30 秒 (ComfyUI)", 0.016, 0.048, 0.010, 0.06, "单卡仅能串行处理", "成本极低但需要自己部署维护模型(如Wan2.1/Animatediff)，有冷启动排队和显卡抢占问题"],
    ["AutoDL 算力云", "RTX 4090 24GB (包月独占)", "GPU 包月预付", "¥1,200 / 月", "30 秒 (满载月产8万镜)", 0.015, 0.045, 0.009, 0.05, "独占算力无抢占", "适合日单量稳定突破 500 条后的私有化降本改造，闲置时会产生固定折旧亏损"],
    ["AutoDL 算力云", "A800 80GB (按量计费)", "GPU 按时出租", "¥5.59 / 小时", "60 秒 (大参数模型)", 0.093, 0.279, 0.056, 0.34, "适合大参数模型微调", "适合测试自研 14B 级角色专属 LoRA 适配器，不适合做面向C端的单次并发推理"],
    ["阿里云 PAI / 腾讯云", "NVIDIA A10 24GB Serverless", "弹性推理计费", "¥0.0018 / 秒 (约6.5元/时)", "35 秒", 0.063, 0.189, 0.038, 0.23, "自动扩缩容至0", "兼顾私有化模型安全性与自动伸缩，但前期部署与工程运维门槛高"],
    ["【推荐】混合架构策略", "火山SEED 2.5 API + 4090闲时渲染", "混合调度", "动态路由调度", "15~25 秒", 0.20, 0.60, 0.12, 0.72, "兼顾弹性与低成本", "【战略建议】：0~3个月纯API冷启动；4~6个月引入4090跑慢速Relax任务，API保高峰"]
]

for row in compute_data:
    ws2.append(row)

# ---------------------------------------------------------------------------------------------------
# Sheet 3: MemeMorph 本平台会员与定价体系方案建议
# ---------------------------------------------------------------------------------------------------
ws3 = wb.create_sheet(title="MemeMorph定价体系建议")

ws3.append(["MemeMorph 梗影AI — 商业化会员套餐与算力定价模型 (建议落地方案)"])
ws3.append(["基于单条 15s 成品消耗 45 算力、单镜头重抽 10 算力、综合成本 ¥1.0~1.3 元/条 精准反推测算"])
ws3.append([])

headers3 = [
    "套餐类型", "套餐名称", "定位与用户画像", "售价(元)", "计费周期", 
    "基础算力(点)", "赠送算力(点)", "总计可用算力(点)", "预估完整成片(条)", "折合单镜重抽(次)", 
    "单条折合售价(元)", "平台单条成本(元)", "平台单条毛利(元)", "毛利率(%)", "核心特权与功能矩阵"
]
ws3.append(headers3)

pricing_data = [
    ["单次加油包", "新手试水包", "首次尝鲜、低门槛体验用户", 19.9, "一次性", 180, 20, 200, 4.4, 20, 4.52, 1.20, 3.32, 0.735, "标准画质720P / 无水印 / 1个任务并发 / 算力永久有效"],
    ["单次加油包", "爆款创作者包", "自媒体个人创作者 (主推爆款)", 59.0, "一次性", 600, 150, 750, 16.7, 75, 3.53, 1.10, 2.43, 0.688, "1080P超清 / 赠单镜重抽特权 / 2个任务并发 / 剪映草稿包导出"],
    ["单次加油包", "硬核量产加量包", "突发爆款追热点创作者", 129.0, "一次性", 1500, 300, 1800, 40.0, 180, 3.23, 1.05, 2.18, 0.675, "1080P超清 / 优先排队通道 / 3并发 / 免费解锁所有角色基因库"],
    ["订阅型会员", "月度创作者会员", "每周更新1-2条的稳定自媒体博主", 49.0, "月付 (自动续费39)", 500, 100, 600, 13.3, 60, 3.68, 1.10, 2.58, 0.701, "每月赠600算力(月底清零) + 加购加油包享8.5折 + 快速通道"],
    ["订阅型会员", "月度高能会员 (含Relax)", "高频短视频达人、二创高产玩家", 99.0, "月付 (自动续费79)", 1200, 300, 1500, 33.3, 150, 2.97, 1.05, 1.92, 0.646, "【核心卖点】：点数用完解锁【无限Relax闲时排队生成】+ 3并发"],
    ["订阅型会员", "季度爆品会员", "跨周期运营的自媒体工作室", 129.0, "季付 (折43元/月)", 1600, 400, 2000, 44.4, 200, 2.90, 1.05, 1.85, 0.638, "送全套爆款脚本库 + 角色独家私有定制1个 + 专属客服支持"],
    ["订阅型会员", "年度合伙人 VIP", "全职自媒体团队/个人工作室", 399.0, "年付 (折33.25元/月)", 5000, 2000, 7000, 155.6, 700, 2.56, 1.00, 1.56, 0.609, "【锁定高LTV】：7000算力分批/随时提 + 全年无限Relax慢速 + 5并发"],
    ["团队/机构", "MCN 矩阵机构月卡", "MCN公会、批量起号团队", 199.0, "月付", 2500, 500, 3000, 66.7, 300, 2.98, 1.00, 1.98, 0.664, "开放 RESTful 批量生片 API / 5并发并行 / 专属企业群1对1保障"],
    ["团队/机构", "MCN 矩阵机构年卡", "大型数字内容营销机构", 1999.0, "年付 (折166元/月)", 30000, 6000, 36000, 800.0, 3600, 2.50, 0.95, 1.55, 0.620, "私有部署咨询 / 独立API密钥 / 10并发 / 无限团队子账号共享"],
    ["零散补电", "单镜微调点卡 (Re-roll)", "算力差额临时补足", 9.9, "一次性", 100, 0, 100, 2.2, 10, 4.50, 1.20, 3.30, 0.733, "极速补足算力缺口，专门用于满意度不达标时的局部镜头重抽"]
]

for row in pricing_data:
    ws3.append(row)

# ---------------------------------------------------------------------------------------------------
# Sheet 4: Unit Economics 与平台盈利测算
# ---------------------------------------------------------------------------------------------------
ws4 = wb.create_sheet(title="Unit Economics与盈利测算")

ws4.append(["MemeMorph 梗影AI — 平台业务规模与财务盈利精算模型 (月度与年化测算)"])
ws4.append(["模拟从冷启动期 (日产50条) 到爆发期 (日产2000条) 的直接成本、固定支出、毛利润与现金流演进"])
ws4.append([])

headers4 = [
    "发展阶段", "日活用户数(DAU)", "日成片量(条)", "月总成片量(条)", "付费转化率(%)", 
    "月活跃付费用户", "平均客单价(ARPU)", "月度总营收(元)", "API生成直接成本(元)", 
    "质检重抽折损(20%)", "轻量服务器+存储带宽(元)", "月总营业成本(元)", "月度毛利润(元)", 
    "综合毛利率(%)", "年化净收益折算(元)", "运营状态评估"
]
ws4.append(headers4)

financial_data = [
    ["1. 冷启动期 (1-2月)", 100, 50, 1500, 0.15, 15, 59.0, 7500, 1125, 225, 150, 1500, 6000, 0.800, 72000, "极轻资产验证，纯依靠火山引擎API，月固定支出仅¥150，完全无亏损风险"],
    ["2. 爬坡增长期 (3-4月)", 500, 200, 6000, 0.18, 90, 59.0, 28000, 4500, 900, 350, 5750, 22250, 0.795, 267000, "社区裂变初步成型，创作者包月复购提升，现金流稳健正向"],
    ["3. 规模化阶段 (5-8月)", 2000, 800, 24000, 0.20, 400, 68.0, 112000, 18000, 3600, 1200, 22800, 89200, 0.796, 1070400, "达成年化百万利润基线，开始引入包月4090跑慢速任务进一步压缩20%成本"],
    ["4. 爆发成熟期 (9-12月)", 6000, 2500, 75000, 0.22, 1320, 75.0, 360000, 52500, 10500, 3500, 66500, 293500, 0.815, 3522000, "自媒体与MCN大规模使用，平台品牌护城河形成，具备抗风险与自研模型能力"]
]

for row in financial_data:
    ws4.append(row)

# ---------------------------------------------------------------------------------------------------
# Apply Formatting & Styles across all worksheets
# ---------------------------------------------------------------------------------------------------
for ws in [ws1, ws2, ws3, ws4]:
    ws.views.sheetView[0].showGridLines = True
    
    # Title & Subtitle styling
    ws["A1"].font = TITLE_FONT
    ws["A2"].font = SUBTITLE_FONT
    
    # Headers in Row 4
    header_row = 4
    for col_idx in range(1, ws.max_column + 1):
        cell = ws.cell(row=header_row, column=col_idx)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    
    # Data Rows styling
    for row_idx in range(5, ws.max_row + 1):
        is_even = (row_idx % 2 == 0)
        for col_idx in range(1, ws.max_column + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = DATA_FONT
            cell.border = thin_border
            
            # Default stripe fill
            if is_even:
                cell.fill = GRAY_FILL
                
            # Alignments & Number formats
            val = cell.value
            header_val = str(ws.cell(row=header_row, column=col_idx).value or "")
            if isinstance(val, (int, float)):
                if "%" in header_val or "率" in header_val:
                    cell.number_format = "0.0%"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif "元" in header_val or "价" in header_val or "成本" in header_val or "营收" in header_val or "毛利" in header_val:
                    if isinstance(val, float) and val < 10:
                        cell.number_format = "¥#,##0.00"
                    else:
                        cell.number_format = "¥#,##0"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                # Text alignment
                if col_idx in [1, 2]:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
                elif col_idx in [ws.max_column]:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

    # Specific highlighting in Sheet 3
    if ws.title == "MemeMorph定价体系建议":
        for r in range(5, ws.max_row + 1):
            tier_name = ws.cell(row=r, column=2).value
            if tier_name in ["爆款创作者包", "月度高能会员 (含Relax)", "年度合伙人 VIP"]:
                for c in range(1, ws.max_column + 1):
                    ws.cell(row=r, column=c).fill = RECOMMEND_FILL
                ws.cell(row=r, column=2).font = ACCENT_FONT
                ws.cell(row=r, column=14).font = ACCENT_FONT

    # Adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row in [1, 2]:
                continue
            v_str = str(cell.value or "")
            # Count Chinese chars as ~2 length
            c_len = sum(2 if ord(char) > 127 else 1 for char in v_str)
            if c_len > max_len:
                max_len = c_len
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

# Save Workbook
excel_path = "D:\\meme-rotoscope-studio\\MemeMorph_算力与会员定价全景精算表.xlsx"
wb.save(excel_path)
print(f"Successfully generated Excel file at: {excel_path}")
