![Python](https://img.shields.io/badge/-Python-F9DC3E.svg?logo=python&style=flat)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![PyPI Downloads](https://static.pepy.tech/badge/yurenizer)
# yurenizer
表記を統一することで文章中の表記揺れを解消するPythonライブラリ

English README is here.  
https://github.com/sea-turt1e/yurenizer/blob/main/README.md

## 概要
yurenizerは、日本語の表記揺れを検出し、統一するためのツールです。  
例えば、「パソコン」や「パーソナル・コンピュータ」、「パーソナルコンピュータ」などを「パーソナルコンピューター」に統一することができます。  
このルールは[Sudachi同義語辞書](https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md)に準じています。

## Webデモ
yunenizerのWebデモを以下のリンクから利用できます。  
[yurenizer Web-demo](https://yurenizer.net/)  
<div><video controls src="https://github.com/user-attachments/assets/fdcbaa1a-5692-4c30-a8e1-188d5016443d" muted="false"></video></div>

## インストール
```bash
pip install yurenizer
```

## 同義語辞書のダウンロード
```bash
curl -L -o /path/to/synonyms.txt https://raw.githubusercontent.com/WorksApplications/SudachiDict/refs/heads/develop/src/main/text/synonyms.txt
```

## 使用方法
### すぐ使いたい場合
```python
from yurenizer import SynonymNormalizer, NormalizerConfig
normalizer = SynonymNormalizer(synonym_file_path="path/to/synonym_file_path")
text = "「パソコン」は「パーソナルコンピュータ」の「synonym」で、「パーソナル・コンピュータ」と表記することもあります。"
print(normalizer.normalize(text))
# 出力: 「パーソナルコンピューター」は「パーソナルコンピューター」の「シノニム」で、「パーソナルコンピューター」と表記することもあります。
```

### 設定を変更する場合
normalize関数の引数に`NormalizerConfig`を指定することで、正規化の制御を行うことができます。  

#### 設定を変更する場合の使用例
```python
from yurenizer import SynonymNormalizer, NormalizerConfig
normalizer = SynonymNormalizer(synonym_file_path="path/to/synonym_file_path")
text = "「東日本旅客鉄道」は「JR東」や「JR-East」とも呼ばれます"
config = NormalizerConfig(
            unify_level="lexeme",
            taigen=True, 
            yougen=False,
            expansion="from_another", 
            other_language=False,
            alias=False,
            old_name=False,
            misuse=False,
            alphabetic_abbreviation=True, # アルファベットの略語のみを正規化する
            non_alphabetic_abbreviation=False,
            alphabet=False,
            orthographic_variation=False,
            misspelling=False
        )
print(f"出力: {normalizer.normalize(text, config)}")
# 出力: 「東日本旅客鉄道」は「JR東」や「東日本旅客鉄道」とも呼ばれます
```

## 設定の詳細

yurenizerの設定は、以下のような階層構造に基づいて正規化の範囲や対象を制御します。

---

### **1. unify_level（統一レベル）**
まず、**どのレベルまで統一するか**を`unify_level`で指定します。

| **値**          | **説明**                                                                                                                                                            |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `lexeme`       | 最も広範な統一を行います。後述の **a, b, cグループ全て** を統一対象とします。                                                                                     |
| `word_form`    | 語形単位での統一を行います。後述の **b, cグループ** を統一対象とします。                                                                                          |
| `abbreviation` | 略語単位での統一を行います。後述の **cグループ** のみを統一対象とします。                                                                                          |

---

### **2. taigen / yougen（統一対象の選択）**
`taigen`と`yougen`フラグを使用して、統一対象に含める品詞を制御します。

| **設定項目** | **デフォルト値** | **説明**                                                                                              |
|--------------|------------------|--------------------------------------------------------------------------------------------------------|
| `taigen`     | `True`           | 体言（名詞など）を統一対象に含めるかを指定します。`False`にすると含みません。                                                              |
| `yougen`     | `False`          | 用言（動詞や形容詞など）を統一対象に含めるかを指定します。`True`にすると含みます（ただし見出し語に統一されます）。                          |

---

### **3. expansion（展開フラグ）**
同義語辞書の展開制御フラグに基づき、統一範囲をさらに詳細に制御します。

| **値**         | **説明**                                                                                             |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `from_another`| 同義語辞書で展開制御フラグが`0`のもの（通常許可されたもの）を展開対象とします。                                                         |
| `any`         | 展開制御フラグに関係なく、全ての同義語を展開対象とします。                                                                               |

---

### **4. 統一の詳細設定（a, b, cグループ）**

#### **aグループ: 広範な語彙の統一**  
以下の設定項目で、語彙や意味に基づく統一を制御します。

| **設定項目**     | **デフォルト値** | **説明**                                                                                              |
|------------------|------------------|--------------------------------------------------------------------------------------------------------|
| `other_language` | `True`           | 日本語以外の言語（英語など）を日本語に統一するかを指定します。`False`にすると無効。                                                         |
| `alias`          | `True`           | 別称を統一するかを指定します。`False`にすると無効。                                                                                       |
| `old_name`       | `True`           | 旧称を統一するかを指定します。`False`にすると無効。                                                                                       |
| `misuse`         | `True`           | 誤用を統一するかを指定します。`False`にすると無効。                                                                                       |

---

#### **bグループ: 略語の統一**  
以下の設定項目で、略語の統一を制御します。

| **設定項目**                | **デフォルト値** | **説明**                                                                                              |
|-----------------------------|------------------|--------------------------------------------------------------------------------------------------------|
| `alphabetic_abbreviation`   | `True`           | アルファベットの略語を統一するかを指定します。`False`にすると無効。                                                                        |
| `non_alphabetic_abbreviation`| `True`          | 日本語の略語を統一するかを指定します。`False`にすると無効。                                                                                 |

---

#### **cグループ: 表記揺れの統一**  
以下の設定項目で、表記や誤りに基づく統一を制御します。

| **設定項目**        | **デフォルト値** | **説明**                                                                                              |
|---------------------|------------------|--------------------------------------------------------------------------------------------------------|
| `alphabet`          | `True`           | アルファベットの表記揺れを統一するかを指定します。`False`にすると無効。                                                                     |
| `orthographic_variation` | `True`       | 異表記を統一するかを指定します。`False`にすると無効。                                                                                       |
| `misspelling`       | `True`           | 誤表記を統一するかを指定します。`False`にすると無効。                                                                                       |

---

### **5. custom_synonym（カスタム辞書）**
カスタム辞書を使用する場合は、以下の設定項目で制御します。

| **設定項目**      | **デフォルト値** | **説明**                                                                                              |
|-------------------|------------------|--------------------------------------------------------------------------------------------------------|
| `custom_synonym`  | `True`           | カスタム辞書を使用するかを指定します。`False`にすると無効。                                                                                 |

---

このように統一の範囲や対象を段階的に制御することで、柔軟な正規化を実現します。

## SudachiDictの指定
SudachiDictの種類によって分割される長さが変わります。デフォルトは"full"ですが、"small"、または"core"を指定することができます。  
"small"または"core"を指定する場合はインストールして、`SynonymNormalizer()`の引数に指定してください。
```bash
pip install sudachidict_small
# or
pip install sudachidict_core
```

```python
normalizer = SynonymNormalizer(sudachi_dict="small")
# or
normalizer = SynonymNormalizer(sudachi_dict="core")
```
※SudachiDictの詳細はこちらをご覧ください。  

## カスタム辞書の指定
ユーザー自身のカスタム辞書を指定することができます。  
カスタム辞書とSudachi同義語辞書に同じ語がある場合、カスタム辞書が優先されます。  

### カスタム辞書のフォーマット
カスタム辞書は以下のようなフォーマットのjsonファイルを作成してください。  
```json
{
    "代表語1": ["同義語1_1", "同義語1_2", ...], 
    "代表語2": ["同義語2_1", "同義語2_2", ...],
    ...
}
```
#### 例
以下のようなファイルを作成した場合、"幽白"、"ゆうはく"、"幽☆遊☆白書"は"幽遊白書"に正規化されます。
```json
{
    "幽遊白書": ["幽白", "ゆうはく", "幽☆遊☆白書"]
}
```

### 指定方法
```python
normalizer = SynonymNormalizer(custom_synonyms_file="path/to/custom_dict.json")
```

## Zenn解説記事
yurenizerの解説記事をZennに投稿しています。  
[ルールベースで表記揺れを解消！Pythonライブラリ「yurenizer」](https://zenn.dev/sea_turt1e/articles/afbe326366f1e7)

## ライセンス
本プロジェクトは[Apache License 2.0](LICENSE)の下でライセンスされています。

### 使用しているオープンソースソフトウェア
- [Sudachi 同義語辞書](https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md): Apache License 2.0
- [SudachiPy](https://github.com/WorksApplications/SudachiPy): Apache License 2.0
- [SudachiDict](https://github.com/WorksApplications/SudachiDict): Apache License 2.0

本ライブラリは形態素解析にSudachiPyとその辞書であるSudachiDictを使用しています。これらもApache License 2.0の下で配布されています。

詳細なライセンス情報については、各プロジェクトのLICENSEファイルをご確認ください。
- [Sudachi 同義語辞書のLICENSE](https://github.com/WorksApplications/SudachiDict/blob/develop/LICENSE-2.0.txt)
※ Sudachi 辞書と同じライセンスで提供されています。
- [SudachiPyのLICENSE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE)
- [SudachiDictのLICENSE](https://github.com/WorksApplications/SudachiDict/blob/develop/LICENSE-2.0.txt)


