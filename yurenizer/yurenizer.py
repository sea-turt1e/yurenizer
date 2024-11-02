import csv
import json
from collections import defaultdict
from typing import Dict, List, Optional, Set, Union

import ipdb
from entities import (
    AlphabetAbbreviation,
    Alphabet,
    Expansion,
    FlgInput,
    JapaneseAbbreviation,
    Missspelling,
    OrthographicVariation,
    Taigen,
    Yougen,
    Synonym,
    SynonymField,
)
from sudachipy import Morpheme, dictionary, tokenizer


class SynonymNormalizer:
    def __init__(self, custom_synonym_file: Optional[str] = None) -> None:
        """
        SudachiDictの同義語辞書を使用した表記ゆれ統一ツールの初期化

        Args:
            custom_synonym_file: 追加の同義語定義ファイル（任意）
        """
        # Sudachi初期化
        sudachi_dic = dictionary.Dictionary(dict="full")  # TODO: sudachiの辞書を指定できるようにする
        self.tokenizer_obj = sudachi_dic.create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

        # 品詞マッチ
        self.taigen_matcher = sudachi_dic.pos_matcher(lambda x: x[0] == "名詞")
        self.yougen_matcher = sudachi_dic.pos_matcher(lambda x: x[0] in ["動詞", "形容詞"])

        # 同義語辞書の初期化
        self.synonym_dict: Dict[str, Set[str]] = {}
        self.group_dict: Dict[str, str] = {}  # 単語から同義語グループIDへのマッピング

        # SudachiDictの同義語ファイルを読み込み
        synonyms = self.load_sudachi_synonyms()
        self.synonyms = {int(k): v for k, v in synonyms.items()}

        # # カスタム同義語の読み込み
        # if custom_synonym_file:
        #     self.load_custom_synonyms(custom_synonym_file)

    def load_sudachi_synonyms(self, synonym_file: str = "yurenizer/data/synonyms.txt"):
        """
        SudachiDictのsynonyms.txtから同義語情報を読み込む
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

    # def load_custom_synonyms(self, file_path: str):
    #     """
    #     カスタム同義語定義を読み込む

    #     Args:
    #         file_path: 同義語定義JSONファイルのパス

    #     JSONフォーマット:
    #     {
    #         "標準形": ["同義語1", "同義語2", ...],
    #         ...
    #     }
    #     """
    #     try:
    #         with open(file_path, "r", encoding="utf-8") as f:
    #             custom_synonyms = json.load(f)
    #             for standard, synonyms in custom_synonyms.items():
    #                 if standard not in self.synonym_dict:
    #                     self.synonym_dict[standard] = set()
    #                 self.synonym_dict[standard].update(synonyms)

    #                 # グループ辞書にも追加
    #                 group_id = f"custom_{standard}"
    #                 for word in [standard] + synonyms:
    #                     self.group_dict[word] = group_id

    #     except Exception as e:
    #         print(f"カスタム同義語ファイル読み込みエラー: {e}")

    def get_standard_form(self, morpheme: Morpheme, expansion: Expansion) -> str:
        """
        単語の代表表記を取得

        Args:
            morpheme: 形態素情報
            expansion: 同義語展開の制御フラグ
        Returns:
            標準形（同義語が見つからない場合は元の単語）
        """
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
        japanese_abbreviation: JapaneseAbbreviation = JapaneseAbbreviation.ENABLE,
        alphabet: Alphabet = Alphabet.ENABLE,
        alphabet_abbreviation: AlphabetAbbreviation = AlphabetAbbreviation.ENABLE,
        orthographic_variation: OrthographicVariation = OrthographicVariation.ENABLE,
        missspelling: Missspelling = Missspelling.ENABLE,
    ):
        flg_input = FlgInput(
            yougen=yougen,
            taigen=taigen,
            expansion=expansion,
            japanese_abbreviation=japanese_abbreviation,
            alphabet=alphabet,
            alphabet_abbreviation=alphabet_abbreviation,
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
        flg_normalize = False  # 代表表記するかどうか
        if self.__flg_normalize_by_pos(morpheme, flg_input):
            if self.__flg_normalize_by_alphabet_abbreviation2alphabet(morpheme, flg_input):
                flg_normalize = True
            elif self.__flg_normalize_by_japanese_abbreviation(morpheme, flg_input):
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
                return self.get_standard_form(morpheme, flg_input.expansion)

        return morpheme.surface()

    def __flg_normalize_by_pos(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        品詞情報によって、正規化するかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        flg = False
        if flg_input.taigen == Taigen.INCLUDE and self.taigen_matcher(morpheme):
            return True
        if flg_input.yougen == Yougen.INCLUDE and self.yougen_matcher(morpheme):
            return True
        return flg

    def __flg_normalize_by_alphabet_abbreviation2alphabet(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        アルファベットの略語をアルファベット表記するかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.alphabet_abbreviation == AlphabetAbbreviation.ENABLE and morpheme.surface().isascii():
            abbreviation_id = self.get_synonym_value_from_morpheme(morpheme, SynonymField.ABBREVIATION)
            if abbreviation_id == 1:
                return True
        return False

    def __flg_normalize_by_japanese_abbreviation(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        日本語の略語を名寄せするかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.japanese_abbreviation == JapaneseAbbreviation.ENABLE and not morpheme.surface().isascii():
            abbreviation_id = self.get_synonym_value_from_morpheme(morpheme, SynonymField.ABBREVIATION)
            if abbreviation_id == 2:
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
            if spelling_inconsistency == 1:
                return True
        return False

    def __flg_normalize_by_orthographic_variation(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        異表記を名寄せするかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.orthographic_variation == OrthographicVariation.ENABLE:
            spelling_inconsistency = self.get_synonym_value_from_morpheme(morpheme, SynonymField.SPELLING_INCONSISTENCY)
            if spelling_inconsistency == 2:
                return True
        return False

    def __flg_normalize_by_missspelling(self, morpheme: Morpheme, flg_input: FlgInput) -> bool:
        """
        誤表記を名寄せするかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_input: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        if flg_input.missspelling == Missspelling.ENABLE:
            spelling_inconsistency = self.get_synonym_value_from_morpheme(morpheme, SynonymField.SPELLING_INCONSISTENCY)
            if spelling_inconsistency == 3:
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
            if flg_expansion == 0:
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
    #         standard = self.get_standard_form(normalized)
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
        japanese_abbreviation=JapaneseAbbreviation.ENABLE,
        alphabet=Alphabet.ENABLE,
        alphabet_abbreviation=AlphabetAbbreviation.ENABLE,
        orthographic_variation=OrthographicVariation.ENABLE,
        missspelling=Missspelling.ENABLE,
    )
    # 正規化ツールの初期化
    normalizer = SynonymNormalizer()

    # テスト用テキスト
    texts = [
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
