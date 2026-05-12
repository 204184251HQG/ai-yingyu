"""
词途 · AI 英语单词学习闯关系统 — CustomTkinter 图形界面
覆盖小学/初中/高中 · 清新蓝绿配色 · 封面页 + 底部导航栏 + 多功能页
"""

import os, sys, random, math
import customtkinter as ctk
from tkinter import messagebox

from ai_model import (
    predict_topic, predict_difficulty, predict_vocab_by_grade,
    predict_sentence_type, auto_extract_sentence_features,
    analyze_word_basic, count_letters,
    get_all_model_info,
    YY_TIPS, TOPIC_LABELS, DIFFICULTY_LABELS, POS_LABELS,
    CORRECT_MSGS, WRONG_MSGS,
)
from yingyu_data import (
    YY_TOPICS, WORDS, SENTENCE_TRAIN_DATA, SENTENCE_LABELS, GRADE_VOCAB,
    LEVELS, count_words_by_level, get_words_by_level,
    record_quiz, get_stats, build_quiz, get_words_by_topic,
    load_custom_words, add_custom_word, delete_custom_word,
    make_choose_meaning_question, make_choose_word_question,
    make_listen_question, make_spell_question,
)
import voice

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── 配色（可爱风 · 樱花马卡龙）──
C_PRIMARY = "#fb7185"           # 樱花粉
C_PRIMARY_DARK = "#f43f5e"
C_PRIMARY_LIGHT = "#ffe4e6"
C_BG = "#fffafb"                # 奶白带粉底
C_CARD = "#ffffff"
C_TEXT = "#3f3f46"              # 柔和深灰
C_SUB = "#71717a"
C_MUTED = "#a1a1aa"
C_BORDER = "#fbcfe8"            # 淡粉描边（柔和不刈）
C_DIVIDER = "#fce7f3"           # 极淡粉分隔、进度条底
C_BLUE = "#60a5fa"              # 柔和天蓝
C_BLUE_DARK = "#3b82f6"
C_BLUE_LIGHT = "#dbeafe"
C_GREEN = "#86efac"             # 嫩薄荷
C_GREEN_DARK = "#4ade80"
C_GREEN_LIGHT = "#dcfce7"
C_ORANGE = "#fdba74"            # 桃色
C_ORANGE_DARK = "#fb923c"
C_ORANGE_LIGHT = "#ffedd5"
C_RED = "#fb7185"               # 同主色系
C_RED_DARK = "#f43f5e"
C_RED_LIGHT = "#ffe4e6"
C_PURPLE = "#c4b5fd"            # 淡紫
C_PURPLE_DARK = "#a78bfa"
C_PURPLE_LIGHT = "#ede9fe"
C_PINK = "#f9a8d4"              # 浅粉
C_PINK_LIGHT = "#fce7f3"
C_YELLOW = "#fcd34d"            # 蜜橙黄
C_YELLOW_LIGHT = "#fef9c3"

MODE_LABEL = {
    "choose_meaning": "看词选义",
    "choose_word": "看义选词",
    "listen": "听音辨词",
    "spell": "拼写练习",
}
POS_BADGE = {
    "n": "n.", "v": "v.", "adj": "adj.", "adv": "adv.",
    "prep": "prep.", "conj": "conj.", "int": "int.",
    "num": "num.", "pron": "pron.",
}

# 主题的可爱 emoji 图标（不侵入数据层）
TOPIC_EMOJI = {
    "basic": "💬", "school": "🎒", "nature": "🌳", "food": "🍰",
    "family": "🏠", "numtime": "⏰", "colorshape": "🎨", "action": "🌟",
}

def _card(parent, **kw):
    fg = kw.pop("fg_color", C_CARD)
    bd = kw.pop("border_color", C_BORDER)
    bw = kw.pop("border_width", 1)  # 可爱风：柔和淡粉描边
    cr = kw.pop("corner_radius", 20)  # 可爱风：更圆润
    return ctk.CTkFrame(parent, fg_color=fg, corner_radius=cr,
                        border_width=bw, border_color=bd, **kw)


