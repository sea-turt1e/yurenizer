import csv
import json
from collections import defaultdict
from typing import Dict, List, Optional, Set

import ipdb
from entities import (
    AlphabetAbbreviation,
    AlphabetNotation,
    Expansion,
    FlgOption,
    JapaneseAbbreviation,
    Missspelling,
    OrthographicVariation,
    Taigen,
    Yougen,
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
        sudachi_dic = dictionary.Dictionary()
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

        # カスタム同義語の読み込み
        if custom_synonym_file:
            self.load_custom_synonyms(custom_synonym_file)

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
                {
                    "taigen_or_yougen": int(line[1]),  # Taigen or Yougen(体言or用言)
                    "flg_expansion": int(line[2]),  # 展開制御フラグ
                    "lexeme_id": int(line[3].split("/")[0]),  # グループ内の語彙素番号
                    "word_form": int(line[4]),  # 同一語彙素内での語形種別
                    "abbreviation": int(line[5]),  # 略語
                    "spelling_inconsistencies": int(line[6]),  # 表記揺れ情報
                    "field": line[7],  # 分野情報
                    "lemma": line[8],  # 見出し語
                }
            )
        return synonyms

    def load_custom_synonyms(self, file_path: str):
        """
        カスタム同義語定義を読み込む

        Args:
            file_path: 同義語定義JSONファイルのパス

        JSONフォーマット:
        {
            "標準形": ["同義語1", "同義語2", ...],
            ...
        }
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                custom_synonyms = json.load(f)
                for standard, synonyms in custom_synonyms.items():
                    if standard not in self.synonym_dict:
                        self.synonym_dict[standard] = set()
                    self.synonym_dict[standard].update(synonyms)

                    # グループ辞書にも追加
                    group_id = f"custom_{standard}"
                    for word in [standard] + synonyms:
                        self.group_dict[word] = group_id

        except Exception as e:
            print(f"カスタム同義語ファイル読み込みエラー: {e}")

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
        synonym_group = self.synonyms[morpheme.synonym_group_ids()[0]]
        if synonym_group:
            if expansion == Expansion.ANY:
                return synonym_group[0]["lemma"]
            elif expansion == Expansion.FROM_ANOTHER:
                if {s["lemma"]: s["flg_expansion"] for s in synonym_group}.get(morpheme.normalized_form()) == 0:
                    return synonym_group[0]["lemma"]
        return morpheme.normalized_form()

    def normalize(
        self,
        text: str,
        has_taigen: Taigen = Taigen.INCLUDE,
        has_yougen: Yougen = Taigen.EXCLUDE,
        expansion: Expansion = Expansion.FROM_ANOTHER,
        alphabet_abbreviation: AlphabetAbbreviation = AlphabetAbbreviation.ENABLE,
        japanese_abbreviation: JapaneseAbbreviation = JapaneseAbbreviation.ENABLE,
        alphabet_notation: AlphabetNotation = AlphabetNotation.ENABLE,
        orthographic_variation: OrthographicVariation = OrthographicVariation.ENABLE,
        missspelling: Missspelling = Missspelling.ENABLE,
    ):
        flg_option = FlgOption(
            yougen=has_yougen,
            taigen=has_taigen,
            expansion=expansion,
            alphabet_abbreviation=alphabet_abbreviation,
            japanese_abbreviation=japanese_abbreviation,
            alphabet_notation=alphabet_notation,
            orthographic_variation=orthographic_variation,
            missspelling=missspelling,
        )

        return self.__normalize_text(text=text, flg_option=flg_option)

    def __normalize_text(self, text: str, flg_option: FlgOption) -> str:
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
            self.normalize_word(morpheme, flg_option)

    def normalize_word(self, morpheme: Morpheme, flg_option: FlgOption) -> str:
        """
        単語の表記ゆれと同義語を統一する

        Args:
            morpheme: 形態素情報
            flg_option: 正規化のオプション
        Returns:
            正規化された文字列
        """
        flg_normalize = False
        if self.__flg_normalize_by_pos(morpheme, flg_option):
            ipdb.set_trace()
            # TODO: 判定の仕方を考える。
            if self.__flg_normalize_by_alphabet_abbreviation(morpheme, flg_option):
                flg_normalize = True
            elif self.__flg_normalize_by_japanese_abbreviation(morpheme, flg_option):
                flg_normalize = True
            elif self.__flg_normalize_by_alphabet_notation(morpheme, flg_option):
                flg_normalize = True
            elif self.__flg_normalize_by_orthographic_variation(morpheme, flg_option):
                flg_normalize = True
            elif self.__flg_normalize_by_missspelling(morpheme, flg_option):
                flg_normalize = True

        if flg_normalize:
            if flg_option.expansion in (Expansion.ANY, Expansion.FROM_ANOTHER):
                # 同義語グループのIDsを取得
                synonym_group_ids = morpheme.synonym_group_ids()
                if len(synonym_group_ids) > 1:
                    return morpheme.normalized_form()
                # 同義語展開
                return self.get_standard_form(morpheme, flg_option.expansion)
        return morpheme.normalized_form()

    def __flg_normalize_by_pos(self, morpheme: Morpheme, flg_option: FlgOption) -> bool:
        """
        品詞情報によって、正規化するかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_option: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        flg = False
        if flg_option.taigen == Taigen.INCLUDE and self.taigen_matcher(morpheme):
            return True
        if flg_option.yougen == Yougen.INCLUDE and self.yougen_matcher(morpheme):
            return True
        return flg

    def __flg_normalize_by_alphabet_abbreviation(self, morpheme: Morpheme, flg_option: FlgOption) -> bool:
        """
        アルファベットの略語を名寄せするかどうかを判断する

        Args:
            morpheme: 形態素情報
            flg_option: 正規化のオプション
        Returns:
            正規化する場合はTrue, しない場合はFalse
        """
        # morpheme.surface()がアルファベットかどうか判断
        if flg_option.alphabet_abbreviation == AlphabetAbbreviation.ENABLE and morpheme.surface().isascii():
            return True
        return False

    def tokenize(self, text: str) -> List[str]:
        """
        テキストを形態素解析する

        Args:
            text: 形態素解析する文字列
        Returns:
            形態素のリスト
        """

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

    def get_synonyms(self, word: str) -> Set[str]:
        """
        単語の同義語セットを取得

        Args:
            word: 対象の単語
        Returns:
            同義語のセット
        """
        # グループ辞書から同義語グループを探す
        group_id = self.group_dict.get(word)
        if group_id:
            # 同じグループに属する全ての単語を返す
            for standard, synonyms in self.synonym_dict.items():
                if word in synonyms:
                    return synonyms
        return set()

    def analyze_variants(self, text: str) -> List[Dict[str, any]]:
        """
        テキスト中の表記ゆれと同義語を分析

        Args:
            text: 分析する文字列
        Returns:
            異形情報のリスト
        """
        tokens = self.tokenizer_obj.tokenize(text, self.mode)
        variants = []

        for token in tokens:
            surface = token.surface()
            normalized = token.normalized_form()
            standard = self.get_standard_form(normalized)
            synonyms = self.get_synonyms(normalized)

            if surface != standard or synonyms:
                variant_info = {
                    "surface": surface,
                    "normalized": normalized,
                    "standard": standard,
                    "synonyms": list(synonyms),
                    "part_of_speech": token.part_of_speech(),
                    "group_id": self.group_dict.get(normalized),
                }
                variants.append(variant_info)

        return variants


# 使用例
if __name__ == "__main__":
    # 正規化ツールの初期化
    normalizer = SynonymNormalizer()

    # テスト用テキスト
    text = "alphabet曖昧なバス停で待機する。スマホを確認する。"

    morphemes = normalizer.normalize(text)
    for morpheme in morphemes:
        normalizer.flg_normalize_by_alphabet_abbreviation(morpheme, FlgOption)
    print(morphemes)

    # # テキストの正規化
    # normalized = normalizer.normalize_text(test_text)
    # print(f"正規化結果: {normalized}")

    # # 異形の分析
    # variants = normalizer.analyze_variants(test_text)
    # print("\n異形分析結果:")
    # print(json.dumps(variants, ensure_ascii=False, indent=2))

    # # 特定の単語の同義語を取得
    # word = "待機"
    # synonyms = normalizer.get_synonyms(word)
    # print(f"\n「{word}」の同義語: {synonyms}")
