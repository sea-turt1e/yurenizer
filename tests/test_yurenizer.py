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
        text = "NISA"
        test_flags = default_disabled_flags.copy()
        test_flags["alphabetic_abbreviation"] = AlphabeticAbbreviation.ENABLE
        result = normalizer.normalize(text, **test_flags)
        assert result == "少額投資非課税制度"

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
        text = "ジェネレーティブ"
        test_flags = default_disabled_flags.copy()
        test_flags["missspelling"] = Missspelling.ENABLE
        result = normalizer.normalize(text, **test_flags)
        assert result == "ジェネラティブ"

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

        def test_get_standard_form(self, normalizer):
            text = "USA"
            morphemes = normalizer.get_morphemes(text)
            standard_form = normalizer.get_standard_form(morphemes[0], Expansion.ANY)
            assert standard_form == "アメリカ合衆国"

        def test_get_standard_form_no_synonym(self, normalizer):
            text = "テスト"
            morphemes = normalizer.get_morphemes(text)
            standard_form = normalizer.get_standard_form(morphemes[0], Expansion.ANY)
            assert standard_form == "テスト"

        def test_get_synonym_value_from_morpheme(self, normalizer):
            text = "USA"
            morphemes = normalizer.get_morphemes(text)
            synonym_value = normalizer.get_synonym_value_from_morpheme(morphemes[0], SynonymField.FLG_EXPANSION)
            assert synonym_value == 0  # Expected value based on synonyms.txt

        def test_normalize_word(self, normalizer):
            text = "USA"
            morphemes = normalizer.get_morphemes(text)
            flg_input = FlgInput()
            normalized_word = normalizer.normalize_word(morphemes[0], flg_input)
            assert normalized_word == "アメリカ合衆国"

        def test_normalize_empty_text(self, normalizer):
            text = ""
            result = normalizer.normalize(text)
            assert result == ""

        def test_normalize_nonexistent_word(self, normalizer):
            text = "架空の言葉"
            result = normalizer.normalize(text)
            assert result == "架空の言葉"

        def test_get_morphemes_empty_text(self, normalizer):
            text = ""
            morphemes = normalizer.get_morphemes(text)
            assert morphemes == []

        def test_get_synonym_group_no_synonym(self, normalizer):
            text = "テスト"
            morphemes = normalizer.get_morphemes(text)
            synonym_group = normalizer.get_synonym_group(morphemes[0])
            assert synonym_group is None

        def test_normalize_with_yougen_include(self, normalizer):
            text = "食べる"
            result = normalizer.normalize(text, yougen=Yougen.INCLUDE)
            assert result == text  # Adjust expected value based on synonyms.txt

        def test_normalize_with_taigen_exclude(self, normalizer):
            text = "テストを実行する"
            result = normalizer.normalize(text, taigen=Taigen.EXCLUDE)
            assert result == "テストを実行する"

        def test_normalize_other_language_disable(self, normalizer):
            text = "USA"
            result = normalizer.normalize(text, other_language=OtherLanguage.DISABLE)
            assert result == "USA"

        def test_normalize_alphabet_disable(self, normalizer):
            text = "check"
            result = normalizer.normalize(text, alphabet=Alphabet.DISABLE)
            assert result == "check"

        def test_normalize_with_misspelling_disable(self, normalizer):
            text = "インターフェイス"
            result = normalizer.normalize(text, missspelling=Missspelling.DISABLE)
            assert result == "インターフェイス"

        def test_normalize_long_text(self, normalizer):
            text = "これは長いテキストのテストです。USAでチェックを行う。パソコンを使う。"
            result = normalizer.normalize(text)
            expected = "これは長いテキストのテストです。アメリカ合衆国で確認を行う。パーソナルコンピュータを使う。"
            assert result == expected

        def test_normalize_with_symbols(self, normalizer):
            text = "テスト!これは、どうですか？"
            result = normalizer.normalize(text)
            assert result == text

        def test_normalize_with_numbers(self, normalizer):
            text = "2021年のデータ"
            result = normalizer.normalize(text)
            assert result == text

        def test_normalize_with_emojis(self, normalizer):
            text = "テスト😊"
            result = normalizer.normalize(text)
            assert result == text

        def test_normalize_with_mixed_script(self, normalizer):
            text = "Checkを行う。"
            result = normalizer.normalize(text)
            expected = "チェックを行う。"
            assert result == expected

        def test_normalize_with_katakana(self, normalizer):
            text = "コンピューター"
            result = normalizer.normalize(text)
            assert result == text  # Adjust expected value if necessary

        def test_normalize_with_hiragana(self, normalizer):
            text = "ありがとう"
            result = normalizer.normalize(text)
            assert result == text

        def test_normalize_with_kanji(self, normalizer):
            text = "山"
            result = normalizer.normalize(text)
            assert result == text

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
