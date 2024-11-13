from dataclasses import dataclass, asdict
from enum import Enum
import json


class TaigenOrYougen(Enum):
    # Noun or Verb（体言または用言）
    TAIGEN = 1
    YOUGEN = 2


class FlgExpantion(Enum):
    # Synonym expansion control flag（同義語展開の制御フラグ）
    ANY = 0  # Always use for expansion（常に展開に使用する）
    FROM_ANOTHER = 1  # Does not trigger expansion from itself but can be expanded from other entries in the same group（自分自身が展開のトリガーとはならないが、同グループ内の別の見出しからは展開される）
    NOT_ALL = 2  # Never use for expansion; used as deletion history to prevent re-registration of harmful words（常に展開に使用しない ※削除履歴として利用 (弊害語などが誤って再登録されるのを防ぐため)）


class WordForm(Enum):
    # Word form type within the same lexeme（同一語彙内での語形種別）
    REPRESENTATIVE = 0  # Representative word（代表語）
    TRANSLATION = 1  # Translation（対訳）
    ALIAS = 2  # Alias（別称）
    OLD_NAME = 3  # Old name（旧称）
    MISUSE = 4  # Misuse（誤用）


class Abbreviation(Enum):
    # Abbreviation（略語）
    REPRESENTATIVE = 0  # Representative（代表語）
    ALPHABET = 1  # Alphabetical abbreviation（アルファベット表記の略語）
    NOT_ALPHABET = 2  # Non-alphabetical abbreviation（アルファベット表記以外の略語）


class SpellingInconsistency(Enum):
    # Spelling inconsistency（表記揺れ）
    REPRESENTATIVE = 0  # Representative（代表語）
    ALPHABET = 1  # Alphabet notation（アルファベット表記）
    ORTHOGRAPHIC_VARIATION = 2  # Orthographic variation（異表記）
    MISSPELLING = 3  # Misspelling（誤表記）


class SynonymField(Enum):
    TAIGEN_OR_YOUGEN = "taigen_or_yougen"
    FLG_EXPANSION = "flg_expansion"
    LEXEME_ID = "lexeme_id"
    WORD_FORM = "word_form"
    ABBREVIATION = "abbreviation"
    SPELLING_INCONSISTENCY = "spelling_inconsistency"
    FIELD = "field"
    LEMMA = "lemma"

    def __str__(self):
        return self.value


@dataclass
class Synonym:
    taigen_or_yougen: TaigenOrYougen
    flg_expansion: FlgExpantion
    lexeme_id: int
    word_form: WordForm
    abbreviation: Abbreviation
    spelling_inconsistency: SpellingInconsistency
    field: str
    lemma: str

    def __str__(self):
        return json.dumps(asdict(self), ensure_ascii=False)
