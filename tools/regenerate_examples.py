"""regenerate_examples.py — 重写词库里模板化/无意义的例句。

策略：
1. 识别"低质量例句"（占总词量 ~76%）：
   - "This is a/an X." / "It is very X." / "I X every day."
   - 空字符串
   - 明显无效如 "This is a today.", "I divide every day."
2. 用按词性 + 主题分组的多模板池重写，每词由 hash(word) 选模板，保证可复现。
3. 同步生成 example_zh（中文翻译）。
4. 对常见功能词（today/tonight/every/the/I/you/he/she/...）使用专属精修例句。

不改动：原本就不属于上述坏模板的、自然合理的例句一律保留。
"""
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "data/wordbank/primary.json",
    ROOT / "data/wordbank/middle.json",
    ROOT / "data/wordbank/high.json",
]

BAD_PATTERNS = [
    re.compile(r"^this is an? \w+\.?$", re.IGNORECASE),
    re.compile(r"^it is very \w+\.?$", re.IGNORECASE),
    re.compile(r"^i \w+ every day\.?$", re.IGNORECASE),
    re.compile(r"^there are \w+\.?$", re.IGNORECASE),
    re.compile(r"^he answered \w+\.?$", re.IGNORECASE),
]


# ── 词性模板池：每条 (英文, 中文) ──
TEMPLATES = {
    # 名词：模板里不加 a/an，避免抽象名词、不可数名词被强加冠词
    "n": [
        ("We learned about {w} in our last lesson.", "我们上节课学了{m}。"),
        ("The teacher mentioned {w} during class.", "老师在课上提到了{m}。"),
        ("Many students are interested in {w}.", "许多学生对{m}感兴趣。"),
        ("Have you ever heard of {w} before?", "你以前听说过{m}吗？"),
        ("{w_cap} is an important topic in this book.", "{m}是这本书里的重要话题。"),
        ("My sister often talks about {w}.", "姐姐经常谈论{m}。"),
        ("We had a long discussion about {w} yesterday.", "昨天我们就{m}进行了长时间讨论。"),
        ("The article gave a clear example of {w}.", "这篇文章给出了一个关于{m}的清晰例子。"),
        ("Children should know more about {w}.", "孩子们应该多了解{m}。"),
        ("{w_cap} plays an important role in our daily life.", "{m}在我们的日常生活中扮演着重要角色。"),
    ],
    # 动词：多用“want to / how to / try to”等包裹式语梣，兼容及物/不及物动词
    "v": [
        ("She is learning how to {w} this year.", "她今年正在学习如何{m}。"),
        ("I want to {w} better than before.", "我想比以前{m}得更好。"),
        ("They will try to {w} this weekend.", "这周末他们会尝试{m}。"),
        ("Don't forget to {w} before you leave.", "你走之前别忘了{m}。"),
        ("My father teaches me how to {w}.", "爸爸教我如何{m}。"),
        ("It's not easy to {w} at first.", "一开始{m}并不容易。"),
        ("You should {w} more carefully next time.", "下次你应该更仔细地{m}。"),
        ("We need to {w} together as a team.", "我们需要作为一个团队一起{m}。"),
        ("Let me show you how to {w}.", "让我告诉你如何{m}。"),
        ("She decided to {w} again next week.", "她决定下周再{m}一次。"),
    ],
    # 形容词：中文填填 meaning 后由后处理去重“的的”，避免词义有褐贬倾向
    "adj": [
        ("The new project sounds quite {w} to me.", "这个新项目听起来相当{m}。"),
        ("Her opinion on this matter is rather {w}.", "她对这件事的看法相当{m}。"),
        ("He found the lecture very {w}.", "他觉得这场讲座非常{m}。"),
        ("This kind of design seems {w} to most people.", "这种设计在多数人看来是{m}。"),
        ("The result of the experiment was {w}.", "实验的结果{m}。"),
        ("She made a {w} decision in the end.", "最后她做出了一个{m}决定。"),
        ("Many people consider this idea {w}.", "很多人认为这个想法{m}。"),
        ("His handwriting is surprisingly {w}.", "他的字迹出乎意料地{m}。"),
        ("To us, the question seemed {w} at first.", "这个问题在我们看来一开始{m}。"),
        ("It will be a {w} day for the whole class.", "对全班来说这会是{m}的一天。"),
    ],
    # 副词：中文 meaning 常带“地”，后处理去重“地地”
    "adv": [
        ("She finished her homework {w}.", "她{m}做完了作业。"),
        ("He answered the teacher's question {w}.", "他{m}回答了老师的问题。"),
        ("The children listened {w} during the story.", "听故事时孩子们{m}听着。"),
        ("My grandmother walks {w} in the morning.", "奶奶早上{m}走路。"),
        ("She smiled at the baby {w}.", "她{m}对宝宝微笑。"),
        ("He read the letter {w} aloud.", "他{m}大声读出这封信。"),
        ("The old man speaks {w} about his hometown.", "老人{m}谈起他的家乡。"),
        ("She closed the door {w} so as not to wake the baby.", "她{m}关上门，以免吓醒宝宝。"),
    ],
    # prep 与 pron 句型变化大，不靠模板，全部去 WORD_OVERRIDES 里一一精写
    "prep": [],
    "pron": [],
    "conj": [
        ("I like both English {w} math.", "我既喜欢英语{m}数学。"),
        ("He stayed at home {w} it was raining.", "他待在家里，{m}下雨了。"),
        ("Hurry up, {w} we will be late.", "快点，{m}我们就要迟到了。"),
        ("She is tired, {w} she keeps working.", "她累了，{m}她仍在继续工作。"),
    ],
    # num: 全部去 WORD_OVERRIDES 里一一处理（区分基数/序数）
    "num": [],
    "art": [
        ("I bought {w} interesting book yesterday.", "我昨天买了{m}有趣的书。"),
        ("Please pass me {w} pen on the desk.", "请把桌上{m}笔递给我。"),
    ],
    "modal": [
        ("You {w} finish your homework first.", "你{m}先完成作业。"),
        ("We {w} go swimming this weekend.", "我们这个周末{m}去游泳。"),
        ("She said she {w} come tomorrow.", "她说她明天{m}来。"),
    ],
    "aux": [
        ("{w_cap} you like a cup of tea?", "你{m}来一杯茶吗？"),
        ("{w_cap} she finish the project on time?", "她{m}按时完成项目吗？"),
    ],
    "int": [],
}


