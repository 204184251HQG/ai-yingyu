"""
词途 · AI 英语单词学习闯关系统 — 单词词库 + 句型数据 + 学习记录
覆盖小学/初中/高中三学段：词库存放于 data/wordbank/{primary,middle,high}.json
（对标百词斩教材分册全集，目标量级 5000+ 词），配套例句，支持多种题型派生
"""
import json, os, pathlib, random

_HERE = pathlib.Path(__file__).parent
RECORD_FILE = _HERE / "yingyu_records.json"
CUSTOM_WORDS_FILE = _HERE / "yingyu_custom_words.json"
WORDBANK_DIR = _HERE / "data" / "wordbank"

# ── 8大词汇主题 ──
YY_TOPICS = {
    "basic": {
        "name": "基础词汇",
        "icon": "[基]",
        "color": "#2563eb",
        "desc": "日常生活中最常用的基础英语单词",
        "tips": [
            "Hello / Hi 都是问候语，Hi 更口语化",
            "yes 表示同意，no 表示否定",
            "please 礼貌用语，请求时使用",
            "thank you 表达感谢，对应 you're welcome",
            "good morning / afternoon / evening 区分时段",
        ],
    },
    "school": {
        "name": "学校生活",
        "icon": "[校]",
        "color": "#0d9488",
        "desc": "学校、文具、学科相关词汇",
        "tips": [
            "teacher 老师，student 学生",
            "classroom 教室，由 class + room 组成",
            "math、English、Chinese 都是学科名",
            "pencil 铅笔，pen 钢笔，eraser 橡皮",
            "book 书，notebook 笔记本",
        ],
    },
    "nature": {
        "name": "自然世界",
        "icon": "[然]",
        "color": "#16a34a",
        "desc": "动物、植物、天气等自然词汇",
        "tips": [
            "动物名词如 dog、cat、bird 通常可数",
            "weather 天气，sunny / rainy / cloudy 描述天气",
            "tree 树，flower 花，grass 草",
            "river 河，mountain 山，sea 海",
            "spring、summer、autumn、winter 四季",
        ],
    },
    "food": {
        "name": "食物饮食",
        "icon": "[食]",
        "color": "#d97706",
        "desc": "食物、饮料、餐具相关词汇",
        "tips": [
            "apple 苹果，banana 香蕉，orange 橙子",
            "rice 米饭、bread 面包、noodle 面条",
            "milk 牛奶、water 水、juice 果汁",
            "breakfast 早餐、lunch 午餐、dinner 晚餐",
            "delicious 美味的，常用形容词",
        ],
    },
    "family": {
        "name": "家庭朋友",
        "icon": "[亲]",
        "color": "#dc2626",
        "desc": "家庭成员、人物关系词汇",
        "tips": [
            "father / dad 爸爸，mother / mom 妈妈",
            "brother 兄弟，sister 姐妹",
            "grandfather 爷爷/外公，grandmother 奶奶/外婆",
            "uncle 叔伯舅，aunt 姑姨婶",
            "friend 朋友，classmate 同学",
        ],
    },
    "numtime": {
        "name": "数字时间",
        "icon": "[数]",
        "color": "#7c3aed",
        "desc": "数字、星期、月份、时间表达",
        "tips": [
            "1-12 是 one 到 twelve",
            "13-19 词尾通常 -teen，20-90 整十词尾 -ty",
            "Monday 到 Sunday 是星期",
            "January 到 December 是月份",
            "o'clock 表示整点，half past 表示半点",
        ],
    },
    "colorshape": {
        "name": "颜色形状",
        "icon": "[色]",
        "color": "#db2777",
        "desc": "颜色与几何形状词汇",
        "tips": [
            "red 红，yellow 黄，blue 蓝，green 绿",
            "black 黑，white 白，brown 棕，pink 粉",
            "circle 圆，square 方，triangle 三角",
            "形容词通常放在名词前：a red apple",
            "light / dark 可修饰颜色：light blue",
        ],
    },
    "action": {
        "name": "动作情感",
        "icon": "[动]",
        "color": "#ea580c",
        "desc": "常用动词、情感形容词",
        "tips": [
            "动词 run、jump、walk、swim 描述动作",
            "happy 开心，sad 难过，angry 生气",
            "like / love 喜欢/喜爱，区分程度",
            "动词第三人称单数加 -s：He runs",
            "现在分词加 -ing：I am running",
        ],
    },
}

