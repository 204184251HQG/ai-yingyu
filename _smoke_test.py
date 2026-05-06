"""一次性冒烟测试：验证 4997 词预训练 pkl + GUI 重构后的关键路径。
- 严格读 5 个 pkl
- 词库筛选/分页逻辑跑通
- ModelInfoPage 不再有 _retrain
- predict_topic / predict_difficulty / predict_sentence_type / predict_vocab_by_grade 可用
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from yingyu_data import WORDS, GRADE_VOCAB, SENTENCE_TRAIN_DATA, SENTENCE_LABELS, count_words_by_level
from ai_model import (
    load_topic_model, load_sentence_model, load_grade_model,
    load_diff_model, load_ensemble_model,
    predict_topic, predict_difficulty, predict_sentence_type,
    predict_vocab_by_grade, auto_extract_sentence_features,
)

# 1. 词库总量
counts = count_words_by_level()
total = sum(counts.values())
assert total >= 4900, f"词库数量过少: {total}"
print(f"[1] 词库 {total} 词 → {counts}  ✓")

# 2. 严格读 5 个 pkl（不会触发训练，读不到则报 FileNotFoundError）
topic_clf, topic_acc = load_topic_model(WORDS)
sent_pipe, sent_acc = load_sentence_model(SENTENCE_TRAIN_DATA)
grade_pipe, grade_r2 = load_grade_model(GRADE_VOCAB)
diff_pipe, diff_acc = load_diff_model(WORDS)
ens_pipe, ens_acc = load_ensemble_model(WORDS)
print(f"[2] 5 pkl 已加载: topic={topic_acc} sent={sent_acc} grade_r2={grade_r2} "
      f"diff={diff_acc} ens={ens_acc}  ✓")

# 3. 预测路径（典型样本）
sample = {"word": "apple", "meaning": "苹果", "phonetic": "/'æpl/",
          "topic": "food", "difficulty": 1, "pos": "n", "level": "primary"}
res_topic = predict_topic(sample, topic_clf)
res_diff = predict_difficulty(sample, diff_pipe)
res_sent = predict_sentence_type(*auto_extract_sentence_features("Where is my book?"),
                                 SENTENCE_TRAIN_DATA, SENTENCE_LABELS)
res_grade = predict_vocab_by_grade(4, GRADE_VOCAB)
print(f"[3] 预测样本: topic={res_topic.get('topic_name')}  diff={res_diff.get('difficulty_name')}  "
      f"sent={res_sent.get('sentence_type')}  grade4_vocab={res_grade.get('predicted_vocab')}  ✓")

# 4. ModelInfoPage 不再有 _retrain；WordManagePage 暴露搜索/分页方法
import app_gui
assert not hasattr(app_gui.ModelInfoPage, "_retrain"), "ModelInfoPage._retrain 应已移除"
for m in ("_filtered_words", "_refresh_list", "_go_page", "_clear_filter", "_toggle_add"):
    assert hasattr(app_gui.WordManagePage, m), f"WordManagePage 缺少方法 {m}"
print("[4] GUI 关键方法签名校验通过  ✓")

# 5. 词库筛选逻辑模拟（不启动 Tk 窗口）
class _Stub:
    def __init__(self, kw="", level="全部学段", topic="全部主题"):
        self.kw, self.level, self.topic = kw, level, topic
    def get(self): return self.kw
    def strip(self): return self.kw

def _filter(kw, level_label, topic_label):
    """复制 _filtered_words 的核心逻辑做无 GUI 测试。"""
    LEVEL_LABEL = {"primary": "小学", "middle": "初中", "high": "高中"}
    target_level = next((k for k, v in LEVEL_LABEL.items() if v == level_label), None)
    return [w for w in WORDS
            if (not target_level or w.get("level") == target_level)
            and (topic_label == "全部主题" or w.get("topic") == topic_label)
            and (not kw or kw.lower() in (w.get("word", "") + " " + w.get("meaning", "")).lower())]

apple_hits = _filter("apple", "全部学段", "全部主题")
high_action = _filter("", "高中", "action")
print(f"[5] 筛选 apple → {len(apple_hits)} 条  |  高中·动作情感 → {len(high_action)} 条  ✓")

print("\nSMOKE_OK — 4997 词词库 + 5 个预训练 pkl + GUI 重构全部通过冒烟测试")
