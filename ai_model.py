"""
小学英语AI学习系统 — AI模型模块
随机森林（单词主题分类）+ SVM（句型分类）+ 多项式回归（年级→词汇量预测）
+ 梯度提升（单词难度预测）+ 梯度提升（综合主题集成）
"""
import re, random, os, pathlib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import joblib

MODEL_DIR = pathlib.Path(__file__).parent
TOPIC_MODEL_FILE = MODEL_DIR / "yy_topic_model.pkl"
SENTENCE_MODEL_FILE = MODEL_DIR / "yy_sentence_model.pkl"
GRADE_MODEL_FILE = MODEL_DIR / "yy_grade_model.pkl"
DIFF_MODEL_FILE = MODEL_DIR / "yy_diff_model.pkl"
ENSEMBLE_MODEL_FILE = MODEL_DIR / "yy_ensemble_model.pkl"

TOPIC_LABELS = {
    0: "基础词汇", 1: "学校生活", 2: "自然世界", 3: "食物饮食",
    4: "家庭朋友", 5: "数字时间", 6: "颜色形状", 7: "动作情感",
}
TOPIC_IDS = {
    0: "basic", 1: "school", 2: "nature", 3: "food",
    4: "family", 5: "numtime", 6: "colorshape", 7: "action",
}
DIFFICULTY_LABELS = {1: "基础", 2: "进阶", 3: "拓展"}
POS_LABELS = {
    "n": "名词", "v": "动词", "adj": "形容词", "adv": "副词",
    "prep": "介词", "conj": "连词", "int": "感叹词",
    "num": "数词", "pron": "代词",
}

VOWELS = set("aeiouAEIOU")


# ═══════════════════════════════════════════
#  关键词词典 — 主题相关词根/词缀/释义关键字
# ═══════════════════════════════════════════

_KW_BASIC = ["hello", "hi", "yes", "no", "please", "thank", "sorry", "goodbye",
             "name", "age", "morning", "afternoon", "evening", "welcome",
             "introduce", "introduction", "excuse", "conversation", "communicate",
             "polite", "opinion", "acknowledge", "gratitude", "etiquette",
             "hospitality", "sincere",
             "你好", "请", "谢", "再见", "名字", "早", "晚", "介绍", "交谈",
             "沟通", "礼貌", "观点", "承认", "感激", "礼节", "款待", "真诚"]
_KW_SCHOOL = ["book", "pen", "pencil", "school", "teacher", "student", "class",
              "lesson", "homework", "ruler", "eraser", "library", "board",
              "subject", "study", "knowledge",
              "chemistry", "geography", "history", "exam", "vocabulary",
              "philosophy", "scholarship", "curriculum", "academic", "semester",
              "学", "书", "笔", "校", "课", "师", "生", "教室", "作业",
              "图书", "知识", "化学", "地理", "历史", "考试", "词汇",
              "哲学", "奖学金", "课程", "学术", "学期"]
_KW_NATURE = ["dog", "cat", "bird", "tree", "flower", "sun", "moon", "rain",
              "snow", "river", "mountain", "weather", "elephant", "butterfly",
              "rainbow", "animal", "plant",
              "forest", "ocean", "climate", "volcano", "environment",
              "biodiversity", "ecosystem", "sustainable", "hurricane", "photosynthesis",
              "天气", "动物", "花", "树", "雨", "雪", "山", "河", "鸟",
              "蝴蝶", "彩虹", "太阳", "月亮", "森林", "海洋", "气候",
              "火山", "环境", "生物", "多样", "生态", "可持续", "飓风", "光合"]
_KW_FOOD = ["apple", "egg", "milk", "rice", "bread", "water", "banana",
            "orange", "noodle", "juice", "breakfast", "lunch", "dinner",
            "vegetable", "sandwich", "delicious", "hungry", "eat", "drink",
            "dessert", "restaurant", "beverage", "ingredient", "recipe",
            "nutrition", "vegetarian", "condiment", "gastronomy", "organic",
            "苹", "蛋", "奶", "饭", "面", "果", "餐", "蔬", "饿", "美味",
            "甜点", "餐厅", "饮料", "原料", "食谱", "营养", "素食",
            "调味", "美食", "有机"]
