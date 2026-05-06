# 词途 · AI 英语单词学习闯关系统

> 覆盖小学 / 初中 / 高中 · 百词斩式闯关 · AI 智能诊断

## 项目简介

「词途 · AI 英语单词学习闯关系统」是一款面向 K-12 全学段学生的英语词汇 AI 学习工具，覆盖小学、初中、高中三大学段，将 Python 编程与英语学科深度融合。系统收录 **8 大主题、3 大学段共 4997 个英语单词**（小学 714 + 初中 1496 + 高中 2787，覆盖课标全量词汇），集成 **百词斩式闯关、AI 单词识别、句型分析、学习记录统计** 四大功能，支持按学段筛选词量、按主题/学段/关键字快速搜索词库，帮助同学们在 AI 辅助下高效记忆单词、掌握句型。**5 个 AI 模型由开发者预训练并内置于发行包，用户启动即用、零联网、零账号、双击即用。**

## 功能特色

### 📖 多学段主题词库（4997 词，课标全量）
- 收录 **4997 个英语单词**，按学段分档：小学 **714** 词 / 初中 **1496** 词 / 高中 **2787** 词
- 覆盖 8 大主题：基础词汇、学校生活、自然世界、食物饮食、家庭朋友、数字时间、颜色形状、动作情感
- 首页一键切换「全学段 / 小学 / 初中 / 高中」，闯关题目自动按学段抽词
- 每个单词配有音标、词性、难度、英文例句与中文翻译
- **词库管理页支持搜索 + 学段/主题筛选 + 分页浏览**（每页 30 词，共约 167 页）
- 教师可在词库管理页添加自定义单词，自定义词自动进入闯关与 AI 识别（不会触发重训）

### 🎯 百词斩式闯关
- 四种题型：**看词选义**（英→中）、**看义选词**（中→英）、**听音辨词**（音标→单词）、**拼写练习**（首字母提示，键入英文）
- 每关随机抽 5 个单词，每词随机派一种题型，**听说读写四角度全覆盖**
- 答对按钮变绿、答错变红并高亮正确答案，附带英文例句即时学习
- 实时计分、进度条、闯关结算页

### 🤖 AI 智能识别
- 使用 5 个 scikit-learn 模型在本地完成多维度诊断（**全部由开发者预训练并以 `yy_*.pkl` 形式内置**）：
  - **RandomForest（300 棵树·max_depth=18·24 维特征）** 单词主题分类  ·  准确率 **54.4%**（8 类，相对随机基线 12.5% 提升 4.4×）
  - **SVM-RBF（8 维特征，含 `has_not` / `starts_wh` 判别位）** 英语句型识别（陈述/一般疑问/特殊疑问/感叹/祈使/否定）·  准确率 **97.1%**
  - **Polynomial Ridge** 年级→词汇量预测  ·  **R²=0.992**
  - **GradientBoosting（41 维特征，含学段强特征）** 单词难度预测  ·  准确率 **99.8%**
  - **Ensemble GradientBoosting（300 轮）** 综合主题分类  ·  准确率 **54.5%**
- 输入任意英文单词，自动判断主题、难度、构词特征（音节数、silent-e、复杂辅音簇等）
- 输入任意英文句子，识别句型类型并显示概率分布

### 📊 学习记录
- 自动保存所有答题历史
- 按题型/主题统计正确率，识别"已掌握"单词
- 教师可查看班级薄弱主题，数据驱动备课

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 编程语言 |
| CustomTkinter | 现代化 GUI 界面（清新蓝绿配色 #0d9488） |
| scikit-learn | 5 个本地 AI 模型（RF / SVM / GBDT / Ridge） |
| NumPy | 数值计算与特征工程 |
| joblib | AI 模型持久化 |
| python-pptx | 演示 PPT 自动生成 |

## 项目结构

```
ai-yingyu/
├── main.py                  # 主入口
├── app_gui.py               # GUI 界面（封面 + 8 个功能页 + 关于）
├── ai_model.py              # 5 个 AI 模型 + 英语小工具（严格读取 pkl）
├── yingyu_data.py           # 单词加载 + 题目派生 + 学习记录
├── build_models.py          # 开发者用：一键预训练 5 个模型并落盘 pkl
├── data/                    # 全量词库（按学段拆分）
│   ├── primary.json         # 小学 714 词
│   ├── middle.json          # 初中 1496 词
│   └── high.json            # 高中 2787 词
├── requirements.txt         # 依赖列表
├── yy_topic_model.pkl       # 主题分类（RF，约 94 MB）
├── yy_sentence_model.pkl    # 句型识别（SVM）
├── yy_grade_model.pkl       # 年级回归（Ridge）
├── yy_diff_model.pkl        # 难度预测（GBDT）
├── yy_ensemble_model.pkl    # 综合主题（GBDT）
├── yingyu_records.json      # 学习记录（运行时生成）
├── yingyu_custom_words.json # 自定义词库（运行时生成）
└── docs/                    # 案例提交三件套
    ├── 附件1_案例信息表.md
    ├── 附件2_开发与应用报告.md
    ├── 附件3_演示视频脚本与PPT大纲.md
    ├── generate_ppt.py
    └── 词途_演示PPT.pptx
```

