import csv
import json
from collections import defaultdict
from typing import Dict, List, Optional, Set, Union

import ipdb
from yurenizer.entities import (
    AlphabeticAbbreviation,
    Alphabet,
    Expansion,
    FlgInput,
    NonAlphabeticAbbreviation,
    Missspelling,
    OrthographicVariation,
    Taigen,
    Yougen,
    OtherLanguage,
    TaigenOrYougen,
    FlgExpantion,
    Abbreviation,
    SpellingInconsistency,
    SynonymField,
    Synonym,
    SynonymField,
    SudachiDictType,
    NormalizerConfig,
)
from sudachipy import Morpheme, dictionary, tokenizer


class SynonymNormalizer:
    def __init__(
        self, sudachi_dict: SudachiDictType = SudachiDictType.FULL.value, custom_synonyms_file: Optional[str] = None
    ) -> None:
        """
        SudachiDictの同義語辞書を使用した表記ゆれ統一ツールの初期化

        Args:
            custom_synonym_file: 追加の同義語定義ファイル（任意）
        """
        # Sudachi初期化
        sudachi_dic = dictionary.Dictionary(dict=sudachi_dict)
        self.tokenizer_obj = sudachi_dic.create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

        # 品詞マッチ
        self.taigen_matcher = sudachi_dic.pos_matcher(lambda x: x[0] == "名詞")
        self.yougen_matcher = sudachi_dic.pos_matcher(lambda x: x[0] in ["動詞", "形容詞"])

        # SudachiDictの同義語ファイルを読み込み
        synonyms = self.load_sudachi_synonyms()
        self.synonyms = {int(k): v for k, v in synonyms.items()}

        # カスタム同義語の読み込み
        self.custom_synonyms = {}
        if custom_synonyms_file:
            self.custom_synonyms = self.load_custom_synonyms(custom_synonyms_file)

    def load_sudachi_synonyms(self, synonym_file: str = "yurenizer/data/synonyms.txt"):
        """
        SudachiDictのsynonyms.txtから同義語情報を読み込む

        Args:
            synonym_file: 同義語ファイルのパス
        Returns:
            同義語情報の辞書
        """
        with open(synonym_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            data = [row for row in reader]

        synonyms = defaultdict(list)
        for line in data:
            if not line:
                continue
            synonyms[line[0]].append(
                Synonym(
                    taigen_or_yougen=int(line[1]),  # Taigen or Yougen(体言or用言)
                    flg_expansion=int(line[2]),  # 展開制御フラグ
                    lexeme_id=int(line[3].split("/")[0]),  # グループ内の語彙素番号
                    word_form=int(line[4]),  # 同一語彙素内での語形種別
                    abbreviation=int(line[5]),  # 略語
                    spelling_inconsistency=int(line[6]),  # 表記揺れ情報
                    field=line[7],  # 分野情報
                    lemma=line[8],
                )  # 見出し語
            )
        return synonyms

    def load_custom_synonyms(self, file_path: str) -> Dict[str, Set[str]]:
        """
        カスタム同義語定義を読み込む

        Args:
            file_path: 同義語定義JSONファイルのパス

        JSONフォーマット:
        {
            "標準形": ["同義語1", "同義語2", ...],
            ...
        }
        Returns:
            カスタム同義語定義の辞書 (標準形: (同義語1, 同義語2, ...))
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                custom_synonyms = json.load(f)
                custom_synonyms = {k: set(v) for k, v in custom_synonyms.items() if v}
                return custom_synonyms

        except Exception as e:
            raise ValueError(f"カスタム同義語定義の読み込みに失敗しました: {e}")

    def get_standard_yougen(self, morpheme: Morpheme, expansion: Expansion) -> str:
        """
        用言の代表表記を取得

        Args:
            morpheme: 形態素情報
            expansion: 同義語展開の制御フラグ
        Returns:
            標準形（同義語が見つからない場合は元の単語）
        """
        # カスタム同義語定義を使用
        custom_representation = self.normalize_word_by_custom_synonyms(morpheme.surface())
        if custom_representation:
            return custom_representation

        # グループ辞書から同義語グループを探す
        synonym_group = self.get_synonym_group(morpheme)
        if synonym_group:
            yougen_group = [s for s in synonym_group if s.taigen_or_yougen == TaigenOrYougen.YOUGEN.value]
            if expansion == Expansion.ANY:
                return yougen_group[0].lemma
            elif expansion == Expansion.FROM_ANOTHER:
                if {y.lemma: y.flg_expansion for y in yougen_group}.get(morpheme.normalized_form()) == 0:
                    return yougen_group[0].lemma
        return morpheme.surface()

    def get_standard_taigen(self, morpheme: Morpheme, expansion: Expansion) -> str:
        """
        体言の代表表記を取得

        Args:
            morpheme: 形態素情報
            expansion: 同義語展開の制御フラグ
        Returns:
            標準形（同義語が見つからない場合は元の単語）
        """
        # カスタム同義語定義を使用
        custom_representation = self.normalize_word_by_custom_synonyms(morpheme.surface())
        if custom_representation:
            return custom_representation
        # グループ辞書から同義語グループを探す
        synonym_group = self.get_synonym_group(morpheme)
        if synonym_group:
            if expansion == Expansion.ANY:
                return synonym_group[0].lemma
            elif expansion == Expansion.FROM_ANOTHER:
                if {s.lemma: s.flg_expansion for s in synonym_group}.get(morpheme.normalized_form()) == 0:
                    return synonym_group[0].lemma
        return morpheme.surface()

    def normalize(
        self,
        text: str,
        config: NormalizerConfig = NormalizerConfig(),
    ) -> str:
        """
        テキストの表記ゆれと同義語を統一する

        Args:
            config: 正規化のオプション

        Returns:
            正規化された文字列
        """
        if not text:
            raise ValueError("テキストが空です")
        flg_input = FlgInput(
            yougen=Yougen.from_int(config.yougen),
            taigen=Taigen.from_int(config.taigen),
            expansion=Expansion.from_str(config.expansion),
            other_language=OtherLanguage.from_int(config.other_language),
            alphabet=Alphabet.from_int(config.alphabet),
            alphabetic_abbreviation=AlphabeticAbbreviation.from_int(config.alphabetic_abbreviation),
            non_alphabetic_abbreviation=NonAlphabeticAbbreviation.from_int(config.non_alphabetic_abbreviation),
            orthographic_variation=OrthographicVariation.from_int(config.orthographic_variation),
            missspelling=Missspelling.from_int(config.missspelling),
        )
        return self.__normalize_text(text=text, flg_input=flg_input)

    def __normalize_text(self, text: str, flg_input: FlgInput) -> str:
        """
        テキストの表記ゆれと同義語を統一する

        Args:
            text: 正規化する文字列
        Returns:
            正規化された文字列
        """
        morphemes = self.get_morphemes(text)
        normalized_parts = []
        for morpheme in morphemes:
            normalized_parts.append(self.normalize_word(morpheme, flg_input))
        return "".join(normalized_parts)

    def normalize_word(self, morpheme: Morpheme, flg_input: FlgInput) -> str:
        """
        単語の表記ゆれと同義語を統一する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化された文字列
        """
        # 用言の場合
        if self.yougen_matcher(morpheme) and flg_input.yougen == Yougen.INCLUDE:
            return self.get_standard_yougen(morpheme, flg_input.expansion)

        # 体言の場合
        flg_normalize = False  # 代表表記するかどうか
        if self.taigen_matcher(morpheme) and flg_input.taigen == Taigen.INCLUDE:
            if self.__flg_normalize_other_language(morpheme, flg_input):
                flg_normalize = True
            elif self.__flg_normalize_by_alphabetic_abbreviation(morpheme, flg_input):
                flg_normalize = True
            elif self.__flg_normalize_by_non_alphabetic_abbreviation(morpheme, flg_input):
                flg_normalize = True
            elif self.__flg_normalize_by_alphabet_notation(morpheme, flg_input):
                flg_normalize = True
            elif self.__flg_normalize_by_orthographic_variation(morpheme, flg_input):
                flg_normalize = True
            elif self.__flg_normalize_by_missspelling(morpheme, flg_input):
                flg_normalize = True
            elif self.__flg_normalize_by_expansion(morpheme, flg_input):
                flg_normalize = True

        if flg_normalize:
            if flg_input.expansion in (Expansion.ANY, Expansion.FROM_ANOTHER):
                # 同義語グループのIDsを取得
                synonym_group_ids = morpheme.synonym_group_ids()
                if len(synonym_group_ids) > 1:
                    return morpheme.surface()
                # 同義語展開
                return self.get_standard_taigen(morpheme, flg_input.expansion)

        return morpheme.surface()

    def normalize_word_by_custom_synonyms(self, word: str) -> Optional[str]:
        """
        カスタム同義語定義を使用して単語を正規化する。なければそのまま返す

        Args:
            word: 正規化する単語
        Returns:
            正規化された単語
        """
        for k, v in self.custom_synonyms.items():
            if word in v:
                return k
        return None

    def __flg_normalize_other_language(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        多言語を日本語にするかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.other_language == OtherLanguage.ENABLE and not morpheme.surface().isascii():
            return True
        return False

    def __flg_normalize_by_alphabetic_abbreviation(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        アルファベットの略語を正規化するかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.alphabetic_abbreviation == AlphabeticAbbreviation.ENABLE and morpheme.surface().isascii():
            abbreviation_id = self.get_synonym_value_from_morpheme(morpheme, SynonymField.ABBREVIATION)
            if abbreviation_id == Abbreviation.ALPHABET.value:
                return True
        return False

    def __flg_normalize_by_non_alphabetic_abbreviation(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        日本語の略語を正規化するかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if (
            flg_input.non_alphabetic_abbreviation == NonAlphabeticAbbreviation.ENABLE
            and not morpheme.surface().isascii()
        ):
            abbreviation_id = self.get_synonym_value_from_morpheme(morpheme, SynonymField.ABBREVIATION)
            if abbreviation_id == Abbreviation.NOT_ALPHABET.value:
                return True
        return False

    def __flg_normalize_by_alphabet_notation(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        アルファベットを日本語にするかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.alphabet == Alphabet.ENABLE and morpheme.surface().isascii():
            spelling_inconsistency = self.get_synonym_value_from_morpheme(morpheme, SynonymField.SPELLING_INCONSISTENCY)
            if spelling_inconsistency == SpellingInconsistency.ALPHABET.value:
                return True
        return False

    def __flg_normalize_by_orthographic_variation(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        異表記を正規化するかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.orthographic_variation == OrthographicVariation.ENABLE:
            spelling_inconsistency = self.get_synonym_value_from_morpheme(morpheme, SynonymField.SPELLING_INCONSISTENCY)
            if spelling_inconsistency == SpellingInconsistency.ORTHOGRAPHIC_VARIATION.value:
                return True
        return False

    def __flg_normalize_by_missspelling(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        誤表記を正規化するかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.missspelling == Missspelling.ENABLE:
            spelling_inconsistency = self.get_synonym_value_from_morpheme(morpheme, SynonymField.SPELLING_INCONSISTENCY)
            if spelling_inconsistency == SpellingInconsistency.MISSPELLING.value:
                return True
        return False

    def __flg_normalize_by_expansion(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        同義語展開の制御フラグによって、正規化するかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.expansion == Expansion.ANY:
            return True
        if flg_input.expansion == Expansion.FROM_ANOTHER:
            flg_expansion = self.get_synonym_value_from_morpheme(morpheme, SynonymField.FLG_EXPANSION)
            if flg_expansion == FlgExpantion.ANY.value:
                return True
        return False

    def get_morphemes(self, text: str) -> List[str]:
        """
        テキストを形態素解析する

        Args:
            text: 形態素解析する文字列
        Returns:
            形態素のリスト
        """
        tokens = self.tokenizer_obj.tokenize(text, self.mode)
        return [token for token in tokens]

    def get_synonym_group(self, morpheme: Morpheme):
        synonym_group_ids = morpheme.synonym_group_ids()
        if synonym_group_ids:
            return self.synonyms[synonym_group_ids[0]]
        return None

    def get_synonym_value_from_morpheme(
        self, morpheme: Morpheme, synonym_attr: SynonymField
    ) -> Optional[Union[str, int]]:
        synonym_group = self.get_synonym_group(morpheme)
        if synonym_group:
            return next(
                (getattr(item, synonym_attr.value) for item in synonym_group if item.lemma == morpheme.surface()), None
            )
        return None