# ── 学段标签 ──
LEVELS = {
    "primary": {"name": "小学", "color": "#16a34a", "grade_range": (1, 6)},
    "middle":  {"name": "初中", "color": "#0d9488", "grade_range": (7, 9)},
    "high":    {"name": "高中", "color": "#7c3aed", "grade_range": (10, 12)},
}


# ── 单词词库（从 data/wordbank/*.json 加载） ──
# 字段：word / meaning / phonetic / pos / topic / difficulty / example / example_zh
# level 字段由文件名自动注入（primary.json / middle.json / high.json）
# 全量词库不内联在本模块，避免主文件体积膨胀

_FALLBACK_WORDS = [
    {"word": "hello", "meaning": "你好", "phonetic": "/həˈləʊ/", "pos": "int", "topic": "basic", "difficulty": 1, "example": "Hello!", "example_zh": "你好！", "level": "primary"},
    {"word": "apple", "meaning": "苹果", "phonetic": "/ˈæpl/", "pos": "n", "topic": "food", "difficulty": 1, "example": "I eat an apple.", "example_zh": "我吃一个苹果。", "level": "primary"},
    {"word": "book", "meaning": "书", "phonetic": "/bʊk/", "pos": "n", "topic": "school", "difficulty": 1, "example": "I read a book.", "example_zh": "我看书。", "level": "primary"},
]


def _load_wordbank_from_json():
    """从 data/wordbank/{primary,middle,high}*.json 加载词库。

    - 每学段允许多个分片文件（如 primary.json / primary_a.json / primary_b.json），按文件名排序合并。
    - 任一 JSON 缺失/损坏则跳过该文件。
    - level 字段按文件名前缀自动注入（以 JSON 内部为准可覆盖）。
    - 三个学段全部无文件时返回 _FALLBACK_WORDS 兜底。
    """
    out = []
    if not WORDBANK_DIR.exists():
        return [dict(w) for w in _FALLBACK_WORDS]
    for level in ("primary", "middle", "high"):
        # 主文件 + 分片文件：{level}.json, {level}_a.json, {level}_b.json …
        files = sorted(
            list(WORDBANK_DIR.glob(f"{level}.json")) +
            list(WORDBANK_DIR.glob(f"{level}_*.json"))
        )
        for fp in files:
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            for w in data:
                w.setdefault("level", level)
                out.append(w)
    return out or [dict(w) for w in _FALLBACK_WORDS]


WORDS = _load_wordbank_from_json()


# ── 句型分类训练数据 ──
# 9 元组格式：
#   (word_count, has_q, has_e, has_be, has_aux, has_modal, has_not, starts_wh, label)
# 类别：0=陈述句 1=一般疑问句 2=特殊疑问句 3=感叹句 4=祈使句 5=否定句
SENTENCE_LABELS = {
    0: "陈述句",
    1: "一般疑问句",
    2: "特殊疑问句",
    3: "感叹句",
    4: "祈使句",
    5: "否定句",
}

