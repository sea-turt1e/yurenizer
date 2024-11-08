from dataclasses import dataclass, asdict
from enum import Enum
import json


class TaigenOrYougen(Enum):
    # 体言または用言
    TAIGEN = 1
    YOUGEN = 2


class FlgExpantion(Enum):
    # 同義語展開の制御フラグ
    ANY = 0  # 常に展開に使用する
    FROM_ANOTHER = 1  # 自分自身が展開のトリガーとはならないが、同グループ内の別の見出しからは展開される
    NOT_ALL = 2  # 常に展開に使用しない ※削除履歴として利用 (弊害語などが誤って再登録されるのを防ぐため)


class WordForm(Enum):
    # 同一語彙内での語形種別
    REPRESENTATIVE = 0  # 代表語
    TRANSLATION = 1  # 対訳
    ALIAS = 2  # 別称
    OLD_NAME = 3  # 旧称
    MISUSE = 4  # 誤用


class Abbreviation(Enum):
    # 略語
    REPRESENTATIVE = 0  # 代表語
    ALPHABET = 1  # アルファベット表記の略語
    NOT_ALPHABET = 2  # アルファベット表記以外の略語


class SpellingInconsistency(Enum):
    # 表記揺れ
    REPRESENTATIVE = 0  # 代表語
    ALPHABET = 1  # アルファベット表記
    ORTHOGRAPHIC_VARIATION = 2  # 異表記
    MISSPELLING = 3  # 誤表記


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