def _clean_zh(s: str) -> str:
    """后处理中文例句：去重「的的/地地/了了」等重复模板产生的赘余。"""
    if not s:
        return s
    while "的的" in s:
        s = s.replace("的的", "的")
    while "地地" in s:
        s = s.replace("地地", "地")
    while "了了" in s:
        s = s.replace("了了", "了")
    return s


# ── 功能词白名单：精修例句（覆盖最常出现的"This is a today."类爆款错句）──
WORD_OVERRIDES = {
    # ── 名词表息语/问候语 ──
    "hi": ("Hi! Nice to meet you here.", "嘿！很高兴在这里见到你。"),
    "hello": ("Hello, everyone! Welcome to our class.", "大家好！欢迎来到我们的课堂。"),
    "goodbye": ("Goodbye, see you tomorrow morning.", "再见，明早见。"),
    "oh": ("Oh, I almost forgot to bring my key.", "哦，我差点忘记带钥匙了。"),

    # ── 代词（pron pos） ──
    "this": ("This is the most interesting book I have read.", "这是我读过的最有趣的一本书。"),
    "that": ("That over there is our new English teacher.", "那边那位是我们的新英语老师。"),
    "these": ("These are my favorite story books.", "这些是我最喜欢的故事书。"),
    "those": ("Those flowers in the garden look beautiful.", "花园里那些花看起来很漂亮。"),
    "who": ("Who is the boy standing by the door?", "站在门边的那个男孩是谁？"),
    "what": ("What did you have for breakfast this morning?", "你今天早上吃了什么早餐？"),
    "each": ("Each of us got a small present from the teacher.", "每个人都从老师那里得到了一份小礼物。"),
    "both": ("Both of my parents work as engineers.", "我父母都是工程师。"),

    # ── 数学介词 ──
    "plus": ("Two plus three equals five.", "二加三等于五。"),
    "minus": ("Ten minus four is six.", "十减四是六。"),
    "times": ("Three times four equals twelve.", "三乘以四等于十二。"),

    # ── 基数词 ──
    "zero": ("The temperature dropped below zero last night.", "昨夜温度降到了零以下。"),
    "one": ("I have one elder brother and two younger sisters.", "我有一个哥哥和两个妹妹。"),
    "two": ("There are two cats sleeping on the sofa.", "沙发上有两只猫在睡觉。"),
    "three": ("My family lives in a house with three bedrooms.", "我家住在一个三间卧室的房子里。"),
    "four": ("There are four seasons in a year.", "一年有四个季节。"),
    "five": ("School starts at five minutes past eight.", "学校八点零五开始上课。"),
    "six": ("My little brother is six years old.", "我弟弟六岁了。"),
    "seven": ("There are seven days in a week.", "一周有七天。"),
    "eight": ("I usually go to bed at eight o'clock.", "我通常八点上床睡觉。"),
    "nine": ("Nine students stayed after class to ask questions.", "课后有九个学生留下来提问。"),
    "ten": ("He can count from one to ten in English.", "他能用英语从一数到十。"),
    "eleven": ("My uncle has eleven sheep on his farm.", "叔叔的农场里养了十一只羊。"),
    "twelve": ("There are twelve months in a year.", "一年有十二个月。"),
    "thirteen": ("My cousin will be thirteen years old next month.", "下个月我堂兄就十三岁了。"),
    "fourteen": ("There are fourteen new words in this lesson.", "这课有十四个生词。"),
    "fifteen": ("The bus will leave in fifteen minutes.", "公共汽车还有十五分钟就走了。"),
    "sixteen": ("You can drive a car at sixteen in some countries.", "在一些国家十六岁就可以开车。"),
    "seventeen": ("My sister is seventeen and in high school.", "姐姐十七岁了，读高中。"),
    "eighteen": ("He turned eighteen last Sunday.", "上星期天他满十八岁了。"),
    "nineteen": ("There are nineteen pupils in our music club.", "我们音乐社有十九名同学。"),
    "twenty": ("I have read twenty books this year.", "今年我读了二十本书。"),
    "thirty": ("The class lasts about thirty minutes.", "这节课大约持续三十分钟。"),
    "forty": ("My father is forty years old this year.", "我爸爸今年四十岁。"),
    "fifty": ("Our school has more than fifty teachers.", "我们学校有五十多名老师。"),
    "sixty": ("There are sixty seats in this small theater.", "这个小剧场有六十个座位。"),
    "seventy": ("My grandfather is already seventy.", "我爷爷已经七十岁了。"),
    "eighty": ("The library has more than eighty new books.", "图书馆新增了八十多本书。"),
    "ninety": ("She lived to be ninety years old.", "她活到了九十岁。"),
    "hundred": ("More than a hundred students joined the contest.", "有一百多名学生参加了比赛。"),
    "thousand": ("This city has a population of one thousand people.", "这座城市有一千人口。"),
    "million": ("This bridge cost over five million yuan to build.", "这座桥花了五百多万元才建成。"),

    # ── 序数词 ──
    "first": ("This is the first time I have visited Beijing.", "这是我第一次来北京。"),
    "second": ("He came in second place in the running race.", "他在跑步比赛中获得了第二名。"),
    "third": ("My desk is the third one from the door.", "我的桌子是从门口数第三张。"),
    "fourth": ("Today is the fourth day of our trip.", "今天是我们旅行的第四天。"),
    "fifth": ("She lives on the fifth floor of the building.", "她住在这栋楼的五楼。"),
    "twentieth": ("My birthday is on the twentieth of March.", "我的生日是三月二十号。"),
    "hundredth": ("This is the hundredth book in our class library.", "这是我们班级图书角的第一百本书。"),
    "thousandth": ("He celebrated the thousandth day of his hobby.", "他庆祝了自己坚持爱好的第一千天。"),

    # 时间词
    "today": ("We have an English test today.", "今天我们有一场英语测验。"),
    "tonight": ("I will watch a movie with my family tonight.", "今晚我会和家人一起看电影。"),
    "yesterday": ("Yesterday I went to the library after school.", "昨天放学后我去了图书馆。"),
    "tomorrow": ("We are going camping tomorrow.", "我们明天要去野营。"),
    "now": ("Please come downstairs now; dinner is ready.", "现在请下楼，晚饭好了。"),
    "then": ("She finished her homework, then went to bed.", "她做完作业，然后就上床睡觉了。"),
    "soon": ("The bus will arrive soon.", "公共汽车很快就要到了。"),
    "later": ("I will call you back later.", "我晚些时候再给你回电话。"),
    "every": ("I read English books every day.", "我每天都读英语书。"),
    "always": ("She is always kind to her classmates.", "她对同学们总是很友善。"),
    "often": ("My dad often takes me to the park.", "爸爸经常带我去公园。"),
    "sometimes": ("Sometimes I help my mom cook dinner.", "有时我会帮妈妈做晚饭。"),
    "usually": ("I usually get up at six thirty.", "我通常六点半起床。"),
    "never": ("He never eats breakfast in a hurry.", "他从不匆忙吃早餐。"),
    "seldom": ("She seldom talks during class.", "她在课堂上很少说话。"),
    "ever": ("Have you ever been to Beijing?", "你去过北京吗？"),

    # 处所/方向词
    "here": ("Please put the umbrella here by the door.", "请把雨伞放在门边这里。"),
    "there": ("Look! There is a rainbow over there.", "看！那边有一道彩虹。"),
    "where": ("Where do you usually have lunch?", "你通常在哪里吃午饭？"),
    "everywhere": ("Books are everywhere in his room.", "他房间里到处都是书。"),

    # 数量词
    "very": ("This question is very difficult for me.", "这道题对我来说非常难。"),
    "much": ("He doesn't have much time today.", "他今天没有太多时间。"),
    "many": ("There are many flowers in the garden.", "花园里有许多花。"),
    "more": ("Could you give me a little more juice?", "你能再给我一点果汁吗？"),
    "less": ("We should use less water every day.", "我们每天应该少用一些水。"),
    "few": ("Few students passed the math test.", "很少有学生通过了数学测验。"),
    "little": ("There is a little milk left in the fridge.", "冰箱里还剩一点牛奶。"),
    "all": ("All the students are ready for the exam.", "所有学生都准备好考试了。"),
    "some": ("Would you like some apples?", "你想要一些苹果吗？"),
    "any": ("Do you have any questions for me?", "你有什么问题要问我吗？"),
    "no": ("There is no milk in the fridge.", "冰箱里没有牛奶。"),
    "none": ("None of us knew the answer.", "我们当中没有人知道答案。"),
    "both": ("Both of my parents are teachers.", "我父母都是老师。"),
    "each": ("Each child got a small gift.", "每个孩子都得到了一份小礼物。"),
    "either": ("You can choose either of these books.", "这两本书你都可以选。"),
    "neither": ("Neither of them likes football.", "他们俩都不喜欢足球。"),

    # 系动词与 be 动词
    "am": ("I am a student of Class Two.", "我是二班的一名学生。"),
    "is": ("She is my best friend at school.", "她是我学校里最好的朋友。"),
    "are": ("They are playing basketball on the playground.", "他们正在操场上打篮球。"),
    "was": ("I was at home yesterday afternoon.", "昨天下午我在家。"),
    "were": ("They were excited about the trip.", "他们对那次旅行感到很兴奋。"),
    "be": ("Please be quiet in the library.", "在图书馆请保持安静。"),

    # 助动词与情态动词
    "do": ("Do you like English songs?", "你喜欢英文歌吗？"),
    "does": ("Does your sister study in this school?", "你妹妹在这所学校读书吗？"),
    "did": ("Did you finish your homework yesterday?", "你昨天完成作业了吗？"),
    "have": ("I have two younger brothers.", "我有两个弟弟。"),
    "has": ("She has a beautiful red dress.", "她有一条漂亮的红色连衣裙。"),
    "had": ("We had a great party last weekend.", "上周末我们开了一个很棒的派对。"),
    "will": ("I will visit my grandparents next Sunday.", "下星期天我会去看望祖父母。"),
    "would": ("I would like a glass of water, please.", "请给我一杯水。"),
    "shall": ("Shall we go to the movies tonight?", "我们今晚去看电影好吗？"),
    "should": ("You should drink more water every day.", "你每天应该多喝水。"),
    "can": ("I can swim very well now.", "我现在游泳游得很好。"),
    "could": ("Could you open the window for me?", "你能为我打开窗户吗？"),
    "may": ("May I borrow your eraser, please?", "我可以借一下你的橡皮吗？"),
    "might": ("It might rain in the afternoon.", "下午可能会下雨。"),
    "must": ("Students must wear school uniforms on Monday.", "周一学生必须穿校服。"),

    # 主格代词
    "i": ("I want to be a doctor when I grow up.", "我长大后想成为一名医生。"),
    "you": ("You are very kind to help me.", "你帮我，真是太好了。"),
    "he": ("He is reading a book in the library.", "他在图书馆看书。"),
    "she": ("She loves dancing after school.", "她喜欢放学后跳舞。"),
    "it": ("It is a sunny day today.", "今天是个晴天。"),
    "we": ("We are good friends from the same class.", "我们是同班的好朋友。"),
    "they": ("They are playing soccer in the field.", "他们在操场上踢足球。"),

    # 宾格代词
    "me": ("Could you tell me the way to the hospital?", "你能告诉我去医院的路吗？"),
    "him": ("My mom asked him to come for dinner.", "妈妈邀请他来吃晚饭。"),
    "us": ("Please join us for lunch tomorrow.", "明天请加入我们一起吃午饭。"),
    "them": ("Don't forget to thank them for the gift.", "别忘了感谢他们送的礼物。"),

    # 物主代词
    "my": ("My favorite subject is English.", "我最喜欢的科目是英语。"),
    "your": ("Your idea sounds very interesting.", "你的主意听起来很有趣。"),
    "his": ("His sister is a famous doctor.", "他姐姐是一位著名的医生。"),
    "her": ("Her smile makes everyone happy.", "她的笑容让每个人都开心。"),
    "its": ("The cat is licking its paws.", "那只猫在舔自己的爪子。"),
    "our": ("Our school has a big library.", "我们学校有一个大图书馆。"),
    "their": ("Their team won the football match.", "他们队赢得了足球比赛。"),

    # 名词性物主代词
    "mine": ("That blue bag on the desk is mine.", "桌上那个蓝色的包是我的。"),
    "yours": ("Is this red pencil yours?", "这支红色铅笔是你的吗？"),
    "hers": ("This new dictionary is hers.", "这本新词典是她的。"),
    "ours": ("The garden behind the school is ours.", "学校后面的花园是我们的。"),
    "theirs": ("The big house on the hill is theirs.", "山上那座大房子是他们的。"),

    # 反身代词
    "myself": ("I made this paper plane all by myself.", "这架纸飞机是我自己做的。"),
    "yourself": ("Take care of yourself in this cold weather.", "这种冷天气里要照顾好自己。"),
    "himself": ("He cooked dinner for himself last night.", "昨晚他给自己做了晚饭。"),
    "herself": ("She finished the puzzle by herself.", "她自己完成了那个拼图。"),
    "ourselves": ("We can solve the problem ourselves.", "这个问题我们自己能解决。"),

    # 冠词
    "a": ("I bought a new pen at the bookstore.", "我在书店买了一支新笔。"),
    "an": ("She is reading an interesting story.", "她在读一个有趣的故事。"),
    "the": ("The sun rises in the east.", "太阳从东方升起。"),

    # 常用连词
    "and": ("My brother and I went to the zoo last Sunday.", "上星期天我和哥哥去了动物园。"),
    "but": ("She is tired but still keeps working.", "她累了但仍在继续工作。"),
    "or": ("Would you like tea or coffee?", "你想喝茶还是咖啡？"),
    "so": ("It was raining, so we stayed at home.", "下雨了，所以我们待在家里。"),
    "because": ("I was late because the bus broke down.", "我迟到了，因为公共汽车坏了。"),
    "if": ("If you study hard, you will pass the exam.", "如果你努力学习，就会通过考试。"),
    "when": ("When I came home, my dad was cooking.", "我回到家时，爸爸正在做饭。"),
    "while": ("She listened to music while doing homework.", "她做作业时听音乐。"),
    "though": ("Though it was cold, the children kept playing.", "尽管天冷，孩子们仍在玩。"),
    "although": ("Although he is young, he is very brave.", "虽然他年纪小，但很勇敢。"),

    # 介词
    "in": ("There are many flowers in the garden.", "花园里有很多花。"),
    "on": ("The book is on the desk.", "书在桌子上。"),
    "at": ("We meet at the school gate every morning.", "我们每天早上在校门口见面。"),
    "to": ("She went to the supermarket with her mother.", "她和妈妈去了超市。"),
    "for": ("This gift is for my best friend.", "这份礼物是给我最好的朋友的。"),
    "with": ("I went to the park with my brother.", "我和弟弟一起去了公园。"),
    "from": ("This letter is from my pen friend.", "这封信是我笔友寄来的。"),
    "about": ("We talked about the new movie.", "我们谈论了那部新电影。"),
    "of": ("The color of the sky is blue.", "天空的颜色是蓝色。"),
    "by": ("The window was opened by the wind.", "窗户被风吹开了。"),
    "before": ("Wash your hands before dinner.", "吃晚饭前要洗手。"),
    "after": ("We went home after the football match.", "足球比赛结束后我们回家了。"),
    "under": ("The cat is sleeping under the bed.", "猫在床下睡觉。"),
    "over": ("A bird flew over the river.", "一只鸟飞过河面。"),
    "between": ("There is a chair between the two desks.", "两张桌子中间有一把椅子。"),
    "near": ("Our school is near the park.", "我们学校在公园附近。"),
    "behind": ("The garden is behind the house.", "花园在房子后面。"),
    "beside": ("She sat beside her best friend.", "她坐在最好的朋友旁边。"),
    "into": ("The mouse ran into the hole.", "老鼠跑进了洞里。"),
    "without": ("We can't live without water.", "没有水我们就活不下去。"),
}


