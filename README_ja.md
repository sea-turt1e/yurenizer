# yurenizer
Pythonで動く日本語の表記揺れ対策ツール

English README is here.

## 概要
yurenizerは、日本語の表記揺れを検出し、統一するためのツールです。  
例えば、「パソコン」や「パーソナル・コンピュータ」、「パーソナルコンピュータ」などを「パーソナルコンピューター」に統一することができます。  
このルールは[Sudachi同義語辞書](https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md#%E5%90%8C%E7%BE%A9%E8%AA%9E%E8%BE%9E%E6%9B%B8%E3%82%BD%E3%83%BC%E3%82%B9-%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88)に準じています。


## インストール
```bash
pip install yurenizer
```

## 使用方法
```python
from yurenizer import SynonymNormalizer
normalizer = SynonymNormalizer()
text = "パソコンはパーソナルコンピュータの同義語で、パーソナル・コンピュータと言ったりパーソナル・コンピューターと言ったりします。"
print(normalizer.normalize(text))
# 出力: パーソナルコンピューターはパーソナルコンピューターのシノニムで、パーソナルコンピューターと言ったりパーソナルコンピューターと言ったりします。
```

## 引数の指定
normalize関数の引数に以下のオプションを指定することができます。
- taigen（default=1）: 統一するのに体言を含むかどうかのフラグ。デフォルトは含む。含まない場合は0を指定。
- yougen（default=0）: 統一するのに用言を含むかどうかのフラグ。デフォルトは含まない。含む場合は1を指定。ただし用言は
- expansion（default="from_another"）: 同義語展開の制御フラグ。デフォルトは展開制御フラグが0のもののみ展開。"ANY"を指定すると展開制御フラグが常に展開する。
- other_language（default=1）: 日本語以外の言語を日本語に正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合は0を指定。
- alphabet（default=1）: アルファベットの表記揺れを正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合は0を指定。
- alphabetic_abbreviation（default=1）: アルファベットの略語を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合は0を指定。
- non_alphabetic_abbreviation（default=1）: 日本語の略語を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合は0を指定。
- orthographic_variation（default=1）: 異表記を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合は0を指定。
- missspelling（default=1）: 誤表記を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合は0を指定。

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

## ライセンス
本プロジェクトは[Apache License 2.0](LICENSE)の下でライセンスされています。

### 使用しているオープンソースソフトウェア
- [Sudachi 同義語辞書](https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md#%E5%90%8C%E7%BE%A9%E8%AA%9E%E8%BE%9E%E6%9B%B8%E3%82%BD%E3%83%BC%E3%82%B9-%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88): Apache License 2.0
- [SudachiPy](https://github.com/WorksApplications/SudachiPy): Apache License 2.0
- [SudachiDict](https://github.com/WorksApplications/SudachiDict): Apache License 2.0

本ライブラリは形態素解析にSudachiPyとその辞書であるSudachiDictを使用しています。これらもApache License 2.0の下で配布されています。

詳細なライセンス情報については、各プロジェクトのLICENSEファイルをご確認ください。
- [Sudachi 同義語辞書のLICENSE](https://github.com/WorksApplications/SudachiDict/blob/develop/LICENSE-2.0.txt)
※ Sudachi 辞書と同じライセンスで提供されています。
- [SudachiPyのLICENSE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE)
- [SudachiDictのLICENSE](https://github.com/WorksApplications/SudachiDict/blob/develop/LICENSE-2.0.txt)