## 快速开始

### 用户使用（已含预训练模型）

```bash
pip install -r requirements.txt
python main.py
```

5 个 `yy_*.pkl` 已经随发行包提供，启动后立即可用，**无需训练、无需联网、无需账号**。

### 开发者重训（仅当修改词库 / 模型代码后需要）

```bash
python build_models.py
```

会读取 `data/` 下三份词库（共 4997 词），按学段规模自适应数据增强（5000 词时 augment=3，约 2 万样本），重训 5 个模型并覆盖落盘 `yy_*.pkl`。整体耗时约 25 分钟（GBDT 是瓶颈）。

## AI 算法说明

本系统使用 **5 个轻量级 scikit-learn 模型** 在本地完成英语词汇的多维度智能分析：

1. **特征提取**：从每个单词中提取 24 维基础特征（长度、元音数、辅音数、是否首字母元音、连字符、释义长度、8 个主题关键词命中数、5 种词性 one-hot），难度模型补充 17 维语音/形态/学段特征（音节数、双字母、silent-e、th/sh/ch 组合、复杂辅音簇、词性难度系数、学段映射 0/1/2）；句型模型采用 8 维特征（单词数、`?`、`!`、be/aux/modal 命中、`has_not`、`starts_wh`）；
2. **自适应数据增强**：根据词库规模自动调整 augment 倍数（4997 词 × 3 = 约 2 万样本，避免训练耗时爆炸）；句型训练数据每类 30 条，AUG 后 1600+ 样本；
3. **多模型训练**：分别训练主题分类（RF 300 棵树·max_depth=18）、句型识别（SVM-RBF）、年级词汇量回归（Polynomial Ridge degree=2）、难度预测（GBDT 400 轮）、集成主题分类（GBDT 300 轮）；
4. **预测输出**：对任意单词/句子毫秒级返回各类别概率分布与综合诊断。

> 4997 词训练的真实精度：主题 **54.4%**（8 类，随机 12.5% 基线 4.4× 提升） / 句型 **97.1%** / 年级 R² **0.992** / 难度 **99.8%** / 综合 **54.5%**。
>
> 主题分类精度大幅低于难度/句型，是因为 5000 词级真实词汇语义边界天然模糊（如 *run* 同时属于「动作情感」和「学校生活」），而 24 维语形特征本身对主题区分度有限——这正反映了真实词汇分类的客观难度，区别于早期 200 词玩具数据集上的过拟合假象。

## 主题词库覆盖

8 大主题 × 3 个学段共 **4997 词**，分布如下：

| 学段 | 词量 | 代表词样本 |
|------|:---:|------|
| 小学（primary） | 714 | hello / apple / school / red / family / play / morning / sunny … |
| 初中（middle） | 1496 | discover / cuisine / nutrient / curriculum / ancestor / decade / hexagonal / contemplate … |
| 高中（high） | 2787 | inevitable / quintessential / photosynthesis / philanthropy / rectitude / millennium / spectrum / disseminate … |
| **合计** | **4997** | 覆盖 K-12 课标全量词汇 |

> 词库以 JSON 形式存放在 `data/{primary,middle,high}.json`，可独立维护、扩充和审校。

## 重新生成演示 PPT

```bash
python docs/generate_ppt.py
```

输出 `docs/词途_演示PPT.pptx`（9 页 16:9 高清）。

## 打包发布

打包前请先运行 `python build_models.py` 确保 `yy_*.pkl` 已落盘并可被严格加载。

```bash
python -m PyInstaller --onefile --windowed --name "词途AI英语单词学习闯关系统" \
    --add-data "yy_topic_model.pkl;." \
    --add-data "yy_sentence_model.pkl;." \
    --add-data "yy_grade_model.pkl;." \
    --add-data "yy_diff_model.pkl;." \
    --add-data "yy_ensemble_model.pkl;." \
    --add-data "data;data" \
    main.py
```

生成的单文件 EXE 约 **150 MB**（含 5 个 pkl + 词库 JSON + Python 运行时），双击即用。

## 致谢与 AI 标注

- 词库初稿、特征工程方案、代码骨架由 **DeepSeek-V3 / 通义千问 / Claude** 协助生成，最终代码与文案均经作者人工校对修订；
- 演示视频解说由作者本人录制，**未使用 AI 语音合成**；
- 演示中 AI 模型识别画面已加 "AI 生成" 水印，符合《生成式人工智能服务管理暂行办法》。