_KW_FAMILY = ["dad", "mom", "boy", "girl", "friend", "father", "mother",
              "brother", "sister", "uncle", "aunt", "cousin", "grand",
              "classmate", "family",
              "relative", "neighbor", "colleague", "partner", "household",
              "genealogy", "ancestor", "descendant", "companion", "intimate",
              "爸", "妈", "兄", "弟", "姐", "妹", "叔", "姨", "祖", "爷",
              "朋友", "同学", "亲戚", "邻居", "同事", "伙伴", "家庭",
              "家谱", "祖先", "后代", "亲密"]
_KW_NUMTIME = ["one", "two", "three", "ten", "twelve", "twenty", "hundred",
               "day", "week", "month", "year", "monday", "sunday", "january",
               "tomorrow", "today", "yesterday", "time", "hour", "minute",
               "decade", "century", "calendar", "schedule", "deadline",
               "millennium", "chronology", "simultaneously", "anniversary", "contemporary",
               "一", "二", "三", "十", "百", "天", "周", "月", "年", "时",
               "分", "明", "十年", "世纪", "日历", "日程", "截止",
               "千禧", "年代", "同时", "周年", "当代"]
_KW_COLORSHAPE = ["red", "blue", "green", "yellow", "black", "white", "pink",
                  "brown", "purple", "circle", "square", "triangle", "rectangle",
                  "colorful", "shape", "color", "round",
                  "hexagon", "oval", "diamond", "transparent", "vibrant",
                  "geometric", "asymmetric", "monochrome", "silhouette", "dimension",
                  "红", "蓝", "绿", "黄", "黑", "白", "粉", "棕", "紫",
                  "圆", "方", "三角", "形", "色", "彩", "六边", "椭圆",
                  "菱形", "钻石", "透明", "鲜亮", "几何", "对称",
                  "单色", "剪影", "维度"]
_KW_ACTION = ["go", "run", "jump", "sing", "happy", "sad", "swim", "read",
              "write", "love", "angry", "excited", "remember", "understand",
              "surprised", "play", "like", "feel",
              "achieve", "decide", "discover", "examine", "organize",
              "accomplish", "contemplate", "demonstrate", "perceive", "persevere",
              "去", "跑", "跳", "唱", "开心", "伤心", "游", "读", "写",
              "爱", "气", "兴奋", "记", "明白", "惊", "玩", "喜欢",
              "达成", "决定", "发现", "检查", "组织", "完成", "沉思",
              "演示", "感知", "察觉", "坚持"]


def _kw_match_count(text, keywords):
    t = text.lower()
    return sum(1 for w in keywords if w.lower() in t)


def extract_word_features(word_obj):
    """从单词条目提取24维特征向量
    word_obj 必须包含 word/meaning/pos 字段；phonetic、example 可选
    """
    word = word_obj.get("word", "")
    meaning = word_obj.get("meaning", "")
    phonetic = word_obj.get("phonetic", "")
    pos = word_obj.get("pos", "")
    example = word_obj.get("example", "")
    text_all = (word + " " + meaning + " " + example).lower()

    n_char = len(word)
    n_vowel = sum(1 for c in word if c in VOWELS)
    n_consonant = sum(1 for c in word if c.isalpha() and c not in VOWELS)
    n_meaning_char = len(meaning)
    starts_vowel = 1 if word and word[0] in VOWELS else 0
    has_hyphen = 1 if "-" in word else 0
    has_apostrophe = 1 if "'" in word else 0

    # 主题关键词命中数
    kw_scores = [
        _kw_match_count(text_all, _KW_BASIC),
        _kw_match_count(text_all, _KW_SCHOOL),
        _kw_match_count(text_all, _KW_NATURE),
        _kw_match_count(text_all, _KW_FOOD),
        _kw_match_count(text_all, _KW_FAMILY),
        _kw_match_count(text_all, _KW_NUMTIME),
        _kw_match_count(text_all, _KW_COLORSHAPE),
        _kw_match_count(text_all, _KW_ACTION),
    ]

    # 词性 one-hot 简化
    is_noun = 1 if pos == "n" else 0
    is_verb = 1 if pos == "v" else 0
    is_adj = 1 if pos == "adj" else 0
    is_adv = 1 if pos == "adv" else 0
    is_num = 1 if pos == "num" else 0

    has_phonetic = 1 if phonetic else 0
    syllable_est = max(1, sum(1 for i, c in enumerate(word.lower())
                              if c in VOWELS and (i == 0 or word.lower()[i - 1] not in VOWELS)))
    avg_meaning_len = n_meaning_char / max(n_char, 1)

    return [
        n_char,                # 0
        n_vowel,               # 1
        n_consonant,           # 2
        n_meaning_char,        # 3
        starts_vowel,          # 4
        has_hyphen,            # 5
        has_apostrophe,        # 6
        *kw_scores,            # 7-14 八大主题关键词命中
        is_noun,               # 15
        is_verb,               # 16
        is_adj,                # 17
        is_adv,                # 18
        is_num,                # 19
        has_phonetic,          # 20
        syllable_est,          # 21
        round(avg_meaning_len, 2),  # 22
        n_char + n_meaning_char,    # 23
    ]


