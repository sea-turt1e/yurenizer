![Python](https://img.shields.io/badge/-Python-F9DC3E.svg?logo=python&style=flat)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![PyPI Downloads](https://static.pepy.tech/badge/yurenizer)

# yurenizer
This is a Japanese text normalizer that resolves spelling inconsistencies.

Japanese README is Here.（日本語のREADMEはこちら）  
https://github.com/sea-turt1e/yurenizer/blob/main/README_ja.md

## Overview
yurenizer is a tool for detecting and unifying variations in Japanese text notation.  
For example, it can unify variations like "パソコン" (pasokon), "パーソナル・コンピュータ" (personal computer), and "パーソナルコンピュータ" into "パーソナルコンピューター".  
These rules follow the [Sudachi Synonym Dictionary](https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md).

## web-based Demo
You can try the web-based demo here.  
[yurenizer Web-demo](https://yurenizer.net/)  
<div><video controls src="https://github.com/user-attachments/assets/fdcbaa1a-5692-4c30-a8e1-188d5016443d" muted="false"></video></div>

## Installation
```bash
pip install yurenizer
```

## Download Synonym Dictionary
```bash
curl -L -o /path/to/synonyms.txt https://raw.githubusercontent.com/WorksApplications/SudachiDict/refs/heads/develop/src/main/text/synonyms.txt
```

## Usage
### Quick Start
```python
from yurenizer import SynonymNormalizer, NormalizerConfig
normalizer = SynonymNormalizer(synonym_file_path="path/to/synonym_file_path")
text = "「パソコン」は「パーソナルコンピュータ」の「synonym」で、「パーソナル・コンピュータ」と表記することもあります。"
print(normalizer.normalize(text))
# Output: 「パーソナルコンピューター」は「パーソナルコンピューター」の「シノニム」で、「パーソナルコンピューター」と表記することもあります。
```

### Customizing Settings
You can control normalization by specifying `NormalizerConfig` as an argument to the normalize function.

#### Example with Custom Settings
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
            alphabetic_abbreviation=True, # Normalize only alphabetic abbreviations
            non_alphabetic_abbreviation=False,
            alphabet=False,
            orthographic_variation=False,
            misspelling=False
        )
print(f"Output: {normalizer.normalize(text, config)}")
# Output: 「東日本旅客鉄道」は「JR東」や「東日本旅客鉄道」とも呼ばれます
```


---

## **Configuration Details**

The settings in *yurenizer* are organized hierarchically, allowing you to control the scope and target of normalization.

---

### **1. unify_level (Normalization Level)**

First, specify the **level of normalization** with the `unify_level` parameter.

| **Value**          | **Description**                                                                                                                                 |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `lexeme`          | Performs the most comprehensive normalization, targeting **all groups (a, b, c)** mentioned below.                                              |
| `word_form`       | Normalizes by word form, targeting **groups b and c**.                                                                                         |
| `abbreviation`    | Normalizes by abbreviation, targeting **group c** only.                                                                                        |

---

### **2. taigen / yougen (Target Selection)**

Use the `taigen` and `yougen` flags to control which parts of speech are included in the normalization.

| **Setting**   | **Default Value** | **Description**                                                                                              |
|---------------|-------------------|--------------------------------------------------------------------------------------------------------------|
| `taigen`      | `True`            | Includes nouns and other substantives in the normalization. Set to `False` to exclude them.                  |
| `yougen`      | `False`           | Includes verbs and other predicates in the normalization. Set to `True` to include them (normalized to their lemma). |

---

### **3. expansion (Expansion Flag)**

The expansion flag determines how synonyms are expanded based on the synonym dictionary's internal control flags.

| **Value**         | **Description**                                                                                       |
|--------------------|-------------------------------------------------------------------------------------------------------|
| `from_another`   | Expands only the synonyms with a control flag value of `0` in the synonym dictionary.                 |
| `any`            | Expands all synonyms regardless of their control flag value.                                         |

---

### **4. Detailed Normalization Settings (a, b, c Groups)**

#### **a Group: Comprehensive Lexical Normalization**
Controls normalization based on vocabulary and semantics using the following settings:

| **Setting**       | **Default Value** | **Description**                                                                                              |
|--------------------|-------------------|--------------------------------------------------------------------------------------------------------------|
| `other_language`  | `True`            | Normalizes non-Japanese terms (e.g., English) to Japanese. Set to `False` to disable this feature.            |
| `alias`           | `True`            | Normalizes aliases. Set to `False` to disable this feature.                                                  |
| `old_name`        | `True`            | Normalizes old names. Set to `False` to disable this feature.                                                |
| `misuse`          | `True`            | Normalizes misused terms. Set to `False` to disable this feature.                                            |

---

#### **b Group: Abbreviation Normalization**
Controls normalization of abbreviations using the following settings:

| **Setting**                 | **Default Value** | **Description**                                                                                              |
|------------------------------|-------------------|--------------------------------------------------------------------------------------------------------------|
| `alphabetic_abbreviation`   | `True`            | Normalizes abbreviations written in alphabetic characters. Set to `False` to disable this feature.           |
| `non_alphabetic_abbreviation` | `True`          | Normalizes abbreviations written in non-alphabetic characters (e.g., Japanese). Set to `False` to disable this feature. |

---

#### **c Group: Orthographic Normalization**
Controls normalization of orthographic variations and errors using the following settings:

| **Setting**              | **Default Value** | **Description**                                                                                              |
|---------------------------|-------------------|--------------------------------------------------------------------------------------------------------------|
| `alphabet`               | `True`            | Normalizes alphabetic variations. Set to `False` to disable this feature.                                    |
| `orthographic_variation` | `True`            | Normalizes orthographic variations. Set to `False` to disable this feature.                                  |
| `misspelling`            | `True`            | Normalizes misspellings. Set to `False` to disable this feature.                                             |

---

### **5. custom_synonym (Custom Dictionary)**

If you want to use a custom dictionary, control its behavior with the following setting:

| **Setting**       | **Default Value** | **Description**                                                                                              |
|--------------------|-------------------|--------------------------------------------------------------------------------------------------------------|
| `custom_synonym`   | `True`            | Enables the use of a custom dictionary. Set to `False` to disable it.                                        |

---

This hierarchical configuration allows for flexible normalization by defining the scope and target in detail.
## Specifying SudachiDict
The length of text segmentation varies depending on the type of SudachiDict. Default is "full", but you can specify "small" or "core".  
To use "small" or "core", install it and specify in the `SynonymNormalizer()` arguments:
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
※ Please refer to SudachiDict documentation for details.

## Custom Dictionary Specification
You can specify your own custom dictionary.  
If the same word exists in both the custom dictionary and Sudachi synonym dictionary, the custom dictionary takes precedence.

### Custom Dictionary Format
The custom dictionary file should be in JSON, CSV, or TSV format.
- JSON file
```json
{
    "Representative word 1": ["Synonym 1_1", "Synonym 1_2", ...],
    "Representative word 2": ["Synonym 2_1", "Synonym 2_2", ...],
}
```
- CSV file
```
Representative word 1,Synonym 1_1,Synonym 1_2,...
Representative word 2,Synonym 2_1,Synonym 2_2,...
```
- TSV file
```
Representative word 1	Synonym 1_1	Synonym 1_2	...
Representative word 2	Synonym 2_1	Synonym 2_2	...
...
```

#### Example
If you create a file like the one below, "幽白", "ゆうはく", and "幽☆遊☆白書" will be normalized to "幽遊白書".

- JSON file
```json
{
    "幽遊白書": ["幽白", "ゆうはく", "幽☆遊☆白書"],
}
```
- CSV file
```csv
幽遊白書,幽白,ゆうはく,幽☆遊☆白書
```
- TSV file
```tsv
幽遊白書	幽白	ゆうはく	幽☆遊☆白書
```

### How to Specify
```python
normalizer = SynonymNormalizer(custom_synonyms_file="path/to/custom_dict_file")
```

## License
This project is licensed under the [Apache License 2.0](LICENSE).

### Open Source Software Used
- [Sudachi Synonym Dictionary](https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md): Apache License 2.0
- [SudachiPy](https://github.com/WorksApplications/SudachiPy): Apache License 2.0
- [SudachiDict](https://github.com/WorksApplications/SudachiDict): Apache License 2.0

This library uses SudachiPy and its dictionary SudachiDict for morphological analysis. These are also distributed under the Apache License 2.0.

For detailed license information, please check the LICENSE files of each project:
- [Sudachi Synonym Dictionary LICENSE](https://github.com/WorksApplications/SudachiDict/blob/develop/LICENSE-2.0.txt)
※ Provided under the same license as the Sudachi dictionary.
- [SudachiPy LICENSE](https://github.com/WorksApplications/SudachiPy/blob/develop/LICENSE)
- [SudachiDict LICENSE](https://github.com/WorksApplications/SudachiDict/blob/develop/LICENSE-2.0.txt)