SENTENCE_TRAIN_DATA = [
    # ─── 陈述句 (0): has_q=0, has_e=0, has_not=0, starts_wh=0 ───
    (4, 0, 0, 1, 0, 0, 0, 0, 0), (5, 0, 0, 1, 0, 0, 0, 0, 0),
    (6, 0, 0, 1, 0, 0, 0, 0, 0), (7, 0, 0, 1, 0, 0, 0, 0, 0),
    (5, 0, 0, 0, 0, 0, 0, 0, 0), (6, 0, 0, 0, 0, 0, 0, 0, 0),
    (4, 0, 0, 0, 0, 0, 0, 0, 0), (5, 0, 0, 0, 1, 0, 0, 0, 0),
    (6, 0, 0, 0, 1, 0, 0, 0, 0), (7, 0, 0, 0, 1, 0, 0, 0, 0),
    (5, 0, 0, 0, 0, 1, 0, 0, 0), (6, 0, 0, 0, 0, 1, 0, 0, 0),
    (8, 0, 0, 1, 0, 0, 0, 0, 0), (5, 0, 0, 1, 0, 0, 0, 0, 0),
    (4, 0, 0, 1, 0, 0, 0, 0, 0), (6, 0, 0, 1, 0, 0, 0, 0, 0),
    (7, 0, 0, 1, 0, 0, 0, 0, 0), (5, 0, 0, 0, 0, 0, 0, 0, 0),
    (6, 0, 0, 0, 0, 0, 0, 0, 0), (4, 0, 0, 0, 1, 0, 0, 0, 0),
    (5, 0, 0, 0, 1, 0, 0, 0, 0), (7, 0, 0, 0, 1, 0, 0, 0, 0),
    (6, 0, 0, 0, 0, 1, 0, 0, 0), (5, 0, 0, 1, 1, 0, 0, 0, 0),
    (8, 0, 0, 1, 0, 0, 0, 0, 0), (9, 0, 0, 1, 0, 0, 0, 0, 0),
    (4, 0, 0, 1, 0, 0, 0, 0, 0), (5, 0, 0, 1, 0, 0, 0, 0, 0),
    (6, 0, 0, 1, 0, 0, 0, 0, 0), (7, 0, 0, 0, 0, 0, 0, 0, 0),

    # ─── 一般疑问句 (1): has_q=1, has_e=0, has_not=0, starts_wh=0 ───
    (4, 1, 0, 1, 0, 0, 0, 0, 1), (5, 1, 0, 1, 0, 0, 0, 0, 1),
    (3, 1, 0, 1, 0, 0, 0, 0, 1), (6, 1, 0, 1, 0, 0, 0, 0, 1),
    (4, 1, 0, 0, 1, 0, 0, 0, 1), (5, 1, 0, 0, 1, 0, 0, 0, 1),
    (6, 1, 0, 0, 1, 0, 0, 0, 1), (3, 1, 0, 0, 1, 0, 0, 0, 1),
    (4, 1, 0, 0, 0, 1, 0, 0, 1), (5, 1, 0, 0, 0, 1, 0, 0, 1),
    (3, 1, 0, 0, 0, 1, 0, 0, 1), (6, 1, 0, 0, 0, 1, 0, 0, 1),
    (5, 1, 0, 1, 0, 0, 0, 0, 1), (4, 1, 0, 1, 0, 0, 0, 0, 1),
    (6, 1, 0, 1, 0, 0, 0, 0, 1), (5, 1, 0, 0, 1, 0, 0, 0, 1),
    (4, 1, 0, 0, 1, 0, 0, 0, 1), (5, 1, 0, 0, 1, 0, 0, 0, 1),
    (4, 1, 0, 0, 0, 1, 0, 0, 1), (5, 1, 0, 0, 0, 1, 0, 0, 1),
    (3, 1, 0, 1, 0, 0, 0, 0, 1), (4, 1, 0, 1, 0, 0, 0, 0, 1),
    (5, 1, 0, 1, 0, 0, 0, 0, 1), (6, 1, 0, 0, 1, 0, 0, 0, 1),
    (5, 1, 0, 0, 1, 0, 0, 0, 1), (4, 1, 0, 0, 0, 1, 0, 0, 1),
    (3, 1, 0, 1, 0, 0, 0, 0, 1), (5, 1, 0, 1, 0, 0, 0, 0, 1),
    (4, 1, 0, 0, 1, 0, 0, 0, 1), (5, 1, 0, 0, 0, 1, 0, 0, 1),

    # ─── 特殊疑问句 (2): has_q=1, has_not=0, starts_wh=1 ───
    (5, 1, 0, 1, 0, 0, 0, 1, 2), (4, 1, 0, 1, 0, 0, 0, 1, 2),
    (6, 1, 0, 1, 0, 0, 0, 1, 2), (7, 1, 0, 1, 0, 0, 0, 1, 2),
    (5, 1, 0, 0, 1, 0, 0, 1, 2), (6, 1, 0, 0, 1, 0, 0, 1, 2),
    (4, 1, 0, 0, 1, 0, 0, 1, 2), (7, 1, 0, 0, 1, 0, 0, 1, 2),
    (5, 1, 0, 0, 0, 1, 0, 1, 2), (6, 1, 0, 0, 0, 1, 0, 1, 2),
    (4, 1, 0, 0, 0, 1, 0, 1, 2), (5, 1, 0, 1, 0, 0, 0, 1, 2),
    (6, 1, 0, 1, 0, 0, 0, 1, 2), (4, 1, 0, 1, 0, 0, 0, 1, 2),
    (5, 1, 0, 0, 1, 0, 0, 1, 2), (6, 1, 0, 0, 1, 0, 0, 1, 2),
    (4, 1, 0, 0, 1, 0, 0, 1, 2), (5, 1, 0, 0, 0, 1, 0, 1, 2),
    (6, 1, 0, 0, 0, 1, 0, 1, 2), (5, 1, 0, 1, 0, 0, 0, 1, 2),
    (7, 1, 0, 1, 0, 0, 0, 1, 2), (4, 1, 0, 1, 0, 0, 0, 1, 2),
    (6, 1, 0, 0, 1, 0, 0, 1, 2), (5, 1, 0, 0, 1, 0, 0, 1, 2),
    (4, 1, 0, 0, 0, 1, 0, 1, 2), (5, 1, 0, 0, 0, 1, 0, 1, 2),
    (6, 1, 0, 1, 0, 0, 0, 1, 2), (5, 1, 0, 1, 0, 0, 0, 1, 2),
    (4, 1, 0, 0, 1, 0, 0, 1, 2), (5, 1, 0, 0, 1, 0, 0, 1, 2),

    # ─── 感叹句 (3): has_e=1, has_q=0, has_not=0 ───
    (4, 0, 1, 1, 0, 0, 0, 1, 3),  # What a nice day!
    (3, 0, 1, 0, 0, 0, 0, 1, 3),  # How wonderful!
    (5, 0, 1, 1, 0, 0, 0, 1, 3),  # What a beautiful flower!
    (3, 0, 1, 1, 0, 0, 0, 1, 3),  # How cute it is!
    (4, 0, 1, 1, 0, 0, 0, 1, 3),  # What an amazing view!
    (3, 0, 1, 1, 0, 0, 0, 1, 3),
    (4, 0, 1, 1, 0, 0, 0, 1, 3),
    (5, 0, 1, 1, 0, 0, 0, 1, 3),
    (3, 0, 1, 0, 0, 0, 0, 1, 3),
    (4, 0, 1, 0, 0, 0, 0, 1, 3),
    (5, 0, 1, 1, 0, 0, 0, 1, 3),
    (3, 0, 1, 1, 0, 0, 0, 1, 3),
    (4, 0, 1, 1, 0, 0, 0, 0, 3),  # 不以 wh 开头 (Oh, it's beautiful!)
    (5, 0, 1, 1, 0, 0, 0, 0, 3),
    (3, 0, 1, 1, 0, 0, 0, 0, 3),
    (4, 0, 1, 0, 0, 0, 0, 0, 3),
    (5, 0, 1, 1, 0, 0, 0, 0, 3),
    (3, 0, 1, 1, 0, 0, 0, 0, 3),
    (4, 0, 1, 0, 0, 0, 0, 0, 3),
    (5, 0, 1, 1, 0, 0, 0, 0, 3),
    (3, 0, 1, 1, 0, 0, 0, 1, 3),
    (4, 0, 1, 1, 0, 0, 0, 1, 3),
    (5, 0, 1, 1, 0, 0, 0, 1, 3),
    (3, 0, 1, 0, 0, 0, 0, 1, 3),
    (4, 0, 1, 1, 0, 0, 0, 1, 3),
    (5, 0, 1, 0, 0, 0, 0, 1, 3),
    (3, 0, 1, 1, 0, 0, 0, 1, 3),
    (4, 0, 1, 1, 0, 0, 0, 1, 3),
    (5, 0, 1, 1, 0, 0, 0, 0, 3),
    (3, 0, 1, 1, 0, 0, 0, 0, 3),

    # ─── 祈使句 (4): has_q=0, has_be=0, has_aux=0, has_modal=0, has_not=0, starts_wh=0 ───
    (3, 0, 0, 0, 0, 0, 0, 0, 4), (2, 0, 0, 0, 0, 0, 0, 0, 4),
    (4, 0, 0, 0, 0, 0, 0, 0, 4), (3, 0, 0, 0, 0, 0, 0, 0, 4),
    (5, 0, 0, 0, 0, 0, 0, 0, 4), (3, 0, 1, 0, 0, 0, 0, 0, 4),
    (4, 0, 1, 0, 0, 0, 0, 0, 4), (2, 0, 1, 0, 0, 0, 0, 0, 4),
    (3, 0, 0, 0, 0, 0, 0, 0, 4), (4, 0, 0, 0, 0, 0, 0, 0, 4),
    (5, 0, 0, 0, 0, 0, 0, 0, 4), (3, 0, 0, 0, 0, 0, 0, 0, 4),
    (4, 0, 0, 0, 0, 0, 0, 0, 4), (3, 0, 1, 0, 0, 0, 0, 0, 4),
    (5, 0, 1, 0, 0, 0, 0, 0, 4), (4, 0, 0, 0, 0, 0, 0, 0, 4),
    (3, 0, 0, 0, 0, 0, 0, 0, 4), (2, 0, 0, 0, 0, 0, 0, 0, 4),
    (3, 0, 0, 0, 0, 0, 0, 0, 4), (4, 0, 0, 0, 0, 0, 0, 0, 4),
    (5, 0, 0, 0, 0, 0, 0, 0, 4), (3, 0, 1, 0, 0, 0, 0, 0, 4),
    (4, 0, 1, 0, 0, 0, 0, 0, 4), (3, 0, 0, 0, 0, 0, 0, 0, 4),
    (5, 0, 0, 0, 0, 0, 0, 0, 4), (4, 0, 0, 0, 0, 0, 0, 0, 4),
    (3, 0, 0, 0, 0, 0, 0, 0, 4), (4, 0, 1, 0, 0, 0, 0, 0, 4),
    (3, 0, 0, 0, 0, 0, 0, 0, 4), (5, 0, 0, 0, 0, 0, 0, 0, 4),

    # ─── 否定句 (5): has_q=0, has_e=0, has_not=1, starts_wh=0 ───
    (5, 0, 0, 1, 0, 0, 1, 0, 5), (6, 0, 0, 1, 0, 0, 1, 0, 5),
    (4, 0, 0, 1, 0, 0, 1, 0, 5), (5, 0, 0, 0, 1, 0, 1, 0, 5),
    (6, 0, 0, 0, 1, 0, 1, 0, 5), (4, 0, 0, 0, 1, 0, 1, 0, 5),
    (5, 0, 0, 0, 0, 1, 1, 0, 5), (6, 0, 0, 0, 0, 1, 1, 0, 5),
    (4, 0, 0, 0, 0, 1, 1, 0, 5), (5, 0, 0, 1, 0, 0, 1, 0, 5),
    (7, 0, 0, 1, 0, 0, 1, 0, 5), (6, 0, 0, 1, 0, 0, 1, 0, 5),
    (5, 0, 0, 0, 1, 0, 1, 0, 5), (6, 0, 0, 0, 1, 0, 1, 0, 5),
    (7, 0, 0, 0, 1, 0, 1, 0, 5), (5, 0, 0, 0, 0, 1, 1, 0, 5),
    (6, 0, 0, 0, 0, 1, 1, 0, 5), (7, 0, 0, 0, 0, 1, 1, 0, 5),
    (5, 0, 0, 1, 0, 0, 1, 0, 5), (4, 0, 0, 1, 0, 0, 1, 0, 5),
    (5, 0, 0, 0, 1, 0, 1, 0, 5), (4, 0, 0, 0, 1, 0, 1, 0, 5),
    (6, 0, 0, 0, 1, 0, 1, 0, 5), (5, 0, 0, 0, 0, 1, 1, 0, 5),
    (4, 0, 0, 0, 0, 1, 1, 0, 5), (6, 0, 0, 0, 0, 1, 1, 0, 5),
    (5, 0, 0, 1, 0, 0, 1, 0, 5), (6, 0, 0, 1, 0, 0, 1, 0, 5),
    (4, 0, 0, 1, 0, 0, 1, 0, 5), (5, 0, 0, 0, 1, 0, 1, 0, 5),
]