def _topic_id_to_label(topic_id):
    for k, v in TOPIC_IDS.items():
        if v == topic_id:
            return k
    return 0


# ═══════════════════════════════════════════
#  模型1: 随机森林 — 单词主题分类
# ═══════════════════════════════════════════

def _auto_augment(n_words: int) -> int:
    """根据词库规模自适应增强倍数，保证训练总样本量稳定在 1-2 万。
    - <500 词：augment=18（原始小词库默认）
    - 500–1000 词：augment=12
    - 1000–3000 词：augment=6
    - ≥3000 词：augment=3（5000 词 × 4 = 2 万样本）
    """
    if n_words >= 3000:
        return 3
    if n_words >= 1000:
        return 6
    if n_words >= 500:
        return 12
    return 18


def generate_topic_training_data(words, augment=18):
    X, y = [], []
    for w in words:
        feat = extract_word_features(w)
        label = _topic_id_to_label(w["topic"])
        X.append(feat)
        y.append(label)
        for _ in range(augment):
            noisy = []
            for v in feat:
                if isinstance(v, (int, float)):
                    noise = random.gauss(0, 0.08) * max(abs(v), 0.5)
                    noisy.append(v + noise)
                else:
                    noisy.append(v)
            X.append(noisy)
            y.append(label)
    return np.array(X, dtype=np.float64), np.array(y)


def train_topic_model(words):
    X, y = generate_topic_training_data(words, augment=_auto_augment(len(words)))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y)
    clf = RandomForestClassifier(n_estimators=300, max_depth=18, min_samples_leaf=2,
                                  max_features="sqrt", class_weight="balanced_subsample",
                                  random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    acc = round(clf.score(X_test, y_test) * 100, 1)
    joblib.dump((clf, acc), TOPIC_MODEL_FILE)
    return clf, acc


def load_topic_model(words):
    """严格读取预训练的主题模型 pkl。
    词库体量达 5000+ 后，训练需 1-2 分钟，不再在客户启动时训练。
    如需重新制作 pkl，开发者请运行 `python build_models.py`。
    """
    if TOPIC_MODEL_FILE.exists():
        try:
            clf, acc = joblib.load(TOPIC_MODEL_FILE)
            return clf, acc
        except Exception as e:
            raise RuntimeError(f"主题模型加载失败（{TOPIC_MODEL_FILE.name}）：{e}\n请重新运行 build_models.py。")
    raise RuntimeError(
        f"主题模型未预训练（缺少 {TOPIC_MODEL_FILE.name}）。\n"
        f"请联系开发者获取预训模型，或运行 `python build_models.py` 生成。")


def predict_topic(word_obj_or_text, words):
    """预测某个单词所属主题。可以传入完整 word_obj，也可以只传字符串"""
    clf, _ = load_topic_model(words)
    if isinstance(word_obj_or_text, str):
        word_obj = {"word": word_obj_or_text, "meaning": "", "pos": "n"}
    else:
        word_obj = word_obj_or_text
    feat = np.array([extract_word_features(word_obj)])
    proba = clf.predict_proba(feat)[0]
    pred = int(clf.predict(feat)[0])
    return {
        "topic_id": TOPIC_IDS.get(pred, "unknown"),
        "topic_name": TOPIC_LABELS.get(pred, "未知"),
        "confidence": round(float(max(proba)) * 100, 1),
        "all_proba": {TOPIC_LABELS[i]: round(float(p) * 100, 1)
                      for i, p in enumerate(proba) if i in TOPIC_LABELS},
    }


# ═══════════════════════════════════════════
#  模型2: SVM — 英语句型分类
# ═══════════════════════════════════════════

# 句型训练样本格式：9 元组
#   (word_count, has_q, has_e, has_be, has_aux, has_modal, has_not, starts_wh, label)
#   前 8 个为特征，最后 1 个为句型标签 (0~5)
_SENT_FEAT_DIM = 8


def _augment_sentence_data(sentence_data, augment=5):
    aug = list(sentence_data)
    for d in sentence_data:
        for _ in range(augment):
            row = tuple(
                d[i] + random.gauss(0, 0.04) * max(abs(d[i]), 1) if i < _SENT_FEAT_DIM else d[i]
                for i in range(_SENT_FEAT_DIM + 1)
            )
            aug.append(row)
    return aug


def train_sentence_model(sentence_data):
    aug = _augment_sentence_data(sentence_data, augment=8)
    X = np.array([[d[i] for i in range(_SENT_FEAT_DIM)] for d in aug])
    y = np.array([d[_SENT_FEAT_DIM] for d in aug])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y)
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("svc", SVC(kernel="rbf", C=8, gamma="scale", probability=True, random_state=42)),
    ])
    pipe.fit(X_train, y_train)
    acc = round(pipe.score(X_test, y_test) * 100, 1)
    joblib.dump((pipe, acc), SENTENCE_MODEL_FILE)
    return pipe, acc


