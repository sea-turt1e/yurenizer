import csv
import json
from collections import defaultdict
from importlib import resources
from typing import Dict, List, Set

import ipdb
from sudachipy import dictionary, tokenizer


class SudachiSynonymNormalizer:
    def __init__(self, custom_synonym_file: str = None):
        """
        SudachiDictの同義語辞書を使用した表記ゆれ統一ツールの初期化

        Args:
            custom_synonym_file: 追加の同義語定義ファイル（任意）
        """
        # Sudachi初期化
        self.tokenizer_obj = dictionary.Dictionary().create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

        # 同義語辞書の初期化
        self.synonym_dict: Dict[str, Set[str]] = {}
        self.group_dict: Dict[str, str] = {}  # 単語から同義語グループIDへのマッピング

        # SudachiDictの同義語ファイルを読み込み
        self.load_sudachi_synonyms()

        # カスタム同義語の読み込み
        if custom_synonym_file:
            self.load_custom_synonyms(custom_synonym_file)

    def load_sudachi_synonyms(self, synonym_file: str = "synonyms.txt"):
        """
        SudachiDictのsynonyms.txtから同義語情報を読み込む
        """
        with open(synonym_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            data = [row for row in reader]

        synonyms = defaultdict(dict)
        for line in data:
            if not line:
                continue
            synonyms[line[0]] = (
                {
                    "taigen_or_yougen": line[1],  # Taigen or Yougen(体言or用言)
                    "flg_expansion": line[2],  # 展開制御フラグ
                    "lexeme_id": line[3],  # グループ内の語彙素番号
                    "word_form": line[4],  # 同一語彙素内での語形種別
                    "abbreviation": line[5],  # 略語
                    "spelling_inconsistencies": line[6],  # 表記揺れ情報
                    "field": line[7],  # 分野情報
                    "lemma": line[8],  # 見出し語
                },
            )
        ipdb.set_trace()

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

    def get_standard_form(self, word: str) -> str:
        """
        単語の標準形を取得

        Args:
            word: 対象の単語
        Returns:
            標準形（同義語が見つからない場合は元の単語）
        """
        # グループ辞書から同義語グループを探す
        group_id = self.group_dict.get(word)
        if group_id:
            # 同じグループに属する単語から標準形を探す
            for standard, synonyms in self.synonym_dict.items():
                if word in synonyms:
                    return standard
        return word

    def normalize_text(self, text: str) -> str:
        """
        テキストの表記ゆれと同義語を統一する

        Args:
            text: 正規化する文字列
        Returns:
            正規化された文字列
        """
        tokens = self.tokenizer_obj.tokenize(text, self.mode)
        normalized_parts = []

        for token in tokens:
            # 基本的な表記ゆれの正規化
            norm_form = token.normalized_form()

            # 品詞情報の取得
            pos = token.part_of_speech()

            # 内容語の場合のみ同義語変換を適用
            if pos[0] in ["名詞", "動詞", "形容詞"]:
                norm_form = self.get_standard_form(norm_form)

            normalized_parts.append(norm_form)

        return "".join(normalized_parts)

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
    normalizer = SudachiSynonymNormalizer()

    # テスト用テキスト
    test_text = "バス停で待機する。スマホを確認する。"

    # テキストの正規化
    normalized = normalizer.normalize_text(test_text)
    print(f"正規化結果: {normalized}")

    # 異形の分析
    variants = normalizer.analyze_variants(test_text)
    print("\n異形分析結果:")
    print(json.dumps(variants, ensure_ascii=False, indent=2))

    # 特定の単語の同義語を取得
    word = "待機"
    synonyms = normalizer.get_synonyms(word)
    print(f"\n「{word}」の同義語: {synonyms}")