# ════════════════════════════════════════════
#  封面页
# ════════════════════════════════════════════
class SplashPage(ctk.CTkFrame):
    def __init__(self, master, on_start):
        super().__init__(master, fg_color=C_BG)
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.pack(expand=True)
        ab = ctk.CTkFrame(center, fg_color=C_PRIMARY_LIGHT, width=110, height=110, corner_radius=55)
        ab.pack(pady=(0, 8))
        ab.pack_propagate(False)
        ctk.CTkLabel(ab, text="词途", font=ctk.CTkFont(size=34, weight="bold"),
                     text_color=C_PRIMARY).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(center, text="词途",
                     font=ctk.CTkFont(size=44, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(pady=(6, 2))
        ctk.CTkLabel(center, text="AI 英语单词学习闯关系统",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(pady=(0, 2))
        ctk.CTkLabel(center, text="小学 · 初中 · 高中 全学段",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C_PRIMARY).pack(pady=(0, 4))
        ctk.CTkLabel(center, text="A word a day keeps the worry away",
                     font=ctk.CTkFont(size=14), text_color=C_SUB).pack(pady=(0, 8))

        # 顶部装饰字母
        deco = ctk.CTkFrame(center, fg_color="transparent")
        deco.pack(pady=(0, 16))
        for sym, clr in [("A", C_BLUE), ("B", C_GREEN), ("C", C_ORANGE),
                          ("D", C_PURPLE), ("E", C_PINK), ("F", C_PRIMARY),
                          ("G", C_RED), ("H", C_YELLOW)]:
            eb = ctk.CTkFrame(deco, fg_color=clr, width=34, height=34, corner_radius=17)
            eb.pack(side="left", padx=3)
            eb.pack_propagate(False)
            ctk.CTkLabel(eb, text=sym, font=ctk.CTkFont(size=14, weight="bold"),
                         text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        features = [
            ("练", "百词斩闯关", "看词选义、看义选词、听音、拼写多种题型", C_ORANGE_LIGHT, C_ORANGE),
            ("脑", "AI 智能识别", "自动判断单词所属主题、难度、词性", C_BLUE_LIGHT, C_BLUE),
            ("书", "句型分析", "识别陈述句、疑问句、感叹句等英语句型", C_PURPLE_LIGHT, C_PURPLE),
            ("星", "学习档案", "记录闯关进度，已掌握单词一目了然", C_GREEN_LIGHT, C_GREEN),
        ]
        grid = ctk.CTkFrame(center, fg_color="transparent")
        grid.pack(pady=(0, 24))
        for icon, title, desc, bg, clr in features:
            row = _card(grid)
            row.pack(fill="x", padx=60, pady=4, ipady=6)
            ib = ctk.CTkFrame(row, fg_color=bg, width=36, height=36, corner_radius=10)
            ib.pack(side="left", padx=(12, 8))
            ib.pack_propagate(False)
            ctk.CTkLabel(ib, text=icon, font=ctk.CTkFont(size=16, weight="bold"),
                         text_color=clr).place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(row, text=title, font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C_TEXT, anchor="w", width=110).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=12),
                         text_color=C_SUB, anchor="w").pack(side="left", padx=(0, 12))
        ctk.CTkButton(center, text="Let's Go!  开启英语之旅", font=ctk.CTkFont(size=18, weight="bold"),
                      width=280, height=52, corner_radius=26, fg_color=C_PRIMARY,
                      hover_color=C_PRIMARY_DARK, text_color="white",
                      command=on_start).pack(pady=(0, 10))
        ctk.CTkLabel(self, text="v1.0  |  Practice makes perfect",
                     font=ctk.CTkFont(size=10), text_color=C_MUTED).pack(side="bottom", pady=(0, 6))


# ════════════════════════════════════════════
#  首页
# ════════════════════════════════════════════
class HomePage(ctk.CTkFrame):
    def __init__(self, master, nav_fn, current_level="all", set_level_fn=None):
        super().__init__(master, fg_color=C_BG)
        self.navigate = nav_fn
        self.current_level = current_level
        self.set_level_fn = set_level_fn
        stats = get_stats()

        banner = ctk.CTkFrame(self, fg_color=C_PRIMARY, corner_radius=0)
        banner.pack(fill="x", padx=0, pady=(0, 14))
        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="x", padx=20, pady=16)
        bi_top = ctk.CTkFrame(bi, fg_color="transparent")
        bi_top.pack(fill="x")

        # 左侧：大头 mascot 头像
        ctk.CTkLabel(bi_top, text="🐰", font=ctk.CTkFont(size=46),
                     text_color="white").pack(side="left", padx=(0, 12))

        welcome_box = ctk.CTkFrame(bi_top, fg_color="transparent")
        welcome_box.pack(side="left", anchor="w")
        ctk.CTkLabel(welcome_box, text="Welcome back  欢迎回来 ♡",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(welcome_box, text="今天也要开心地背单词喔～",
                     font=ctk.CTkFont(size=13),
                     text_color="white").pack(anchor="w", pady=(2, 0))

        # 右侧：动物群 + 小装饰
        ctk.CTkLabel(bi_top, text="🐱  �  🌸  🎀  ⭐",
                     font=ctk.CTkFont(size=22),
                     text_color="white").pack(side="right", anchor="e", padx=(8, 0))

        sub = (f"已答题 {stats['total']} 次  ·  正确率 {stats['accuracy']}%  "
               f"·  已掌握单词 {stats['mastered_words']}/{stats['encountered_words']}")
        ctk.CTkLabel(bi, text=sub, font=ctk.CTkFont(size=14),
                     text_color="white").pack(anchor="w", pady=(10, 0))

        tip = random.choice(YY_TIPS)
        tip_card = _card(self, fg_color=C_BLUE_LIGHT, border_color=C_BLUE)
        tip_card.pack(fill="x", padx=16, pady=(0, 12))
        tip_inner = ctk.CTkFrame(tip_card, fg_color="transparent")
        tip_inner.pack(fill="x", padx=14, pady=12)
        # 左侧圆形粉色提示 chip
        tip_chip = ctk.CTkFrame(tip_inner, fg_color=C_PRIMARY, width=44, height=44,
                                 corner_radius=22)
        tip_chip.pack(side="left", padx=(0, 12))
        tip_chip.pack_propagate(False)
        ctk.CTkLabel(tip_chip, text="提", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(tip_inner, text=f"今日小提示：{tip}",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_BLUE, wraplength=560, justify="left"
                     ).pack(side="left", anchor="w")

        # 学段筛选条
        level_bar = ctk.CTkFrame(self, fg_color="transparent")
        level_bar.pack(fill="x", padx=18, pady=(0, 8))
        ctk.CTkLabel(level_bar, text="学段：", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C_TEXT).pack(side="left", padx=(0, 6))
        lvc = count_words_by_level()
        total_count = sum(lvc.values())
        level_options = [
            ("all",     f"全学段 ({total_count})",                C_PRIMARY),
            ("primary", f"小学 ({lvc.get('primary', 0)})",        LEVELS["primary"]["color"]),
            ("middle",  f"初中 ({lvc.get('middle', 0)})",         LEVELS["middle"]["color"]),
            ("high",    f"高中 ({lvc.get('high', 0)})",           LEVELS["high"]["color"]),
        ]
        for lv, lbl, clr in level_options:
            active = (lv == self.current_level)
            ctk.CTkButton(
                level_bar, text=lbl,
                width=104, height=32, corner_radius=16,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=(clr if active else C_CARD),
                hover_color=clr, text_color=("white" if active else clr),
                border_width=(0 if active else 1), border_color=clr,
                command=lambda l=lv: self._on_level_change(l),
            ).pack(side="left", padx=3)

        # 主题词库标题区（带 mascot 装饰）
        topic_head = ctk.CTkFrame(self, fg_color="transparent")
        topic_head.pack(fill="x", padx=18, pady=(10, 6))
        ctk.CTkLabel(topic_head, text="�", font=ctk.CTkFont(size=24),
                     text_color=C_PRIMARY).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(topic_head, text="主题词库",
                     font=ctk.CTkFont(size=21, weight="bold"),
                     text_color=C_TEXT).pack(side="left")
        ctk.CTkLabel(topic_head, text="点一下卡片就能开始闯关喔～",
                     font=ctk.CTkFont(size=12),
                     text_color=C_SUB).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(topic_head, text="🐰  🐱  🐻",
                     font=ctk.CTkFont(size=20),
                     text_color=C_PRIMARY).pack(side="right")

        # 滚动主题列表
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        for tid, info in YY_TOPICS.items():
            self._topic_row(scroll, tid, info, stats)

    def _on_level_change(self, level):
        if self.set_level_fn:
            self.set_level_fn(level)
        self.navigate("home")

    def _topic_row(self, parent, tid, info, stats):
        topic_clr = info.get('color', C_PRIMARY)
        # 卡片边框用主题色 → 列表彩色密度提升
        card = _card(parent, border_color=topic_clr)
        card.pack(fill="x", padx=4, pady=4)
        card.configure(cursor="hand2")
        cb = lambda e, t=tid: self.navigate("quiz", t)
        card.bind("<Button-1>", cb)

        # 左侧：主题色大圆形 chip（emoji 图标）
        chip = ctk.CTkFrame(card, fg_color=topic_clr, width=58, height=58,
                             corner_radius=20)
        chip.pack(side="left", padx=(12, 8), pady=10)
        chip.pack_propagate(False)
        emo_lbl = ctk.CTkLabel(chip, text=TOPIC_EMOJI.get(tid, "★"),
                                font=ctk.CTkFont(size=28), text_color="white")
        emo_lbl.place(relx=0.5, rely=0.5, anchor="center")
        chip.bind("<Button-1>", cb)
        emo_lbl.bind("<Button-1>", cb)

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True, padx=4, pady=10)
        lbl1 = ctk.CTkLabel(left, text=info['name'],
                            font=ctk.CTkFont(size=17, weight="bold"),
                            text_color=C_TEXT)
        lbl1.pack(anchor="w")
        # 当前学段下该主题可用词量
        topic_pool = [w for w in WORDS if w["topic"] == tid]
        if self.current_level != "all":
            topic_pool = [w for w in topic_pool if w.get("level", "primary") == self.current_level]
        sub_text = f"{info['desc']}  ·  可用 {len(topic_pool)} 词"
        lbl2 = ctk.CTkLabel(left, text=sub_text, font=ctk.CTkFont(size=13),
                            text_color=C_SUB)
        lbl2.pack(anchor="w")

        ts = stats["by_topic"].get(tid, {"total": 0, "correct": 0})
        acc = round(ts["correct"] / ts["total"] * 100) if ts["total"] > 0 else 0
        clr_acc = (C_GREEN_DARK if acc >= 70 else (C_ORANGE_DARK if acc >= 40 else C_RED_DARK)) if ts["total"] > 0 else C_MUTED
        lbl3 = ctk.CTkLabel(card, text=f"{acc}%" if ts["total"] > 0 else "—",
                            font=ctk.CTkFont(size=22, weight="bold"),
                            text_color=clr_acc, width=64)
        lbl3.pack(side="right", padx=14)
        for w in (left, lbl1, lbl2, lbl3):
            w.bind("<Button-1>", cb)
            w.configure(cursor="hand2")


# ════════════════════════════════════════════
#  闯关练习页（百词斩风格 · 多题型）
# ════════════════════════════════════════════
class QuizPage(ctk.CTkFrame):
    def __init__(self, master, nav_fn, topic=None, level="all"):
        super().__init__(master, fg_color=C_BG)
        self.navigate = nav_fn
        self.topic = topic or "basic"
        self.level = level or "all"
        self.questions = build_quiz(self.topic, count=5,
                                    level=(None if self.level == "all" else self.level))
        self.idx = 0
        self.score = 0
        self.answered = False

        info = YY_TOPICS.get(self.topic, {})
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(14, 4))
        ctk.CTkLabel(head, text=f"{info.get('icon', '')}  {info.get('name', '闯关')}",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(side="left")
        # 学段徽章
        if self.level != "all" and self.level in LEVELS:
            lv_clr = LEVELS[self.level]["color"]
            ctk.CTkLabel(head, text=LEVELS[self.level]["name"],
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="white", fg_color=lv_clr,
                         corner_radius=10, width=48, height=24
                         ).pack(side="left", padx=8)
        ctk.CTkButton(head, text="返回", width=64, height=32, corner_radius=8,
                      fg_color=C_CARD, hover_color=C_PRIMARY_LIGHT,
                      text_color=C_PRIMARY, border_width=1, border_color=C_BORDER,
                      font=ctk.CTkFont(size=13),
                      command=lambda: self.navigate("home")).pack(side="right")

        self.progress_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13),
                                           text_color=C_SUB)
        self.progress_label.pack(anchor="w", padx=18)

        # 进度条
        self.bar_bg = ctk.CTkFrame(self, fg_color=C_DIVIDER, height=6, corner_radius=3)
        self.bar_bg.pack(fill="x", padx=18, pady=(4, 8))
        self.bar_bg.pack_propagate(False)
        self.bar = ctk.CTkFrame(self.bar_bg, fg_color=C_PRIMARY, corner_radius=3)
        self.bar.place(relx=0, rely=0, relwidth=0.01, relheight=1)

        # 题卡
        self.q_card = _card(self)
        self.q_card.pack(fill="x", padx=16, pady=(0, 8))

        # 题卡顶部：mascot 鼓励语带
        mascot_row = ctk.CTkFrame(self.q_card, fg_color="transparent")
        mascot_row.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(mascot_row, text="🐰", font=ctk.CTkFont(size=26),
                     text_color=C_PRIMARY).pack(side="left")
        ctk.CTkLabel(mascot_row, text="加油哦～ 这道题你一定会的！",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_PRIMARY).pack(side="left", padx=(6, 0))
        ctk.CTkLabel(mascot_row, text="🌸  ⭐  🎀",
                     font=ctk.CTkFont(size=16),
                     text_color=C_PRIMARY).pack(side="right")

        self.mode_badge = ctk.CTkLabel(self.q_card, text="", font=ctk.CTkFont(size=12, weight="bold"),
                                       text_color="white", fg_color=C_PRIMARY,
                                       corner_radius=8, width=88, height=24)
        self.mode_badge.pack(anchor="w", padx=14, pady=(6, 4))
        self.q_label = ctk.CTkLabel(self.q_card, text="", font=ctk.CTkFont(size=26, weight="bold"),
                                    text_color=C_TEXT, wraplength=560, justify="center")
        self.q_label.pack(padx=16, pady=(4, 4))
        self.phon_label = ctk.CTkLabel(self.q_card, text="", font=ctk.CTkFont(size=14),
                                       text_color=C_SUB)
        self.phon_label.pack(padx=16, pady=(0, 6))
        self.speak_btn = ctk.CTkButton(self.q_card, text="🔊  重听", width=120, height=36,
                                        font=ctk.CTkFont(size=15, weight="bold"),
                                        fg_color=C_BLUE, hover_color=C_BLUE_DARK,
                                        corner_radius=10, command=self._speak_current)
        self.diff_label = ctk.CTkLabel(self.q_card, text="", font=ctk.CTkFont(size=12),
                                       text_color=C_MUTED)
        self.diff_label.pack(padx=16, anchor="w")

        # 选项区 / 拼写区
        self.opt_frame = ctk.CTkFrame(self.q_card, fg_color="transparent")
        self.opt_frame.pack(fill="x", padx=12, pady=(8, 14))
        self.opt_buttons = []
        self.spell_entry = None
        self.spell_submit_btn = None
        self.spell_hint_label = None

        # 反馈（评价 / 例句 / 释义）：字号特别加大
        feedback_card = ctk.CTkFrame(self, fg_color="transparent")
        feedback_card.pack(fill="x", padx=18, pady=(0, 4))
        self.feedback_label = ctk.CTkLabel(feedback_card, text="", font=ctk.CTkFont(size=16, weight="bold"),
                                           text_color=C_GREEN, wraplength=600, justify="left")
        self.feedback_label.pack(anchor="w")

        self.next_btn = ctk.CTkButton(self, text="下一题 →", font=ctk.CTkFont(size=16, weight="bold"),
                                      fg_color=C_PRIMARY, hover_color=C_PRIMARY_DARK,
                                      corner_radius=12, height=46, width=160, command=self._next)
        self.next_btn.pack(pady=(4, 10))

        if not self.questions:
            self.q_label.configure(text="该主题暂无单词")
            self.next_btn.configure(state="disabled", text="返回首页",
                                    command=lambda: self.navigate("home"))
        else:
            self._show_question()

    def _show_question(self):
        if self.idx >= len(self.questions):
            self._show_result()
            return
        q = self.questions[self.idx]
        self.answered = False
        self.progress_label.configure(
            text=f"第 {self.idx + 1}/{len(self.questions)} 题  |  得分 {self.score}")
        self.bar.place_configure(relwidth=max(0.01, self.idx / len(self.questions)))

        self.mode_badge.configure(text=MODE_LABEL.get(q["mode"], q["mode"]))
        # 听音辨词时不直接展示英文（避免泄题），其他题型按原 question 显示
        if q["mode"] == "listen":
            self.q_label.configure(text="🎧  听发音，选英文单词")
        else:
            self.q_label.configure(text=q["question"])
        self.phon_label.configure(text=q.get("phonetic", "") or "")
        self.diff_label.configure(text=f"难度：{DIFFICULTY_LABELS.get(q['difficulty'], '')}")
        self.feedback_label.configure(text="")
        self.next_btn.configure(state="disabled")

        # 喇叭按钮：听音模式醒目显示并自动发一次音；其他模式展示英文时也允许重听
        self.speak_btn.pack_forget()
        if q.get("word"):
            if q["mode"] == "listen":
                self.speak_btn.configure(text="🔊  播放发音", fg_color=C_BLUE,
                                          width=160, height=42)
                self.speak_btn.pack(pady=(4, 6))
                self.after(150, lambda w=q["word"]: voice.speak(w))
            elif q["mode"] == "choose_meaning":
                # 题面是英文，提供小喇叭辅助听音
                # spell / choose_word / listen 不在答题前显示，避免泄题
                self.speak_btn.configure(text="🔊  听发音", fg_color=C_BLUE,
                                          width=130, height=36)
                self.speak_btn.pack(pady=(2, 6))

        # 清空选项区
        for b in self.opt_buttons:
            b.destroy()
        self.opt_buttons = []
        if self.spell_entry:
            self.spell_entry.destroy()
            self.spell_entry = None
        if self.spell_submit_btn:
            self.spell_submit_btn.destroy()
            self.spell_submit_btn = None
        if self.spell_hint_label:
            self.spell_hint_label.destroy()
            self.spell_hint_label = None

        if q["mode"] == "spell":
            self._render_spell(q)
        else:
            self._render_options(q)

    def _render_options(self, q):
        # 2×2 网格布局：选项左右两列，字号加大
        self.opt_frame.grid_columnconfigure(0, weight=1, uniform="opt")
        self.opt_frame.grid_columnconfigure(1, weight=1, uniform="opt")
        for i, opt in enumerate(q["options"]):
            btn = ctk.CTkButton(self.opt_frame,
                                text=f"  {chr(65 + i)}.  {opt}",
                                font=ctk.CTkFont(size=16, weight="bold"),
                                fg_color=C_CARD, hover_color=C_PRIMARY_LIGHT,
                                text_color=C_TEXT, border_width=1, border_color=C_BORDER,
                                corner_radius=10, height=52, anchor="w",
                                command=lambda idx=i: self._answer_choice(idx))
            btn.grid(row=i // 2, column=i % 2, sticky="nsew", padx=6, pady=4)
            self.opt_buttons.append(btn)

    def _render_spell(self, q):
        # 拼写模式用单列（不占用 grid 配置，避免与选项二列冲突）
        self.opt_frame.grid_columnconfigure(0, weight=1, uniform="opt")
        self.opt_frame.grid_columnconfigure(1, weight=0, uniform="opt")
        self.spell_hint_label = ctk.CTkLabel(self.opt_frame, text=f"提示：{q['hint']}",
                                              font=ctk.CTkFont(size=16, weight="bold"),
                                              text_color=C_PRIMARY)
        self.spell_hint_label.grid(row=0, column=0, columnspan=2, pady=(4, 8), padx=20, sticky="w")
        self.spell_entry = ctk.CTkEntry(self.opt_frame, height=46, corner_radius=10,
                                         border_color=C_BORDER, font=ctk.CTkFont(size=18),
                                         placeholder_text="在这里输入英文单词...")
        self.spell_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=4)
        self.spell_entry.bind("<Return>", lambda e: self._answer_spell())
        self.spell_entry.focus_set()
        self.spell_submit_btn = ctk.CTkButton(self.opt_frame, text="提交答案",
                                               font=ctk.CTkFont(size=15, weight="bold"),
                                               fg_color=C_PRIMARY, hover_color=C_PRIMARY_DARK,
                                               corner_radius=10, height=40, width=140,
                                               command=self._answer_spell)
        self.spell_submit_btn.grid(row=2, column=0, columnspan=2, pady=8)

    def _speak_current(self):
        if self.idx < len(self.questions):
            word = self.questions[self.idx].get("word")
            if word:
                voice.speak(word)

    def _answer_choice(self, chosen):
        if self.answered:
            return
        self.answered = True
        q = self.questions[self.idx]
        correct = q["answer"]
        is_correct = (chosen == correct)
        if is_correct:
            self.score += 1
            self.opt_buttons[chosen].configure(fg_color=C_GREEN_LIGHT, border_color=C_GREEN)
            msg = random.choice(CORRECT_MSGS) + self._extra_info(q)
            self.feedback_label.configure(text=msg, text_color=C_GREEN)
        else:
            self.opt_buttons[chosen].configure(fg_color=C_RED_LIGHT, border_color=C_RED)
            self.opt_buttons[correct].configure(fg_color=C_GREEN_LIGHT, border_color=C_GREEN)
            answer_text = q["options"][correct]
            msg = (random.choice(WRONG_MSGS)
                   + f"\n正确答案：{chr(65 + correct)}. {answer_text}"
                   + self._extra_info(q))
            self.feedback_label.configure(text=msg, text_color=C_RED)
        record_quiz(q["topic"], q["difficulty"], q["mode"], is_correct, q.get("word"))
        # 答完播报正确单词，强化记忆（无论对错）
        if q.get("word"):
            self.after(200, lambda w=q["word"]: voice.speak(w))
        self.next_btn.configure(state="normal")

    def _answer_spell(self):
        if self.answered or not self.spell_entry:
            return
        q = self.questions[self.idx]
        user_ans = self.spell_entry.get().strip()
        is_correct = user_ans.lower() == q["answer_text"].lower()
        self.answered = True
        self.spell_entry.configure(state="disabled")
        self.spell_submit_btn.configure(state="disabled")
        if is_correct:
            self.score += 1
            self.spell_entry.configure(border_color=C_GREEN, text_color=C_GREEN)
            msg = random.choice(CORRECT_MSGS) + self._extra_info(q)
            self.feedback_label.configure(text=msg, text_color=C_GREEN)
        else:
            self.spell_entry.configure(border_color=C_RED, text_color=C_RED)
            msg = (random.choice(WRONG_MSGS)
                   + f"\n正确拼写：{q['answer_text']}"
                   + self._extra_info(q))
            self.feedback_label.configure(text=msg, text_color=C_RED)
        record_quiz(q["topic"], q["difficulty"], q["mode"], is_correct, q.get("word"))
        if q.get("word"):
            self.after(200, lambda w=q["word"]: voice.speak(w))
        self.next_btn.configure(state="normal")

    def _extra_info(self, q):
        parts = []
        if q.get("example"):
            parts.append(f"\n例句：{q['example']}")
            if q.get("example_zh"):
                parts.append(f" — {q['example_zh']}")
        if q["mode"] == "listen" and q.get("meaning"):
            parts.append(f"\n释义：{q['meaning']}")
        return "".join(parts)

    def _next(self):
        self.idx += 1
        self._show_question()

    def _show_result(self):
        for w in self.q_card.winfo_children():
            w.destroy()
        for b in self.opt_buttons:
            b.destroy()
        self.feedback_label.configure(text="")
        self.next_btn.pack_forget()
        self.bar.place_configure(relwidth=1)
        n = len(self.questions)
        acc = round(self.score / n * 100) if n else 0
        passed = acc >= 60

        ctk.CTkLabel(self.q_card,
                     text=("闯关成功！" if passed else "加油，再来一轮！"),
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=(C_GREEN if passed else C_ORANGE)
                     ).pack(pady=(22, 8))
        ctk.CTkLabel(self.q_card, text=f"得分：{self.score}/{n}  ·  正确率：{acc}%",
                     font=ctk.CTkFont(size=18, weight="bold"), text_color=C_TEXT).pack(pady=(0, 8))
        tip = random.choice(YY_TOPICS.get(self.topic, {}).get("tips", YY_TIPS))
        ctk.CTkLabel(self.q_card, text=f"小贴士：{tip}", font=ctk.CTkFont(size=14),
                     text_color=C_SUB, wraplength=520).pack(padx=20, pady=(4, 18))
        btn_row = ctk.CTkFrame(self.q_card, fg_color="transparent")
        btn_row.pack(pady=(0, 16))
        ctk.CTkButton(btn_row, text="再来一轮", font=ctk.CTkFont(size=16, weight="bold"),
                      fg_color=C_PRIMARY, hover_color=C_PRIMARY_DARK, corner_radius=12,
                      width=140, height=44, command=lambda: self.navigate("quiz", self.topic)
                      ).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="返回首页", font=ctk.CTkFont(size=16),
                      fg_color=C_CARD, hover_color=C_PRIMARY_LIGHT, text_color=C_PRIMARY,
                      border_width=1, border_color=C_PRIMARY, corner_radius=12,
                      width=140, height=44, command=lambda: self.navigate("home")
                      ).pack(side="left", padx=6)