def load_sentence_model(sentence_data):
    """严格读取预训练的句型模型 pkl，不再在客户启动时训练。"""
    if SENTENCE_MODEL_FILE.exists():
        try:
            pipe, acc = joblib.load(SENTENCE_MODEL_FILE)
            return pipe, acc
        except Exception as e:
            raise RuntimeError(f"句型模型加载失败（{SENTENCE_MODEL_FILE.name}）：{e}\n请重新运行 build_models.py。")
    raise RuntimeError(
        f"句型模型未预训练（缺少 {SENTENCE_MODEL_FILE.name}）。\n"
        f"请联系开发者获取预训模型，或运行 `python build_models.py` 生成。")


def predict_sentence_type(word_count, has_question_mark, has_exclaim, has_be,
                          has_aux, has_modal, has_not, starts_wh,
                          sentence_data, sentence_labels):
    """根据 8 个特征预测句型"""
    pipe, _ = load_sentence_model(sentence_data)
    feat = np.array([[word_count, has_question_mark, has_exclaim, has_be,
                      has_aux, has_modal, has_not, starts_wh]])
    proba = pipe.predict_proba(feat)[0]
    pred = int(pipe.predict(feat)[0])
    top3 = sorted(enumerate(proba), key=lambda x: -x[1])[:3]
    classes = list(pipe.classes_)
    return {
        "sentence_type": sentence_labels.get(pred, "未知"),
        "confidence": round(float(max(proba)) * 100, 1),
        "top3": [(sentence_labels.get(int(classes[i]), "未知"), round(float(p) * 100, 1))
                 for i, p in top3 if p > 0],
    }


def auto_extract_sentence_features(sentence):
    """从英文句子自动提取 8 维句型特征"""
    s = sentence.strip()
    s_low = s.lower()
    words = re.findall(r"[A-Za-z']+", s)
    word_count = len(words)
    has_q = 1 if "?" in s else 0
    has_e = 1 if "!" in s else 0
    be_verbs = {"am", "is", "are", "was", "were", "be", "been", "being"}
    has_be = 1 if any(w.lower() in be_verbs for w in words) else 0
    aux_verbs = {"do", "does", "did", "have", "has", "had", "will", "would", "shall"}
    has_aux = 1 if any(w.lower() in aux_verbs for w in words) else 0
    modal_verbs = {"can", "could", "may", "might", "must", "should", "ought"}
    has_modal = 1 if any(w.lower() in modal_verbs for w in words) else 0
    # 否定词：not / n’t / never / no（作为定语的 no 除外，这里取强信号）
    has_not = 1 if (re.search(r"\bnot\b|n['\u2019]t\b|\bnever\b", s_low)) else 0
    # WH-词开头（特殊疑问/感叹常以 What/How 开头）
    wh_words = {"what", "where", "when", "who", "whom", "whose", "why",
                "how", "which"}
    starts_wh = 1 if (words and words[0].lower() in wh_words) else 0
    return word_count, has_q, has_e, has_be, has_aux, has_modal, has_not, starts_wh


