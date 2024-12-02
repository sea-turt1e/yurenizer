from typing import Dict, List, Optional, Set, Union

from sudachipy import dictionary, tokenizer
from sudachipy.morpheme import Morpheme

from .entities import (
    Abbreviation,
    Alias,
    Alphabet,
    AlphabeticAbbreviation,
    CusotomSynonym,
    Expansion,
    FlgExpantion,
    FlgInput,
    Misspelling,
    Misuse,
    NonAlphabeticAbbreviation,
    NormalizerConfig,
    OldName,
    OrthographicVariation,
    OtherLanguage,
    SpellingInconsistency,
    SudachiDictType,
    Synonym,
    SynonymField,
    Taigen,
    TaigenOrYougen,
    UnifyLevel,
    WordForm,
    Yougen,
)
from .loaders import load_custom_synonyms, load_sudachi_synonyms


class SynonymNormalizer:
    def __init__(
        self,
        synonym_file_path: str,
        sudachi_dict: SudachiDictType = SudachiDictType.FULL.value,
        custom_synonyms_file: Optional[str] = None,
    ) -> None:
        """
        Initialize the tool for unifying spelling variations using SudachiDict's synonym dictionary.

        Args:
            synonym_file_path: Path to the SudachiDict synonym file
            sudachi_dict: SudachiDict type (default: full)
            custom_synonyms_file: Path to the custom synonym definition file
        """
        # Initialize Sudachi
        sudachi_dic = dictionary.Dictionary(dict=sudachi_dict)
        self.tokenizer_obj = sudachi_dic.create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

        # Part-of-speech matching
        self.taigen_matcher = sudachi_dic.pos_matcher(lambda x: x[0] == "名詞")
        self.yougen_matcher = sudachi_dic.pos_matcher(lambda x: x[0] in ["動詞", "形容詞"])

        # Load synonyms from SudachiDict's synonym file
        synonyms = load_sudachi_synonyms(synonym_file_path)
        self.synonyms = {int(k): v for k, v in synonyms.items()}

        # Load custom synonyms
        self.custom_synonyms: Dict[str, Set[str]] = {}
        if custom_synonyms_file:
            self.custom_synonyms = load_custom_synonyms(custom_synonyms_file)

    def normalize(
        self,
        text: str,
        config: NormalizerConfig = NormalizerConfig(),
    ) -> str:
        """
        Normalize text by unifying spelling variations and synonyms.

        Args:
            text: Text to normalize
            config: Normalization options

        Returns:
            Normalized text
        """
        if not text:
            raise ValueError("Input text is empty.")

        # Convert config to FlgInput with hierarchical conditions
        flg_input = self._prepare_normalization_flags(config)

        # If all flags are disabled, return the original text
        if not self._should_normalize(flg_input):
            return text

        return self._normalize_text(text, flg_input)

    def _prepare_normalization_flags(self, config: NormalizerConfig) -> FlgInput:
        """
        Prepare normalization flags with hierarchical conditions.

        Args:
            config: Normalization configuration

        Returns:
            Prepared FlgInput with hierarchical flags
        """
        flg_input = FlgInput(
            taigen=Taigen.from_int(config.taigen),
            yougen=Yougen.from_int(config.yougen),
            expansion=Expansion.from_str(config.expansion),
            unify_level=UnifyLevel.from_str(config.unify_level),
            other_language=OtherLanguage.from_int(config.other_language),
            alias=Alias.from_int(config.alias),
            old_name=OldName.from_int(config.old_name),
            misuse=Misuse.from_int(config.misuse),
            alphabetic_abbreviation=AlphabeticAbbreviation.from_int(config.alphabetic_abbreviation),
            non_alphabetic_abbreviation=NonAlphabeticAbbreviation.from_int(config.non_alphabetic_abbreviation),
            alphabet=Alphabet.from_int(config.alphabet),
            orthographic_variation=OrthographicVariation.from_int(config.orthographic_variation),
            misspelling=Misspelling.from_int(config.misspelling),
            custom_synonym=CusotomSynonym.from_int(config.custom_synonym),
        )

        # Hierarchical flag settings
        if (
            flg_input.alphabet == Alphabet.ENABLE
            or flg_input.orthographic_variation == OrthographicVariation.ENABLE
            or flg_input.misspelling == Misspelling.ENABLE
        ):
            flg_input.alphabetic_abbreviation = AlphabeticAbbreviation.ENABLE
            flg_input.non_alphabetic_abbreviation = NonAlphabeticAbbreviation.ENABLE

        if (
            flg_input.alphabetic_abbreviation == AlphabeticAbbreviation.ENABLE
            or flg_input.non_alphabetic_abbreviation == NonAlphabeticAbbreviation.ENABLE
        ):
            flg_input.other_language = OtherLanguage.ENABLE
            flg_input.alias = Alias.ENABLE
            flg_input.old_name = OldName.ENABLE
            flg_input.misuse = Misuse.ENABLE

        return flg_input

    def _should_normalize(self, flg_input: FlgInput) -> bool:
        """
        Determine if normalization should be performed based on input flags.

        Args:
            flg_input: Normalization flags

        Returns:
            Whether normalization should be performed
        """
        return not (
            flg_input.custom_synonym == CusotomSynonym.DISABLE
            and flg_input.other_language == OtherLanguage.DISABLE
            and flg_input.alias == Alias.DISABLE
            and flg_input.old_name == OldName.DISABLE
            and flg_input.misuse == Misuse.DISABLE
        )

    def _normalize_text(self, text: str, flg_input: FlgInput) -> str:
        """
        Internal method to normalize text with given flags.

        Args:
            text: Text to normalize
            flg_input: Normalization flags

        Returns:
            Normalized text
        """
        morphemes = self.get_morphemes(text)
        normalized_parts = [self._normalize_word(morpheme, flg_input) for morpheme in morphemes]
        return "".join(normalized_parts)

    def _normalize_word(self, morpheme: Morpheme, flg_input: FlgInput) -> str:
        """
        Normalize a word by unifying spelling variations and synonyms（表記揺れと同義語を統一して単語を正規化する）

        Args:
            morpheme: Morpheme information（形態素情報）
            flg_input: Normalization options（正規化オプション）

        Returns:
            Normalized word（正規化された単語）

        Example:
            normalized_word = _normalize_word(morpheme, flg_input)
        """
        # Use custom synonym definitions
        custom_representation = self.get_custom_synonym(morpheme)
        if custom_representation:
            return custom_representation
        # If all flags are disabled, return the original word
        if (
            flg_input.other_language == OtherLanguage.DISABLE
            and flg_input.alias == Alias.DISABLE
            and flg_input.old_name == OldName.DISABLE
            and flg_input.misuse == Misuse.DISABLE
        ):
            return morpheme.surface()
        # Determine whether it's yougen or taigen
        is_yougen = self.yougen_matcher(morpheme)
        is_taigen = self.taigen_matcher(morpheme)
        if (flg_input.yougen == Yougen.INCLUDE and is_yougen) or (flg_input.taigen == Taigen.INCLUDE and is_taigen):
            pass
        else:
            return morpheme.surface()

        if not is_yougen and True not in [
            flg_input.other_language.value,
            flg_input.alias.value,
            flg_input.old_name.value,
            flg_input.misuse.value,
            flg_input.alphabetic_abbreviation.value,
            flg_input.non_alphabetic_abbreviation.value,
            flg_input.alphabet.value,
            flg_input.orthographic_variation.value,
            flg_input.misspelling.value,
        ]:
            return morpheme.surface()

        # Get synonym group for each taigen or yougen
        synonym_group = self.get_synonym_group(morpheme, is_yougen, is_taigen)
        if not synonym_group:
            return morpheme.surface()

        # Change subsequent processing according to the expansion control flag
        if flg_input.expansion == Expansion.ANY:
            if not self._is_input_word_expansion_any_or_from_another(morpheme, synonym_group):
                return morpheme.surface()
        elif flg_input.expansion == Expansion.FROM_ANOTHER:
            if not self.is_input_word_expansion_from_another(morpheme, synonym_group):
                return morpheme.surface()
        else:
            return morpheme.surface()

        # Narrow down the synonym group to the same lexeme
        if (
            flg_input.other_language == OtherLanguage.ENABLE
            or flg_input.alias == Alias.ENABLE
            or flg_input.old_name == OldName.ENABLE
            or flg_input.misuse == Misuse.ENABLE
        ):
            synonym_group = self._get_represent_synonym_group_lexeme_id(flg_input, morpheme, synonym_group)
        if not synonym_group:
            return morpheme.surface()

        # Get the synonym group with the same word form
        if (
            flg_input.alphabetic_abbreviation == AlphabeticAbbreviation.ENABLE
            or flg_input.non_alphabetic_abbreviation == NonAlphabeticAbbreviation.ENABLE
            or flg_input.alphabet == Alphabet.ENABLE
            or flg_input.orthographic_variation == OrthographicVariation.ENABLE
            or flg_input.misspelling == Misspelling.ENABLE
        ):
            synonym_group = self._get_represent_synonym_group_by_same_word_form(flg_input, morpheme, synonym_group)

        if not synonym_group:
            return morpheme.surface()

        # Get the synonym group with the same abbreviation
        if (
            flg_input.alphabet == Alphabet.ENABLE
            or flg_input.orthographic_variation == OrthographicVariation.ENABLE
            or flg_input.misspelling == Misspelling.ENABLE
        ):
            synonym_group = self.get_represent_synonym_group_by_same_abbreviation(flg_input, morpheme, synonym_group)
        if not synonym_group:
            return morpheme.surface()

        # Obtain the representative notation from the synonym group. Narrow down according to the expansion control flag
        represent_synonym = synonym_group[0]
        if represent_synonym:
            return represent_synonym.lemma
        return morpheme.surface()

    def _is_input_word_expansion_any_or_from_another(self, morpheme: Morpheme, synonym_group: List[Synonym]) -> bool:
        """
        Judge whether the input word is expanded by synonyms（入力単語が同義語展開されるかどうかを判断する）

        Args:
            morpheme: Morpheme information（形態素情報）
            synonym_group: Synonym group（同義語グループ）

        Returns:
            True if the input word is expanded by synonyms, False otherwise（同義語展開される場合はTrue, されない場合はFalse）

        Example:
            is_expansion = _is_input_word_expansion_any_or_from_another(morpheme, synonym_group)
        """
        flg_expansion = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.FLG_EXPANSION)
        if flg_expansion in (FlgExpantion.ANY.value, FlgExpantion.FROM_ANOTHER.value):
            return True
        return False

    def is_input_word_expansion_from_another(self, morpheme: Morpheme, synonym_group: List[Synonym]) -> bool:
        """
        Judge whether the input word is expanded by synonyms from another（入力単語が他の同義語展開されるかどうかを判断する）

        Args:
            morpheme: Morpheme information（形態素情報）
            synonym_group: Synonym group（同義語グループ）

        Returns:
            True if the input word is expanded by synonyms from another, False otherwise（他の同義語展開される場合はTrue, されない場合はFalse）

        Example:
            is_expansion = is_input_word_expansion_from_another(morpheme, synonym_group)
        """
        flg_expansion = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.FLG_EXPANSION)
        if flg_expansion == FlgExpantion.ANY.value:
            return True
        return False

    def _get_represent_synonym_group_lexeme_id(
        self, flg_input: FlgInput, morpheme: Morpheme, synonym_group: List[Synonym]
    ) -> List[Synonym]:
        """
        Get the synonym group of the same lexeme id（同じ語彙素IDの同義語グループを取得）

        Args:
            morpheme: Morpheme information（形態素情報）
            synonym_group: Synonym group（同義語グループ）

        Returns:
            Synonym object list（Synonymオブジェクトのリスト）

        Example:
            synonym_group = _get_represent_synonym_group_lexeme_id(flg_input, morpheme, synonym_group)
        """
        is_expansion = False
        filtered_synonym_group = []
        lexeme_id = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.LEXEME_ID)
        word_form = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.WORD_FORM)
        if word_form == WordForm.REPRESENTATIVE.value:
            is_expansion = True
        elif flg_input.other_language == OtherLanguage.ENABLE and word_form == WordForm.TRANSLATION.value:
            is_expansion = True
        elif flg_input.alias == Alias.ENABLE and word_form == WordForm.ALIAS.value:
            is_expansion = True
        elif flg_input.old_name == OldName.ENABLE and word_form == WordForm.OLD_NAME.value:
            is_expansion = True
        elif flg_input.misuse == Misuse.ENABLE and word_form == WordForm.MISUSE.value:
            is_expansion = True
        if is_expansion:
            filtered_synonym_group = [s for s in synonym_group if s.lexeme_id == lexeme_id]
        return filtered_synonym_group

    def _get_represent_synonym_group_by_same_word_form(
        self, flg_input: FlgInput, morpheme: Morpheme, synonym_group: List[Synonym]
    ) -> List[Synonym]:
        """
        Get the synonym group of the same word form（同じ語形の同義語グループを取得）

        Args:
            morpheme: Morpheme information（形態素情報）
            synonym_group: Synonym group（同義語グループ）

        Returns:
            Synonym object list（Synonymオブジェクトのリスト）

        Example:
            synonym_group = _get_represent_synonym_group_by_same_word_form(flg_input, morpheme, synonym_group)
        """
        is_expansion = False
        filtered_synonym_group = []
        word_form = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.WORD_FORM)
        abbreviation = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.ABBREVIATION)
        if abbreviation == Abbreviation.REPRESENTATIVE.value:
            is_expansion = True
        elif (
            flg_input.alphabetic_abbreviation == AlphabeticAbbreviation.ENABLE
            and abbreviation == Abbreviation.ALPHABET.value
        ):
            is_expansion = True
        elif (
            flg_input.non_alphabetic_abbreviation == NonAlphabeticAbbreviation.ENABLE
            and abbreviation == Abbreviation.NOT_ALPHABET.value
        ):
            is_expansion = True
        if is_expansion:
            if flg_input.unify_level == UnifyLevel.LEXEME:
                return synonym_group
            elif flg_input.unify_level in (UnifyLevel.WORD_FORM, UnifyLevel.ABBREVIATION):
                filtered_synonym_group = [s for s in synonym_group if s.word_form == word_form]
        return filtered_synonym_group

    def get_represent_synonym_group_by_same_abbreviation(
        self, flg_input: FlgInput, morpheme: Morpheme, synonym_group: List[Synonym]
    ) -> List[Synonym]:
        """
        Get the synonym group of the same abbreviation（同じ略語・略称の同義語グループを取得）

        Args:
            morpheme: Morpheme information（形態素情報）
            synonym_group: Synonym group（同義語グループ）

        Returns:
            Synonym object list（Synonymオブジェクトのリスト）

        Example:
            synonym_group = get_represent_synonym_group_by_same_abbreviation(flg_input, morpheme, synonym_group)
        """
        is_expansion = False
        filtered_synonym_group = []
        abbreviation = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.ABBREVIATION)
        spelling_inconsistency = self.get_synonym_value_from_morpheme(
            morpheme, synonym_group, SynonymField.SPELLING_INCONSISTENCY
        )
        if spelling_inconsistency == SpellingInconsistency.REPRESENTATIVE.value:
            is_expansion = True
        elif flg_input.alphabet == Alphabet.ENABLE and spelling_inconsistency == SpellingInconsistency.ALPHABET.value:
            is_expansion = True
        elif (
            flg_input.orthographic_variation == OrthographicVariation.ENABLE
            and spelling_inconsistency == SpellingInconsistency.ORTHOGRAPHIC_VARIATION.value
        ):
            is_expansion = True
        elif (
            flg_input.misspelling == Misspelling.ENABLE
            and spelling_inconsistency == SpellingInconsistency.MISSPELLING.value
        ):
            is_expansion = True
        if is_expansion:
            if flg_input.unify_level in (UnifyLevel.LEXEME, UnifyLevel.WORD_FORM):
                return synonym_group
            elif flg_input.unify_level == UnifyLevel.ABBREVIATION:
                filtered_synonym_group = [s for s in synonym_group if s.abbreviation == abbreviation]
        return filtered_synonym_group

    def _normalize_word_by_custom_synonyms(self, word: str) -> Optional[str]:
        """
        Normalize a word by custom synonyms（カスタム同義語で単語を正規化する）

        Args:
            word: Word to normalize（正規化する単語）

        Returns:
            Normalized word（正規化された単語）

        Example:
            normalized_word = _normalize_word_by_custom_synonyms(word)
        """
        for k, v in self.custom_synonyms.items():
            if word in v:
                return k
        return None

    def get_custom_synonym(self, morpheme: Morpheme) -> Optional[str]:
        """
        Get the custom synonym representation of a word（単語のカスタム同義語表現を取得）

        Args:
            morpheme: Morpheme information（形態素情報）

        Returns:
            Custom synonym representation（カスタム同義語表現）

        Example:
            custom_representation = get_custom_synonym(morpheme)
        """
        custom_representation = self._normalize_word_by_custom_synonyms(morpheme.surface())
        if custom_representation:
            return custom_representation
        return None

    def get_morphemes(self, text: str) -> List[str]:
        """
        Get morphemes from text（テキストから形態素を取得）

        Args:
            text: Text to tokenize（トークン化するテキスト）

        Returns:
            Morphemes（形態素）
        """
        tokens = self.tokenizer_obj.tokenize(text, self.mode)
        return [token for token in tokens]

    def get_synonym_group(self, morpheme: Morpheme, is_yougen: bool, is_taigen: bool) -> Optional[List[Synonym]]:
        """
        Get the synonym group of the morpheme（形態素の同義語グループを取得）

        Args:
            morpheme: Morpheme information（形態素情報）

        Returns:
            Synonym group（同義語グループ）

        Example:
            synonym_group = get_synonym_group(morpheme)
        """

        synonym_group_ids = morpheme.synonym_group_ids()
        if synonym_group_ids:
            # Only when there is one synonym group ID. If there are multiple, we cannot determine, so return None. If there is no ID, also return None.
            if len(synonym_group_ids) == 1:
                synonym_group = self.synonyms[synonym_group_ids[0]]
                if is_yougen:
                    return [s for s in synonym_group if s.taigen_or_yougen == TaigenOrYougen.YOUGEN.value]
                if is_taigen:
                    return [s for s in synonym_group if s.taigen_or_yougen == TaigenOrYougen.TAIGEN.value]
        return None

    def get_synonym_value_from_morpheme(
        self, morpheme: Morpheme, synonym_group: List[Synonym], synonym_attr: SynonymField
    ) -> Union[str, int]:
        return next(
            (getattr(item, synonym_attr.value) for item in synonym_group if item.lemma == morpheme.surface()), None
        )