# ════════════════════════════════════════════
#  AI助手页（识别单词主题 + 难度）
# ════════════════════════════════════════════
class AIAnalysisPage(ctk.CTkFrame):
    def __init__(self, master, nav_fn):
        super().__init__(master, fg_color=C_BG)
        self.navigate = nav_fn
        ctk.CTkLabel(self, text="AI 单词智能识别",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(anchor="w", padx=18, pady=(14, 4))
        ctk.CTkLabel(self, text="输入一个英语单词，AI 自动判断它属于哪个主题、难度等级",
                     font=ctk.CTkFont(size=12), text_color=C_SUB
                     ).pack(anchor="w", padx=18, pady=(0, 8))

        form = _card(self)
        form.pack(fill="x", padx=16, pady=(0, 8))
        r1 = ctk.CTkFrame(form, fg_color="transparent")
        r1.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(r1, text="单词:", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C_TEXT, width=60).pack(side="left")
        self.word_entry = ctk.CTkEntry(r1, height=34, corner_radius=8, border_color=C_BORDER,
                                        font=ctk.CTkFont(size=14),
                                        placeholder_text="例如 banana")
        self.word_entry.pack(side="left", fill="x", expand=True)
        self.word_entry.insert(0, "banana")

        r2 = ctk.CTkFrame(form, fg_color="transparent")
        r2.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(r2, text="中文释义:", font=ctk.CTkFont(size=12),
                     text_color=C_TEXT, width=80).pack(side="left")
        self.meaning_entry = ctk.CTkEntry(r2, height=30, corner_radius=8, border_color=C_BORDER,
                                           placeholder_text="可选，如 香蕉")
        self.meaning_entry.pack(side="left", fill="x", expand=True)
        self.meaning_entry.insert(0, "香蕉")

        r3 = ctk.CTkFrame(form, fg_color="transparent")
        r3.pack(fill="x", padx=14, pady=(4, 10))
        ctk.CTkLabel(r3, text="词性:", font=ctk.CTkFont(size=12),
                     text_color=C_TEXT, width=60).pack(side="left")
        self.pos_var = ctk.StringVar(value="名词 n.")
        self.pos_menu = ctk.CTkOptionMenu(
            r3, values=[f"{POS_LABELS[k]} {POS_BADGE[k]}" for k in POS_BADGE],
            variable=self.pos_var, width=140, height=30,
            fg_color=C_CARD, button_color=C_PRIMARY,
            button_hover_color=C_PRIMARY_DARK, text_color=C_TEXT)
        self.pos_menu.pack(side="left", padx=(0, 8))

        ctk.CTkButton(self, text="开始识别", font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=C_PRIMARY, hover_color=C_PRIMARY_DARK, corner_radius=12,
                      height=40, command=self._predict).pack(pady=(2, 10))

        self.result_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.result_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    def _predict(self):
        word = self.word_entry.get().strip()
        meaning = self.meaning_entry.get().strip()
        if not word:
            messagebox.showwarning("提示", "请输入英语单词")
            return
        pos_text = self.pos_var.get()
        pos_key = "n"
        for k, v in POS_BADGE.items():
            if v in pos_text:
                pos_key = k
                break

        word_obj = {"word": word, "meaning": meaning, "pos": pos_key,
                    "phonetic": "", "example": ""}

        for w in self.result_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.result_frame, text="AI 正在识别，请稍候...",
                     font=ctk.CTkFont(size=14), text_color=C_SUB
                     ).pack(pady=40)

        import threading
        threading.Thread(target=self._run_predict,
                         args=(word_obj,), daemon=True).start()

    def _run_predict(self, word_obj):
        try:
            topic = predict_topic(word_obj, WORDS)
            diff = predict_difficulty(word_obj, WORDS)
            analysis = analyze_word_basic(word_obj["word"])
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda: self._render_error(msg))
            return
        self.after(0, lambda: self._render_predict(word_obj, topic, diff, analysis))

    def _render_error(self, msg):
        for w in self.result_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.result_frame, text=f"识别失败：{msg}",
                     font=ctk.CTkFont(size=13), text_color=C_RED,
                     wraplength=480).pack(pady=20, padx=14, anchor="w")

    def _render_predict(self, word_obj, result, diff, analysis):
        for w in self.result_frame.winfo_children():
            w.destroy()
        card = _card(self.result_frame)
        card.pack(fill="x", pady=4)
        info = YY_TOPICS.get(result["topic_id"], {})
        ctk.CTkLabel(card, text=f"{info.get('icon', '')}  这个词属于：{result['topic_name']}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(padx=14, pady=(12, 4), anchor="w")
        ctk.CTkLabel(card, text=f"确定程度：{result['confidence']}%",
                     font=ctk.CTkFont(size=13), text_color=C_GREEN
                     ).pack(padx=14, anchor="w")
        ctk.CTkLabel(card, text="各主题可能性：",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=C_TEXT).pack(padx=14, pady=(8, 2), anchor="w")
        for topic_name, prob in sorted(result["all_proba"].items(), key=lambda x: -x[1]):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=1)
            ctk.CTkLabel(row, text=topic_name, font=ctk.CTkFont(size=11),
                         text_color=C_TEXT, width=80).pack(side="left")
            bar_bg = ctk.CTkFrame(row, fg_color=C_DIVIDER, height=12, corner_radius=6)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(4, 8))
            bar_bg.pack_propagate(False)
            bar = ctk.CTkFrame(bar_bg, fg_color=C_PRIMARY if prob > 10 else C_MUTED,
                               corner_radius=6)
            bar.place(relx=0, rely=0, relwidth=max(prob, 2) / 100, relheight=1)
            ctk.CTkLabel(row, text=f"{prob}%", font=ctk.CTkFont(size=11),
                         text_color=C_SUB, width=45).pack(side="right")
        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()

        # ── 难度识别 ──
        card2 = _card(self.result_frame)
        card2.pack(fill="x", pady=4)
        ctk.CTkLabel(card2, text=f"这个词的难度：{diff['difficulty_name']}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(padx=14, pady=(12, 4), anchor="w")
        ctk.CTkLabel(card2, text=f"确定程度：{diff['confidence']}%",
                     font=ctk.CTkFont(size=13), text_color=C_GREEN
                     ).pack(padx=14, anchor="w")
        diff_row = ctk.CTkFrame(card2, fg_color="transparent")
        diff_row.pack(fill="x", padx=14, pady=(4, 10))
        for dname, dp in diff["all_proba"].items():
            lbl = ctk.CTkFrame(diff_row, fg_color=C_CARD, corner_radius=10,
                               border_width=1, border_color=C_BORDER)
            lbl.pack(side="left", padx=4, pady=2, expand=True, fill="x")
            ctk.CTkLabel(lbl, text=f"{dname}\n{dp}%",
                         font=ctk.CTkFont(size=12), text_color=C_TEXT
                         ).pack(padx=8, pady=6)

        # ── 构词分析 ──
        card3 = _card(self.result_frame)
        card3.pack(fill="x", pady=4)
        ctk.CTkLabel(card3, text="单词构词分析",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_BLUE).pack(padx=14, pady=(12, 4), anchor="w")
        info_text = (f"长度 {analysis['length']} 字母  ·  "
                     f"元音 {analysis['vowels']}  ·  "
                     f"辅音 {analysis['consonants']}  ·  "
                     f"音节估计 {analysis['syllables']} 个")
        ctk.CTkLabel(card3, text=info_text, font=ctk.CTkFont(size=12),
                     text_color=C_TEXT).pack(padx=14, anchor="w", pady=(2, 4))
        for f in analysis["features"]:
            ctk.CTkLabel(card3, text=f"  · {f}", font=ctk.CTkFont(size=11),
                         text_color=C_SUB).pack(padx=14, anchor="w")
        ctk.CTkFrame(card3, fg_color="transparent", height=10).pack()


# ════════════════════════════════════════════
#  句型分析页（SVM）
# ════════════════════════════════════════════
class SentencePage(ctk.CTkFrame):
    def __init__(self, master, nav_fn):
        super().__init__(master, fg_color=C_BG)
        self.navigate = nav_fn
        # 标题区带 mascot 装饰
        sent_head = ctk.CTkFrame(self, fg_color="transparent")
        sent_head.pack(fill="x", padx=18, pady=(14, 4))
        ctk.CTkLabel(sent_head, text="🦊", font=ctk.CTkFont(size=28),
                     text_color=C_PRIMARY).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(sent_head, text="英语句型分析",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(side="left")
        ctk.CTkLabel(sent_head, text="🌸  🐰  ⭐",
                     font=ctk.CTkFont(size=20),
                     text_color=C_PRIMARY).pack(side="right")
        ctk.CTkLabel(self, text="输入一句英语，AI 自动识别它属于哪种句型",
                     font=ctk.CTkFont(size=13), text_color=C_SUB
                     ).pack(anchor="w", padx=18, pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=(0, 6))

        # 上层：自动模式 + 手动模式 左右两列
        two_col = ctk.CTkFrame(scroll, fg_color="transparent")
        two_col.pack(fill="x", padx=14, pady=(0, 8))
        two_col.grid_columnconfigure(0, weight=1, uniform="sent")
        two_col.grid_columnconfigure(1, weight=1, uniform="sent")

        # ── 自动模式（左）──上色：淡蓝底 + 蓝描边
        auto_card = _card(two_col, fg_color=C_BLUE_LIGHT, border_color=C_BLUE)
        auto_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
        ctk.CTkLabel(auto_card, text="自动模式（推荐）",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C_BLUE).pack(padx=14, pady=(12, 4), anchor="w")
        ctk.CTkLabel(auto_card, text="直接输入一句英语，系统自动提取特征",
                     font=ctk.CTkFont(size=12), text_color=C_SUB
                     ).pack(padx=14, anchor="w")
        self.sent_entry = ctk.CTkEntry(auto_card, height=38, corner_radius=8,
                                        border_color=C_BORDER, font=ctk.CTkFont(size=15),
                                        placeholder_text="例如 Where is my book?")
        self.sent_entry.pack(fill="x", padx=14, pady=8)
        self.sent_entry.insert(0, "Where is my book?")
        ctk.CTkButton(auto_card, text="自动识别", font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=C_BLUE, hover_color=C_BLUE_DARK, corner_radius=10,
                      height=38, width=140,
                      command=self._auto_predict).pack(padx=14, pady=(0, 14), anchor="w")

        # ── 手动模式（右）──上色：淡紫底 + 紫描边
        form = _card(two_col, fg_color=C_PURPLE_LIGHT, border_color=C_PURPLE)
        form.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)
        ctk.CTkLabel(form, text="手动模式（自定义 8 特征）",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C_PURPLE).pack(padx=14, pady=(12, 4), anchor="w")
        fields = [
            ("单词数", "5"),
            ("是否含问号 (0/1)", "1"),
            ("是否含感叹号 (0/1)", "0"),
            ("是否含 be 动词 (0/1)", "1"),
            ("是否含助动词 do/does/did/will (0/1)", "0"),
            ("是否含情态动词 can/may/must (0/1)", "0"),
            ("是否含否定词 not/never (0/1)", "0"),
            ("是否以 WH 词开头 what/where (0/1)", "1"),
        ]
        self.entries = []
        for label, default in fields:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=13),
                         text_color=C_TEXT, width=220, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, font=ctk.CTkFont(size=13), height=32,
                                 corner_radius=8, border_color=C_BORDER, width=70)
            entry.pack(side="right", padx=(6, 0))
            entry.insert(0, default)
            self.entries.append(entry)
        ctk.CTkButton(form, text="手动识别", font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=C_PURPLE, hover_color=C_PURPLE_DARK, corner_radius=10,
                      height=38, width=140, command=self._manual_predict
                      ).pack(padx=14, pady=(8, 14), anchor="w")

        # 下层：识别结果 / 解释区（后面起到越宽越好，现在上面两列后顶部留出更多位置）
        self.result_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.result_frame.pack(fill="x", padx=16, pady=(0, 12))

    def _auto_predict(self):
        text = self.sent_entry.get().strip()
        if not text:
            messagebox.showwarning("提示", "请输入英语句子")
            return
        feats = auto_extract_sentence_features(text)
        self._render_result(feats, src_text=text)

    def _manual_predict(self):
        try:
            vals = [float(e.get()) for e in self.entries]
        except ValueError:
            messagebox.showwarning("提示", "请输入有效数字")
            return
        self._render_result(tuple(vals), src_text=None)

    def _render_result(self, feats, src_text=None):
        for w in self.result_frame.winfo_children():
            w.destroy()
        result = predict_sentence_type(*feats, SENTENCE_TRAIN_DATA, SENTENCE_LABELS)
        card = _card(self.result_frame)
        card.pack(fill="x", pady=4)
        if src_text:
            ctk.CTkLabel(card, text=f"原句：{src_text}", font=ctk.CTkFont(size=12),
                         text_color=C_SUB, wraplength=480
                         ).pack(padx=14, pady=(10, 2), anchor="w")
        ctk.CTkLabel(card, text=f"这是一个：{result['sentence_type']}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(padx=14, pady=(8, 4), anchor="w")
        ctk.CTkLabel(card, text=f"确定程度：{result['confidence']}%",
                     font=ctk.CTkFont(size=13), text_color=C_GREEN
                     ).pack(padx=14, anchor="w")
        if result["top3"]:
            ctk.CTkLabel(card, text="最可能的句型：",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=C_TEXT).pack(padx=14, pady=(8, 2), anchor="w")
            for name, prob in result["top3"]:
                ctk.CTkLabel(card, text=f"  · {name}  {prob}%",
                             font=ctk.CTkFont(size=12), text_color=C_SUB
                             ).pack(padx=14, anchor="w")
        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()


# ════════════════════════════════════════════
#  英语工具箱页
# ════════════════════════════════════════════
class ToolPage(ctk.CTkFrame):
    def __init__(self, master, nav_fn):
        super().__init__(master, fg_color=C_BG)
        self.navigate = nav_fn
        ctk.CTkLabel(self, text="英语工具箱",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(anchor="w", padx=18, pady=(14, 4))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(4, 6))

        # ── 年级 → 词汇量 ──
        sec1 = _card(scroll)
        sec1.pack(fill="x", padx=4, pady=6)
        ctk.CTkLabel(sec1, text="年级 → 推荐词汇量",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_PURPLE).pack(padx=14, pady=(10, 2), anchor="w")
        r1 = ctk.CTkFrame(sec1, fg_color="transparent")
        r1.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(r1, text="年级 (1-6):", font=ctk.CTkFont(size=12),
                     text_color=C_TEXT).pack(side="left")
        self.grade_entry = ctk.CTkEntry(r1, width=80, height=30, corner_radius=8,
                                         border_color=C_BORDER)
        self.grade_entry.pack(side="left", padx=6)
        self.grade_entry.insert(0, "4")
        ctk.CTkButton(r1, text="查一查", width=70, height=30, corner_radius=8,
                      fg_color=C_PURPLE, hover_color=C_PURPLE_DARK,
                      command=self._predict_vocab).pack(side="left", padx=4)
        self.vocab_result = ctk.CTkLabel(sec1, text="", font=ctk.CTkFont(size=12),
                                         text_color=C_SUB, wraplength=480, justify="left")
        self.vocab_result.pack(padx=14, pady=(2, 10), anchor="w")

        # ── 单词构词分析 ──
        sec2 = _card(scroll)
        sec2.pack(fill="x", padx=4, pady=6)
        ctk.CTkLabel(sec2, text="单词构词分析",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_BLUE).pack(padx=14, pady=(10, 2), anchor="w")
        r2 = ctk.CTkFrame(sec2, fg_color="transparent")
        r2.pack(fill="x", padx=14, pady=4)
        self.word_entry = ctk.CTkEntry(r2, height=30, corner_radius=8,
                                        border_color=C_BORDER,
                                        placeholder_text="输入英语单词...")
        self.word_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.word_entry.insert(0, "running")
        ctk.CTkButton(r2, text="分析", width=60, height=30, corner_radius=8,
                      fg_color=C_BLUE, hover_color=C_BLUE_DARK,
                      command=self._analyze_word).pack(side="left", padx=4)
        self.word_result = ctk.CTkLabel(sec2, text="", font=ctk.CTkFont(size=12),
                                         text_color=C_SUB, wraplength=480, justify="left")
        self.word_result.pack(padx=14, pady=(2, 10), anchor="w")

        # ── 文本字数/句数统计 ──
        sec3 = _card(scroll)
        sec3.pack(fill="x", padx=4, pady=6)
        ctk.CTkLabel(sec3, text="英语文本统计",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_GREEN).pack(padx=14, pady=(10, 2), anchor="w")
        self.count_box = ctk.CTkTextbox(sec3, height=70, font=ctk.CTkFont(size=12),
                                         border_width=1, border_color=C_BORDER, corner_radius=8)
        self.count_box.pack(fill="x", padx=14, pady=4)
        self.count_box.insert("0.0", "Hello! How are you today? I am fine, thank you.")
        ctk.CTkButton(sec3, text="统计", width=80, height=30, corner_radius=8,
                      fg_color=C_GREEN, hover_color=C_GREEN_DARK,
                      command=self._count).pack(padx=14, pady=(2, 4), anchor="w")
        self.count_result = ctk.CTkLabel(sec3, text="", font=ctk.CTkFont(size=12),
                                          text_color=C_SUB, wraplength=480)
        self.count_result.pack(padx=14, pady=(0, 10), anchor="w")

        # ── 单词速查（从词库中查） ──
        sec4 = _card(scroll)
        sec4.pack(fill="x", padx=4, pady=6)
        ctk.CTkLabel(sec4, text="词库速查",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_ORANGE).pack(padx=14, pady=(10, 2), anchor="w")
        r4 = ctk.CTkFrame(sec4, fg_color="transparent")
        r4.pack(fill="x", padx=14, pady=4)
        self.lookup_entry = ctk.CTkEntry(r4, height=30, corner_radius=8,
                                          border_color=C_BORDER,
                                          placeholder_text="输入英文单词或中文释义...")
        self.lookup_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.lookup_entry.insert(0, "apple")
        ctk.CTkButton(r4, text="查询", width=60, height=30, corner_radius=8,
                      fg_color=C_ORANGE, hover_color=C_ORANGE_DARK,
                      command=self._lookup).pack(side="left", padx=4)
        self.lookup_result = ctk.CTkLabel(sec4, text="", font=ctk.CTkFont(size=12),
                                           text_color=C_SUB, wraplength=480, justify="left")
        self.lookup_result.pack(padx=14, pady=(2, 10), anchor="w")

    def _predict_vocab(self):
        try:
            grade = float(self.grade_entry.get())
        except ValueError:
            messagebox.showwarning("提示", "请输入有效年级（1-6）")
            return
        r = predict_vocab_by_grade(grade, GRADE_VOCAB)
        self.vocab_result.configure(
            text=f"{int(grade)}年级建议英语词汇量约 {r['predicted_vocab']} 个单词\n"
                 f"模型公式：{r['formula']}（R²={r['r_squared']}）")

    def _analyze_word(self):
        word = self.word_entry.get().strip()
        if not word:
            messagebox.showwarning("提示", "请输入英语单词")
            return
        a = analyze_word_basic(word)
        feat_text = "、".join(a["features"]) if a["features"] else "无特殊构词"
        self.word_result.configure(
            text=f"长度 {a['length']} 字母  ·  元音 {a['vowels']}  ·  "
                 f"辅音 {a['consonants']}  ·  音节估计 {a['syllables']}\n"
                 f"构词特征：{feat_text}")

    def _count(self):
        text = self.count_box.get("0.0", "end").strip()
        if not text:
            messagebox.showwarning("提示", "请输入文本")
            return
        r = count_letters(text)
        self.count_result.configure(
            text=f"字母 {r['letters']}  ·  数字 {r['digits']}  ·  "
                 f"单词 {r['words']}  ·  句子 {r['sentences']}  ·  "
                 f"总字符 {r['total_chars']}")

    def _lookup(self):
        kw = self.lookup_entry.get().strip().lower()
        if not kw:
            messagebox.showwarning("提示", "请输入查询词")
            return
        all_words = WORDS + load_custom_words()
        results = [w for w in all_words
                   if kw in w["word"].lower() or kw in w["meaning"]]
        if not results:
            self.lookup_result.configure(text="未找到匹配的单词")
            return
        lines = []
        for w in results[:8]:
            tname = YY_TOPICS.get(w["topic"], {}).get("name", w["topic"])
            d = DIFFICULTY_LABELS.get(w["difficulty"], "")
            pos = POS_BADGE.get(w["pos"], w["pos"])
            lines.append(f"  · {w['word']} {pos} {w.get('phonetic', '')} —— {w['meaning']}"
                         f"  [{tname}/{d}]")
        more = f"\n（共 {len(results)} 条，仅显示前 8 条）" if len(results) > 8 else ""
        self.lookup_result.configure(text="\n".join(lines) + more)


# ════════════════════════════════════════════
#  词库管理页 — 浏览全词库 + 搜索 + 分页 + 自定义增删
# ════════════════════════════════════════════
class WordManagePage(ctk.CTkFrame):
    TOPIC_KEYS = list(YY_TOPICS.keys())
    TOPIC_NAMES = [YY_TOPICS[k]["name"] for k in TOPIC_KEYS]
    LEVEL_LABEL = {"primary": "小学", "middle": "初中", "high": "高中"}
    DIFF_MAP = {1: "基础", 2: "进阶", 3: "拓展"}
    POS_KEYS = list(POS_BADGE.keys())
    POS_NAMES = [f"{POS_LABELS[k]} {POS_BADGE[k]}" for k in POS_KEYS]
    PAGE_SIZE = 30

    def __init__(self, master, nav_fn):
        super().__init__(master, fg_color=C_BG)
        self.navigate = nav_fn
        self.page = 0
        self.add_collapsed = True

        # 标题区
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(14, 4))
        ctk.CTkLabel(head, text="词库管理",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(side="left")
        self.toggle_add_btn = ctk.CTkButton(head, text="＋ 添加自定义单词",
                                             width=130, height=32, corner_radius=10,
                                             fg_color=C_GREEN, hover_color=C_GREEN_DARK,
                                             font=ctk.CTkFont(size=12, weight="bold"),
                                             command=self._toggle_add)
        self.toggle_add_btn.pack(side="right")
        self.summary_lbl = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(size=12),
                                         text_color=C_SUB)
        self.summary_lbl.pack(anchor="w", padx=18, pady=(0, 6))

        # ── 添加区（默认折叠）──
        self.add_card = _card(self)
        self._build_add_card(self.add_card)

        # ── 搜索 / 筛选条 ──
        filter_card = _card(self)
        filter_card.pack(fill="x", padx=16, pady=(2, 6))
        fr = ctk.CTkFrame(filter_card, fg_color="transparent")
        fr.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(fr, text="🔍", font=ctk.CTkFont(size=14),
                     text_color=C_PRIMARY).pack(side="left", padx=(2, 4))
        self.search_entry = ctk.CTkEntry(fr, height=32, corner_radius=8,
                                          border_color=C_BORDER,
                                          placeholder_text="输入英文或中文搜索…")
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_filter_change())

        self.level_var = ctk.StringVar(value="全部学段")
        ctk.CTkOptionMenu(fr, values=["全部学段", "小学", "初中", "高中"],
                          variable=self.level_var, width=100, height=30,
                          fg_color=C_CARD, button_color=C_PRIMARY,
                          button_hover_color=C_PRIMARY_DARK, text_color=C_TEXT,
                          command=lambda _: self._on_filter_change()
                          ).pack(side="left", padx=(8, 4))

        self.topic_filter_var = ctk.StringVar(value="全部主题")
        ctk.CTkOptionMenu(fr, values=["全部主题"] + self.TOPIC_NAMES,
                          variable=self.topic_filter_var, width=110, height=30,
                          fg_color=C_CARD, button_color=C_PRIMARY,
                          button_hover_color=C_PRIMARY_DARK, text_color=C_TEXT,
                          command=lambda _: self._on_filter_change()
                          ).pack(side="left", padx=4)

        ctk.CTkButton(fr, text="清除", width=56, height=30, corner_radius=8,
                      fg_color=C_MUTED, hover_color=C_SUB,
                      command=self._clear_filter).pack(side="left", padx=(6, 0))

        # ── 词条列表 ──
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        # ── 分页栏 ──
        self.page_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.page_bar.pack(fill="x", padx=18, pady=(0, 8))
        self.prev_btn = ctk.CTkButton(self.page_bar, text="◀ 上一页", width=80, height=30,
                                       corner_radius=8, fg_color=C_PRIMARY,
                                       hover_color=C_PRIMARY_DARK,
                                       font=ctk.CTkFont(size=12),
                                       command=lambda: self._go_page(-1))
        self.prev_btn.pack(side="left")
        self.page_lbl = ctk.CTkLabel(self.page_bar, text="",
                                      font=ctk.CTkFont(size=12, weight="bold"),
                                      text_color=C_TEXT)
        self.page_lbl.pack(side="left", expand=True)
        self.next_btn = ctk.CTkButton(self.page_bar, text="下一页 ▶", width=80, height=30,
                                       corner_radius=8, fg_color=C_PRIMARY,
                                       hover_color=C_PRIMARY_DARK,
                                       font=ctk.CTkFont(size=12),
                                       command=lambda: self._go_page(1))
        self.next_btn.pack(side="right")

        self._refresh_list()

    # ─────────── 添加区构建 ───────────
    def _build_add_card(self, parent):
        ctk.CTkLabel(parent, text="添加新单词（自定义词进入闯关 / AI 识别）",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=C_GREEN).pack(padx=14, pady=(10, 4), anchor="w")

        def _row(lbl, ph, attr):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(row, text=lbl, font=ctk.CTkFont(size=12),
                         text_color=C_TEXT, width=70).pack(side="left")
            ent = ctk.CTkEntry(row, height=30, corner_radius=8,
                                border_color=C_BORDER, placeholder_text=ph)
            ent.pack(side="left", fill="x", expand=True)
            setattr(self, attr, ent)

        _row("单词:", "English word", "word_entry")
        _row("中文释义:", "如 苹果", "meaning_entry")
        _row("音标:", "如 /'æpl/", "phon_entry")

        row4 = ctk.CTkFrame(parent, fg_color="transparent")
        row4.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(row4, text="词性:", font=ctk.CTkFont(size=12),
                     text_color=C_TEXT).pack(side="left")
        self.pos_var = ctk.StringVar(value=self.POS_NAMES[0])
        ctk.CTkOptionMenu(row4, values=self.POS_NAMES, variable=self.pos_var,
                          width=120, height=28, fg_color=C_CARD,
                          button_color=C_PRIMARY, button_hover_color=C_PRIMARY_DARK,
                          text_color=C_TEXT).pack(side="left", padx=(4, 8))
        ctk.CTkLabel(row4, text="主题:", font=ctk.CTkFont(size=12),
                     text_color=C_TEXT).pack(side="left")
        self.topic_var = ctk.StringVar(value=self.TOPIC_NAMES[0])
        ctk.CTkOptionMenu(row4, values=self.TOPIC_NAMES, variable=self.topic_var,
                          width=100, height=28, fg_color=C_CARD,
                          button_color=C_PRIMARY, button_hover_color=C_PRIMARY_DARK,
                          text_color=C_TEXT).pack(side="left", padx=(4, 8))
        ctk.CTkLabel(row4, text="难度:", font=ctk.CTkFont(size=12),
                     text_color=C_TEXT).pack(side="left")
        self.diff_var = ctk.StringVar(value="基础")
        ctk.CTkOptionMenu(row4, values=["基础", "进阶", "拓展"], variable=self.diff_var,
                          width=78, height=28, fg_color=C_CARD,
                          button_color=C_PRIMARY, button_hover_color=C_PRIMARY_DARK,
                          text_color=C_TEXT).pack(side="left", padx=(4, 0))

        _row("例句:", "可选，英文例句", "example_entry")
        _row("例句翻译:", "可选，例句中文翻译", "example_zh_entry")

        ctk.CTkButton(parent, text="添加单词", font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color=C_GREEN, hover_color=C_GREEN_DARK, corner_radius=10,
                      height=34, command=self._add).pack(padx=14, pady=(8, 12), anchor="w")

    def _toggle_add(self):
        self.add_collapsed = not self.add_collapsed
        if self.add_collapsed:
            self.add_card.pack_forget()
            self.toggle_add_btn.configure(text="＋ 添加自定义单词")
        else:
            self.add_card.pack(fill="x", padx=16, pady=(0, 6),
                               before=self.list_frame.master if False else None)
            # 重新挂载到正确位置
            self.add_card.pack_forget()
            self.add_card.pack(fill="x", padx=16, pady=(0, 6))
            self.toggle_add_btn.configure(text="收起添加面板")

    # ─────────── 添加 / 删除 ───────────
    def _add(self):
        word = self.word_entry.get().strip()
        meaning = self.meaning_entry.get().strip()
        phon = self.phon_entry.get().strip()
        if not word:
            messagebox.showwarning("提示", "请输入英语单词")
            return
        if not meaning:
            messagebox.showwarning("提示", "请输入中文释义")
            return
        pos_text = self.pos_var.get()
        pos_key = self.POS_KEYS[self.POS_NAMES.index(pos_text)]
        topic_key = self.TOPIC_KEYS[self.TOPIC_NAMES.index(self.topic_var.get())]
        diff_val = {"基础": 1, "进阶": 2, "拓展": 3}.get(self.diff_var.get(), 1)
        example = self.example_entry.get().strip()
        example_zh = self.example_zh_entry.get().strip()

        add_custom_word(word, meaning, phon, pos_key, topic_key, diff_val,
                        example, example_zh)
        messagebox.showinfo("成功", "单词已添加！")
        for ent in (self.word_entry, self.meaning_entry, self.phon_entry,
                    self.example_entry, self.example_zh_entry):
            ent.delete(0, "end")
        self.page = 0
        self._refresh_list()

    def _delete_custom(self, custom_idx):
        if messagebox.askyesno("确认", "确定要删除这个自定义单词吗？"):
            delete_custom_word(custom_idx)
            self._refresh_list()

    # ─────────── 筛选 / 分页 ───────────
    def _clear_filter(self):
        self.search_entry.delete(0, "end")
        self.level_var.set("全部学段")
        self.topic_filter_var.set("全部主题")
        self._on_filter_change()

    def _on_filter_change(self):
        self.page = 0
        self._refresh_list()

    def _go_page(self, delta):
        self.page += delta
        self._refresh_list()

    def _filtered_words(self):
        kw = self.search_entry.get().strip().lower()
        level_label = self.level_var.get()
        topic_label = self.topic_filter_var.get()

        target_level = None
        for k, v in self.LEVEL_LABEL.items():
            if v == level_label:
                target_level = k
                break

        target_topic = None
        if topic_label != "全部主题":
            for k, name in zip(self.TOPIC_KEYS, self.TOPIC_NAMES):
                if name == topic_label:
                    target_topic = k
                    break

        customs = load_custom_words()
        # 标记自定义词在 customs 中的索引，便于删除按钮回找
        all_entries = []
        for i, w in enumerate(customs):
            all_entries.append(("custom", i, w))
        for w in WORDS:
            all_entries.append(("builtin", -1, w))

        def _match(w):
            if target_level and w.get("level") != target_level:
                return False
            if target_topic and w.get("topic") != target_topic:
                return False
            if kw:
                hay = (w.get("word", "") + " " + w.get("meaning", "")).lower()
                if kw not in hay:
                    return False
            return True

        return [e for e in all_entries if _match(e[2])]

    def _refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        entries = self._filtered_words()
        total = len(entries)
        if total == 0:
            ctk.CTkLabel(self.list_frame, text="未找到匹配的单词，换个关键字试试～",
                         font=ctk.CTkFont(size=13), text_color=C_MUTED
                         ).pack(pady=30)
            self.summary_lbl.configure(text="共 0 条")
            self.page_lbl.configure(text="0 / 0 页")
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")
            return

        max_page = (total - 1) // self.PAGE_SIZE
        if self.page < 0:
            self.page = 0
        if self.page > max_page:
            self.page = max_page

        start = self.page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, total)
        page_entries = entries[start:end]

        for src, custom_idx, w in page_entries:
            card = _card(self.list_frame)
            card.pack(fill="x", pady=2)
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=12, pady=6)

            tname = YY_TOPICS.get(w["topic"], {}).get("name", w.get("topic", ""))
            lname = self.LEVEL_LABEL.get(w.get("level", ""), "")
            dname = self.DIFF_MAP.get(w.get("difficulty", 1), "")
            pos = POS_BADGE.get(w.get("pos", "n"), "")

            tag = "  ⭐自定义" if src == "custom" else ""
            ctk.CTkLabel(left,
                         text=f"{w['word']}  {pos}  {w.get('phonetic', '')}{tag}",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C_TEXT).pack(anchor="w")
            meta = f"释义：{w['meaning']}"
            if lname or tname or dname:
                meta += f"   |   {lname}·{tname}·{dname}"
            ctk.CTkLabel(left, text=meta, font=ctk.CTkFont(size=11),
                         text_color=C_SUB, wraplength=440, justify="left"
                         ).pack(anchor="w")
            if w.get("example"):
                ctk.CTkLabel(left, text=f"例：{w['example']}",
                             font=ctk.CTkFont(size=11), text_color=C_MUTED,
                             wraplength=440, justify="left").pack(anchor="w")

            if src == "custom":
                ctk.CTkButton(card, text="删除", width=50, height=28, corner_radius=8,
                              fg_color=C_RED, hover_color=C_RED_DARK, text_color="white",
                              font=ctk.CTkFont(size=11),
                              command=lambda idx=custom_idx: self._delete_custom(idx)
                              ).pack(side="right", padx=10)

        self.summary_lbl.configure(
            text=f"共 {total} 条匹配（词库 {len(WORDS)} 词 + 自定义 {len(load_custom_words())} 词）")
        self.page_lbl.configure(text=f"第 {self.page + 1} / {max_page + 1} 页")
        self.prev_btn.configure(state="normal" if self.page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.page < max_page else "disabled")


