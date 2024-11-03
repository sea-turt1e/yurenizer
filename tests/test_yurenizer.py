import pytest
from pathlib import Path
from yurenizer.yurenizer import SynonymNormalizer
import os
import json

from yurenizer.entities import (
    Taigen,
    Yougen,
    Expansion,
    OtherLanguage,
    Alphabet,
    AlphabeticAbbreviation,
    NonAlphabeticAbbreviation,
    OrthographicVariation,
    Missspelling,
    SynonymField,
    FlgInput,
)


class TestSynonymNormalizer:
    @pytest.fixture
    def normalizer(self):
        return SynonymNormalizer()

    def test_initialization(self, normalizer):
        assert normalizer is not None
        assert normalizer.tokenizer_obj is not None
        assert normalizer.synonyms is not None

    def test_normalize_basic_text(self, normalizer):
        text = "テストを実行する"
        result = normalizer.normalize(text)
        assert isinstance(result, str)
        assert result != ""

    @pytest.fixture
    def default_disabled_flags(self):
        """taigen、expansion以外、全てのフラグをDISABLEにした基本設定を返すフィクスチャ"""
        return {
            "taigen": Taigen.INCLUDE,
            "yougen": Yougen.EXCLUDE,
            "expansion": Expansion.FROM_ANOTHER,
            "other_language": OtherLanguage.DISABLE,
            "alphabet": Alphabet.DISABLE,
            "alphabetic_abbreviation": AlphabeticAbbreviation.DISABLE,
            "non_alphabetic_abbreviation": NonAlphabeticAbbreviation.DISABLE,
            "orthographic_variation": OrthographicVariation.DISABLE,
            "missspelling": Missspelling.DISABLE,
        }

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("USA", "USA"),
            ("America", "アメリカ合衆国"),
            ("checkを行う。", "checkを行う。"),
        ],
    )
    def test_normalize_with_different_inputs(self, normalizer, text, expected):
        result = normalizer.normalize(text)
        assert result == expected

    @pytest.mark.parametrize(
        "text,expansion,expected",
        [
            ("USA", Expansion.ANY, "アメリカ合衆国"),
            ("USA", Expansion.FROM_ANOTHER, "USA"),
            ("チェック", Expansion.ANY, "確認"),
            ("チェック", Expansion.FROM_ANOTHER, "チェック"),
        ],
    )
    def test_normalize_with_different_expansions(self, normalizer, text, expansion, expected):
        result = normalizer.normalize(text, expansion=expansion)
        assert result == expected

    def test_normalize_with_custom_options(self, normalizer):
        text = "USA"
        result = normalizer.normalize(
            text,
            taigen=Taigen.INCLUDE,
            yougen=Yougen.EXCLUDE,
            expansion=Expansion.FROM_ANOTHER,
            alphabet=Alphabet.DISABLE,
        )
        assert result == "USA"

    def test_normalize_text_with_alphabetic_abbreviation(self, normalizer, default_disabled_flags):
        text = "TDL"
        test_flags = default_disabled_flags.copy()
        test_flags["alphabetic_abbreviation"] = AlphabeticAbbreviation.ENABLE
        test_flags["expansion"] = Expansion.ANY
        result = normalizer.normalize(text, **test_flags)
        assert result == "東京ディズニーランド"

    def test_normalize_japanese_abbreviation(self, normalizer, default_disabled_flags):
        text = "パソコン"
        test_flags = default_disabled_flags.copy()
        test_flags["non_alphabetic_abbreviation"] = NonAlphabeticAbbreviation.ENABLE
        result = normalizer.normalize(text, **test_flags)
        assert result == "パーソナルコンピューター"

    def test_normalize_orthographic_variation(self, normalizer, default_disabled_flags):
        text = "パーソナル・コンピューター"
        test_flags = default_disabled_flags.copy()
        test_flags["orthographic_variation"] = OrthographicVariation.ENABLE
        result = normalizer.normalize(text, **test_flags)
        assert result == "パーソナルコンピューター"

    def test_normalize_misspelling(self, normalizer, default_disabled_flags):
        text = "ソルダ"
        test_flags = default_disabled_flags.copy()
        test_flags["missspelling"] = Missspelling.ENABLE
        result = normalizer.normalize(text, **test_flags)
        assert result == "ソルダー"

    def test_get_morphemes(self, normalizer):
        text = "テストを実行する"
        morphemes = normalizer.get_morphemes(text)
        assert len(morphemes) > 0
        assert all(hasattr(m, "surface") for m in morphemes)

    def test_get_synonym_group(self, normalizer):
        text = "USA"
        morphemes = normalizer.get_morphemes(text)
        synonym_group = normalizer.get_synonym_group(morphemes[0])
        assert synonym_group is not None
        assert len(synonym_group) > 0

    def test_invalid_input(self, normalizer):
        with pytest.raises(Exception):
            normalizer.normalize("")

    def test_load_sudachi_synonyms(self, normalizer):
        synonyms = normalizer.load_sudachi_synonyms()
        assert len(synonyms) > 0
        assert all(isinstance(k, str) for k in synonyms.keys())

    def test_normalize_long_text(self, normalizer):
        text = "これは長いテキストのテストです。USAでチェックを行う。パソコンを使う。"
        result = normalizer.normalize(text)
        expected = "これは長いテキストのテストです。USAでチェックを行う。パーソナルコンピューターを使う。"
        assert result == expected

    def test_normalize_yougen(self, normalizer, default_disabled_flags):
        text = "問う"
        test_flags = default_disabled_flags.copy()
        test_flags["yougen"] = Yougen.INCLUDE
        test_flags["taigen"] = Taigen.EXCLUDE
        result = normalizer.normalize(text, **test_flags)
        assert result == "チェックする"

        result = normalizer.normalize(text, yougen=Yougen.INCLUDE)

        # def test_normalize_with_custom_synonym_file(self):
        #     custom_file = "custom_synonyms.json"
        #     custom_synonyms = {"こんにちは": ["おはよう", "こんばんは"]}
        #     with open(custom_file, "w", encoding="utf-8") as f:
        #         json.dump(custom_synonyms, f, ensure_ascii=False)
        #     normalizer = SynonymNormalizer(custom_synonym_file=custom_file)
        #     text = "おはよう"
        #     result = normalizer.normalize(text)
        #     assert result == "こんにちは"
        #     os.remove(custom_file)

        def test_load_sudachi_synonyms_file_not_found(self):
            normalizer = SynonymNormalizer()
            with pytest.raises(FileNotFoundError):
                normalizer.load_sudachi_synonyms("non_existent_file.txt")
