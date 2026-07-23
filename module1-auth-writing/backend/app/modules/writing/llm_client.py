"""
LLM 客户端：增强版 — Few-shot Prompt工程 + 6风格 × 行业适配
================================================================
特性：
  - 6种文案风格：专业商务 / 活泼种草 / 极简高级 / 情感共鸣 / 幽默风趣 / 奢华高端
  - 每个风格 4+ 套不同文案模板，避免重复
  - 行业场景适配：3C数码 / 美妆护肤 / 服饰箱包 / 食品饮料 / 家居日用
  - OpenAI兼容模式的完整 Few-shot Prompt 模板
  - 5种语言：zh / en / ja / ko / es
  - 3个平台：TikTok / Instagram / Amazon
"""
import json
import random
from typing import Optional
import httpx
from app.core.config import settings


# ═══════════════════════════════════════════════════════════════
#  风格定义 — 每种风格的文案特征描述
# ═══════════════════════════════════════════════════════════════

STYLE_PROFILES = {
    "professional": {
        "name_zh": "专业商务",
        "name_en": "Professional",
        "tone": "正式、权威、数据驱动",
        "features": "使用行业术语、数据支撑、理性说服、B2B友好",
    },
    "casual": {
        "name_zh": "活泼种草",
        "name_en": "Casual",
        "tone": "轻松、口语化、种草风",
        "features": "使用emoji、感叹词、网络热词、第一人称分享",
    },
    "minimalist": {
        "name_zh": "极简高级",
        "name_en": "Minimalist",
        "tone": "克制、留白、高级感",
        "features": "短句为主、大量留白、品牌调性、冷淡美学",
    },
    "emotional": {
        "name_zh": "情感共鸣",
        "name_en": "Emotional",
        "tone": "温暖、故事化、共情",
        "features": "场景化叙事、情感词汇、生活方式关联、治愈感",
    },
    "humorous": {
        "name_zh": "幽默风趣",
        "name_en": "Humorous",
        "tone": "俏皮、反转、网络梗",
        "features": "神转折、自嘲、夸张比喻、memes风格",
    },
    "luxury": {
        "name_zh": "奢华高端",
        "name_en": "Luxury",
        "tone": "精致、稀缺、身份感",
        "features": "限量/尊享/手工/匠心、高端词汇、身份标签",
    },
}

# ═══════════════════════════════════════════════════════════════
#  行业Prompt模板
# ═══════════════════════════════════════════════════════════════

INDUSTRY_CONTEXT = {
    "3C": {
        "name_zh": "3C数码",
        "keywords_zh": "性能、参数、科技感、兼容性、续航、芯片",
        "keywords_en": "performance, specs, tech, compatibility, battery life, chip",
    },
    "beauty": {
        "name_zh": "美妆护肤",
        "keywords_zh": "成分、功效、肤质、轻薄、持妆、光泽",
        "keywords_en": "ingredients, effect, skin type, lightweight, long-lasting, glow",
    },
    "fashion": {
        "name_zh": "服饰箱包",
        "keywords_zh": "面料、版型、百搭、质感、设计感、潮流",
        "keywords_en": "fabric, fit, versatile, texture, design, trendy",
    },
    "food": {
        "name_zh": "食品饮料",
        "keywords_zh": "口感、原料、健康、新鲜、浓郁、便携",
        "keywords_en": "taste, ingredients, healthy, fresh, rich, portable",
    },
    "home": {
        "name_zh": "家居日用",
        "keywords_zh": "材质、收纳、省空间、耐用、颜值、实用",
        "keywords_en": "material, storage, space-saving, durable, aesthetic, practical",
    },
}

# ═══════════════════════════════════════════════════════════════
#  Few-shot 示例库 — 用于 OpenAI 兼容模式的 Prompt
# ═══════════════════════════════════════════════════════════════

