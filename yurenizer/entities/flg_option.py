# Definition of flag options（フラグオプションの定義）

from dataclasses import dataclass
from enum import Enum


class UnifyLevel(Enum):
    # Flag to specify the unification level（統一レベルを指定するフラグ）
    LEXEME = "lexeme"  # Unify words with the same lexeme number（語彙素番号が同じもので統一）
    WORD_FORM = "word_form"  # Unify words with the same word form number（語形番号が同じもので統一）
    ABBREVIATION = "abbreviation"  # Unify words with the same abbreviation number（略語番号が同じもので統一）

    @classmethod
    def from_str(cls, value: str):
        return cls(value)


class Taigen(Enum):
    # Flag to include Taigen (nouns)（体言を含むかどうかのフラグ）
    EXCLUDE = 0
    INCLUDE = 1

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Yougen(Enum):
    # Flag to include Yougen (verbs and adjectives)（用言を含むかどうかのフラグ）
    EXCLUDE = 0
    INCLUDE = 1

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Expansion(Enum):
    # Synonym expansion control flag（同義語展開の制御フラグ）
    ANY = "any"  # Always use for expansion（常に展開に使用する）
    FROM_ANOTHER = "from_another"  # Does not trigger expansion from itself but can be expanded from other entries in the same group（自分自身が展開のトリガーとはならないが、同グループ内の別の見出しからは展開される）
    NOT_ALL = "not_all"  # Never use for expansion; used to prevent re-registration of harmful words（常に展開に使用しない ※削除履歴として利用）

    @classmethod
    def from_str(cls, value: str):
        return cls(value)


class OtherLanguage(Enum):
    # Flag to normalize other languages to Japanese（他言語を日本語へ正規化するかどうかのフラグ）
    DISABLE = 0  # Do not normalize other languages（多言語を日本語へ正規化しない）
    ENABLE = 1  # Normalize other languages（多言語を日本語へ正規化する）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Alias(Enum):
    # Flag to use aliases（別称を使用するかどうかのフラグ）
    DISABLE = 0  # Do not use aliases（別称を使用しない）
    ENABLE = 1  # Use aliases（別称を使用する）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class OldName(Enum):
    # Flag to use old names（旧称を使用するかどうかのフラグ）
    DISABLE = 0  # Do not use old names（旧称を使用しない）
    ENABLE = 1  # Use old names（旧称を使用する）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Misuse(Enum):
    # Flag to use misused words（誤用を使用するかどうかのフラグ）
    DISABLE = 0  # Do not use misused words（誤用を使用しない）
    ENABLE = 1  # Use misused words（誤用を使用する）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class AlphabeticAbbreviation(Enum):
    # Flag to normalize alphabetic abbreviations（アルファベットの略語を正規化するかどうかのフラグ）
    DISABLE = 0  # Do not normalize alphabetic abbreviations（アルファベットの略語正規化を行わない）
    ENABLE = 1  # Normalize alphabetic abbreviations（アルファベットの略語正規化を行う）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class NonAlphabeticAbbreviation(Enum):
    # Flag to normalize non-alphabetic abbreviations（日本語の略語を正規化するかどうかのフラグ）
    DISABLE = 0  # Do not normalize non-alphabetic abbreviations（日本語の略語正規化を行わない）
    ENABLE = 1  # Normalize non-alphabetic abbreviations（日本語の略語正規化を行う）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Alphabet(Enum):
    # Flag to normalize alphabetic spelling variations（アルファベットの表記揺れを正規化するかどうかのフラグ）
    DISABLE = 0  # Do not normalize alphabetic spelling variations（アルファベットの表記揺れを正規化しない）
    ENABLE = 1  # Normalize alphabetic spelling variations（アルファベットの表記揺れを正規化する）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class OrthographicVariation(Enum):
    # Flag to normalize orthographic variations（異表記を正規化するかどうかのフラグ）
    DISABLE = 0  # Do not normalize orthographic variations（異表記を正規化しない）
    ENABLE = 1  # Normalize orthographic variations（異表記を正規化する）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class Misspelling(Enum):
    # Flag to normalize misspellings（誤表記を正規化するかどうかのフラグ）
    DISABLE = 0  # Do not normalize misspellings（誤字を正規化しない）
    ENABLE = 1  # Normalize misspellings（誤字を正規化する）

    @classmethod
    def from_int(cls, value: int):
        return cls(value)


class CusotomSynonym(Enum):
    # Flag to use custom synonyms（カスタムシノニムを使用するかどうかのフラグ）
    DISABLE = 0  # Do not use custom synonyms（カスタムシノニムを使用しない）
    ENABLE = 1  # Use custom synonyms（カスタムシノニムを使用する）

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
    misspelling: Misspelling = Misspelling.ENABLE
    custom_synonym: CusotomSynonym = CusotomSynonym.ENABLE
