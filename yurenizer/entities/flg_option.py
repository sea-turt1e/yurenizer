# Description: フラグオプションの定義

from dataclasses import dataclass
from enum import Enum


class Taigen(Enum):
    # 体言を含むかどうかのフラグ
    EXCLUDE = 0
    INCLUDE = 1


class Yougen(Enum):
    # 用言を含むかどうかのフラグ
    EXCLUDE = 0
    INCLUDE = 1


class Expansion(Enum):
    # 同義語展開の制御フラグ
    ANY = "any"  # 常に展開に使用する
    FROM_ANOTHER = "from_another"  # 自分自身が展開のトリガーとはならないが、同グループ内の別の見出しからは展開される
    NOT_ALL = "not_all"  # 常に展開に使用しない ※削除履歴として利用 (弊害語などが誤って再登録されるのを防ぐため)


class OtherLanguage(Enum):
    # 多言語を日本語へ名寄せするかどうかのフラグ
    DISABLE = 0  # 多言語を日本語へ名寄せしない
    ENABLE = 1  # 多言語を日本語へ名寄せする


class AlphabeticAbbreviation(Enum):
    # アルファベットの略語を名寄せするかどうかのフラグ
    DISABLE = 0  # アルファベットの略語名寄せを行わない
    ENABLE = 1  # アルファベットの略語名寄せを行う


class NonAlphabeticAbbreviation(Enum):
    # 日本語の略語を名寄せするかどうかのフラグ
    DISABLE = 0  # 日本語の略語名寄せを行わない
    ENABLE = 1  # 日本語の略語名寄せを行う


class Alphabet(Enum):
    # アルファベットの表記揺れを名寄せするかどうかのフラグ
    DISABLE = 0  # アルファベットの表記揺れを名寄せしない
    ENABLE = 1  # アルファベットの表記揺れを名寄せする


class OrthographicVariation(Enum):
    # 異表記を名寄せするかどうかのフラグ
    DISABLE = 0  # 異表記を名寄せしない
    ENABLE = 1  # 異表記を名寄せする


class Missspelling(Enum):
    # 誤表記を名寄せするかどうかのフラグ
    DISABLE = 0  # 誤字を名寄せしない
    ENABLE = 1  # 誤字を名寄せする


@dataclass
class FlgInput:
    yougen: Yougen = Yougen.EXCLUDE
    taigen: Taigen = Taigen.INCLUDE
    expansion: Expansion = Expansion.FROM_ANOTHER
    other_language: OtherLanguage = OtherLanguage.ENABLE
    alphabet: Alphabet = Alphabet.ENABLE
    alphabetic_abbreviation: AlphabeticAbbreviation = AlphabeticAbbreviation.ENABLE
    non_alphabetic_abbreviation: NonAlphabeticAbbreviation = NonAlphabeticAbbreviation.ENABLE
    orthographic_variation: OrthographicVariation = OrthographicVariation.ENABLE
    missspelling: Missspelling = Missspelling.ENABLE


@dataclass
class FlgNormalize:
    abbreviation: bool = True
    notation: bool = True