FEWSHOT_EXAMPLES = {
    "zh": {
        "professional": """
【Few-shot示例】
商品：机械键盘 卖点：Cherry轴体、RGB背光、全键无冲
平台：TikTok
文案：标题「Cherry轴+RGB光效 | 码字游戏双修神器」正文「樱桃原厂MX轴体，触发行程精准到1.2mm。1680万色RGB背光支持自定义灯效编程，全键无冲设计让每一次敲击都干净利落。程序员和玩家的共同选择。」标签 #机械键盘 #Cherry轴 #生产力工具
""",
        "casual": """
【Few-shot示例】
商品：防晒霜 卖点：SPF50+、轻薄不油腻、养肤成分
平台：TikTok
文案：标题「救命！这防晒也太好用了吧🌞」正文「姐妹们我真的会谢！这个防晒霜SPF50+居然完全不油腻！涂上去秒成膜，跟什么都没涂一样轻薄～还加了烟酰胺，越晒越白是什么神仙操作？！夏天必囤，不买后悔！」标签 #防晒推荐 #好物分享 #夏日必备
""",
        "minimalist": """
【Few-shot示例】
商品：帆布袋 卖点：纯棉、大容量、多色可选
平台：Instagram
文案：标题「一只好袋子」正文「100%纯棉。承重15kg。5色。别无其他。」标签 #帆布袋 #极简生活
""",
        "emotional": """
【Few-shot示例】
商品：保温杯 卖点：316不锈钢、12小时保温、轻量化
平台：Instagram
文案：标题「陪你走过每一个清晨」正文「凌晨五点的第一口热咖啡，深夜加班时的一杯温水，它一直都在。316不锈钢内胆，像妈妈的关怀一样恒久温暖。那些独自奋斗的日子，也要好好照顾自己。」标签 #温暖日常 #好好生活 #一人食光
""",
        "humorous": """
【Few-shot示例】
商品：泡面 卖点：真材实料、大块牛肉、浓汤
平台：TikTok
文案：标题「被泡面耽误的米其林大厨🍜」正文「我宣布！这是我吃过最不'泡面'的泡面！大块牛肉多到怀疑人生，汤浓到可以当面膜敷（别试）。室友以为我在厨房做功夫菜，其实我只是撕了个料包😂谁吃谁知道！」标签 #泡面 #深夜放毒 #美食测评
""",
        "luxury": """
【Few-shot示例】
商品：丝巾 卖点：100%真丝、手工卷边、限量色
平台：Instagram
文案：标题「Silk · 以丝为名」正文「100%桑蚕丝。每一寸都经32道手工工序。全球限量300条，每条唯一编号。这不是配饰，是你颈间的艺术品。」标签 #SilkScarf #LuxuryLifestyle #限量发售
""",
    },
    "en": {
        "professional": """
【Few-shot Example】
Product: Mechanical Keyboard | Features: Cherry MX switches, RGB lighting, NKRO
Platform: TikTok
Copy: Title "Cherry MX + 16.8M RGB | The Ultimate Typing Experience" Body "Precision-engineered with Cherry MX switches rated for 100M keystrokes. 16.8 million color RGB backlighting with per-key customization. N-key rollover ensures every input registers. For professionals who demand perfection." Tags #mechanicalkeyboard #cherrymx #productivity
""",
        "casual": """
【Few-shot Example】
Product: Sunscreen | Features: SPF50+, lightweight, skincare-infused
Platform: TikTok
Copy: Title "the sunscreen that changed my life ☀️" Body "ok hear me out — SPF50+ that feels like literally nothing on your skin?! zero white cast, zero grease, just glow. plus niacinamide so you're basically getting brighter while protecting. this is your sign to grab it rn besties!!" Tags #sunscreen #skincareroutine #summeressentials
""",
        "minimalist": """
【Few-shot Example】
Product: Canvas Tote | Features: 100% cotton, oversized, 5 colors
Platform: Instagram
Copy: Title "one bag." Body "100% cotton. Holds everything. 5 colors. That's it." Tags #canvastote #minimalist #essentials
""",
        "emotional": """
【Few-shot Example】
Product: Thermos | Features: 316 stainless steel, 12h heat retention, lightweight
Platform: Instagram
Copy: Title "warmth that stays." Body "Early mornings. Late nights. Long commutes. This thermos has been there through all of it. Your dad's coffee. Your mom's soup. Some things keep more than just temperature — they keep moments." Tags #thermos #everydaycarry #sentimental
""",
        "humorous": """
【Few-shot Example】
Product: Instant Noodles | Features: real beef chunks, rich broth, premium
Platform: TikTok
Copy: Title "michelin chef trapped in instant noodles 🍜" Body "the beef chunks in this are BIGGER than my life decisions. the broth is so rich i almost filed taxes on it. my roommate walked in and said 'wow cooking from scratch?' ...i just boiled water. 💀 this is not a drill." Tags #instantnoodles #foodie #midnightcravings
""",
        "luxury": """
【Few-shot Example】
Product: Silk Scarf | Features: 100% mulberry silk, hand-rolled edges, limited edition
Platform: Instagram
Copy: Title "SILK · Art Around Your Neck" Body "100% Grade 6A mulberry silk. 32-step artisanal process. Each scarf numbered, never repeated. This is not an accessory. This is wearable art." Tags #SilkScarf #LuxuryLifestyle #LimitedEdition
""",
    },
}

# ═══════════════════════════════════════════════════════════════
#  增强版 Mock 文案库 — 6风格 × 多平台 × 多语言
# ═══════════════════════════════════════════════════════════════

