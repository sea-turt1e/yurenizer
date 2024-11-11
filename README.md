# yurenizer
This is a Japanese text normalizer that resolves spelling inconsistencies.

Japanese README is Here.（日本語のREADMEはこちら）  
https://github.com/sea-turt1e/yurenizer/blob/main/README_ja.md

## Overview
yurenizer is a tool for detecting and unifying variations in Japanese text notation.  
For example, it can unify variations like "パソコン" (pasokon), "パーソナル・コンピュータ" (personal computer), and "パーソナルコンピュータ" into "パーソナルコンピューター".  
These rules follow the [Sudachi Synonym Dictionary](https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md).

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
text = "パソコンはパーソナルコンピュータの同義語です"
config = NormalizerConfig(taigen=True, yougen=False, expansion="from_another", other_language=False, alphabet=False, alphabetic_abbreviation=False, non_alphabetic_abbreviation=False, orthographic_variation=False, missspelling=False)
print(normalizer.normalize(text, config))
# Output: パソコンはパーソナルコンピュータの同義語で、パーソナル・コンピュータと言ったりパーソナル・コンピューターと言ったりします。
```

#### Configuration Details
- unify_level (default="lexeme"): Flag to specify unification level. Default "lexeme" unifies based on lexeme number. "word_form" option unifies based on word form number. "abbreviation" option unifies based on abbreviation number.
- taigen (default=True): Flag to include nouns in unification. Default is to include. Specify False to exclude.
- yougen (default=False): Flag to include conjugated words in unification. Default is to exclude. Specify True to include.
- expansion (default="from_another"): Synonym expansion control flag. Default only expands those with expansion control flag 0. Specify "ANY" to always expand.
- other_language (default=True): Flag to normalize non-Japanese languages to Japanese. Default is to normalize. Specify False to disable.
- alias (default=True): Flag to normalize aliases. Default is to normalize. Specify False to disable.
- old_name (default=True): Flag to normalize old names. Default is to normalize. Specify False to disable.
- misuse (default=True): Flag to normalize misused terms. Default is to normalize. Specify False to disable.
- alphabetic_abbreviation (default=True): Flag to normalize alphabetic abbreviations. Default is to normalize. Specify False to disable.
- non_alphabetic_abbreviation (default=True): Flag to normalize Japanese abbreviations. Default is to normalize. Specify False to disable.
- alphabet (default=True): Flag to normalize alphabet variations. Default is to normalize. Specify False to disable.
- orthographic_variation (default=True): Flag to normalize orthographic variations. Default is to normalize. Specify False to disable.
- misspelling (default=True): Flag to normalize misspellings. Default is to normalize. Specify False to disable.
- custom_synonym (default=True): Flag to use user-defined custom synonyms. Default is to use. Specify False to disable.

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
Create a JSON file with the following format for your custom dictionary:
```json
{
    "representative_word1": ["synonym1_1", "synonym1_2", ...],
    "representative_word2": ["synonym2_1", "synonym2_2", ...],
    ...
}
```

#### Example
If you create a file like this, "幽白", "ゆうはく", and "幽☆遊☆白書" will be normalized to "幽遊白書":
```json
{
    "幽遊白書": ["幽白", "ゆうはく", "幽☆遊☆白書"]
}
```

### How to Specify
```python
normalizer = SynonymNormalizer(custom_synonyms_file="path/to/custom_dict.json")
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
