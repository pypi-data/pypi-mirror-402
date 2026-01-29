# rulelift - 信用风险规则有效性分析工具

## 项目概述

rulelift 是一个用于信用风险管理中策略规则自动挖掘、有效性分析及监控的 Python 工具包。

- **实时评估监控上线规则的效度**：解决规则拦截样本无标签的问题，借助客户评级分布差异，实时评估逾期率、召回率、精确率、lift 值、相关性、规则间的增益、稳定性等核心指标
- **自动化挖掘高价值的规则**：自动从数据中挖掘有效的风控规则，支持单特征、多特征交叉、决策树、随机森林、XGB、孤立森林等多种规则挖掘方法
- **可视化展示**：直观呈现变量分布、变量效度、规则效果、特征重要性、决策树结构和规则关系
- **成本效益高**：无需分流测试，基于规则命中用户记录即可评估规则效果，降低测试成本

它帮助风控团队评估优化规则的实际效果，识别冗余规则，自动挖掘有效规则，优化策略组合，提高风险控制能力，降低风控成本。

## 📚 目录

- [项目概述](#项目概述)
- [完整的安装使用方法](#完整的安装使用方法)
  - 使用 pip 安装（推荐）
  - [从源码安装](#从源码安装)
  - 离线使用方式（考虑生产环境是无网）
- [快速开始](#快速开始)
  - [1. 基本导入](#1-基本导入)
  - [2. 加载示例数据](#2-加载示例数据)
  - [3. 规则挖掘基础案例](#3-规则挖掘基础案例)
    - [3.1 单特征规则挖掘](#31-单特征规则挖掘)
    - [3.2 多特征交叉规则挖掘](#32-多特征交叉规则挖掘)
    - [3.3 树模型规则挖掘](#33-树模型规则挖掘)
    - [3.4 多特征交叉规则挖掘（包含损失率指标）](#34-多特征交叉规则挖掘包含损失率指标)
  - [4. 规则评估基础案例](#4-规则评估基础案例)
    - [4.1 规则效度评估](#41-规则效度评估)
    - [4.2 规则相关性分析](#42-规则相关性分析)
    - [4.3 策略增益计算](#43-策略增益计算)
  - [5. 变量分析基础案例](#5-变量分析基础案例)
- [核心功能详解](#核心功能详解)
  - [1. 树规则提取（TreeRuleExtractor）](#1-树规则提取treeruleextractor)
  - [2. 单特征规则挖掘（SingleFeatureRuleMiner）](#2-单特征规则挖掘singlefeatureminer）
  - [3. 多特征交叉规则挖掘（MultiFeatureRuleMiner）](#3-多特征交叉规则挖掘multifeaturerulerminer)
  - [4. 变量分析（VariableAnalyzer）](#4-变量分析variableanalyzer)
  - [5. 规则效度分析监控模块（analyze_rules）](#5-规则效度分析监控模块analyze_rules)
  - [6. 策略相关性、增益计算（calculate_strategy_gain）](#6-策略相关性增益计算calculate_strategy_gain)
- [核心指标说明](#核心指标说明)
  - [规则评估指标](#规则评估指标)
  - [变量分析指标](#变量分析指标)
  - [常见问题（FAQ）](#常见问题faq)
  - [版本信息](#版本信息)
  - [更新日志](#更新日志)
  - [许可证](#许可证)
  - [项目地址](#项目地址)
  - [联系方式](#联系方式)
  - [贡献指南](#贡献指南)
## 📦 项目依赖包

### 核心依赖
项目依赖项精简，兼容性良好，仅需要常见的依赖包
| 依赖包 | 版本要求 | 用途 |
|--------|----------|------|
| pandas | >=1.0.0,<2.4.0 | 数据处理和分析 |
| numpy | >=1.18.0,<2.5.0 | 数值计算 |
| scikit-learn | >=0.24.0,<1.9.0 | 机器学习算法 |
| matplotlib | >=3.3.0,<3.11.0 | 基础可视化 |
| seaborn | >=0.11.0,<0.14.0 | 统计可视化 |
| openpyxl | >=3.0.0 | Excel文件读写 |
## 🎯 项目功能概览

rulelift 提供了完整的规则挖掘和评估解决方案，包含以下核心功能模块：

| 功能模块 | 主要功能 | 适用场景 |
|---------|---------|---------|
| **规则挖掘** | 单特征规则挖掘、多特征交叉规则挖掘、树模型规则挖掘 | 从数据中自动挖掘有效的风控规则 |
| **规则评估** | 规则效度评估、规则相关性分析、策略增益计算 | 评估上线规则的实际效果，识别冗余规则 |
| **变量分析** | 变量效度分析、分箱分析、PSI计算 | 识别重要变量，优化特征工程 |
| **可视化** | 规则效果可视化、特征重要性图、决策树结构图 | 直观呈现分析结果，便于决策 |
| **损失率分析** | 损失率计算、损失提升度分析 | 评估规则的实际损失风险 |

### 功能特点

✅ **全面的规则挖掘**：支持5种树模型算法（DT、RF、CHI2、XGB、ISF）
✅ **灵活的评估方式**：支持用户评级评估和目标标签评估
✅ **丰富的指标体系**：包含badrate、lift、precision、recall、F1、loss_rate、loss_lift等30+指标
✅ **业务解释性强**：支持特征趋势配置，避免不符合业务逻辑的规则
✅ **损失率支持**：支持损失率和损失提升度计算，全面评估风险
✅ **可视化完善**：提供热力图、特征重要性图、决策树结构图等多种可视化
✅ **易于使用**：提供简洁的API和详细的示例代码

---

## 完整的安装使用方法

### 使用 pip 安装（推荐）

```bash
pip install rulelift
```

### 从源码安装

```bash
git clone https://github.com/aialgorithm/rulelift.git
cd rulelift
pip install -e .
```

## 离线使用方式（考虑生产环境是无网）

### 方式一：离线安装rulelift及相关依赖

1. **在有网络的环境中下载依赖包**：

```bash
# 下载rulelift及其所有依赖
pip download rulelift -d ./packages/
```

2. **将下载的packages文件夹传输到离线环境**

3. **在离线环境中安装**：

```bash
# 进入packages文件夹
cd ./packages/

# 安装所有依赖包
pip install *.whl --no-index --find-links=.
```

### 方式二：通过源码直接调用

1. **下载源码**：

   * 从GitHub下载源码包：<https://github.com/aialgorithm/rulelift>

2. **将源码包传输到离线环境并解压**
需要手动安装pandas、numpy、scikit-learn、matplotlib、seaborn
3. **在Python代码中添加源码路径并导入**：

```python
import sys
import os

# 添加源码路径到系统路径
sys.path.append('/path/to/rulelift-master')

# 直接导入模块
from rulelift import load_example_data, analyze_rules, TreeRuleExtractor
```

## 快速开始

### 1. 基本导入

```python
from rulelift import (
    load_example_data, preprocess_data,
    SingleFeatureRuleMiner, MultiFeatureRuleMiner, TreeRuleExtractor,
    VariableAnalyzer, analyze_rules, calculate_strategy_gain
)
```

### 2. 加载示例数据

```python
# 加载示例数据
df = load_example_data('feas_target.csv')
```

### 3. 规则挖掘基础案例


#### 树模型规则挖掘

```python
from rulelift import TreeRuleExtractor

# 初始化树规则提取器
tree_miner = TreeRuleExtractor(
    df, 
    target_col='ISBAD', 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],
    algorithm='rf',  # 使用随机森林算法
    max_depth=5,
    n_estimators=10,
    test_size=0.3,
    random_state=42
)

# 训练模型
train_acc, test_acc = tree_miner.train()
print(f"训练集准确率: {train_acc:.4f}")
print(f"测试集准确率: {test_acc:.4f}")

# 提取规则
rules = tree_miner.extract_rules()
print(f"提取的规则数量: {len(rules)}")

# 获取规则DataFrame
rules_df = tree_miner.get_rules_as_dataframe(sort_by_lift=True)
print(rules_df.head())
```

**输出示例**：
```
训练集准确率: 0.8500
测试集准确率: 0.8200
提取的规则数量: 31
         rule_id                                        rule  predicted_class  class_probability  sample_count
0             0  ALI_FQZSCORE <= 535.0000                1            0.6500           120
1             1  BAIDU_FQZSCORE <= 420.0000                1            0.5800            95
2             2  ALI_FQZSCORE <= 535.0000 AND BAIDU_FQZSCORE <= 420.0000  1            0.7200           80
```

### 4. 规则评估基础案例

#### 规则效度评估

```python
from rulelift import analyze_rules

# 加载规则命中数据
hit_rule_df = load_example_data('hit_rule_info.csv')

# 通过用户评级评估规则效度
result_by_rating = analyze_rules(
    hit_rule_df, 
    rule_col='RULE',
    user_id_col='USER_ID',
    user_level_badrate_col='USER_LEVEL_BADRATE',
    hit_date_col='HIT_DATE',
    include_stability=True
)
print(result_by_rating[['RULE', 'actual_lift', 'actual_badrate', 'hit_rate_cv']].head())
```

**输出示例**：
```
         RULE  actual_lift  actual_badrate  hit_rate_cv
0  rule1     2.3456789      0.3456789     0.123456
1  rule2     2.123456      0.234567      0.145678
2  rule3     1.987654      0.123456      0.156789
```

### 5. 变量分析基础案例

```python
from rulelift import VariableAnalyzer

# 初始化变量分析器
var_analyzer = VariableAnalyzer(
    df, 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'], 
    target_col='ISBAD'
)

# 分析所有变量的效度指标
var_metrics = var_analyzer.analyze_all_variables()
print("所有变量效度指标:")
print(var_metrics)

# 分析单个变量的分箱情况
feature = 'ALI_FQZSCORE'
bin_analysis = var_analyzer.analyze_single_variable(feature, n_bins=10)
print(f"\n{feature} 分箱分析:")
print(bin_analysis)
```

**输出示例**：
```
所有变量效度指标:
        variable        iv        ks        auc  missing_rate  single_value_rate  min_value  max_value  median_value  mean_diff  corr_with_target  psi
0  ALI_FQZSCORE  0.456789  0.452345  0.723456      0.012345      0.0456789      0.987654      0.723456      0.012345      0.456789      0.012345
1  BAIDU_FQZSCORE  0.3456789  0.3456789  0.678901      0.023456      0.056789      0.976543      0.678901      0.023456      0.3456789      0.023456

ALI_FQZSCORE 分箱分析:
        bin_range  count  bad_count  good_count  badrate  sample_ratio  cumulative_badrate
0  (514.999, 705.0]    120         78         42   0.6500        0.2400          0.6500
1  (705.0, 745.0]       95         55         40   0.5789        0.1900          0.6150
2  (745.0, 780.0]       80         45         35   0.5625        0.1600          0.5950
```

---

## 核心功能详解

### 1. 树规则提取（TreeRuleExtractor）

TreeRuleExtractor 是一个统一的树模型规则提取类，支持多种算法（DT、RF、CHI2、XGB、ISF）。支持业务解释性配置、支持树复杂度及规则精度配置、支持评估规则全面方面指标badrate、损失率指标等等。

#### 1.1 支持的算法

| 算法 | 说明 | 适用场景 |
|------|------|----------|
| `dt` | 决策树（Decision Tree） | 快速生成规则，适合初步探索 |
| `rf` | 随机森林（Random Forest） | 规则稳定性好，多样性高，适合生产环境 |
| `chi2` | 卡方决策树（Chi-square Decision Tree） | 适合分类特征较多的场景 |
| `xgb` | XGBoost（梯度提升树） | 规则精度高，适合复杂场景 |
| `isf` | 孤立森林（Isolation Forest） | 适合挖掘异常样本的规则 |

#### 1.2 初始化参数详解

```python
from rulelift import TreeRuleExtractor

tree_miner = TreeRuleExtractor(
    df, 
    target_col='ISBAD',           # 目标字段名，默认为'ISBAD'
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],  # 排除的字段名列表
    algorithm='rf',                # 算法类型：'dt'、'rf'、'chi2'、'xgb'、'isf'，默认为'dt'
    
    # 树复杂度配置
    max_depth=5,                  # 决策树最大深度，控制树的复杂度，默认为5
    min_samples_split=10,         # 分裂节点所需的最小样本数，控制规则精度，默认为10
    min_samples_leaf=5,           # 叶子节点的最小样本数，控制规则精度，默认为5
    n_estimators=10,              # 随机森林/XGBoost/孤立森林中树的数量，默认为10
    max_features='sqrt',           # 每棵树分裂时考虑的最大特征数：'sqrt'或'log2'，默认为'sqrt'
    
    # 数据划分配置
    test_size=0.3,                # 测试集比例，默认为0.3
    random_state=42,              # 随机种子，保证结果可复现，默认为42
    
    # 损失率指标配置
    amount_col='AMOUNT',          # 金额字段名，用于计算损失率指标，默认为None
    ovd_bal_col='OVD_BAL',        # 逾期金额字段名，用于计算损失率指标，默认为None
    
    # 业务解释性配置
    feature_trends={              # 特征与目标标签的正负相关性字典，用于避免不符合业务解释性的规则
        'ALI_FQZSCORE': -1,      # 负相关：分数越低，违约概率越高
        'BAIDU_FQZSCORE': -1,    # 负相关：分数越低，违约概率越高
        'NUMBER OF LOAN APPLICATIONS TO PBOC': 1  # 正相关：申请次数越多，违约概率越高
    }
)

# 训练模型
train_acc, test_acc = tree_miner.train()
print(f"训练集准确率: {train_acc:.4f}")
print(f"测试集准确率: {test_acc:.4f}")

# 提取规则
rules = tree_miner.extract_rules()
print(f"提取的规则数量: {len(rules)}")

# 获取规则DataFrame
rules_df = tree_miner.get_rules_as_dataframe(deduplicate=True, sort_by_lift=True)
print(rules_df.head())
```

#### 1.3 特征趋势判断（feature_trends）

规则挖掘中加入业务逻辑判断，`feature_trends` 参数用于配置特征与目标标签的正负相关性，避免不符合业务解释性的规则。

**参数说明**：
- `feature_trends`: Dict[str, int]，键为特征名，值为 1（正相关）或 -1（负相关），仅挖掘符合特征业务逻辑的规则
  - **正相关（值为1）**：表示特征数值越大，目标标签（违约概率）越高，如多头申请次数
  - **负相关（值为-1）**：特征数值越小，目标标签（违约概率）越高，如信用评分

**使用示例**：

```python
# 使用特征趋势过滤
tree_miner = TreeRuleExtractor(
    df, 
    target_col='ISBAD', 
    exclude_cols=['ID', 'CREATE_TIME'],
    algorithm='rf',
    feature_trends={
        'ALI_FQZSCORE': -1,      # 负相关：分数越低，违约概率越高
        'BAIDU_FQZSCORE': -1,    # 负相关：分数越低，违约概率越高
        'NUMBER OF LOAN APPLICATIONS TO PBOC': 1  # 正相关：申请次数越多，违约概率越高
    }
)

# 提取规则（会自动过滤不符合业务解释性的规则）
rules = tree_miner.extract_rules()
```

**效果示例**：

不使用 `feature_trends`：
```
Rule 1: BAIDU_FQZSCORE > 327.0000  # 该拦截规则，可能不符合业务解释性
Rule 2: NUMBER OF LOAN APPLICATIONS TO PBOC <= 5.0000  # 该拦截规则，可能不符合业务解释性
```

使用 `feature_trends`：
```
Rule 1: BAIDU_FQZSCORE <= 535.0000  # 负相关 
Rule 2: NUMBER OF LOAN APPLICATIONS TO PBOC > 2.0000  # 正相关 
```

#### 1.5 训练模型

```python
# 训练模型
train_acc, test_acc = tree_miner.train()
print(f"训练集准确率: {train_acc:.4f}")
print(f"测试集准确率: {test_acc:.4f}")
```

**返回值说明**：
- 对于 DT、RF、CHI2、XGB 算法：返回 `(train_acc, test_acc)`，分别为训练集和测试集的准确率
- 对于 ISF 算法：返回 `(mean_score, std_score)`，分别为平均异常分数和标准差

#### 1.6 提取规则

```python
# 提取规则
rules = tree_miner.extract_rules()
print(f"提取的规则数量: {len(rules)}")

# 获取规则DataFrame
rules_df = tree_miner.get_rules_as_dataframe(deduplicate=True, sort_by_lift=True)
print(rules_df.head())
```

**参数说明**：
- `deduplicate`: bool，是否去重，默认为False
- `sort_by_lift`: bool，是否按lift倒序排序，默认为False

#### 1.7 规则评估

TreeRuleExtractor 提供了全面的规则评估功能，支持训练集和测试集的效度评估。

**评估指标**：
- **训练集指标**：训练集上的准确率、召回率、精确率、F1分数、lift值、命中率、badrate降低幅度
- **测试集指标**：测试集上的准确率、召回率、精确率、F1分数、lift值、命中率、badrate降低幅度
- **损失率指标**（可选）：如果提供了 `amount_col` 和 `ovd_bal_col`，还会计算损失率和损失lift值

**使用示例**：

```python
# 训练模型
train_acc, test_acc = tree_miner.train()
print(f"训练集准确率: {train_acc:.4f}")
print(f"测试集准确率: {test_acc:.4f}")

# 提取规则
rules = tree_miner.extract_rules()

# 评估规则（包含损失率指标）
eval_results = tree_miner.evaluate_rules()
print(f"评估的规则数量: {len(eval_results)}")
print("规则评估结果（前5条）:")
print(eval_results[['rule', 'train_loss_rate', 'train_loss_lift', 'test_loss_rate', 'test_loss_lift', 'train_lift', 'test_lift']].head())
```

**输出示例**：

```
评估的规则数量: 31
规则评估结果（前5条）:
         rule  train_loss_rate  train_loss_lift  test_loss_rate  test_loss_lift  train_lift  test_lift
0  rule_1         0.3456789       2.3456789      0.234567       1.987654  2.123456      1.987654
1  rule_2         0.234567       1.987654      0.123456       1.876543  1.654321      1.876543
2  rule_3         0.123456       1.765432      0.098765       1.765432  1.543210      1.543210
3  rule_4         0.098765       1.654321      0.076543       1.543210  1.432109      1.432109
4  rule_5         0.076543       1.543210      0.065432       1.432109  1.321098      1.321098
```

**评估指标详细说明**：

| 指标 | 说明 | 计算公式 |
|------|------|----------|
| `train_hit_count` | 训练集命中该规则的样本数 | - |
| `train_bad_count` | 训练集命中该规则的坏样本数 | - |
| `train_good_count` | 训练集命中该规则的好样本数 | - |
| `train_badrate` | 训练集命中该规则的坏样本率 | train_bad_count / train_hit_count |
| `train_precision` | 训练集精确率 | train_bad_count / train_hit_count |
| `train_recall` | 训练集召回率 | train_bad_count / total_bad_train |
| `train_f1` | 训练集F1分数 | 2 * (precision * recall) / (precision + recall) |
| `train_lift` | 训练集lift值 | train_badrate / baseline_badrate_train |
| `train_loss_rate` | 训练集损失率 | total_ovd_bal_bad_selected / total_amount_selected |
| `train_loss_lift` | 训练集损失lift值 | train_loss_rate / overall_loss_rate_train |
| `train_hit_rate` | 训练集命中率 | train_hit_count / total_train_samples |
| `train_baseline_badrate` | 训练集基准badrate | total_bad_train / total_train_samples |
| `train_badrate_after_interception` | 训练集拦截后badrate | (total_bad_train - train_bad_count) / (total_train_samples - train_hit_count) |
| `train_badrate_reduction` | 训练集badrate降低幅度 | (baseline_badrate_train - badrate_after_interception_train) / baseline_badrate_train / train_hit_rate |
| `test_hit_count` | 测试集命中该规则的样本数 | - |
| `test_bad_count` | 测试集命中该规则的坏样本数 | - |
| `test_good_count` | 测试集命中该规则的好样本数 | - |
| `test_badrate` | 测试集命中该规则的坏样本率 | test_bad_count / test_hit_count |
| `test_precision` | 测试集精确率 | test_bad_count / test_hit_count |
| `test_recall` | 测试集召回率 | test_bad_count / total_bad_test |
| `test_f1` | 测试集F1分数 | 2 * (precision * recall) / (precision + recall) |
| `test_lift` | 测试集lift值 | test_badrate / baseline_badrate_test |
| `test_loss_rate` | 测试集损失率 | total_ovd_bal_bad_selected / total_amount_selected |
| `test_loss_lift` | 测试集损失lift值 | test_loss_rate / overall_loss_rate_test |
| `test_hit_rate` | 测试集命中率 | test_hit_count / total_test_samples |
| `test_baseline_badrate` | 测试集基准badrate | total_bad_test / total_test_samples |
| `test_badrate_after_interception` | 测试集拦截后badrate | (total_bad_test - test_bad_count) / (total_test_samples - test_hit_count) |
| `test_badrate_reduction` | 测试集badrate降低幅度 | (baseline_badrate_test - badrate_after_interception_test) / baseline_badrate_test / test_hit_rate |
| `badrate_diff` | 训练集和测试集lift的差异 | train_lift - test_lift |
| `true_positive` | 真阳性（TP） | test_bad_count |
| `false_positive` | 假阳性（FP） | test_good_count |
| `true_negative` | 真阴性（TN） | 未命中且为好样本的数量 |
| `false_negative` | 假阴性（FN） | 未命中且为坏样本的数量 |

#### 1.8 不同算法使用示例

##### 1.8.1 决策树（DT）

```python
# 初始化决策树规则提取器
tree_miner_dt = TreeRuleExtractor(
    df, 
    target_col='ISBAD', 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],
    algorithm='dt',
    max_depth=3, 
    min_samples_split=20,
    min_samples_leaf=10,
    random_state=42
)

# 训练模型
train_acc, test_acc = tree_miner_dt.train()
print(f"训练集准确率: {train_acc:.4f}")
print(f"测试集准确率: {test_acc:.4f}")

# 提取规则
dt_rules = tree_miner_dt.extract_rules()
print(f"提取的规则数量: {len(dt_rules)}")

# 评估规则
eval_results = tree_miner_dt.evaluate_rules()
print(eval_results[['rule', 'test_hit_count', 'test_badrate', 'test_lift']].head())
```

##### 1.8.2 随机森林（RF）

```python
# 初始化随机森林规则提取器
tree_miner_rf = TreeRuleExtractor(
    df, 
    target_col='ISBAD', 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],
    algorithm='rf',
    max_depth=3, 
    min_samples_split=20,
    min_samples_leaf=10,
    n_estimators=5,
    max_features='sqrt',
    random_state=42
)

# 训练模型
train_acc, test_acc = tree_miner_rf.train()
print(f"训练集准确率: {train_acc:.4f}")
print(f"测试集准确率: {test_acc:.4f}")

# 提取规则
rf_rules = tree_miner_rf.extract_rules()
print(f"提取的规则数量: {len(rf_rules)}")

# 评估规则
eval_results = tree_miner_rf.evaluate_rules()
print(eval_results[['rule', 'test_hit_count', 'test_badrate', 'test_lift']].head())
```

##### 1.8.3 卡方决策树（CHI2）

```python
# 初始化卡方决策树规则提取器
tree_miner_chi2 = TreeRuleExtractor(
    df, 
    target_col='ISBAD', 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],
    algorithm='chi2',
    max_depth=3, 
    min_samples_split=20,
    min_samples_leaf=10,
    random_state=42
)

# 训练模型
train_acc, test_acc = tree_miner_chi2.train()
print(f"训练集准确率: {train_acc:.4f}")
print(f"测试集准确率: {test_acc:.4f}")

# 提取规则
chi2_rules = tree_miner_chi2.extract_rules()
print(f"提取的规则数量: {len(chi2_rules)}")

# 评估规则
eval_results = tree_miner_chi2.evaluate_rules()
print(eval_results[['rule', 'test_hit_count', 'test_badrate', 'test_lift']].head())
```

##### 1.8.4 XGBoost（XGB）

```python
# 初始化XGBoost规则提取器，使用特征业务解释性判断
tree_miner_xgb = TreeRuleExtractor(
    df, 
    target_col='ISBAD', 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],
    algorithm='xgb',
    max_depth=3,
    min_samples_split=10,
    min_samples_leaf=10,
    n_estimators=10,
    feature_trends={
        'ALI_FQZSCORE': -1,      # 负相关：分数越低，违约概率越高
        'BAIDU_FQZSCORE': -1,    # 负相关：分数越低，违约概率越高
        'NUMBER OF LOAN APPLICATIONS TO PBOC': 1  # 正相关：申请次数越多，违约概率越高
    },
    random_state=42
)

# 训练模型
train_acc, test_acc = tree_miner_xgb.train()
print(f"训练集准确率: {train_acc:.4f}")
print(f"测试集准确率: {test_acc:.4f}")

# 提取规则
xgb_rules = tree_miner_xgb.extract_rules()
print(f"提取的规则数量: {len(xgb_rules)}")

# 评估规则
eval_results = tree_miner_xgb.evaluate_rules()
print(eval_results[['rule', 'test_hit_count', 'test_badrate', 'test_lift']].head())
```

##### 1.8.5 孤立森林（ISF）

```python
# 初始化孤立森林规则提取器，使用特征趋势判断
tree_miner_isf = TreeRuleExtractor(
    df, 
    target_col='ISBAD', 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],
    algorithm='isf',
    n_estimators=10,
    random_state=42,
    feature_trends={
        'ALI_FQZSCORE': -1,      # 负相关：分数越低，违约概率越高
        'BAIDU_FQZSCORE': -1,    # 负相关：分数越低，违约概率越高
        'NUMBER OF LOAN APPLICATIONS TO PBOC': 1  # 正相关：申请次数越多，违约概率越高
    }
)

# 训练模型
mean_score, std_score = tree_miner_isf.train()
print(f"平均异常分数: {mean_score:.4f}")
print(f"标准差: {std_score:.4f}")

# 提取规则
isf_rules = tree_miner_isf.extract_rules()
print(f"提取的异常规则数量: {len(isf_rules)}")

# 打印规则
tree_miner_isf.print_rules(top_n=5)
```

#### 1.9 可视化功能

##### 1.9.1 特征重要性图

```python
# 绘制特征重要性图
tree_miner.plot_feature_importance(save_path='images/tree_feature_importance.png')
```

##### 1.9.2 决策树结构图

```python
# 绘制决策树结构（仅适用于dt、chi2算法）
tree_miner.plot_decision_tree(save_path='images/tree_decision_structure.pdf')
```

##### 1.9.3 规则评估图

```python
# 绘制规则评估图
tree_miner.plot_rule_evaluation(save_path='images/tree_rule_evaluation.png')
```

#### 1.10 打印规则

```python
# 打印Top 5规则
tree_miner.print_rules(top_n=5)
```

---

### 2. 单特征规则挖掘（SingleFeatureRuleMiner）

用于对数据各特征的不同阈值进行效度分布分析。

#### 2.1 初始化参数详解

```python
from rulelift import SingleFeatureRuleMiner

# 初始化单特征规则挖掘器（不使用损失率指标）
sf_miner = SingleFeatureRuleMiner(
    df, 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],
    target_col='ISBAD'
)

# 初始化单特征规则挖掘器（使用损失率指标）
sf_miner_with_loss = SingleFeatureRuleMiner(
    df, 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'],
    target_col='ISBAD',
    amount_col='AMOUNT',      # 金额字段名
    ovd_bal_col='OVD_BAL'      # 逾期金额字段名
)
```

#### 2.2 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `df` | DataFrame | 必填 | 输入的数据集 |
| `exclude_cols` | List[str] | `None` | 排除的字段名列表 |
| `target_col` | str | `'ISBAD'` | 目标字段名 |
| `amount_col` | str | `None` | 金额字段名，用于计算损失率指标 |
| `ovd_bal_col` | str | `None` | 逾期金额字段名，用于计算损失率指标 |

#### 2.3 分析单个特征

```python
# 分析单个特征
feature = 'ALI_FQZSCORE'
metrics_df = sf_miner.calculate_single_feature_metrics(feature, num_bins=20)
print(f"\n=== {feature} 分箱分析 ===")
print(metrics_df.head())

# 获取Top规则
top_rules = sf_miner.get_top_rules(feature=feature, top_n=5, metric='lift', min_samples=10)
print(f"\n=== Top 5规则 ===")
print(top_rules[['rule_description', 'lift', 'badrate', 'selected_samples']])
```

#### 2.4 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `feature` | str | 必填 | 特征名 |
| `num_bins` | int | `20` | 分箱数量 |
| `top_n` | int | `10` | 返回的规则数量 |
| `metric` | str | `'lift'` | 排序指标：'lift'、'badrate'、'loss_rate'、'loss_lift'等 |
| `min_samples` | int | `10` | 最小样本数过滤 |
| `min_lift` | float | `1.1` | 最小lift值过滤 |

#### 2.5 输出示例

```
=== Top 5规则 ===
                           rule_description      lift  badrate  selected_samples
0  ALI_FQZSCORE <= 665.0000  2.174292  0.666667              51
1  ALI_FQZSCORE <= 688.5000  2.087320  0.640000              75
2  ALI_FQZSCORE <= 705.0000  1.993101  0.611111             108
3  ALI_FQZSCORE <= 725.0000  1.928934  0.580000             150
4  ALI_FQZSCORE <= 745.0000  1.867925  0.555556             180
```

#### 2.6 可视化

```python
# 绘制特征指标分布图
plt = sf_miner.plot_feature_metrics(feature, metric='lift')
plt.savefig(f'{feature}_lift_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
```

---

### 3. 多特征交叉规则挖掘（MultiFeatureRuleMiner）

用于生成双特征交叉分析结果，支持自定义分箱阈值、自动分箱、卡方分箱等多种分箱策略。支持损失率指标计算。

#### 3.1 初始化参数详解

```python
from rulelift import MultiFeatureRuleMiner

# 初始化多特征规则挖掘器（不使用损失率指标）
multi_miner = MultiFeatureRuleMiner(df, target_col='ISBAD')

# 初始化多特征规则挖掘器（使用损失率指标）
multi_miner_with_loss = MultiFeatureRuleMiner(
    df, 
    target_col='ISBAD',
    amount_col='AMOUNT',      # 金额字段名
    ovd_bal_col='OVD_BAL'      # 逾期金额字段名
)
```

#### 3.2 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `df` | DataFrame | 必填 | 输入的数据集 |
| `target_col` | str | `'ISBAD'` | 目标字段名 |
| `amount_col` | str | `None` | 金额字段名，用于计算损失率指标 |
| `ovd_bal_col` | str | `None` | 逾期金额字段名，用于计算损失率指标 |

#### 3.3 生成交叉矩阵

```python
feature1 = 'ALI_FQZSCORE'
feature2 = 'BAIDU_FQZSCORE'

# 生成交叉矩阵
cross_matrix = multi_miner.generate_cross_matrix(
    feature1, feature2,
    max_unique_threshold=5,
    custom_bins1=None,
    custom_bins2=None,
    binning_method='quantile'
)

# 查看交叉矩阵
print(cross_matrix.head())
```

#### 3.4 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `feature1` | str | 必填 | 第一个特征名 |
| `feature2` | str | 必填 | 第二个特征名 |
| `max_unique_threshold` | int | `5` | 最大允许的唯一值数量阈值，超过则进行分箱 |
| `custom_bins1` | List[float] | `None` | 第一个特征的自定义分箱阈值 |
| `custom_bins2` | List[float] | `None` | 第二个特征的自定义分箱阈值 |
| `binning_method` | str | `'quantile'` | 分箱方法：'quantile'（等频）或'chi2'（卡方） |

#### 3.5 支持的指标说明

多特征交叉分析支持多种指标，帮助策略人员全面评估特征组合的风险水平和业务价值：

| 指标 | 定义 | 业务意义 |
|------|------|----------|
| `badrate` | 坏样本比例 = 坏样本数 / 总样本数 | 直接反映该特征组合下的风险水平 |
| `count` | 样本数量 | 反映该特征组合的覆盖范围 |
| `bad_count` | 坏样本数量 | 该特征组合下的坏客户数量 |
| `sample_ratio` | 样本占比 = 该组合样本数 / 总样本数 | 反映该特征组合的业务重要性 |
| `lift` | 提升度 = 该组合badrate / 总样本badrate | 反映该特征组合的风险区分能力，值越大效果越好 |
| `loss_rate` | 损失率 = 损失金额 / 总金额 | 反映该特征组合的实际损失程度（需要提供amount_col和ovd_bal_col） |
| `loss_lift` | 损失提升度 = 该组合loss_rate / 总样本loss_rate | 反映该特征组合的损失区分能力（需要提供amount_col和ovd_bal_col） |

#### 3.6 生成交叉矩阵Excel文件

```python
# 生成交叉矩阵Excel文件（方便策略人员根据交叉矩阵制订规则）
cross_matrices = multi_miner.generate_cross_matrices_excel(
    features_list=['ALI_FQZSCORE', 'BAIDU_FQZSCORE'], 
    output_path='cross_analysis.xlsx'
)
print(f"交叉矩阵Excel文件已保存到: cross_analysis.xlsx")

# 查看生成的Excel文件
# 文件包含多个sheet，每个sheet对应一个特征组合
# 每个sheet包含：badrate、count、sample_ratio、lift等指标
```

#### 3.7 多特征两两交叉分析

支持传入多个特征，自动生成所有两两特征组合的交叉矩阵，方便策略人员全面分析特征间的交互关系。

```python
# 多特征两两交叉分析示例
features_list = ['ALI_FQZSCORE', 'BAIDU_FQZSCORE', 'NUMBER OF LOAN APPLICATIONS TO PBOC']
cross_matrices_multi = multi_miner.generate_cross_matrices_excel(
    features_list=features_list,
    output_path='cross_analysis_multi_features.xlsx',
    metrics=['badrate', 'count', 'sample_ratio', 'lift', 'loss_rate', 'loss_lift'],  # 支持多种指标分析
    binning_method='quantile'  # 支持等频分箱
)
print(f"多特征交叉矩阵Excel文件已保存到: cross_analysis_multi_features.xlsx")
```

#### 3.8 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `features_list` | List[str] | 必填 | 特征清单列表，用于多特征两两组合生成矩阵 |
| `feature1` | str | `None` | 第一个特征名（兼容旧版本，当features_list为None时使用） |
| `feature2` | str | `None` | 第二个特征名（兼容旧版本，当features_list为None时使用） |
| `max_unique_threshold` | int | `5` | 最大允许的唯一值数量阈值，超过则进行分箱 |
| `custom_bins1` | List[float] | `None` | 第一个特征的自定义分箱阈值（仅当features_list长度为2时有效） |
| `custom_bins2` | List[float] | `None` | 第二个特征的自定义分箱阈值（仅当features_list长度为2时有效） |
| `binning_method` | str | `'quantile'` | 分箱方法：'quantile'（等频）或'chi2'（卡方） |
| `output_path` | str | `'cross_analysis.xlsx'` | Excel输出路径 |
| `metrics` | List[str] | `['badrate', 'count', 'sample_ratio']` | 要导出的指标列表，可选：'badrate', 'count', 'bad_count', 'sample_ratio', 'lift', 'loss_rate', 'loss_lift' |

#### 3.9 交叉矩阵Excel文件示例

生成的Excel文件包含多个sheet，每个sheet对应一个特征组合，例如：
- `ALI_FQZSCORE_x_BAIDU_FQZSCORE`：两个特征的交叉矩阵
- `ALI_FQZSCORE_x_NUMBER OF LOAN APPLICATIONS TO PBOC`：另一个特征组合
- 每个sheet包含以下指标：badrate、count、sample_ratio、lift等
- 策略人员可以根据交叉矩阵中的高lift区域制订规则

**Excel文件内容示例**：

| ALI_FQZSCORE | BAIDU_FQZSCORE | badrate | count | sample_ratio | lift |
|--------------|----------------|---------|-------|--------------|------|
| (500, 600]   | (300, 400]     | 0.6667  | 15    | 0.03         | 2.5  |
| (500, 600]   | (400, 500]     | 0.4000  | 25    | 0.05         | 1.5  |
| (600, 700]   | (300, 400]     | 0.5000  | 20    | 0.04         | 1.9  |
| (600, 700]   | (400, 500]     | 0.2000  | 30    | 0.06         | 0.8  |
| (700, 800]   | (300, 400]     | 0.3000  | 18    | 0.036        | 1.15 |
| (700, 800]   | (400, 500]     | 0.1500  | 40    | 0.08         | 0.58 |

**包含损失率指标的Excel示例**（需要在初始化时提供amount_col和ovd_bal_col）：

| ALI_FQZSCORE | BAIDU_FQZSCORE | badrate | count | loss_rate | loss_lift |
|--------------|----------------|---------|-------|-----------|-----------|
| (500, 600]   | (300, 400]     | 0.6667  | 15    | 0.4567    | 2.89      |
| (500, 600]   | (400, 500]     | 0.4000  | 25    | 0.3210    | 2.01      |
| (600, 700]   | (300, 400]     | 0.5000  | 20    | 0.2890    | 1.81      |
| (600, 700]   | (400, 500]     | 0.2000  | 30    | 0.1567    | 0.98      |

#### 3.10 获取Top规则

```python
# 获取Top规则
top_rules = multi_miner.get_cross_rules(
    feature1, feature2,
    top_n=10,
    metric='lift',
    min_samples=10,
    min_lift=1.1,
    max_unique_threshold=5,
    custom_bins1=None,
    custom_bins2=None,
    binning_method='quantile'
)

print(top_rules[['feature1_value', 'feature2_value', 'count', 'badrate', 'lift', 'rule_description']])
```

#### 3.11 可视化

```python
# 绘制交叉热力图
plt = multi_miner.plot_cross_heatmap(feature1, feature2, metric='lift')
plt.savefig('images/cross_feature_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
```

---

### 4. 变量分析（VariableAnalyzer）

支持对特征变量进行全面的效度分析和分箱分析，帮助风控团队识别重要变量，优化特征工程。

#### 4.1 初始化参数详解

```python
from rulelift import VariableAnalyzer

# 初始化变量分析器（不使用损失率指标）
var_analyzer = VariableAnalyzer(
    df, 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'], 
    target_col='ISBAD'
)

# 初始化变量分析器（使用损失率指标）
var_analyzer_with_loss = VariableAnalyzer(
    df, 
    exclude_cols=['ID', 'CREATE_TIME', 'OVD_BAL', 'AMOUNT'], 
    target_col='ISBAD',
    amount_col='AMOUNT',      # 金额字段名
    ovd_bal_col='OVD_BAL'      # 逾期金额字段名
)
```

#### 4.2 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `df` | DataFrame | 必填 | 输入的数据集 |
| `exclude_cols` | List[str] | `None` | 排除的字段名列表 |
| `target_col` | str | `'ISBAD'` | 目标字段名 |
| `amount_col` | str | `None` | 金额字段名，用于计算损失率指标 |
| `ovd_bal_col` | str | `None` | 逾期金额字段名，用于计算损失率指标 |

#### 4.3 分析所有变量的效度指标

```python
# 分析所有变量的效度指标
var_metrics = var_analyzer.analyze_all_variables()
print("\n=== 所有变量效度指标 ===")
print(var_metrics)
```

#### 4.4 分析单个变量的分箱情况

```python
# 分析单个变量的分箱情况
feature = 'ALI_FQZSCORE'
bin_analysis = var_analyzer.analyze_single_variable(feature, n_bins=10)
print(f"\n=== {feature} 分箱分析 ===")
print(bin_analysis)
```

#### 4.5 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `feature` | str | 必填 | 特征名 |
| `n_bins` | int | `10` | 分箱数量 |
| `psi_dt` | str | `None` | PSI计算分割日期 |
| `date_col` | str | `None` | 日期字段名 |

#### 4.6 输出示例

```
=== 所有变量效度指标 ===
        variable        iv        ks        auc  missing_rate  single_value_rate  min_value  max_value  median_value  mean_diff  corr_with_target  psi
0  ALI_FQZSCORE  0.456789  0.452345  0.723456      0.012345      0.0456789      0.987654      0.723456      0.012345      0.456789      0.012345
1  BAIDU_FQZSCORE  0.3456789  0.3456789  0.678901      0.023456      0.056789      0.976543      0.678901      0.023456      0.3456789      0.023456
```

#### 4.7 变量效度指标说明

| 指标 | 定义 | 最佳范围 | 意义 |
|------|------|----------|------|
| `iv` | 信息值(Information Value) | > 0.1 | 变量的预测能力，值越大预测能力越强 |
| `ks` | KS统计量 | > 0.2 | 变量对好坏客户的区分能力，值越大区分能力越强 |
| `auc` | 曲线下面积 | > 0.6 | 变量的整体预测能力，值越大预测能力越强 |
| `missing_rate` | 缺失率 | < 0.1 | 变量的缺失值比例，值越小数据质量越好 |
| `single_value_rate` | 单值率 | < 0.05 | 变量的唯一值比例，值越小区分能力越强 |
| `min_value` | 最小值 | - | 变量的最小值 |
| `max_value` | 最大值 | - | 变量的最大值 |
| `median_value` | 中位数 | - | 变量的中位数，反映中心趋势 |
| `mean_diff` | 均值差异 | > 0.1 | 好坏客户均值差异，值越大区分能力越强 |
| `corr_with_target` | 与目标变量相关系数 | - | 变量与目标变量的相关性，值越大越重要 |
| `psi` | 群体稳定性指标(PSI) | < 0.1 | 变量的稳定性指标，值越小越稳定 |

#### 4.8 可视化

```python
# 可视化变量分箱结果
var_analyzer.plot_variable_bins(feature, n_bins=10)
plt.savefig(f'{feature}_bin_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
```

---

### 5. 规则效度分析监控模块（analyze_rules）

用于实时评估上线规则的效度。解决规则拦截样本无标签的问题，借助客户评级分布差异，推算逾期率、召回率、精确率、lift 值等核心指标。

#### 5.1 初始化参数详解

```python
from rulelift import analyze_rules

# 通过用户评级评估规则效度
result_by_rating = analyze_rules(
    hit_rule_df, 
    rule_col='RULE',
    user_id_col='USER_ID',
    user_level_badrate_col='USER_LEVEL_BADRATE',  # 用户评级坏账率字段
    hit_date_col='HIT_DATE',  # 命中日期，用于计算稳定性指标
    include_stability=True  # 是否包含稳定性指标
)

# 通过目标标签评估规则效度
result_by_target = analyze_rules(
    hit_rule_df, 
    rule_col='RULE',
    user_id_col='USER_ID',
    user_target_col='USER_TARGET',  # 用户实际逾期标签字段
    hit_date_col='HIT_DATE',  # 命中日期，用于计算稳定性指标
    include_stability=True  # 是否包含稳定性指标
)

# 同时使用两种方式评估规则效度
result_combined = analyze_rules(
    hit_rule_df, 
    rule_col='RULE',
    user_id_col='USER_ID',
    user_level_badrate_col='USER_LEVEL_BADRATE',
    user_target_col='USER_TARGET',
    hit_date_col='HIT_DATE',
    include_stability=True  # 是否包含稳定性指标
)
```

#### 5.2 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `rule_score` | DataFrame | 必填 | 规则拦截客户信息 |
| `rule_col` | str | `'RULE'` | 规则字段名 |
| `user_id_col` | str | `'USER_ID'` | 用户编号字段名 |
| `user_level_badrate_col` | str | `None` | 用户评级坏账率字段名（可选） |
| `user_target_col` | str | `None` | 用户实际逾期字段名（可选） |
| `hit_date_col` | str | `None` | 命中日期字段名（可选，用于命中率监控） |
| `metrics` | list | `None` | 指定要计算的指标列表（可选） |
| `include_stability` | bool | `True` | 是否包含稳定性指标 |

#### 5.3 评估方式说明

##### 5.3.1 通过用户评级评估规则

当用户没有实际逾期标签时，可以使用用户评级对应的坏账率来评估规则效果。

**计算指标**：
- `estimated_badrate_pred`: 预估坏账率
- `estimated_recall_pred`: 预估召回率
- `estimated_precision_pred`: 预估精确率
- `estimated_lift_pred`: 预估lift值

##### 5.3.2 通过目标标签评估规则

当用户有实际逾期标签时，可以直接使用目标标签来评估规则效果。

**计算指标**：
- `actual_badrate`: 实际坏账率
- `actual_recall`: 实际召回率
- `actual_precision`: 实际精确率
- `actual_lift`: 实际lift值
- `f1`: F1分数

##### 5.3.3 命中率相关指标

当提供了 `hit_date_col` 时，还会计算以下指标：

| 指标 | 定义 | 业务意义 |
|------|------|----------|
| `base_hit_rate` | 历史平均命中率 | 反映规则的历史命中情况 |
| `current_hit_rate` | 当天命中率 | 反映规则的当前命中情况 |
| `hit_rate_cv` | 命中率变异系数 = 标准差/均值 | 反映规则命中率的稳定性，值越小越稳定 |
| `hit_rate_change_rate` | 命中率变化率 = (当前命中率 - 历史平均命中率) / 历史平均命中率 | 反映规则命中率的变化趋势 |

##### 5.3.4 稳定性指标

当提供了 `hit_date_col` 且 `include_stability=True` 时，还会计算以下稳定性指标：

| 指标 | 定义 | 业务意义 |
|------|------|----------|
| `hit_rate_std` | 命中率标准差 | 反映规则命中率的波动程度 |
| `hit_rate_cv` | 命中率变异系数 | 反映规则命中率的稳定性，值越小越稳定 |
| `max_monthly_change` | 最大月度变化率 | 反映规则命中率的最大波动 |
| `min_monthly_change` | 最小月度变化率 | 反映规则命中率的最小波动 |
| `avg_monthly_change` | 平均月度变化率 | 反映规则命中率的平均变化趋势 |
| `months_analyzed` | 分析的月份数量 | 反映分析的时间跨度 |

#### 5.4 规则相关性分析

```python
from rulelift import analyze_rule_correlation

# 规则相关性分析
correlation_matrix, max_correlation = analyze_rule_correlation(
    hit_rule_df, 
    rule_col='RULE', 
    user_id_col='USER_ID'
)
print(f"   规则相关性矩阵:")
print(correlation_matrix)
print(f"   每条规则的最大相关性:")
for rule, corr in max_correlation.items():
    print(f"   {rule}: {corr['max_correlation_value']:.4f}")
```

**输出示例**：

```
规则相关性矩阵:
          rule1     rule2     rule3
rule1  1.000000  0.234567  0.345678
rule2  0.234567  1.000000  0.456789
rule3  0.345678  0.456789  1.000000

每条规则的最大相关性:
rule1: 0.3457
rule2: 0.4568
rule3: 0.4568
```

#### 5.5 输出示例

```
=== 规则效度分析结果 ===
         RULE  actual_lift  actual_badrate  actual_recall        f1
0  rule1     2.3456789      0.3456789      0.456789  0.3456789
1  rule2     2.123456      0.234567       0.3456789  0.234567
2  rule3     1.987654      0.123456       0.234567  0.123456
```

---

### 6. 策略相关性、增益计算（calculate_strategy_gain）

评估策略组合效果，计算两两规则间的增益。

#### 6.1 初始化参数详解

```python
from rulelift import calculate_strategy_gain

# 定义两个策略组
strategy1 = ['rule1', 'rule2']
strategy2 = ['rule1', 'rule2', 'rule3']

# 计算策略增益（strategy1 到 strategy2 的额外价值）
gain = calculate_strategy_gain(
    hit_rule_df, 
    strategy1, 
    strategy2, 
    user_target_col='USER_TARGET'
)
print(f"\n策略增益: {gain:.4f}")
```

#### 6.2 参数详细说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|----------|------|
| `rule_score` | DataFrame | 必填 | 规则拦截客户信息 |
| `strategy_a_rules` | list | 必填 | 策略A的规则列表 |
| `strategy_b_rules` | list | 必填 | 策略B的规则列表 |
| `user_target_col` | str | `None` | 用户实际逾期字段名（可选） |
| `user_level_badrate_col` | str | `None` | 用户评级坏账率字段名（可选） |

#### 6.3 增益指标说明

| 指标 | 定义 | 业务意义 |
|------|------|----------|
| `gain_users` | 策略A在策略B之后新增的拦截用户数 | 反映策略A的额外覆盖能力 |
| `gain_bads` | 新增拦截用户中的坏客户数 | 反映策略A的额外拦截能力 |
| `gain_badrate` | 新增拦截用户的坏账率 | 反映新增拦截用户的质量 |
| `gain_lift` | 新增拦截用户坏账率相对于策略B坏账率的增益（倍数） | 反映策略A的额外价值 |
| `gain_coverage` | 新增拦截用户占总样本的比例 | 反映策略A的额外覆盖范围 |
| `gain_recall` | 新增拦截用户中的坏客户占总坏客户的比例 | 反映策略A的额外召回能力 |
| `b_hit_users` | 策略B拦截的用户数 | 反映策略B的覆盖范围 |
| `b_badrate` | 策略B拦截用户的坏账率 | 反映策略B的拦截质量 |

#### 6.4 输出示例

```
策略增益: 1.2345
```

---

## 核心指标说明

### 规则评估指标

| 指标 | 定义 | 最佳范围 | 意义 |
|------|------|----------|------|
| `actual_lift` | 规则命中样本逾期率 / 总样本逾期率 | > 1.0 | 规则的风险区分能力，值越大效果越好 |
| `f1` | 2*(精确率*召回率)/(精确率+召回率) | 0-1 | 综合评估规则的精确率和召回率 |
| `actual_badrate` | 规则命中样本中的逾期比例 | 依业务场景而定 | 规则直接拦截的坏客户比例 |
| `actual_recall` | 规则命中的坏客户 / 总坏客户 | 0-1 | 规则对坏客户的覆盖能力 |
| `hit_rate_cv` | 命中率变异系数 = 标准差/均值 | < 0.2 | 规则命中率的稳定性，值越小越稳定 |
| `max_correlation_value` | 与其他规则的最大相关系数 | < 0.5 | 规则的独立性，值越小独立性越好 |

### 变量分析指标

| 指标 | 定义 | 最佳范围 | 意义 |
|------|------|----------|------|
| `iv` | 信息值(Information Value) | > 0.1 | 变量的预测能力，值越大预测能力越强 |
| `ks` | KS统计量 | > 0.2 | 变量对好坏客户的区分能力，值越大区分能力越强 |
| `auc` | 曲线下面积 | > 0.6 | 变量的整体预测能力，值越大预测能力越强 |
| `badrate` | 分箱中的坏客户比例 | 依业务场景而定 | 分箱的风险水平 |
| `cum_badrate` | 累积坏客户比例 | 依业务场景而定 | 累积分箱的风险水平 |

---

## ❓ 常见问题（FAQ）

### Q1: 如何选择合适的规则挖掘算法？

**A**: 根据不同的业务场景选择算法：
- **DT（决策树）**：适合快速探索和初步分析，规则简单易懂
- **RF（随机森林）**：适合生产环境，规则稳定性好，多样性高
- **CHI2（卡方决策树）**：适合分类特征较多的场景
- **XGB（XGBoost）**：适合复杂场景，规则精度高
- **ISF（孤立森林）**：适合挖掘异常样本的规则

### Q2: 如何配置特征趋势（feature_trends）？

**A**: 特征趋势用于避免不符合业务解释性的规则：
```python
feature_trends={
    'ALI_FQZSCORE': -1,      # 负相关：分数越低，违约概率越高
    'BAIDU_FQZSCORE': -1,    # 负相关：分数越低，违约概率越高
    'NUMBER OF LOAN APPLICATIONS TO PBOC': 1  # 正相关：申请次数越多，违约概率越高
}
```

### Q3: 如何计算损失率指标？

**A**: 需要在初始化时提供金额字段和逾期金额字段：
```python
# 对于规则挖掘器
tree_miner = TreeRuleExtractor(
    df, 
    target_col='ISBAD',
    amount_col='AMOUNT',      # 金额字段名
    ovd_bal_col='OVD_BAL'      # 逾期金额字段名
)

# 对于多特征交叉规则挖掘器
multi_miner = MultiFeatureRuleMiner(
    df, 
    target_col='ISBAD',
    amount_col='AMOUNT',      # 金额字段名
    ovd_bal_col='OVD_BAL'      # 逾期金额字段名
)
```

### Q4: 如何评估规则的实际效果？

**A**: 使用 `analyze_rules` 函数评估规则效度：
```python
# 通过用户评级评估
result_by_rating = analyze_rules(
    hit_rule_df, 
    rule_col='RULE',
    user_id_col='USER_ID',
    user_level_badrate_col='USER_LEVEL_BADRATE',
    hit_date_col='HIT_DATE',
    include_stability=True
)

# 通过目标标签评估
result_by_target = analyze_rules(
    hit_rule_df, 
    rule_col='RULE',
    user_id_col='USER_ID',
    user_target_col='USER_TARGET',
    hit_date_col='HIT_DATE',
    include_stability=True
)
```

### Q5: 如何识别冗余规则？

**A**: 使用规则相关性分析识别冗余规则：
```python
# 规则相关性分析
correlation_matrix, max_correlation = analyze_rule_correlation(
    hit_rule_df, 
    rule_col='RULE', 
    user_id_col='USER_ID'
)

# 查看每条规则的最大相关性
for rule, corr in max_correlation.items():
    print(f"{rule}: {corr['max_correlation_value']:.4f}")
```

如果两条规则的相关性过高（> 0.8），则说明它们存在冗余，可以考虑删除其中一条。

### Q6: 如何优化规则组合？

**A**: 使用策略增益计算评估不同规则组合的效果：
```python
# 定义两个策略组
strategy1 = ['rule1', 'rule2']
strategy2 = ['rule1', 'rule2', 'rule3']

# 计算策略增益
gain = calculate_strategy_gain(
    hit_rule_df, 
    strategy1, 
    strategy2, 
    user_target_col='USER_TARGET'
)
print(f"策略增益: {gain:.4f}")
```

如果增益值较高，说明添加新规则能带来显著价值。

### Q7: 如何在离线环境中使用？

**A**: 参考文档中的"离线使用方式"部分，主要有两种方式：
1. **离线安装rulelift及相关依赖**：在有网络的环境中下载依赖包，然后传输到离线环境安装
2. **通过源码直接调用**：下载源码包，手动安装依赖，然后在Python代码中添加源码路径并导入

### Q8: 如何处理缺失值？

**A**: rulelift 会自动处理缺失值：
- 对于数值型特征：缺失值会被填充为0
- 对于类别型特征：缺失值会被填充为'missing'
- 用户也可以在传入数据前自行处理缺失值

### Q9: 如何调整树模型的复杂度？

**A**: 通过以下参数控制树模型的复杂度：
- `max_depth`：决策树最大深度，值越大规则越复杂
- `min_samples_split`：分裂节点所需的最小样本数，值越大规则越保守
- `min_samples_leaf`：叶子节点的最小样本数，值越大叶子节点包含的样本越多
- `n_estimators`：树的数量，值越大模型越稳定但训练时间越长

### Q10: 如何导出规则分析结果？

**A**: 支持多种导出方式：
```python
# 导出为CSV
rules_df.to_csv('rules.csv', index=False, encoding='utf-8-sig')

# 导出为Excel
rules_df.to_excel('rules.xlsx', index=False)

# 生成交叉矩阵Excel文件
cross_matrices = multi_miner.generate_cross_matrices_excel(
    features_list=['ALI_FQZSCORE', 'BAIDU_FQZSCORE'], 
    output_path='cross_analysis.xlsx'
)
```

### Q11: 如何可视化分析结果？

**A**: rulelift 提供了丰富的可视化功能：
```python
# 特征重要性图
tree_miner.plot_feature_importance(save_path='feature_importance.png')

# 决策树结构图
tree_miner.plot_decision_tree(save_path='decision_tree.pdf')

# 规则评估图
tree_miner.plot_rule_evaluation(save_path='rule_evaluation.png')

# 交叉特征热力图
multi_miner.plot_cross_heatmap(feature1, feature2, metric='lift')
```



---

## 版本信息

当前版本：1.2.3

## 更新日志

### v1.2.3 (2025-01-10)
- **新增特征趋势判断功能**：TreeRuleExtractor 支持 `feature_trends` 参数，提升规则的业务解释性
- **优化孤立森林规则提取**：基于树结构提取规则，支持多特征组合
- **优化SingleFeatureRuleMiner**：过滤极端值阈值，避免无意义规则
- **优化MultiFeatureRuleMiner**：添加最小样本数和lift值过滤，添加交叉矩阵Excel生成功能
- **优化规则DataFrame输出**：支持按lift倒序排序
- **修复已知问题**：解决所有已知bug和性能问题

### v1.1.5 (2025-12-23)
- 新增变量分析模块，支持IV、KS、AUC等指标计算
- 实现单变量等频分箱分析功能
- 新增策略自动挖掘功能
- 优化决策树规则显示，加入 lift 值和拦截用户数等指标
- 新增两两策略增益计算功能
- 优化代码质量，修复所有已知问题

### v1.0.0 (2025-12-17)
- 新增命中率变异系数（hit_rate_cv）用于监控规则稳定性
- 新增 F1 分数计算，综合评估规则效果
- 优化规则相关性分析，新增最大相关性指标
- 改进命中率计算逻辑
- 完善文档，新增技术原理和缺陷分析

---

## 许可证

MIT License

---

## 项目地址

- GitHub: https://github.com/aialgorithm/rulelift
- PyPI: https://pypi.org/project/rulelift/

---

## 联系方式

微信&github: aialgorithm
邮箱: 15880982687@qq.com

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！如果您有任何建议或问题，请通过 GitHub Issues 反馈。

---

**开始使用 rulelift 优化您的风控规则系统吧！** 🚀