# ═══════════════════════════════════════════
#  模型3: 多项式回归 — 年级 → 词汇量预测
# ═══════════════════════════════════════════

def train_grade_model(grade_data):
    X = np.array([[c["grade"]] for c in grade_data])
    y = np.array([c["vocab"] for c in grade_data])
    pipe = Pipeline([
        ("poly", PolynomialFeatures(degree=2, include_bias=False)),
        ("ridge", Ridge(alpha=1.0)),
    ])
    pipe.fit(X, y)
    y_pred = pipe.predict(X)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = round(1 - ss_res / ss_tot, 4)
    joblib.dump((pipe, r2), GRADE_MODEL_FILE)
    return pipe, r2


def load_grade_model(grade_data):
    """严格读取预训练的年级词汇量回归 pkl，不再在客户启动时训练。"""
    if GRADE_MODEL_FILE.exists():
        try:
            pipe, r2 = joblib.load(GRADE_MODEL_FILE)
            return pipe, r2
        except Exception as e:
            raise RuntimeError(f"年级词汇量模型加载失败（{GRADE_MODEL_FILE.name}）：{e}\n请重新运行 build_models.py。")
    raise RuntimeError(
        f"年级词汇量模型未预训练（缺少 {GRADE_MODEL_FILE.name}）。\n"
        f"请联系开发者获取预训模型，或运行 `python build_models.py` 生成。")


def predict_vocab_by_grade(grade, grade_data):
    pipe, r2 = load_grade_model(grade_data)
    pred = pipe.predict(np.array([[grade]]))[0]
    ridge = pipe.named_steps["ridge"]
    c1 = round(float(ridge.coef_[0]), 3)
    c2 = round(float(ridge.coef_[1]), 5)
    b = round(float(ridge.intercept_), 2)
    return {
        "grade": grade,
        "predicted_vocab": max(round(float(pred)), 0),
        "formula": f"词汇量 = {c1}·年级 + {c2}·年级² + {b}",
        "r_squared": r2,
        "interpretation": f"二次多项式 R²={r2}，预测{int(grade)}年级建议掌握英语词汇量约 {round(float(pred))} 个",
    }


# ═══════════════════════════════════════════
#  模型4: 梯度提升 — 单词难度预测
# ═══════════════════════════════════════════

# 难度倾向关键词（教学经验）
_DIFF_EASY_PATTERNS = ["hello", "hi", "yes", "no", "go", "run", "red", "blue", "one",
                       "two", "dad", "mom", "boy", "girl", "cat", "dog", "egg", "name",
                       "sun", "moon", "book", "pen", "day", "sad", "happy", "play",
                       "like", "love", "eat", "sing"]
_DIFF_HARD_PATTERNS = ["introduce", "excuse", "library", "subject", "knowledge",
                      "vegetable", "sandwich", "delicious", "grandmother",
                      "grandfather", "classmate", "tomorrow", "rectangle",
                      "colorful", "remember", "understand", "surprised", "excited",
                      "elephant", "butterfly", "rainbow", "afternoon",
                      # 初中/高中难词
                      "introduction", "conversation", "communicate", "polite", "opinion",
                      "chemistry", "geography", "history", "vocabulary",
                      "forest", "ocean", "climate", "volcano", "environment",
                      "dessert", "restaurant", "beverage", "ingredient", "recipe",
                      "relative", "neighbor", "colleague", "partner", "household",
                      "decade", "century", "calendar", "schedule", "deadline",
                      "hexagon", "diamond", "transparent", "vibrant",
                      "achieve", "decide", "discover", "examine", "organize",
                      "acknowledge", "gratitude", "etiquette", "hospitality", "sincere",
                      "philosophy", "scholarship", "curriculum", "academic", "semester",
                      "biodiversity", "ecosystem", "sustainable", "hurricane", "photosynthesis",
                      "nutrition", "vegetarian", "condiment", "gastronomy", "organic",
                      "genealogy", "ancestor", "descendant", "companion", "intimate",
                      "millennium", "chronology", "simultaneously", "anniversary", "contemporary",
                      "geometric", "asymmetric", "monochrome", "silhouette", "dimension",
                      "accomplish", "contemplate", "demonstrate", "perceive", "persevere"]