def is_bad(example, word):
    if not example:
        return True
    s = example.strip()
    for p in BAD_PATTERNS:
        if p.match(s):
            return True
    # "This is a + 已经包括"，这里再加一个直白匹配
    low = s.lower()
    if low.startswith(f"this is a {word.lower()}") or low.startswith(f"this is an {word.lower()}"):
        return True
    if low.startswith(f"it is very {word.lower()}"):
        return True
    return False


def pick_template(word, pos):
    pool = TEMPLATES.get(pos)
    if not pool:
        # 兜底用名词模板
        pool = TEMPLATES["n"]
    rng = random.Random(hash(word) & 0xFFFFFFFF)
    return rng.choice(pool)


def regen(word, meaning, pos):
    if word.lower() in WORD_OVERRIDES:
        return WORD_OVERRIDES[word.lower()]
    en, zh = pick_template(word, pos)
    en_filled = en.replace("{w_cap}", word.capitalize()).replace("{w}", word)
    # 形容词/副词：中文 meaning 常带“的/地”，先去尾再填，避免“相当新鲜的/出乎意料地对称的”。
    m = meaning or word
    if pos in ("adj", "adv"):
        m = m.rstrip("的地")
    zh_filled = zh.replace("{m}", m)
    return en_filled, _clean_zh(zh_filled)


def main():
    grand_total = 0
    grand_changed = 0
    for f in FILES:
        data = json.loads(f.read_text(encoding="utf-8"))
        changed = 0
        for w in data:
            old = (w.get("example") or "").strip()
            # 二者之一触发重写：
            #   1) 该词在精修白名单中（优先覆盖，保证 plus/minus/who/this 等句型重写）
            #   2) 原 example 匹配到“坏模板”或为空
            if w["word"].lower() in WORD_OVERRIDES or is_bad(old, w["word"]):
                en, zh = regen(w["word"], w.get("meaning", ""), w.get("pos", "n"))
                if (en, zh) != (old, w.get("example_zh", "")):
                    w["example"] = en
                    w["example_zh"] = zh
                    changed += 1
        f.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        grand_total += len(data)
        grand_changed += changed
        print(f"[{f.name}] 共 {len(data)} 词，重写 {changed} 例")

    print(f"\n总计：{grand_total} 词，重写 {grand_changed} 例（{grand_changed*100/grand_total:.1f}%）")


if __name__ == "__main__":
    main()