# ── 年级 → 推荐词汇量数据 (用于回归：年级→建议掌握英语词汇量) ──
# 参考义务教育/普通高中英语课程标准分级要求 (1-6 小学 / 7-9 初中 / 10-12 高中)
GRADE_VOCAB = [
    # 小学 1-6
    {"grade": 1, "vocab": 50},
    {"grade": 1, "vocab": 80},
    {"grade": 2, "vocab": 120},
    {"grade": 2, "vocab": 150},
    {"grade": 3, "vocab": 180},
    {"grade": 3, "vocab": 220},
    {"grade": 3, "vocab": 280},
    {"grade": 4, "vocab": 320},
    {"grade": 4, "vocab": 380},
    {"grade": 4, "vocab": 450},
    {"grade": 5, "vocab": 500},
    {"grade": 5, "vocab": 580},
    {"grade": 5, "vocab": 650},
    {"grade": 6, "vocab": 700},
    {"grade": 6, "vocab": 800},
    {"grade": 6, "vocab": 900},
    {"grade": 6, "vocab": 1000},
    # 初中 7-9
    {"grade": 7, "vocab": 1200},
    {"grade": 7, "vocab": 1350},
    {"grade": 8, "vocab": 1500},
    {"grade": 8, "vocab": 1700},
    {"grade": 9, "vocab": 1900},
    {"grade": 9, "vocab": 2100},
    # 高中 10-12
    {"grade": 10, "vocab": 2400},
    {"grade": 10, "vocab": 2700},
    {"grade": 11, "vocab": 3000},
    {"grade": 11, "vocab": 3300},
    {"grade": 12, "vocab": 3500},
    {"grade": 12, "vocab": 3800},
]