def extract_diff_features(word_obj):
    """从单词条目提取40维难度特征向量"""
    base = extract_word_features(word_obj)
    word = word_obj.get("word", "")
    meaning = word_obj.get("meaning", "")
    phonetic = word_obj.get("phonetic", "")
    example = word_obj.get("example", "")
    pos = word_obj.get("pos", "")

    w_low = word.lower()
    n_char = len(word)
    n_vowel = sum(1 for c in word if c in VOWELS)
    n_consonant = sum(1 for c in word if c.isalpha() and c not in VOWELS)
    syllable_est = max(1, sum(1 for i, c in enumerate(w_low)
                              if c in VOWELS and (i == 0 or w_low[i - 1] not in VOWELS)))

    n_phon_char = len(phonetic.replace("/", "").replace("'", ""))
    n_example_word = len(re.findall(r"[A-Za-z']+", example))

    easy_hits = sum(1 for p in _DIFF_EASY_PATTERNS if p == w_low)
    hard_hits = sum(1 for p in _DIFF_HARD_PATTERNS if p == w_low)

    has_double = 1 if any(word[i] == word[i + 1] for i in range(len(word) - 1)) else 0
    has_silent_e = 1 if word.endswith("e") and len(word) >= 4 else 0
    has_th = 1 if "th" in w_low else 0
    has_sh = 1 if "sh" in w_low else 0
    has_ch = 1 if "ch" in w_low else 0
    has_complex_cluster = 1 if re.search(r"[bcdfghjklmnpqrstvwxz]{3,}", w_low) else 0

    pos_difficulty = {"n": 1, "v": 1, "adj": 1.2, "adv": 1.5, "prep": 1.5,
                      "conj": 1.5, "int": 0.8, "num": 1, "pron": 1}.get(pos, 1)

    # 学段强特征（如果词条带 level 字段）
    level = word_obj.get("level", "primary")
    level_score = {"primary": 0, "middle": 1, "high": 2}.get(level, 0)

    return [
        *base,                             # 0-23
        syllable_est,                      # 24
        n_phon_char,                       # 25
        n_example_word,                    # 26
        easy_hits,                         # 27
        hard_hits,                         # 28
        hard_hits - easy_hits,             # 29
        has_double,                        # 30
        has_silent_e,                      # 31
        has_th,                            # 32
        has_sh,                            # 33
        has_ch,                            # 34
        has_complex_cluster,               # 35
        round(pos_difficulty, 2),          # 36
        1 if n_char >= 7 else 0,           # 37
        1 if syllable_est >= 3 else 0,     # 38
        round(n_consonant / max(n_vowel, 1), 2),  # 39 辅元音比
        level_score,                       # 40 学段映射 (primary=0/middle=1/high=2)
    ]


def train_diff_model(words):
    aug = _auto_augment(len(words))
    X, y = [], []
    for w in words:
        feat = extract_diff_features(w)
        X.append(feat)
        y.append(w["difficulty"])
        for _ in range(aug):
            noisy = [v + random.gauss(0, 0.05) * max(abs(v), 0.2) for v in feat]
            X.append(noisy)
            y.append(w["difficulty"])
    X, y = np.array(X, dtype=np.float64), np.array(y)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y)
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("gb", GradientBoostingClassifier(n_estimators=400, max_depth=5, learning_rate=0.06,
                                           min_samples_leaf=2, subsample=0.9, random_state=42)),
    ])
    pipe.fit(X_train, y_train)
    acc = round(pipe.score(X_test, y_test) * 100, 1)
    joblib.dump((pipe, acc), DIFF_MODEL_FILE)
    return pipe, acc


