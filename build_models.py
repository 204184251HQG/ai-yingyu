"""build_models.py — 开发者一键预训练脚本

把 5 个 scikit-learn 模型预训练好并落盘为 yy_*.pkl，随软件分发给客户。
客户启动应用时直接 joblib.load，无需任何训练等待。

用法：
    python build_models.py            # 全部重新预训练
    python build_models.py --check    # 只校验现有 pkl 能否加载（不重训）

预训练完成后的 5 个 pkl：
    yy_topic_rf.pkl       — 单词主题分类（RandomForest, 400 棵树）
    yy_sentence_svm.pkl   — 英语句型分类（SVM-RBF, 8 维特征）
    yy_grade_poly.pkl     — 年级→词汇量回归（Polynomial Ridge）
    yy_diff_gb.pkl        — 单词难度预测（GradientBoosting, 400 轮）
    yy_ensemble_gb.pkl    — 综合主题分类（GradientBoosting, 300 轮）
"""
import argparse
import sys
import time
from pathlib import Path


def _load_data():
    """惰性加载：导入 yingyu_data 触发词库 JSON 加载。"""
    import yingyu_data as d
    return d


def _train_all(d):
    """依次训练 5 个模型，返回 list[(name, metric, elapsed_seconds)]。"""
    from ai_model import (
        train_topic_model,
        train_sentence_model,
        train_grade_model,
        train_diff_model,
        train_ensemble_model,
    )

    print(f"加载词库：{len(d.WORDS)} 词（small/middle/high 共 3 学段）")
    print(f"句型训练样本：{len(d.SENTENCE_TRAIN_DATA)} 条")
    print(f"年级回归数据：{len(d.GRADE_VOCAB)} 条")
    print()

    plan = [
        ("主题分类 (RandomForest)", lambda: train_topic_model(d.WORDS), "acc"),
        ("句型识别 (SVM-RBF)", lambda: train_sentence_model(d.SENTENCE_TRAIN_DATA), "acc"),
        ("年级回归 (Polynomial Ridge)", lambda: train_grade_model(d.GRADE_VOCAB), "R²"),
        ("难度预测 (GradientBoosting)", lambda: train_diff_model(d.WORDS), "acc"),
        ("集成主题 (GradientBoosting)", lambda: train_ensemble_model(d.WORDS), "acc"),
    ]

    results = []
    total_t0 = time.perf_counter()
    for name, fn, metric_name in plan:
        t0 = time.perf_counter()
        print(f"[{len(results) + 1}/{len(plan)}] 训练 {name} ...", flush=True)
        _, metric = fn()
        elapsed = time.perf_counter() - t0
        if metric_name == "acc":
            print(f"      → 准确率 {metric}%   耗时 {elapsed:.1f}s")
        else:
            print(f"      → R² {metric}     耗时 {elapsed:.1f}s")
        results.append((name, metric, elapsed))
    print(f"\n全部预训练完成，总耗时 {time.perf_counter() - total_t0:.1f}s\n")
    return results


def _verify_pkls():
    """加载 5 个 pkl，确认 strict-load 成功。"""
    from ai_model import (
        load_topic_model, load_sentence_model, load_grade_model,
        load_diff_model, load_ensemble_model,
    )
    d = _load_data()

    checks = [
        ("yy_topic_rf.pkl", lambda: load_topic_model(d.WORDS)),
        ("yy_sentence_svm.pkl", lambda: load_sentence_model(d.SENTENCE_TRAIN_DATA)),
        ("yy_grade_poly.pkl", lambda: load_grade_model(d.GRADE_VOCAB)),
        ("yy_diff_gb.pkl", lambda: load_diff_model(d.WORDS)),
        ("yy_ensemble_gb.pkl", lambda: load_ensemble_model(d.WORDS)),
    ]
    ok = True
    for name, fn in checks:
        try:
            _, metric = fn()
            print(f"  [OK] {name}  → {metric}")
        except Exception as e:
            ok = False
            print(f"  [FAIL] {name}  → {e}")
    return ok


def main():
    ap = argparse.ArgumentParser(description="预训练 5 个 AI 模型并落盘 pkl")
    ap.add_argument("--check", action="store_true",
                    help="只校验现有 pkl 能否加载（不重训）")
    args = ap.parse_args()

    here = Path(__file__).parent
    print(f"工作目录：{here}\n")

    if args.check:
        print("== 校验 5 个 pkl ==")
        ok = _verify_pkls()
        sys.exit(0 if ok else 1)

    print("== 预训练 5 个模型 ==")
    d = _load_data()
    results = _train_all(d)

    print("== 校验 pkl 可被严格加载 ==")
    ok = _verify_pkls()
    if not ok:
        print("\n[ERROR] 部分 pkl 加载失败，请检查上面的报错")
        sys.exit(1)

    print("\n== 训练精度汇总 ==")
    for name, metric, elapsed in results:
        unit = "%" if isinstance(metric, (int, float)) and metric > 1 else ""
        print(f"  {name:<32s} {metric}{unit}    ({elapsed:.1f}s)")

    print("\nBUILD_OK — 5 个 pkl 已落盘，可以打包分发。")


if __name__ == "__main__":
    main()