# ── 学习记录 ──
def load_records():
    if RECORD_FILE.exists():
        try:
            return json.loads(RECORD_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_records(records):
    RECORD_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def record_quiz(topic, difficulty, mode, correct, word=None):
    """记录一道题作答结果"""
    records = load_records()
    records.append({
        "topic": topic,
        "difficulty": difficulty,
        "mode": mode,           # choose_meaning / choose_word / spell / listen
        "correct": bool(correct),
        "word": word,
    })
    if len(records) > 3000:
        records = records[-3000:]
    save_records(records)


def get_stats():
    records = load_records()
    total = len(records)
    correct = sum(1 for r in records if r["correct"])
    by_topic = {}
    by_mode = {}
    for r in records:
        t = r["topic"]
        if t not in by_topic:
            by_topic[t] = {"total": 0, "correct": 0}
        by_topic[t]["total"] += 1
        if r["correct"]:
            by_topic[t]["correct"] += 1
        m = r.get("mode", "choose_meaning")
        if m not in by_mode:
            by_mode[m] = {"total": 0, "correct": 0}
        by_mode[m]["total"] += 1
        if r["correct"]:
            by_mode[m]["correct"] += 1
    # 已掌握的单词集合（连续答对2次以上）
    word_acc = {}
    for r in records:
        w = r.get("word")
        if not w:
            continue
        if w not in word_acc:
            word_acc[w] = {"total": 0, "correct": 0}
        word_acc[w]["total"] += 1
        if r["correct"]:
            word_acc[w]["correct"] += 1
    mastered = sum(1 for w, v in word_acc.items() if v["total"] >= 2 and v["correct"] / v["total"] >= 0.8)
    return {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
        "by_topic": by_topic,
        "by_mode": by_mode,
        "mastered_words": mastered,
        "encountered_words": len(word_acc),
    }


def get_words_by_topic(topic, count=5, difficulty=None, level=None):
    """按主题取单词，可按难度/学段过滤；level=None 表示全学段"""
    pool = [w for w in WORDS if w["topic"] == topic]
    pool += [w for w in load_custom_words() if w["topic"] == topic]
    if difficulty is not None:
        pool = [w for w in pool if w["difficulty"] == difficulty]
    if level is not None and level != "all":
        pool = [w for w in pool if w.get("level", "primary") == level]
    if len(pool) <= count:
        return pool[:]
    return random.sample(pool, count)


def get_words_by_level(level, count=None):
    """按学段取单词；level='all' 或 None 表示全学段"""
    if level is None or level == "all":
        pool = WORDS[:] + load_custom_words()
    else:
        pool = [w for w in WORDS if w.get("level", "primary") == level]
        pool += [w for w in load_custom_words() if w.get("level", "primary") == level]
    if count is None or len(pool) <= count:
        return pool
    return random.sample(pool, count)


def count_words_by_level():
    """返回各学段单词数量统计"""
    stats = {lv: 0 for lv in LEVELS}
    for w in WORDS:
        lv = w.get("level", "primary")
        if lv in stats:
            stats[lv] += 1
    return stats


def get_all_words():
    return WORDS[:] + load_custom_words()


# ── 自定义单词管理 ──
def load_custom_words():
    if CUSTOM_WORDS_FILE.exists():
        try:
            return json.loads(CUSTOM_WORDS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_custom_words(words):
    CUSTOM_WORDS_FILE.write_text(
        json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def add_custom_word(word, meaning, phonetic, pos, topic, difficulty, example="", example_zh=""):
    words = load_custom_words()
    words.append({
        "word": word,
        "meaning": meaning,
        "phonetic": phonetic,
        "pos": pos,
        "topic": topic,
        "difficulty": difficulty,
        "example": example,
        "example_zh": example_zh,
        "custom": True,
    })
    save_custom_words(words)
    return words


def delete_custom_word(index):
    words = load_custom_words()
    if 0 <= index < len(words):
        words.pop(index)
        save_custom_words(words)
    return words


# ── 题目派生：从单词生成题目 ──
def make_choose_meaning_question(word_obj, all_words=None, n_options=4):
    """看英文 → 选中文释义"""
    pool = all_words or WORDS
    # 同主题干扰项优先
    same_topic = [w for w in pool if w["topic"] == word_obj["topic"] and w["word"] != word_obj["word"]]
    distractors = random.sample(same_topic, min(n_options - 1, len(same_topic)))
    if len(distractors) < n_options - 1:
        others = [w for w in pool if w["word"] != word_obj["word"]
                  and all(w["meaning"] != d["meaning"] for d in distractors)]
        distractors += random.sample(others, n_options - 1 - len(distractors))
    options = [d["meaning"] for d in distractors] + [word_obj["meaning"]]
    random.shuffle(options)
    return {
        "mode": "choose_meaning",
        "question": word_obj["word"],
        "phonetic": word_obj.get("phonetic", ""),
        "options": options,
        "answer": options.index(word_obj["meaning"]),
        "topic": word_obj["topic"],
        "difficulty": word_obj["difficulty"],
        "word": word_obj["word"],
        "example": word_obj.get("example", ""),
        "example_zh": word_obj.get("example_zh", ""),
    }


def make_choose_word_question(word_obj, all_words=None, n_options=4):
    """看中文 → 选英文单词"""
    pool = all_words or WORDS
    same_topic = [w for w in pool if w["topic"] == word_obj["topic"] and w["word"] != word_obj["word"]]
    distractors = random.sample(same_topic, min(n_options - 1, len(same_topic)))
    if len(distractors) < n_options - 1:
        others = [w for w in pool if w["word"] != word_obj["word"]
                  and all(w["word"] != d["word"] for d in distractors)]
        distractors += random.sample(others, n_options - 1 - len(distractors))
    options = [d["word"] for d in distractors] + [word_obj["word"]]
    random.shuffle(options)
    return {
        "mode": "choose_word",
        "question": word_obj["meaning"],
        "phonetic": word_obj.get("phonetic", ""),
        "options": options,
        "answer": options.index(word_obj["word"]),
        "topic": word_obj["topic"],
        "difficulty": word_obj["difficulty"],
        "word": word_obj["word"],
        "example": word_obj.get("example", ""),
        "example_zh": word_obj.get("example_zh", ""),
    }


def make_listen_question(word_obj, all_words=None, n_options=4):
    """看音标 → 选英文单词（模拟听力）"""
    pool = all_words or WORDS
    # 拼写相近的干扰项优先
    same_topic = [w for w in pool if w["word"] != word_obj["word"]]
    same_topic.sort(key=lambda w: -_word_similarity(w["word"], word_obj["word"]))
    distractors = same_topic[:n_options - 1]
    options = [d["word"] for d in distractors] + [word_obj["word"]]
    random.shuffle(options)
    return {
        "mode": "listen",
        "question": word_obj.get("phonetic", "") or "(无音标)",
        "phonetic": word_obj.get("phonetic", ""),
        "options": options,
        "answer": options.index(word_obj["word"]),
        "topic": word_obj["topic"],
        "difficulty": word_obj["difficulty"],
        "word": word_obj["word"],
        "meaning": word_obj["meaning"],
        "example": word_obj.get("example", ""),
        "example_zh": word_obj.get("example_zh", ""),
    }


def make_spell_question(word_obj):
    """看中文 + 首字母 → 拼写英文"""
    return {
        "mode": "spell",
        "question": word_obj["meaning"],
        "phonetic": word_obj.get("phonetic", ""),
        "hint": word_obj["word"][0] + "_" * (len(word_obj["word"]) - 1),
        "answer_text": word_obj["word"],
        "topic": word_obj["topic"],
        "difficulty": word_obj["difficulty"],
        "word": word_obj["word"],
        "example": word_obj.get("example", ""),
        "example_zh": word_obj.get("example_zh", ""),
    }


def _word_similarity(a, b):
    """简单字符相似度（共同字符比例）"""
    sa, sb = set(a.lower()), set(b.lower())
    if not sa or not sb:
        return 0
    return len(sa & sb) / len(sa | sb)


def build_quiz(topic, count=5, modes=None, level=None):
    """构建一组混合题型的题目，模拟百词斩闯关

    level: 'primary' / 'middle' / 'high' / None(=全学段)
    """
    modes = modes or ["choose_meaning", "choose_word", "listen", "spell"]
    words = get_words_by_topic(topic, count=count, level=level)
    if not words:
        return []
    all_words = get_all_words()
    questions = []
    for w in words:
        m = random.choice(modes)
        if m == "choose_meaning":
            q = make_choose_meaning_question(w, all_words)
        elif m == "choose_word":
            q = make_choose_word_question(w, all_words)
        elif m == "listen":
            q = make_listen_question(w, all_words)
        elif m == "spell":
            q = make_spell_question(w)
        else:
            q = make_choose_meaning_question(w, all_words)
        questions.append(q)
    return questions