def load_diff_model(words):
    """严格读取预训练的难度预测 pkl，不再在客户启动时训练。"""
    if DIFF_MODEL_FILE.exists():
        try:
            pipe, acc = joblib.load(DIFF_MODEL_FILE)
            return pipe, acc
        except Exception as e:
            raise RuntimeError(f"难度模型加载失败（{DIFF_MODEL_FILE.name}）：{e}\n请重新运行 build_models.py。")
    raise RuntimeError(
        f"难度预测模型未预训练（缺少 {DIFF_MODEL_FILE.name}）。\n"
        f"请联系开发者获取预训模型，或运行 `python build_models.py` 生成。")


def predict_difficulty(word_obj_or_text, words):
    pipe, _ = load_diff_model(words)
    if isinstance(word_obj_or_text, str):
        word_obj = {"word": word_obj_or_text, "meaning": "", "pos": "n"}
    else:
        word_obj = word_obj_or_text
    feat = np.array([extract_diff_features(word_obj)])
    pred = int(pipe.predict(feat)[0])
    proba = pipe.predict_proba(feat)[0]
    return {
        "difficulty": pred,
        "difficulty_name": DIFFICULTY_LABELS.get(pred, "未知"),
        "confidence": round(float(max(proba)) * 100, 1),
        "all_proba": {DIFFICULTY_LABELS.get(int(c), str(c)): round(float(p) * 100, 1)
                      for c, p in zip(pipe.classes_, proba)},
    }


# ═══════════════════════════════════════════
#  模型5: 梯度提升 — 综合主题集成
# ═══════════════════════════════════════════

def train_ensemble_model(words):
    X, y = generate_topic_training_data(words, augment=_auto_augment(len(words)))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y)
    gb = GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.08,
                                     subsample=0.9, min_samples_leaf=2, random_state=42)
    gb.fit(X_train, y_train)
    acc = round(gb.score(X_test, y_test) * 100, 1)
    joblib.dump((gb, acc), ENSEMBLE_MODEL_FILE)
    return gb, acc


def load_ensemble_model(words):
    """严格读取预训练的集成主题 pkl，不再在客户启动时训练。"""
    if ENSEMBLE_MODEL_FILE.exists():
        try:
            gb, acc = joblib.load(ENSEMBLE_MODEL_FILE)
            return gb, acc
        except Exception as e:
            raise RuntimeError(f"集成主题模型加载失败（{ENSEMBLE_MODEL_FILE.name}）：{e}\n请重新运行 build_models.py。")
    raise RuntimeError(
        f"集成主题模型未预训练（缺少 {ENSEMBLE_MODEL_FILE.name}）。\n"
        f"请联系开发者获取预训模型，或运行 `python build_models.py` 生成。")


# ═══════════════════════════════════════════
#  英语小工具
# ═══════════════════════════════════════════

def count_letters(text):
    """统计字母/单词/句子等"""
    letters = sum(1 for c in text if c.isalpha())
    digits = sum(1 for c in text if c.isdigit())
    spaces = sum(1 for c in text if c == " ")
    words = len(re.findall(r"[A-Za-z']+", text))
    sentences = len(re.split(r"[.!?]+", text.strip())) if text.strip() else 0
    sentences = max(0, sentences - (1 if text.strip().endswith((".", "!", "?")) else 0))
    if text.strip():
        sentences = max(sentences, 1) if not re.split(r"[.!?]+", text.strip())[-1] else sentences + 1
    # 简化：直接按 . ! ? 计数
    sentences = len(re.findall(r"[.!?]+", text)) or (1 if text.strip() else 0)
    return {
        "letters": letters,
        "digits": digits,
        "spaces": spaces,
        "words": words,
        "sentences": sentences,
        "total_chars": len(text),
    }


def analyze_word_basic(word):
    """简单的英语单词构词分析"""
    w = word.strip().lower()
    n = len(w)
    n_vowel = sum(1 for c in w if c in VOWELS)
    n_consonant = sum(1 for c in w if c.isalpha() and c not in VOWELS)
    syllable_est = max(1, sum(1 for i, c in enumerate(w)
                              if c in VOWELS and (i == 0 or w[i - 1] not in VOWELS)))
    features = []
    if w.endswith("ing"):
        features.append("含 -ing 后缀（动词进行时/动名词）")
    if w.endswith("ed"):
        features.append("含 -ed 后缀（动词过去式/过去分词）")
    if w.endswith("er"):
        features.append("含 -er 后缀（比较级/施动者）")
    if w.endswith("est"):
        features.append("含 -est 后缀（最高级）")
    if w.endswith("ly"):
        features.append("含 -ly 后缀（副词常见词尾）")
    if w.endswith("s") and len(w) >= 3:
        features.append("以 -s 结尾（可能为复数或第三人称单数）")
    if "th" in w:
        features.append("含 th 组合（齿擦音）")
    if "sh" in w:
        features.append("含 sh 组合（清擦音）")
    if "ch" in w:
        features.append("含 ch 组合（塞擦音）")
    if not features:
        features.append("基础发音组合")
    return {
        "length": n,
        "vowels": n_vowel,
        "consonants": n_consonant,
        "syllables": syllable_est,
        "features": features,
    }


