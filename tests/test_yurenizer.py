import pytest
from yurenizer.yurenizer import SynonymNormalizer
from copy import deepcopy

from yurenizer.entities import (
    Expansion,
    OtherLanguage,
    Alphabet,
    NonAlphabeticAbbreviation,
    OrthographicVariation,
    Misspelling,
    NormalizerConfig,
    UnifyLevel,
)


class TestSynonymNormalizer:
    @pytest.fixture
    def normalizer(self):
        return SynonymNormalizer(synonym_file_path="yurenizer/data/synonyms.txt")

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
    def default_flags(self):
        """flgはデフォルトの値を持つフィクスチャ"""
        return NormalizerConfig()

    @pytest.fixture
    def default_disabled_flags(self):
        """taigen以外、全てのフラグをDISABLEにした基本設定を返すフィクスチャ"""
        return NormalizerConfig(
            taigen=True,
            yougen=False,
            expansion="from_another",
            other_language=False,
            alias=False,
            old_name=False,
            misuse=False,
            alphabetic_abbreviation=False,
            non_alphabetic_abbreviation=False,
            alphabet=False,
            orthographic_variation=False,
            misspelling=False,
            custom_synonym=False,
        )

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("チェスト", "チェスト"),
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
            ("USA", Expansion.ANY.value, "USA"),
            ("USA", Expansion.FROM_ANOTHER.value, "USA"),
            ("チェック", Expansion.ANY.value, "チェック"),
            ("チェック", Expansion.FROM_ANOTHER.value, "チェック"),
        ],
    )
    def test_normalize_with_different_expansions_disabled_flags(
        self, normalizer, default_disabled_flags, text, expansion, expected
    ):
        # expansionフラグはバラバラだが、それ以外は全てFalseなので、同義語展開は行われない
        test_flags = deepcopy(default_disabled_flags)
        test_flags.expansion = expansion
        result = normalizer.normalize(text, test_flags)
        assert result == expected

    @pytest.mark.parametrize(
        "text,expansion,expected",
        [
            ("USA", Expansion.ANY.value, "アメリカ合衆国"),
            ("USA", Expansion.FROM_ANOTHER.value, "USA"),
            ("チェック", Expansion.ANY.value, "チェック"),
            ("チェック", Expansion.FROM_ANOTHER.value, "チェック"),
        ],
    )
    def test_normalize_with_different_expansions_enabled_flags(
        self, normalizer, default_flags, text, expansion, expected
    ):
        # expansionフラグはTrueで、それ以外も全てTrueなので、同義語展開が行われる。ただし「チェック」は同じ語彙の語がないので変換されない
        test_flags = deepcopy(default_flags)
        test_flags.expansion = expansion
        result = normalizer.normalize(text, test_flags)
        assert result == expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("JR東日本", "JR東日本"),
            ("JR東", "JR東"),
            ("JR-East", "JR-East"),
        ],
    )
    def test_normalize_not_selected(self, normalizer, default_disabled_flags, text, expected):
        # flg_inputが全てFalseなので、同義語展開は行われない
        test_flags = deepcopy(default_disabled_flags)
        result = normalizer.normalize(text, test_flags)
        assert result == expected

    def test_normalize_with_other_language_able(self, normalizer, default_disabled_flags):
        text = "United States of America"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.other_language = OtherLanguage.ENABLE.value
        result = normalizer.normalize(text, test_flags)
        assert result == "アメリカ合衆国"

    def test_normalize_with_alphabet_disable(self, normalizer, default_flags):
        text = "synonym"
        test_flags = deepcopy(default_flags)
        test_flags.alphabet = Alphabet.DISABLE.value
        result = normalizer.normalize(text, test_flags)
        assert result == "synonym"

    def test_normalize_text_with_alphabetic_abbreviation(self, normalizer, default_disabled_flags):
        text = "UNICEF"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.alphabetic_abbreviation = True
        result = normalizer.normalize(text, test_flags)
        assert result == "国連児童基金"

    def test_normalize_non_alphabetic_abbreviation(self, normalizer, default_disabled_flags):
        text = "パソコン"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.non_alphabetic_abbreviation = NonAlphabeticAbbreviation.ENABLE.value
        result = normalizer.normalize(text, test_flags)
        assert result == "パーソナルコンピューター"

    def test_normalize_orthographic_variation(self, normalizer, default_disabled_flags):
        text = "パーソナル・コンピューター"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.orthographic_variation = OrthographicVariation.ENABLE.value
        result = normalizer.normalize(text, test_flags)
        assert result == "パーソナルコンピューター"

    def test_normalize_misspelling(self, normalizer, default_disabled_flags):
        text = "テトラポット"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.misspelling = Misspelling.ENABLE.value
        result = normalizer.normalize(text, test_flags)
        assert result == "テトラポッド"

    def test_normalize_kaiso_lexeme(self, normalizer, default_flags):
        text = "single log in"
        test_flags = deepcopy(default_flags)
        result = normalizer.normalize(text, test_flags)
        assert result == "シングルログイン"

    def test_normalize_kaiso_word_form_expansion_any(self, normalizer, default_flags):
        text = "USA"
        test_flags = deepcopy(default_flags)
        test_flags.unify_level = UnifyLevel.WORD_FORM.value
        test_flags.expansion = Expansion.ANY.value
        result = normalizer.normalize(text, test_flags)
        assert result == "アメリカ合衆国"

    def test_normalize_kaiso_word_form_expansion_from_another(self, normalizer, default_flags):
        text = "アメリカ"
        test_flags = deepcopy(default_flags)
        test_flags.unify_level = UnifyLevel.WORD_FORM.value
        result = normalizer.normalize(text, test_flags)
        assert result == "アメリカ合衆国"

    def test_normalize_kaiso_abbreviation(self, normalizer, default_flags):
        text = "America"
        test_flags = deepcopy(default_flags)
        test_flags.unify_level = UnifyLevel.ABBREVIATION.value
        result = normalizer.normalize(text, test_flags)
        assert result == "アメリカ"

    def test_get_morphemes(self, normalizer):
        text = "テストを実行する"
        morphemes = normalizer.get_morphemes(text)
        assert len(morphemes) > 0
        assert all(hasattr(m, "surface") for m in morphemes)

    def test_get_synonym_group(self, normalizer):
        text = "USA"
        morphemes = normalizer.get_morphemes(text)
        synonym_group = normalizer.get_synonym_group(morphemes[0], is_yougen=False, is_taigen=True)
        assert synonym_group is not None
        assert len(synonym_group) > 0

    def test_invalid_input(self, normalizer):
        with pytest.raises(Exception):
            normalizer.normalize("")

    def test_load_sudachi_synonyms(self, normalizer):
        synonym_file_path = "yurenizer/data/synonyms.txt"
        synonyms = normalizer.load_sudachi_synonyms(synonym_file_path)
        assert len(synonyms) > 0
        assert all(isinstance(k, str) for k in synonyms.keys())

    def test_normalize_long_text(self, normalizer, default_disabled_flags):
        text = "これは長いテキストのテストです。USAでチェックを行う。パソコンを使う。"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.unify_level = "lexeme"
        test_flags.non_alphabetic_abbreviation = NonAlphabeticAbbreviation.ENABLE.value
        result = normalizer.normalize(text)
        expected = "これは長いテキストのテストです。USAでチェックを行う。パーソナルコンピューターを使う。"
        assert result == expected

    def test_normalize_multiple_synonym_group(self, normalizer, default_flags):
        "同じ単語で複数の同義語グループがある場合は判定ができないので、元の単語が返される"
        text = "PC"
        test_flags = deepcopy(default_flags)
        test_flags.expansion = Expansion.ANY.value
        result = normalizer.normalize(text, test_flags)
        assert result == "PC"

    def test_normalize_yougen(self, normalizer, default_disabled_flags):
        text = "ねたむ"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.yougen = True
        test_flags.orthographic_variation = OrthographicVariation.ENABLE.value
        result = normalizer.normalize(text, test_flags)
        assert result == "妬む"

    def test_normalize_with_custom_synonym_json(self, default_disabled_flags):
        custom_file = "yurenizer/data/custom_synonyms.json"
        custom_normalizer = SynonymNormalizer(
            synonym_file_path="./yurenizer/data/synonyms.txt", custom_synonyms_file=custom_file
        )
        text = "幽☆遊☆白書を読む。ハンターハンターも読む。"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.custom_synonym = True
        result = custom_normalizer.normalize(text, test_flags)
        assert result == "幽遊白書を読む。hunterhunterも読む。"

    def test_normalize_with_custom_synonym_csv(self, default_disabled_flags):
        custom_file = "yurenizer/data/custom_synonyms.csv"
        custom_normalizer = SynonymNormalizer(
            synonym_file_path="./yurenizer/data/synonyms.txt", custom_synonyms_file=custom_file
        )
        text = "幽☆遊☆白書を読む。ハンターハンターも読む。"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.custom_synonym = True
        result = custom_normalizer.normalize(text, test_flags)
        assert result == "幽遊白書を読む。hunterhunterも読む。"

    def test_normalize_with_custom_synonym_tsv(self, default_disabled_flags):
        custom_file = "yurenizer/data/custom_synonyms.tsv"
        custom_normalizer = SynonymNormalizer(
            synonym_file_path="./yurenizer/data/synonyms.txt", custom_synonyms_file=custom_file
        )
        text = "幽☆遊☆白書を読む。ハンターハンターも読む。"
        test_flags = deepcopy(default_disabled_flags)
        test_flags.custom_synonym = True
        result = custom_normalizer.normalize(text, test_flags)
        assert result == "幽遊白書を読む。hunterhunterも読む。"

    def test_load_sudachi_synonyms_file_not_found(self, normalizer):
        with pytest.raises(FileNotFoundError):
            normalizer.load_sudachi_synonyms("non_existent_file.txt")
