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
        taigen: Taigen = Taigen.INCLUDE,
        yougen: Yougen = Taigen.EXCLUDE,
        expansion: Expansion = Expansion.FROM_ANOTHER,
        other_language: OtherLanguage = OtherLanguage.ENABLE,
        alphabet: Alphabet = Alphabet.ENABLE,
        alphabetic_abbreviation: AlphabeticAbbreviation = AlphabeticAbbreviation.ENABLE,
        non_alphabetic_abbreviation: NonAlphabeticAbbreviation = NonAlphabeticAbbreviation.ENABLE,
        orthographic_variation: OrthographicVariation = OrthographicVariation.ENABLE,
        missspelling: Missspelling = Missspelling.ENABLE,
    ):
        """
        テキストの表記ゆれと同義語を統一する

        Args:
            text: 正規化する文字列
            taigen: 統一するのに体言を含むかどうかのフラグ。デフォルトは含む（default=1）。含まない場合は0を指定。
            yougen: 統一するのに用言を含むかどうかのフラグ。デフォルトは含まない（default=0）。含む場合は1を指定。
            expansion: 同義語展開の制御フラグ。デフォルトは展開制御フラグが0のもののみ展開（default="from_another"）。"ANY"を指定すると展開制御フラグが常に展開する。
            other_language: 日本語以外の言語を日本語に正規化するかどうかのフラグ。デフォルトは正規化する（default=1）。正規化しない場合は0を指定。
            alphabet: アルファベットの表記揺れを正規化するかどうかのフラグ。デフォルトは正規化する（default=1）。正規化しない場合は0を指定。
            alphabetic_abbreviation: アルファベットの略語を正規化するかどうかのフラグ。デフォルトは正規化する（default=1）。正規化しない場合は0を指定。
            non_alphabetic_abbreviation: 日本語の略語を正規化するかどうかのフラグ。デフォルトは正規化する（default=1）。正規化しない場合は0を指定。
            orthographic_variation: 異表記を正規化するかどうかのフラグ。デフォルトは正規化する（default=1）。正規化しない場合は0を指定。
            missspelling: 誤表記を正規化するかどうかのフラグ。デフォルトは正規化する（default=1）。正規化しない場合は0を指定。
        Returns:
            正規化された文字列

        See Also:
            SudachiDictの同義語辞書ソース:
            https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md#%E5%90%8C%E7%BE%A9%E8%AA%9E%E8%BE%9E%E6%9B%B8%E3%82%BD%E3%83%BC%E3%82%B9-%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88
        """

        if not text:
            raise ValueError("テキストが空です")
        flg_input = FlgInput(
            yougen=yougen,
            taigen=taigen,
            expansion=expansion,
            other_language=other_language,
            alphabet=alphabet,
            alphabetic_abbreviation=alphabetic_abbreviation,
            non_alphabetic_abbreviation=non_alphabetic_abbreviation,
            orthographic_variation=orthographic_variation,
            missspelling=missspelling,
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

    # def get_synonyms(self, word: str) -> Set[str]:
    #     """
    #     単語の同義語セットを取得

    #     Args:
    #         word: 対象の単語
    #     Returns:
    #         同義語のセット
    #     """
    #     # グループ辞書から同義語グループを探す
    #     group_id = self.group_dict.get(word)
    #     if group_id:
    #         # 同じグループに属する全ての単語を返す
    #         for standard, synonyms in self.synonym_dict.items():
    #             if word in synonyms:
    #                 return synonyms
    #     return set()

    # def analyze_variants(self, text: str) -> List[Dict[str, any]]:
    #     """
    #     テキスト中の表記ゆれと同義語を分析

    #     Args:
    #         text: 分析する文字列
    #     Returns:
    #         異形情報のリスト
    #     """
    #     tokens = self.tokenizer_obj.tokenize(text, self.mode)
    #     variants = []

    #     for token in tokens:
    #         surface = token.surface()
    #         normalized = token.normalized_form()
    #         standard = self.get_standard_taigen(normalized)
    #         synonyms = self.get_synonyms(normalized)

    #         if surface != standard or synonyms:
    #             variant_info = {
    #                 "surface": surface,
    #                 "normalized": normalized,
    #                 "standard": standard,
    #                 "synonyms": list(synonyms),
    #                 "part_of_speech": token.part_of_speech(),
    #                 "group_id": self.group_dict.get(normalized),
    #             }
    #             variants.append(variant_info)

    #     return variants


# 使用例
if __name__ == "__main__":
    flg_input = FlgInput(
        taigen=Taigen.INCLUDE,
        yougen=Yougen.EXCLUDE,
        expansion=Expansion.FROM_ANOTHER,
        other_language=OtherLanguage.ENABLE,
        alphabet=Alphabet.ENABLE,
        alphabetic_abbreviation=AlphabeticAbbreviation.ENABLE,
        non_alphabetic_abbreviation=NonAlphabeticAbbreviation.ENABLE,
        orthographic_variation=OrthographicVariation.ENABLE,
        missspelling=Missspelling.ENABLE,
    )
    # 正規化ツールの初期化
    normalizer = SynonymNormalizer()

    # テスト用テキスト
    texts = [
        "USA",
        "America",
        "alphabet曖昧なバス停で待機する。スマホを確認する。",
        "チェックリストを行う。",
        "チェックを行う",
        "checkを行う。",
    ]
    print("FROM_ANOTHERの場合")
    for text in texts:
        print(f"テキスト:　 {text}")
        normalized_text = normalizer.normalize(text, alphabet=Alphabet.DISABLE, expansion=Expansion.FROM_ANOTHER)
        print(f"正規化結果: {normalized_text}")

    print("ANYの場合")
    for text in texts:
        print(f"テキスト:　 {text}")
        normalized_text = normalizer.normalize(text, expansion=Expansion.ANY)
        print(f"正規化結果: {normalized_text}")