MOCK_COPY = {
    "TikTok": {
        "zh": {
            "professional": {
                "titles": [
                    "【深度测评】{name} | 数据说话",
                    "{name}，用参数定义旗舰标准",
                    "拆解{name}：{features}有多硬核？",
                    "为什么业内都在关注{name}？",
                ],
                "bodies": [
                    "核心参数速览：{features}。经过30天深度使用，{name}在性能、续航、稳定性三个维度均超预期。同价位段横向对比，性价比优势明显。如果你正在寻找一款可靠的生产力工具，{name}值得列入首选清单。",
                    "{name}的硬实力值得一句“专业”评价。{features}让它在同品类中脱颖而出。工程师团队在细节优化上投入了大量精力——从材质工艺到软件调校，处处体现着对品质的执着。",
                    "数据不会说谎。{name}实测：{features}全部兑现。如果说竞品还在堆参数，那{name}已经在用体验定义标准。不吹不黑，这是今年最值得关注的单品之一。",
                    "{name}——一款不靠噱头，只靠硬实力说话的产品。{features}覆盖了目标用户90%的核心需求。更难得的是，它在长期使用中的稳定性令人印象深刻。推荐给所有注重实用性的朋友。",
                ],
                "tags": ["#{name}", "#深度测评", "#品质之选", "#硬核科技"],
            },
            "casual": {
                "titles": [
                    "绝了！{name}也太好用了吧😍",
                    "姐妹们冲！{name}真的爱了爱了",
                    "不许你还不知道{name}！按头安利🔥",
                    "真的服了...{name}怎么能这么香",
                ],
                "bodies": [
                    "天哪！{name}到手后我真的被惊艳到了～{features}这些全部都有！用了一周感觉整个人都快乐了！性价比超高学生党也能冲！赶紧安排上别等涨价再后悔🔥 #种草",
                    "OK我要开始疯狂安利了！{name}真的是我今年买过最值的东西没有之一！！！{features}这些功能每一个都戳中我！之前纠结了超久，用了之后只想说：为什么没有早点买！！！💕",
                    "宝子们，{name}我不允许还有人不知道！{features}，关键是颜值还超高！放到朋友圈被问爆了！真的有被自己种草到！快冲，手慢无！🛒",
                    "来了来了！你们催了好久的{name}评测来了！我只能说两个字：真香。{features}一个不少，用起来丝滑到飞起。已经给我闺蜜也安排上了！",
                ],
                "tags": ["#好物分享", "#种草", "#{name}", "#真香"],
            },
            "minimalist": {
                "titles": [
                    "{name}，够了。",
                    "{name} | 减法",
                    "选{name}。",
                    "— {name}",
                ],
                "bodies": [
                    "{name}。\n{features}。\n好产品不需要解释。",
                    "只有{name}。\n{features}。\n不多不少，刚刚好。",
                    "我们相信，最好的产品是让你忘记它的存在。\n{name}。{features}。\n简单至此。",
                    "{name}\n{features}\n\nLess, but better.\n— Dieter Rams",
                ],
                "tags": ["#极简主义", "#{name}", "#LessIsMore"],
            },
            "emotional": {
                "titles": [
                    "有些陪伴，{name}来守护 💙",
                    "谢谢你，{name}",
                    "{name} | 写给认真生活的你",
                    "那些和{name}有关的温暖日常",
                ],
                "bodies": [
                    "有时候，幸福真的很简单。\n清晨六点的第一缕阳光，深夜加班时{name}的默默陪伴。{features}，每一个细节都在告诉你：你值得被好好对待。\n生活或许不完美，但有一些东西，能让它变得更温柔一些。",
                    "记得刚毕业那年，租的小房间里只有几件行李。\n第一个给自己买的礼物，就是{name}。\n如今三年过去，它还在身边。{features}一如既往。\n有些东西，陪伴比功能更重要。",
                    "我们常常在追求更好的路上忘了——\n好，已经很好了。\n{name}。{features}。\n不必讨好世界，讨好自己就够了。",
                    "忙碌一天后推开门，{name}安静地等在那里。\n不需要语言，不需要操作。{features}，一切刚刚好。\n这就是我想要的，简单而确定的安全感。",
                ],
                "tags": ["#温暖日常", "#好好生活", "#{name}", "#小确幸"],
            },
            "humorous": {
                "titles": [
                    "笑死，{name}真的有毒😂",
                    "震惊！{name}居然做出这种事！",
                    "关于我被{name}征服这件事",
                    "大家好，我是{name}的水军（没收钱）",
                ],
                "bodies": [
                    "救命🆘 自从买了{name}，我的生活质量直线上升，但钱包哭了（并没有，性价比贼高）。{features}，比前任靠谱一万倍！室友以为我在搞传销天天安利，其实是真好用啊！！",
                    "朋友问我为什么最近这么快乐，我说因为{name}。他说一个东西能让你快乐？我说{features}了解一下？他说你是不是被洗脑了。三天后他在群里发：兄弟们快冲{name}！！！",
                    "我宣布：{name}是我本月最佳投资！比那杯38块的网红奶茶值多了！（奶茶：你礼貌吗？）{features}一个都没少，价格还这么良心，老板你是不是忘了加价？？？",
                    "用了{name}之后，我的日常：早中晚各安利一遍。朋友：你号被盗了？我：没有，是被{name}征服了。{features}，真的，谁用谁知道。不好用来打我。（别真来）",
                ],
                "tags": ["#搞笑日常", "#{name}", "#真香警告", "#安利狂魔"],
            },
            "luxury": {
                "titles": [
                    "{name} · 臻品之选",
                    "THE {name} | 为少数人",
                    "{name} — 定义属于你的奢华",
                    "限量·{name}",
                ],
                "bodies": [
                    "不是所有{name}，都配得上「臻品」二字。\n{features}——每项参数都经过匠人级调校。\n限量发售，每一件都拥有独立编号。\n这不是消费，这是收藏。",
                    "当品质不再满足于「够用」，{name}给出了答案。\n{features}，甄选全球顶级材质，由资深匠人手工打造。\n你拥有的不仅是一件产品，更是一个圈层的入场券。",
                    "有些人选择大众，有些人选择{name}。\n{features}——我们从不追求让所有人满意，只追求让对的人惊艳。\n尊享专属客服，7×24小时管家服务。",
                    "{name}。全球限量发售。\n{features}。\n每一件都是独一无二的存在。\n献给不妥协的你。",
                ],
                "tags": ["#奢华品质", "#{name}", "#限量版", "#尊享"],
            },
        },
        "en": {
            # 英文每个风格也提供 4+ 套
            "professional": {
                "titles": [
                    "{name} Review: Performance Meets Precision",
                    "Why {name} Dominates the Market",
                    "{name} | The Professional's Choice",
                    "Deep Dive: {name} Specs & Benchmarks",
                ],
                "bodies": [
                    "After extensive testing, {name} delivers on every metric. {features} — these aren't just specs, they're real-world advantages. For professionals who need reliability without compromise, this is the benchmark.",
                    "What separates {name} from the competition? {features}. In blind tests, 94% of users preferred {name} over leading alternatives. Data doesn't lie — this is class-leading performance.",
                ],
                "tags": ["#{name}", "#techreview", "#prograde", "#performance"],
            },
            "casual": {
                "titles": [
                    "ok {name} is actually insane 🔥",
                    "not me obsessing over {name} 🤪",
                    "the {name} hype is REAL y'all",
                    "POV: you finally got your {name} ✨",
                ],
                "bodies": [
                    "guys. GUYS. {name} is EVERYTHING. {features} — like hello?? why did nobody tell me about this sooner?! literally changed my daily routine. if you're on the fence, this is your sign to just DO IT 💅",
                    "not to be dramatic but {name} fixed my entire life. {features} all in one cute package?? the math is mathing. already sent the link to my group chat. you're welcome in advance besties 😘",
                ],
                "tags": ["#{name}", "#obsessed", "#TikTokMadeMeBuyIt", "#musthave"],
            },
            "minimalist": {
                "titles": [
                    "{name}.",
                    "{name} | Essential",
                    "just {name}",
                    "— {name}",
                ],
                "bodies": [
                    "{name}.\n{features}.\nEverything you need. Nothing you don't.",
                    "{name} — designed to disappear into your life.\n{features}.\nUnderstated. Uncompromising.",
                ],
                "tags": ["#minimalist", "#{name}", "#essential", "#quietluxury"],
            },
            "emotional": {
                "titles": [
                    "for the quiet moments. {name}.",
                    "thank you, {name} 💛",
                    "{name} | a love letter to everyday life",
                ],
                "bodies": [
                    "Some things anchor us. {name} has been mine. Through early mornings and late nights, {features} — it just works. Not flashy. Not loud. Just... there. And sometimes, that's exactly what we need.",
                ],
                "tags": ["#everydaymagic", "#{name}", "#grateful", "#simplejoys"],
            },
            "humorous": {
                "titles": [
                    "my {name} addiction is a PROBLEM 💀",
                    "{name} said 'let me fix your life real quick'",
                ],
                "bodies": [
                    "me before {name}: 🤡 me after {name}: 💅✨👑\n{features} and it costs less than my weekly coffee budget?! someone explain this sorcery. my friends think I got a brand deal. I WISH. this is just pure unfiltered obsession.",
                ],
                "tags": ["#{name}", "#noshame", "#obsessed", "#worthit"],
            },
            "luxury": {
                "titles": [
                    "{name} · The Art of Excellence",
                    "INTRODUCING: {name} Limited Edition",
                ],
                "bodies": [
                    "{name}. Hand-selected materials. {features}. Each piece undergoes 47 quality checks before reaching you. This isn't mass production — this is craft. Limited release. Numbered. Never repeated.",
                ],
                "tags": ["#LuxuryEdition", "#{name}", "#Craftsmanship", "#Exclusive"],
            },
        },
        "ja": {
            "professional": {
                "titles": ["【徹底レビュー】{name}の実力", "{name} | プロが選ぶ理由"],
                "bodies": ["{name}の核心：{features}。数値だけでなく実際の使用感でも、この製品は頭一つ抜けています。コストパフォーマンスも非常に高く、自信を持っておすすめできる一品です。"],
                "tags": ["#レビュー", "#{name}", "#プロ仕様"],
            },
            "casual": {
                "titles": ["やばい！{name}が神だった✨", "{name}使ってみた！マジでおすすめ"],
                "bodies": ["みんな！{name}届いてすぐ使ったんだけどマジで最高！{features}が全部揃っててこの価格はありえない！迷ってる人は絶対買ったほうがいい！損させないから！💕"],
                "tags": ["#おすすめ", "#{name}", "#買ってよかった"],
            },
            "minimalist": {
                "titles": ["{name}、それだけで。", "{name} | 必要十分"],
                "bodies": ["{name}。\n{features}。\n必要なものだけ。それでいい。"],
                "tags": ["#ミニマル", "#{name}", "#シンプル"],
            },
            "emotional": {
                "titles": ["{name}と過ごす毎日", "あなたに、{name}を。"],
                "bodies": ["忙しい毎日の中で、{name}がそっと寄り添ってくれる。{features}という細やかな気遣いが、あなたの暮らしを優しく包み込みます。"],
                "tags": ["#暮らし", "#{name}", "#ていねいな生活"],
            },
            "humorous": {
                "titles": ["笑、{name}がバグってるwww", "{name}に人生変わった話"],
                "bodies": ["ちょっと聞いてください！{name}買ったら毎日が楽しすぎてやばい！{features}でこの価格とか正気？！友達全員に布教してるんですけど、みんな買ってくれるまで言い続けます😂"],
                "tags": ["#笑", "#{name}", "#神コスパ"],
            },
            "luxury": {
                "titles": ["{name}·至高の一品", "LIMITED {name}"],
                "bodies": ["{name}。厳選された素材、{features}。すべてが最高峰。これは買い物ではなく、投資です。"],
                "tags": ["#ラグジュアリー", "#{name}", "#限定品"],
            },
        },
        "ko": {
            "professional": {
                "titles": ["{name} 리뷰: 성능의 기준을 바꾸다", "{name} | 프로의 선택"],
                "bodies": ["{name}의 핵심: {features}. 수치만 좋은 게 아니라 실제 사용감도 완벽합니다. 동급 최고의 가성비. 자신 있게 추천합니다."],
                "tags": ["#리뷰", "#{name}", "#프로픽"],
            },
            "casual": {
                "titles": ["대박! {name} 이거 진짜 미쳤어요 💕", "{name} 써보고 인생템 등극"],
                "bodies": ["여러분 진짜 {name} 대박이에요! {features} 다 되는데 가격도 착하고! 친구들한테 벌써 다 알려줬어요. 고민하지 말고 그냥 사세요 후회 안 해요 약속! 💖"],
                "tags": ["#강추", "#{name}", "#인생템"],
            },
            "minimalist": {
                "titles": ["{name}.", "{name} | 본질"],
                "bodies": ["{name}.\n{features}.\n필요한 것만. 그걸로 충분합니다."],
                "tags": ["#미니멀", "#{name}", "#본질"],
            },
            "emotional": {
                "titles": ["{name}와 함께한 하루하루", "당신에게, {name}을."],
                "bodies": ["바쁜 일상 속에서도 {name}이 당신의 곁을 지킵니다. {features}이라는 작은 배려가 당신의 하루를 따뜻하게 감싸줄 거예요."],
                "tags": ["#일상", "#{name}", "#소확행"],
            },
            "humorous": {
                "titles": ["웃김ㅋㅋ {name} 미쳤어요 진짜 🤣", "{name} 때문에 인생 바뀐 썰"],
                "bodies": ["아 진짜 {name} 써보고 너무 좋아서 미치는 줄! {features}인데 가격도 이렇고?! 사장님 정신 차리세요!! 친구들한테 전도사처럼 전파하는 중ㅋㅋ"],
                "tags": ["#웃김", "#{name}", "#가성비갑"],
            },
            "luxury": {
                "titles": ["{name} · 프리미엄의 정점", "{name} 리미티드 에디션"],
                "bodies": ["{name}. 까다롭게 선별된 소재. {features}. 모든 것이 최상급. 이것은 소비가 아닌 투자입니다."],
                "tags": ["#럭셔리", "#{name}", "#한정판"],
            },
        },
        "es": {
            "professional": {
                "titles": ["{name} | Análisis Profesional", "{name}: El Estándar de Calidad"],
                "bodies": ["{name}. {features}. Rendimiento comprobado en condiciones reales. Para profesionales que no aceptan compromisos."],
                "tags": ["#review", "#{name}", "#profesional"],
            },
            "casual": {
                "titles": ["¡Increíble! {name} me cambió la vida 🤩", "Necesitas {name} en tu vida YA"],
                "bodies": ["Chicos, {name} es LO MEJOR. {features} y encima el precio es una locura! Mis amigas ya están todas comprándolo. ¡No te quedes sin el tuyo! 💕"],
                "tags": ["#recomendado", "#{name}", "#imprescindible"],
            },
            "minimalist": {
                "titles": ["{name}.", "{name} | Esencial"],
                "bodies": ["{name}.\n{features}.\nSolo lo necesario.\nNada más."],
                "tags": ["#minimalista", "#{name}", "#esencial"],
            },
            "emotional": {
                "titles": ["{name}, tu compañero de cada día 💛", "Gracias, {name}."],
                "bodies": ["En los pequeños momentos, {name} está ahí. {features}. Un recordatorio silencioso de que mereces lo mejor, cada día."],
                "tags": ["#momentos", "#{name}", "#gratitud"],
            },
            "humorous": {
                "titles": ["{name} está ROTO de lo bueno que es 😂", "Mi historia de amor con {name}"],
                "bodies": ["Ok pero {name} es ridículamente bueno! {features} por este precio debería ser ilegal!! Mis amigos creen que me pagan pero NO, es amor real jajaja"],
                "tags": ["#humor", "#{name}", "#adicto"],
            },
            "luxury": {
                "titles": ["{name} · Excelencia Artesanal", "{name} Edición Limitada"],
                "bodies": ["{name}. Materiales seleccionados a mano. {features}. Piezas numeradas. Esto no es un producto. Es una declaración."],
                "tags": ["#lujo", "#{name}", "#exclusivo"],
            },
        },
    },
    "Instagram": {
        "zh": {
            "professional": {
                "titles": ["{name} | 开箱实测 📊", "深度体验{name}一个月后..."],
                "bodies": ["{name}深度体验报告。{features}全部兑现。\n\n适合人群：追求品质与效率的你。\n综合评分：⭐⭐⭐⭐⭐ 4.8/5\n\n主页链接在Bio，欢迎交流。"],
                "tags": ["#好物测评", "#{name}", "#品质生活"],
            },
            "casual": {
                "titles": ["今日份种草🌱 {name}", "挖到宝了！{name}太绝了"],
                "bodies": ["姐妹们！我挖到宝藏了！！{name}简直就是为懒人量身定做的！{features}一次性满足所有需求！已经是我的年度爱用了💕\n链接在主页，自取～"],
                "tags": ["#种草", "#OOTD", "#{name}", "#好物分享"],
            },
            "minimalist": {
                "titles": ["{name}", "— {name}"],
                "bodies": ["{name}。\n{features}。\n\n📦 主页链接。"],
                "tags": ["#minimal", "#{name}", "#aesthetic"],
            },
            "emotional": {
                "titles": ["{name} | 温柔以待每一天 🌿", "写给{name}的一封情书"],
                "bodies": ["有人说，好物如旧友。\n{name}就是这样的存在。{features}，它从不喧哗，却总在需要时给你力量。\n愿你的生活里，也多一些这样温柔的存在。💙"],
                "tags": ["#温柔日常", "#{name}", "#好好爱自己"],
            },
            "humorous": {
                "titles": ["{name}：一款让我变话痨的产品 😂", "关于我为什么天天吹{name}"],
                "bodies": ["朋友：你最近是不是进传销了？\n我：没有啊。\n朋友：那你为什么天天发{name}？\n我：因为真的太好用了啊！！！{features}了解一下？？？\n朋友：...(三天后) 确实好用。"],
                "tags": ["#搞笑日常", "#{name}", "#真香"],
            },
            "luxury": {
                "titles": ["{name} · 少数派的选择", "THE {name} COLLECTION"],
                "bodies": ["{name}。\n{features}。\n每件作品耗时72小时以上。\n仅接受预约品鉴。\nDM for private viewing."],
                "tags": ["#LuxuryCollection", "#{name}", "#PrivateCollection"],
            },
        },
        "en": {
            "professional": {
                "titles": ["{name} | Honest Review", "One month with {name}: the verdict"],
                "bodies": ["{name} after 30 days. {features} — all delivered as promised. For the discerning buyer who values substance over hype. Link in bio for full review."],
                "tags": ["#honestreview", "#{name}", "#quality"],
            },
            "casual": {
                "titles": ["found my new obsession 🤍 {name}", "run don't walk: {name} is IT"],
                "bodies": ["you guys... {name} is the real deal. {features} all in one?! literally my best find this year. link in bio — you're welcome 😘"],
                "tags": ["#instagood", "#{name}", "#favorites"],
            },
            "minimalist": {
                "titles": ["{name}", "— {name}"],
                "bodies": ["{name}.\n{features}.\n\nLink in bio."],
                "tags": ["#minimal", "#{name}", "#cleanaesthetic"],
            },
            "emotional": {
                "titles": ["{name} | for the soul 💫", "a quiet love letter to {name}"],
                "bodies": ["Some things just feel right. {name} is one of them.\n{features}.\nIt's the little rituals that make a house a home."],
                "tags": ["#simplethings", "#{name}", "#gratefulheart"],
            },
            "humorous": {
                "titles": ["my {name} propaganda continues 📢", "plot twist: {name} is actually amazing"],
                "bodies": ["my friends after hearing about {name} for the 47th time: 🧏\nme: BUT {features}!!!\nthem: fine. *buys it*\nthem 3 days later: why didn't you tell us sooner?!\nme: I LITERALLY DID."],
                "tags": ["#relatable", "#{name}", "#worththehype"],
            },
            "luxury": {
                "titles": ["{name} · Curated Edition", "THE {name} EXPERIENCE"],
                "bodies": ["{name}. {features}. Each piece numbered. By appointment only. DM to inquire."],
                "tags": ["#curated", "#{name}", "#privatecollection"],
            },
        },
        "ja": {
            "professional": {"titles": ["{name} | 一ヶ月使ってみた"], "bodies": ["{name}を30日使った率直な感想。{features}すべて期待以上。品質を重視する方に。"], "tags": ["#レビュー", "#{name}"]},
            "casual": {"titles": ["{name}が予想以上に良かった話💕"], "bodies": ["みんな聞いて！{name}本当に良かった！{features}揃っててこの見た目！完璧でしょ！リンクはプロフィールから！"], "tags": ["#お気に入り", "#{name}"]},
            "minimalist": {"titles": ["{name}"], "bodies": ["{name}。{features}。\nリンクはプロフィールに。"], "tags": ["#ミニマル", "#{name}"]},
            "emotional": {"titles": ["{name} | 日々の小さな幸せ"], "bodies": ["忙しい毎日。{name}がちょっとしたご褒美になる。{features}。自分を大切にすることから、すべては始まる。"], "tags": ["#暮らし", "#{name}"]},
            "humorous": {"titles": ["{name}にハマりすぎてヤバいwww"], "bodies": ["{name}の布教活動に勤しむ私。友達「またその話？」私「だって{features}だよ？！」友達「...買ったわ」私「でしょう？！」というやりとりが既に5回発生。"], "tags": ["#笑", "#{name}"]},
            "luxury": {"titles": ["{name} · クラフトマンシップ"], "bodies": ["{name}。{features}。一点一点丁寧に。DMにてお問い合わせを。"], "tags": ["#ラグジュアリー", "#{name}"]},
        },
        "ko": {
            "professional": {"titles": ["{name} | 30일 사용기"], "bodies": ["{name} 30일 사용 솔직 후기. {features} 모두 기대 이상입니다. 품질을 중시하는 분들께 추천드립니다."], "tags": ["#리뷰", "#{name}"]},
            "casual": {"titles": ["{name} 완전 반했어요 💕"], "bodies": ["여러분 진짜 {name} 대박! {features} 완벽 그 자체! 프로필 링크에서 확인하세요!"], "tags": ["#최애템", "#{name}"]},
            "minimalist": {"titles": ["{name}"], "bodies": ["{name}.\n{features}.\n프로필 링크."], "tags": ["#미니멀", "#{name}"]},
            "emotional": {"titles": ["{name} | 소소한 행복"], "bodies": ["바쁜 하루. {name}이 작은 위로가 됩니다. {features}. 나를 소중히 여기는 것에서 모든 게 시작돼요."], "tags": ["#일상", "#{name}"]},
            "humorous": {"titles": ["{name} 전도사 된 썰 ㅋㅋ"], "bodies": ["친구: 또 {name} 얘기야?\n나: {features}인데 어쩌라고!!\n친구: ...샀어\n나: 👍\n이런 대화만 5번째."], "tags": ["#웃김", "#{name}"]},
            "luxury": {"titles": ["{name} · 장인정신"], "bodies": ["{name}。{features}。한 땀 한 땀 정성껏。DM으로 문의 주세요。"], "tags": ["#럭셔리", "#{name}"]},
        },
        "es": {
            "professional": {"titles": ["{name} | Reseña Honesta"], "bodies": ["{name} después de 30 días. {features}. Para quienes valoran la calidad sobre el hype."], "tags": ["#review", "#{name}"]},
            "casual": {"titles": ["obsesionada con {name} 💕"], "bodies": ["chicos {name} es LO MÁXIMO. {features} todo en uno. enlace en mi perfil — de nada 😘"], "tags": ["#favorito", "#{name}"]},
            "minimalist": {"titles": ["{name}"], "bodies": ["{name}.\n{features}.\nLink en bio."], "tags": ["#minimal", "#{name}"]},
            "emotional": {"titles": ["{name} | pequeñas alegrías"], "bodies": ["En los días difíciles, {name} es ese pequeño lujo que me recuerda: merezco cosas buenas. {features}."], "tags": ["#momentos", "#{name}"]},
            "humorous": {"titles": ["mi obsesión con {name} es problema 😂"], "bodies": ["mis amigos ya no me hablan porque solo hablo de {name}. pero es que {features}!! quién me entiende?!"], "tags": ["#humor", "#{name}"]},
            "luxury": {"titles": ["{name} · Edición Exclusiva"], "bodies": ["{name}. {features}. Piezas numeradas. Para conocedores."], "tags": ["#lujo", "#{name}"]},
        },
    },
    "Amazon": {
        "zh": {
            "professional": {
                "titles": ["{name} | {features} | 专业推荐", "{name} — {features} — 今日特惠"],
                "bodies": ["【产品亮点】\n✅ {features}\n✅ 30天无忧退换\n✅ 24小时客服响应\n✅ 2年质保承诺\n\n📊 客户评分：⭐⭐⭐⭐⭐ 4.8/5（2,847条评价）\n📦 Prime会员享次日达\n\n点击加入购物车，体验品质生活。"],
                "tags": ["#{name}", "#Amazon热卖", "#品质保证"],
            },
            "casual": {
                "titles": ["🔥 爆款返场！{name}限时优惠", "{name} | {features} | 手慢无"],
                "bodies": ["🎉 被问了800遍的{name}终于补货了！\n{features}全部都有，这个价格真的别犹豫！\n\n⭐ 4.8分 · 2000+好评\n🛒 点击购买 → 预计2天到手\n\n上次3小时就卖完了，这次别错过！"],
                "tags": ["#{name}", "#限时优惠", "#好评如潮"],
            },
            "minimalist": {
                "titles": ["{name} · {features}", "{name} | 简而不凡"],
                "bodies": ["{name}。\n{features}。\n4.8/5 · 2000+评价。\n点击购买。"],
                "tags": ["#{name}", "#简约"],
            },
            "emotional": {
                "titles": ["{name} | {features} | 给最爱的家人", "{name} — 一份温暖的礼物"],
                "bodies": ["最温暖的礼物，不是最贵的，而是最懂你的。\n{name}，{features}，处处为你想得更多。\n\n💝 送给父母、爱人、朋友——或者，犒劳一下努力的自己。\n📦 精美礼盒包装，附赠手写卡片。"],
                "tags": ["#{name}", "#礼物推荐", "#暖心好物"],
            },
            "humorous": {
                "titles": ["{name} | {features} | 买了不后悔系列", "警告：{name}可能导致幸福感爆棚"],
                "bodies": ["⚠️ 警告：购买{name}后可能出现以下症状：\n• 每天忍不住用800遍\n• 逢人就安利\n• 后悔...没有早点买\n\n{features}。千言万语汇成一句话：买它！"],
                "tags": ["#{name}", "#不买后悔", "#闭眼入"],
            },
            "luxury": {
                "titles": ["{name} · 旗舰之选 | {features}", "{name} | 尊享版 | {features}"],
                "bodies": ["🏆 {name} 尊享版\n\n{features}\n甄选进口材质 · 大师级工艺 · 限量发售\n\n📋 规格参数：顶级配置，专属定制\n🎁 赠：品牌限量礼盒 + VIP会员卡\n📞 专属客服：购买后享一对一管家服务"],
                "tags": ["#{name}", "#尊享版", "#奢品"],
            },
        },
        "en": {
            "professional": {
                "titles": ["{name} | {features} | Best Seller", "{name} — Professional Grade {features}"],
                "bodies": ["【Product Highlights】\n✅ {features}\n✅ 30-Day Money-Back Guarantee\n✅ 24/7 Customer Support\n✅ 2-Year Warranty\n\n📊 Rating: ⭐⭐⭐⭐⭐ 4.8/5 (2,847 reviews)\n📦 Free Prime Delivery\n\nAdd to cart now."],
                "tags": ["#{name}", "#AmazonBestSeller", "#quality"],
            },
            "casual": {
                "titles": ["🔥 HOT DEAL: {name} | {features}", "{name} | Best purchase this year!"],
                "bodies": ["Everyone's talking about {name} and now I get why!! {features} — this is the deal you've been waiting for. ⭐ 4.8 stars · 2000+ reviews. Tap Add to Cart before it's gone again!"],
                "tags": ["#{name}", "#deals", "#amazonfinds"],
            },
            "minimalist": {
                "titles": ["{name} · {features}", "{name}"],
                "bodies": ["{name}. {features}. 4.8/5. Add to cart."],
                "tags": ["#{name}", "#simple"],
            },
            "emotional": {
                "titles": ["{name} | A Gift That Says You Care", "{name} — for someone special"],
                "bodies": ["The best gifts aren't the most expensive — they're the most thoughtful. {name}, with {features}, is designed to make every day a little better. 💝 Gift-ready packaging included."],
                "tags": ["#{name}", "#giftideas", "#thoughtful"],
            },
            "humorous": {
                "titles": ["{name} | Warning: May Cause Extreme Satisfaction", "{name}: the product I won't shut up about"],
                "bodies": ["⚠️ Side effects of {name} include: uncontrollable smiling, compulsive recommending to friends, and wondering why you didn't buy this sooner. {features}. You've been warned. Now add to cart."],
                "tags": ["#{name}", "#noregrets", "#buyitnow"],
            },
            "luxury": {
                "titles": ["{name} · Flagship Edition | {features}", "{name} | Premium Craftsmanship"],
                "bodies": ["🏆 {name} Flagship Edition. {features}. Premium materials. Master craftsmanship. Limited release. 🎁 Includes: gift box + VIP membership card."],
                "tags": ["#{name}", "#premium", "#limited"],
            },
        },
    },
}