# ════════════════════════════════════════════
#  学习统计页
# ════════════════════════════════════════════
class StatsPage(ctk.CTkFrame):
    def __init__(self, master, nav_fn):
        super().__init__(master, fg_color=C_BG)
        self.navigate = nav_fn
        stats = get_stats()
        ctk.CTkLabel(self, text="学习统计",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(anchor="w", padx=18, pady=(14, 8))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # 总览卡
        summary = _card(scroll, fg_color=C_PRIMARY_LIGHT, border_color=C_PRIMARY)
        summary.pack(fill="x", padx=4, pady=(0, 10))
        si = ctk.CTkFrame(summary, fg_color="transparent")
        si.pack(fill="x", padx=14, pady=12)
        items = [
            ("已答题", stats["total"], C_PRIMARY),
            ("正确数", stats["correct"], C_GREEN),
            ("正确率", f"{stats['accuracy']}%", C_ORANGE),
            ("已掌握", stats["mastered_words"], C_PURPLE),
        ]
        for label, val, clr in items:
            col = ctk.CTkFrame(si, fg_color="transparent")
            col.pack(side="left", expand=True)
            ctk.CTkLabel(col, text=str(val), font=ctk.CTkFont(size=24, weight="bold"),
                         text_color=clr).pack()
            ctk.CTkLabel(col, text=label, font=ctk.CTkFont(size=11),
                         text_color=C_SUB).pack()

        # 题型统计
        if stats.get("by_mode"):
            ctk.CTkLabel(scroll, text="各题型表现",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C_TEXT).pack(anchor="w", padx=4, pady=(4, 6))
            mode_card = _card(scroll)
            mode_card.pack(fill="x", padx=4, pady=(0, 10))
            for mode_key, ms in stats["by_mode"].items():
                acc = round(ms["correct"] / ms["total"] * 100) if ms["total"] > 0 else 0
                row = ctk.CTkFrame(mode_card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=6)
                ctk.CTkLabel(row, text=MODE_LABEL.get(mode_key, mode_key),
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=C_TEXT, width=90).pack(side="left")
                bar_bg = ctk.CTkFrame(row, fg_color=C_DIVIDER, height=12, corner_radius=6)
                bar_bg.pack(side="left", fill="x", expand=True, padx=8)
                bar_bg.pack_propagate(False)
                clr = C_GREEN if acc >= 70 else (C_ORANGE if acc >= 40 else C_RED)
                bar = ctk.CTkFrame(bar_bg, fg_color=clr, corner_radius=6)
                bar.place(relx=0, rely=0, relwidth=max(acc, 3) / 100, relheight=1)
                ctk.CTkLabel(row, text=f"{ms['total']}题 {acc}%",
                             font=ctk.CTkFont(size=11), text_color=C_SUB,
                             width=80).pack(side="right")

        # 主题统计
        ctk.CTkLabel(scroll, text="各主题掌握情况",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_TEXT).pack(anchor="w", padx=4, pady=(4, 6))
        for tid, info in YY_TOPICS.items():
            ts = stats["by_topic"].get(tid, {"total": 0, "correct": 0})
            acc = round(ts["correct"] / ts["total"] * 100) if ts["total"] > 0 else 0
            card = _card(scroll)
            card.pack(fill="x", padx=4, pady=3)
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=8)
            ctk.CTkLabel(row, text=f"{info['icon']}  {info['name']}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=C_TEXT, width=130).pack(side="left")
            bar_bg = ctk.CTkFrame(row, fg_color=C_DIVIDER, height=14, corner_radius=7)
            bar_bg.pack(side="left", fill="x", expand=True, padx=8)
            bar_bg.pack_propagate(False)
            clr = (C_GREEN if acc >= 70 else (C_ORANGE if acc >= 40 else C_RED)) if ts["total"] > 0 else C_MUTED
            bar = ctk.CTkFrame(bar_bg, fg_color=clr, corner_radius=7)
            bar.place(relx=0, rely=0, relwidth=max(acc, 3) / 100, relheight=1)
            ctk.CTkLabel(row, text=f"{ts['total']}题 {acc}%",
                         font=ctk.CTkFont(size=11), text_color=C_SUB,
                         width=70).pack(side="right")

        # 薄弱主题提示
        if stats["by_topic"]:
            worst = min(
                stats["by_topic"].items(),
                key=lambda x: x[1]["correct"] / x[1]["total"] if x[1]["total"] > 0 else 999)
            if worst[1]["total"] > 0:
                wn = YY_TOPICS.get(worst[0], {}).get("name", worst[0])
                tip_card = _card(scroll, fg_color=C_RED_LIGHT, border_color=C_RED)
                tip_card.pack(fill="x", padx=4, pady=8)
                ctk.CTkLabel(tip_card, text=f"薄弱主题：{wn}，建议多加练习！",
                             font=ctk.CTkFont(size=12), text_color=C_RED,
                             wraplength=460).pack(padx=14, pady=10)


# ════════════════════════════════════════════
#  关于/模型信息页
# ════════════════════════════════════════════
class ModelInfoPage(ctk.CTkFrame):
    def __init__(self, master, nav_fn):
        super().__init__(master, fg_color=C_BG)
        self.navigate = nav_fn
        ctk.CTkLabel(self, text="关于本系统",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(anchor="w", padx=18, pady=(14, 8))
        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=16)
        self.loading_label = ctk.CTkLabel(self.content_frame, text="正在加载系统信息，请稍候...",
                                           font=ctk.CTkFont(size=14), text_color=C_SUB)
        self.loading_label.pack(pady=40)
        import threading
        threading.Thread(target=self._load_info, daemon=True).start()

    def _load_info(self):
        try:
            info = get_all_model_info(WORDS, SENTENCE_TRAIN_DATA, GRADE_VOCAB)
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda: self._render_error(msg))
            return
        self.after(0, lambda: self._render(info))

    def _render_error(self, msg):
        if not self.winfo_exists():
            return
        try:
            self.loading_label.destroy()
        except Exception:
            pass
        ctk.CTkLabel(self.content_frame,
                     text=f"系统信息加载失败：\n{msg}\n\n请在终端执行 `python build_models.py` 重新生成模型 pkl。",
                     font=ctk.CTkFont(size=13), text_color=C_RED,
                     wraplength=500, justify="left"
                     ).pack(pady=20, padx=14, anchor="w")

    def _render(self, info):
        if not self.winfo_exists():
            return
        self.loading_label.destroy()

        intro = _card(self.content_frame, fg_color=C_PRIMARY_LIGHT, border_color=C_PRIMARY)
        intro.pack(fill="x", pady=6)
        ctk.CTkLabel(intro, text="词途 · AI 英语单词学习闯关系统",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(padx=14, pady=(12, 2), anchor="w")
        ctk.CTkLabel(intro,
                     text="覆盖小学/初中/高中 · 5 个机器学习模型 · 8 大主题词库 · 4 种百词斩式题型",
                     font=ctk.CTkFont(size=12),
                     text_color=C_PRIMARY_DARK).pack(padx=14, pady=(0, 12), anchor="w")

        colors = [C_BLUE, C_PRIMARY, C_PURPLE, C_ORANGE, C_PINK]
        icons = ["①", "②", "③", "④", "⑤"]
        for i, m in enumerate(info["models"]):
            card = _card(self.content_frame)
            card.pack(fill="x", pady=6)
            clr = colors[i % len(colors)]
            ctk.CTkLabel(card, text=f"{icons[i % len(icons)]}  {m['name']}",
                         font=ctk.CTkFont(size=15, weight="bold"),
                         text_color=clr).pack(padx=14, pady=(12, 2), anchor="w")
            items = [
                ("算法", m["algorithm"]),
                ("框架", m["library"]),
                ("特征数", m["features"]),
                ("说明", m["description"]),
            ]
            if "accuracy" in m:
                items.append(("准确率", f"{m['accuracy']}%"))
            if "r_squared" in m:
                items.append(("R²", m["r_squared"]))
            for k, v in items:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=14, pady=1)
                ctk.CTkLabel(row, text=f"{k}：", font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=C_TEXT, width=60).pack(side="left")
                ctk.CTkLabel(row, text=str(v), font=ctk.CTkFont(size=12),
                             text_color=C_SUB, wraplength=440, justify="left"
                             ).pack(side="left", anchor="w")
            ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

        # 预训练说明卡片（代替原“重新训练”按钮）
        note = _card(self.content_frame, fg_color=C_PRIMARY_LIGHT, border_color=C_PRIMARY)
        note.pack(fill="x", pady=10)
        ctk.CTkLabel(note, text="模型预训练说明",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C_PRIMARY_DARK).pack(padx=14, pady=(10, 4), anchor="w")
        ctk.CTkLabel(note,
                     text=("5 个 AI 模型均由开发者预训练并内置于发行包中，用户启动即可直接使用。\n"
                           "词库已覆盖小学 / 初中 / 高中 课标全量词汇，自定义词会进入闯关但不会触发重训。"),
                     font=ctk.CTkFont(size=11), text_color=C_SUB,
                     wraplength=460, justify="left"
                     ).pack(padx=14, pady=(0, 12), anchor="w")


