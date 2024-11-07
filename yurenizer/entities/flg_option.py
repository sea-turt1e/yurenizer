# Description: フラグオプションの定義

from dataclasses import dataclass
from enum import Enum


class UnifyLevel(Enum):
    # 統一レベルを指定するフラグ
    LEXEME = "lexeme"  # 語彙素番号が同じもので統一
    WORD_FORM = "word_form"  # 語形番号が同じもので統一
    ABBREVIATION = "abbreviation"  # 略語番号が同じもので統一

    @classmethod
    def from_str(cls, value: str):
        return cls(value)


class Taigen(Enum):
    # 体言を含むかどうかのフラグ
    EXCLUDE = 0
    INCLUDE = 1

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Yougen(Enum):
    # 用言を含むかどうかのフラグ
    EXCLUDE = 0
    INCLUDE = 1

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Expansion(Enum):
    # 同義語展開の制御フラグ
    ANY = "any"  # 常に展開に使用する
    FROM_ANOTHER = "from_another"  # 自分自身が展開のトリガーとはならないが、同グループ内の別の見出しからは展開される
    NOT_ALL = "not_all"  # 常に展開に使用しない ※削除履歴として利用 (弊害語などが誤って再登録されるのを防ぐため)

    @classmethod
    def from_str(cls, value: str):
        return cls(value)


class OtherLanguage(Enum):
    # 他言語を日本語へ正規化するかどうかのフラグ
    DISABLE = 0  # 多言語を日本語へ正規化しない
    ENABLE = 1  # 多言語を日本語へ正規化する

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Alias(Enum):
    # 別称を使用するかどうかのフラグ
    DISABLE = 0  # 別称を使用しない
    ENABLE = 1  # 別称を使用する

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class OldName(Enum):
    # 旧称を使用するかどうかのフラグ
    DISABLE = 0  # 旧称を使用しない
    ENABLE = 1  # 旧称を使用する

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Misuse(Enum):
    # 誤用を使用するかどうかのフラグ
    DISABLE = 0  # 誤用を使用しない
    ENABLE = 1  # 誤用を使用する

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class AlphabeticAbbreviation(Enum):
    # アルファベットの略語を正規化するかどうかのフラグ
    DISABLE = 0  # アルファベットの略語正規化を行わない
    ENABLE = 1  # アルファベットの略語正規化を行う

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class NonAlphabeticAbbreviation(Enum):
    # 日本語の略語を正規化するかどうかのフラグ
    DISABLE = 0  # 日本語の略語正規化を行わない
    ENABLE = 1  # 日本語の略語正規化を行う

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Alphabet(Enum):
    # アルファベットの表記揺れを正規化するかどうかのフラグ
    DISABLE = 0  # アルファベットの表記揺れを正規化しない
    ENABLE = 1  # アルファベットの表記揺れを正規化する

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class OrthographicVariation(Enum):
    # 異表記を正規化するかどうかのフラグ
    DISABLE = 0  # 異表記を正規化しない
    ENABLE = 1  # 異表記を正規化する

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Missspelling(Enum):
    # 誤表記を正規化するかどうかのフラグ
    DISABLE = 0  # 誤字を正規化しない
    ENABLE = 1  # 誤字を正規化する

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class CusotomSynonym(Enum):
    # カスタムシノニムを使用するかどうかのフラグ
    DISABLE = 0  # カスタムシノニムを使用しない
    ENABLE = 1  # カスタムシノニムを使用する

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


@dataclass
class FlgInput:
    unify_level: UnifyLevel = UnifyLevel.LEXEME
    taigen: Taigen = Taigen.INCLUDE
    yougen: Yougen = Yougen.EXCLUDE
    expansion: Expansion = Expansion.FROM_ANOTHER
    other_language: OtherLanguage = OtherLanguage.ENABLE
    alias: Alias = Alias.ENABLE
    old_name: OldName = OldName.ENABLE
    misuse: Misuse = Misuse.ENABLE
    alphabetic_abbreviation: AlphabeticAbbreviation = AlphabeticAbbreviation.ENABLE
    non_alphabetic_abbreviation: NonAlphabeticAbbreviation = NonAlphabeticAbbreviation.ENABLE
    alphabet: Alphabet = Alphabet.ENABLE
    orthographic_variation: OrthographicVariation = OrthographicVariation.ENABLE
    missspelling: Missspelling = Missspelling.ENABLE
    custom_synonym: CusotomSynonym = CusotomSynonym.ENABLE