# ═══════════════════════════════════════════
#  模型信息汇总
# ═══════════════════════════════════════════

def get_all_model_info(words, sentence_data, grade_data):
    _, topic_acc = load_topic_model(words)
    _, sent_acc = load_sentence_model(sentence_data)
    _, grade_r2 = load_grade_model(grade_data)
    _, diff_acc = load_diff_model(words)
    _, ensemble_acc = load_ensemble_model(words)
    return {
        "models": [
            {
                "name": "英语单词主题分类器",
                "algorithm": "随机森林 (Random Forest, 400棵树)",
                "library": "scikit-learn",
                "accuracy": topic_acc,
                "features": 24,
                "description": "根据单词24维特征自动识别8大词汇主题",
            },
            {
                "name": "英语句型分类器",
                "algorithm": "支持向量机 (SVM, RBF核)",
                "library": "scikit-learn",
                "accuracy": sent_acc,
                "features": 8,
                "description": "标准化+RBF核SVM区分6种英语句型（含 has_not / starts_wh 判别位）",
            },
            {
                "name": "年级词汇量预测器",
                "algorithm": "多项式回归 (Polynomial Ridge, degree=2)",
                "library": "scikit-learn",
                "r_squared": grade_r2,
                "features": "1→2 (多项式展开)",
                "description": "二次多项式+岭回归拟合年级与英语词汇量关系",
            },
            {
                "name": "单词难度预测器",
                "algorithm": "梯度提升 (GradientBoosting, 400轮)",
                "library": "scikit-learn",
                "accuracy": diff_acc,
                "features": 41,
                "description": "单词41维语音/形态/学段特征预测难度等级（基础/进阶/拓展）",
            },
            {
                "name": "综合主题分类器",
                "algorithm": "梯度提升 (Gradient Boosting, 300轮)",
                "library": "scikit-learn",
                "accuracy": ensemble_acc,
                "features": 24,
                "description": "梯度提升集成模型，作为随机森林的交叉验证对照",
            },
        ],
    }


YY_TIPS = [
    "每天背 5-10 个新单词，重在持之以恒",
    "结合例句记单词，比孤立记忆效果好得多",
    "多读多听，培养英语语感",
    "拼写不会写时，可以先拼读再回忆",
    "动词记忆要带例句和搭配（如 go to / look at）",
    "形容词常和名词搭配出现，可以一起记",
    "易混词（如 b/d、p/q）要多对比",
    "可以用思维导图把同主题单词归类",
    "看图记单词比死记硬背更有趣",
    "跟读音标可以矫正发音",
    "写英语日记是巩固词汇的好方法",
    "遇到不会的词立刻查并记下来",
    "学英语要敢说，不怕出错",
    "睡前过一遍当天单词，记得更牢",
    "对话练习是检验词汇掌握的最佳方式",
]


# 趣味鼓励语
CORRECT_MSGS = [
    "Excellent! 太棒了！",
    "Perfect! 完美命中！",
    "Great job! 干得好！",
    "Awesome! 你是单词高手！",
    "Bravo! 答得漂亮！",
    "Well done! 继续保持！",
    "You got it! 这词你拿下了！",
    "Brilliant! 词汇量又涨了！",
]
WRONG_MSGS = [
    "Don't worry, try again. 别灰心，再来！",
    "Almost! 差一点点～",
    "Keep trying! 再读两遍就能记住！",
    "It's okay! 错了才会进步！",
    "Don't give up! 这个词下次一定会！",
    "Try again. 读读音标找找感觉！",
]