# ════════════════════════════════════════════
#  主应用
# ════════════════════════════════════════════
class YingyuApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("词途 · AI 英语单词学习闯关系统")
        self.minsize(720, 560)
        self.after(50, lambda: self.state("zoomed"))
        self.configure(fg_color=C_BG)
        self.container = ctk.CTkFrame(self, fg_color=C_BG)
        self.container.pack(fill="both", expand=True)
        self.nav_bar = None
        self.current_page = None
        self.current_nav = None
        self.current_level = "all"   # 全学段 / primary / middle / high
        self._show_splash()

    def set_level(self, level):
        if level in ("all", "primary", "middle", "high"):
            self.current_level = level

    def _show_splash(self):
        self.splash = SplashPage(self.container, self._enter_app)
        self.splash.pack(fill="both", expand=True)

    def _enter_app(self):
        self.splash.destroy()
        self._build_nav()
        self.navigate("home")

    def _build_nav(self):
        self.nav_bar = ctk.CTkFrame(self.container, fg_color=C_CARD, height=56,
                                     corner_radius=0, border_width=1, border_color=C_BORDER)
        self.nav_bar.pack(side="bottom", fill="x")
        self.nav_bar.pack_propagate(False)
        self.nav_buttons = {}
        tabs = [
            ("home", "首页"),
            ("quiz", "闯关"),
            ("ai", "AI 助手"),
            ("sentence", "句型"),
            ("tool", "工具箱"),
            ("manage", "词库"),
            ("stats", "统计"),
            ("models", "关于"),
        ]
        for key, label in tabs:
            btn = ctk.CTkButton(
                self.nav_bar, text=label,
                font=ctk.CTkFont(size=12), fg_color="transparent",
                hover_color=C_PRIMARY_LIGHT, text_color=C_SUB,
                corner_radius=8, width=70, height=50,
                command=lambda k=key: self.navigate(k),
            )
            btn.pack(side="left", expand=True, padx=2, pady=3)
            self.nav_buttons[key] = btn

    def navigate(self, page, topic=None):
        if self.current_page:
            self.current_page.destroy()
        if self.current_nav and self.current_nav in self.nav_buttons:
            self.nav_buttons[self.current_nav].configure(
                fg_color="transparent", text_color=C_SUB)
        # quiz 页可能从首页进入并带 topic，也可从导航直接进入
        nav_key = page if page in self.nav_buttons else "home"
        self.current_nav = nav_key
        if nav_key in self.nav_buttons:
            self.nav_buttons[nav_key].configure(
                fg_color=C_PRIMARY_LIGHT, text_color=C_PRIMARY)

        if page == "home":
            self.current_page = HomePage(self.container, self.navigate,
                                         current_level=self.current_level,
                                         set_level_fn=self.set_level)
        elif page == "quiz":
            self.current_page = QuizPage(self.container, self.navigate, topic,
                                         level=self.current_level)
        elif page == "ai":
            self.current_page = AIAnalysisPage(self.container, self.navigate)
        elif page == "sentence":
            self.current_page = SentencePage(self.container, self.navigate)
        elif page == "tool":
            self.current_page = ToolPage(self.container, self.navigate)
        elif page == "manage":
            self.current_page = WordManagePage(self.container, self.navigate)
        elif page == "stats":
            self.current_page = StatsPage(self.container, self.navigate)
        elif page == "models":
            self.current_page = ModelInfoPage(self.container, self.navigate)
        else:
            self.current_page = HomePage(self.container, self.navigate)
        self.current_page.pack(fill="both", expand=True, before=self.nav_bar)