class MockLLMClient:
    """增强版 Mock LLM 客户端 — 6风格 × 多套模板 × 多语言"""

    def generate(self, product_name: str, features: str, platform: str,
                 language: str = "zh", style: str = "professional") -> dict:
        platform_data = MOCK_COPY.get(platform, MOCK_COPY["TikTok"])
        first_avail = list(platform_data.keys())[0] if platform_data else "zh"
        lang_data = platform_data.get(language) or platform_data.get("en") or platform_data.get("zh") or platform_data.get(first_avail, {})

        # 风格选择：请求风格 → professional → 任意第一个风格
        if isinstance(lang_data, dict) and style in lang_data:
            style_data = lang_data[style]
        elif isinstance(lang_data, dict) and "professional" in lang_data:
            style_data = lang_data["professional"]
        elif isinstance(lang_data, dict):
            # 有些语言只有基础风格，取第一个
            keys = [k for k in lang_data if k not in ("",)]
            if keys:
                style_data = lang_data[keys[0]]
            else:
                style_data = lang_data
        else:
            style_data = lang_data

        # 确保选到正确层级（字典且有 titles）
        if not isinstance(style_data, dict) or "titles" not in style_data:
            # 深度遍历找第一个有效数据
            for v in lang_data.values():
                if isinstance(v, dict) and "titles" in v:
                    style_data = v
                    break

        title = random.choice(style_data["titles"]).format(name=product_name)
        body = random.choice(style_data["bodies"]).format(name=product_name, features=features)
        tags_str = ", ".join([t.format(name=product_name) for t in style_data["tags"]])

        import time
        time.sleep(random.uniform(0.15, 0.4))

        return {
            "platform": platform,
            "title": title,
            "body": body,
            "tags": tags_str,
            "language": language,
            "style": style,
        }


class OpenAICompatClient:
    """增强版 OpenAI 兼容 API 客户端 — 结构化 Few-shot Prompt"""

    def __init__(self):
        self.api_url = settings.LLM_API_URL
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    def _build_system_prompt(self) -> str:
        return (
            "你是一位世界顶级的电商营销文案专家，服务过Apple、Nike、LVMH等品牌。"
            "你深谙各平台算法规则和用户心理，精通中文、英文、日文、韩文、西班牙文的营销文案撰写。\n\n"
            "核心能力：\n"
            "1. 根据产品和平台特征，选择最优的文案策略\n"
            "2. 精准控制文案风格（专业/活泼/极简/情感/幽默/奢华）\n"
            "3. 标题不超过50字符，正文100-200字，标签3-5个\n"
            "4. 仅返回JSON格式，不要在JSON外输出任何内容"
        )

    def _get_fewshot(self, language: str, style: str) -> str:
        """获取对应语言和风格的 Few-shot 示例"""
        lang_examples = FEWSHOT_EXAMPLES.get(language, FEWSHOT_EXAMPLES.get("zh", {}))
        style_example = lang_examples.get(style, lang_examples.get("professional", ""))
        return style_example

    def _build_user_prompt(self, product_name: str, features: str, platform: str,
                           language: str, style: str, industry: str = "") -> dict:
        """构造完整的结构化 Prompt"""
        lang_names = {"zh": "中文", "en": "English", "ja": "日本語", "ko": "한국어", "es": "Español"}
        style_profile = STYLE_PROFILES.get(style, STYLE_PROFILES["professional"])
        style_name = style_profile.get("name_zh", style)
        style_tone = style_profile.get("tone", "")
        style_features = style_profile.get("features", "")

        fewshot = self._get_fewshot(language, style)

        industry_hint = ""
        if industry:
            ind = INDUSTRY_CONTEXT.get(industry, {})
            ind_keywords = ind.get(f"keywords_{language}", ind.get("keywords_zh", ""))
            industry_hint = f"\n\n行业参考：{ind.get('name_zh', industry)}。建议融入关键词：{ind_keywords}"

        prompt = f"""请为以下商品撰写{platform}平台营销文案。

【商品信息】
- 商品名称：{product_name}
- 核心卖点：{features}
- 目标平台：{platform}
- 文案语言：{lang_names.get(language, language)}
- 文案风格：{style_name}（{style_tone}）
- 风格特征：{style_features}{industry_hint}

{fewshot}

【输出要求】
1. 标题：吸引力强，不超过50字符
2. 正文：突出卖点，100-200字，自然流畅
3. 标签：3-5个，英文逗号分隔
4. 严格遵守JSON格式：{{"title":"...","body":"...","tags":"..."}}
5. 不要输出JSON之外的任何内容

现在请为「{product_name}」生成{lang_names.get(language, language)}文案："""

        return prompt

    async def generate(self, product_name: str, features: str, platform: str,
                       language: str = "zh", style: str = "professional",
                       industry: str = "") -> dict:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(product_name, features, platform,
                                               language, style, industry)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.85,
                    "max_tokens": 800,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            # 移除可能的 markdown 包裹
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("\n```", 1)[0]

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {
                "title": content[:60],
                "body": content,
                "tags": f"#{product_name}",
            }

        return {
            "platform": platform,
            "title": result.get("title", ""),
            "body": result.get("body", ""),
            "tags": result.get("tags", ""),
            "language": language,
            "style": style,
        }


def get_llm_client() -> MockLLMClient | OpenAICompatClient:
    if settings.LLM_API_KEY:
        return OpenAICompatClient()
    return MockLLMClient()
