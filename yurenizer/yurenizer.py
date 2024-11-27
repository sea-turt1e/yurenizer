import csv
import json
from collections import defaultdict
from typing import Dict, List, Optional, Set, Union

from yurenizer.entities import (
    AlphabeticAbbreviation,
    Alphabet,
    Expansion,
    FlgInput,
    NonAlphabeticAbbreviation,
    Misspelling,
    CusotomSynonym,
    OrthographicVariation,
    UnifyLevel,
    Taigen,
    Yougen,
    OtherLanguage,
    Alias,
    OldName,
    Misuse,
    TaigenOrYougen,
    FlgExpantion,
    WordForm,
    Abbreviation,
    SpellingInconsistency,
    SynonymField,
    Synonym,
    SudachiDictType,
    NormalizerConfig,
)
from sudachipy import Morpheme, dictionary, tokenizer


class SynonymNormalizer:
    def __init__(
        self,
        synonym_file_path: str,
        sudachi_dict: SudachiDictType = SudachiDictType.FULL.value,
        custom_synonyms_file: Optional[str] = None,
    ) -> None:
        """
        Initialize the tool for unifying spelling variations using SudachiDict's synonym dictionary
        （SudachiDictの同義語辞書を使用した表記揺れ統一ツールの初期化）

        Args:
            synonym_file_path: Path to the SudachiDict synonym file（SudachiDictの同義語ファイルへのパス）
            sudachi_dict: SudachiDict type (default: full)（SudachiDictのタイプ（デフォルト: full））
            custom_synonyms_file: Path to the custom synonym definition file（カスタム同義語定義ファイルへのパス）

        Example:
            normalizer = SynonymNormalizer(synonym_file_path="synonyms.txt")
        """
        # Initialize Sudachi
        sudachi_dic = dictionary.Dictionary(dict=sudachi_dict)
        self.tokenizer_obj = sudachi_dic.create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

        # Part-of-speech matching
        self.taigen_matcher = sudachi_dic.pos_matcher(lambda x: x[0] == "名詞")
        self.yougen_matcher = sudachi_dic.pos_matcher(lambda x: x[0] in ["動詞", "形容詞"])

        # Load synonyms from SudachiDict's synonym file
        synonyms = self.load_sudachi_synonyms(synonym_file_path)
        self.synonyms = {int(k): v for k, v in synonyms.items()}

        # Load custom synonyms
        self.custom_synonyms = {}
        if custom_synonyms_file:
            self.custom_synonyms = self.load_custom_synonyms(custom_synonyms_file)

    def load_sudachi_synonyms(self, synonym_file: str) -> Dict[int, List[Synonym]]:
        """
        Load synonym information from SudachiDict's synonyms.txt（SudachiDictのsynonyms.txtから同義語情報を読み込む）

        Args:
            synonym_file: Path to the SudachiDict synonym file（SudachiDictの同義語ファイルへのパス）

        Returns:
            Synonym information dictionary（同義語情報の辞書）

        Example:
            synonyms = load_sudachi_synonyms("synonyms.txt")
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
                    taigen_or_yougen=int(line[1]),  # Taigen or Yougen
                    flg_expansion=int(line[2]),  # Expansion control flag
                    lexeme_id=int(line[3].split("/")[0]),  # Lexeme number within the group
                    word_form=int(line[4]),  # Word form type within the same lexeme
                    abbreviation=int(line[5]),  # Abbreviation
                    spelling_inconsistency=int(line[6]),  # Spelling inconsistency information
                    field=line[7],  # Field information
                    lemma=line[8],  # Lemma
                )
            )
        return synonyms

    def load_custom_synonyms(self, file_path: str) -> Dict[str, Set[str]]:
        """
        Load custom synonym definition JSON/CSV file（カスタム同義語定義JSON/CSVファイルを読み込む）

        Args:
            file_path: Path to the custom synonym definition JSON/CSV file（カスタム同義語定義JSON/CSVファイルへのパス）

        JSON format（JSONフォーマット）:
        {
            "standard_form": ["synonym1", "synonym2", ...],
            ...
        }
        CSV format（CSVフォーマット）:
            standard_form,synonym1,synonym2,...

        Returns:
            Custom synonym definition（カスタム同義語定義）

        Example:
            custom_synonyms = load_custom_synonyms("custom_synonyms.json")
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith((".csv", ".tsv")):
                    if file_path.endswith(".csv"):
                        delimiter = ","
                    elif file_path.endswith(".tsv"):
                        delimiter = "\t"
                    reader = csv.reader(f, delimiter=delimiter)
                    custom_synonyms = {row[0]: set(row[1:]) for row in reader}
                elif file_path.endswith(".json"):
                    custom_synonyms = json.load(f)
                    custom_synonyms = {k: set(v) for k, v in custom_synonyms.items() if v}
                else:
                    raise ValueError("Invalid file format. Please use JSON or CSV.")
        except Exception as e:
            raise ValueError(f"Failed to load custom synonyms: {e}")
        else:
            return custom_synonyms

    def get_standard_yougen(self, morpheme: Morpheme, expansion: Expansion) -> str:
        """
        Get the standard representation of a verb or adjective（動詞または形容詞の標準形を取得）

        Args:
            morpheme: Morpheme information（形態素情報）
            expansion: Synonym expansion control flag（同義語展開の制御フラグ）

        Returns:
            Standard form（同義語が見つからない場合は元の単語）

        Example:
            standard_yougen = get_standard_yougen(morpheme, expansion)
        """

        # Search for synonym group from the group dictionary
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
        Get the standard representation of a noun（名詞の標準形を取得）

        Args:
            morpheme: Morpheme information（形態素情報）
            expansion: Synonym expansion control flag（同義語展開の制御フラグ）

        Returns:
            Standard form（同義語が見つからない場合は元の単語）

        Example:
            standard_taigen = get_standard_taigen(morpheme, expansion)
        """
        # Search for synonym group from the group dictionary
        synonym_group = self.get_synonym_group(morpheme)
        if synonym_group:
            if expansion == Expansion.ANY:
                return synonym_group[0].lemma
            elif expansion == Expansion.FROM_ANOTHER:
                if {s.lemma: s.flg_expansion for s in synonym_group}.get(morpheme.normalized_form()) == 0:
                    return synonym_group[0].lemma
        return morpheme.surface()

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
        custom_representation = self.normalize_word_by_custom_synonyms(morpheme.surface())
        if custom_representation:
            return custom_representation
        return None

    def normalize(
        self,
        text: str,
        config: NormalizerConfig = NormalizerConfig(),
    ) -> str:
        """
        Normalize text by unifying spelling variations and synonyms（表記揺れと同義語を統一してテキストを正規化する）

        Args:
            text: Text to normalize（正規化するテキスト）
            config: Normalization options（正規化オプション）

        Returns:
            Normalized text（正規化されたテキスト）

        Example:
            normalized_text = normalize(text)
        """
        if not text:
            raise ValueError("Input text is empty.")
        flg_input = FlgInput(
            unify_level=UnifyLevel.from_str(config.unify_level),
            taigen=Taigen.from_int(config.taigen),
            yougen=Yougen.from_int(config.yougen),
            expansion=Expansion.from_str(config.expansion),
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
        # Since the conditions are hierarchical, if the lower-level condition is true, the upper-level condition is also set to true
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

        # If all flags are disabled, return the original text
        if (
            flg_input.custom_synonym == CusotomSynonym.DISABLE
            and flg_input.other_language == OtherLanguage.DISABLE
            and flg_input.alias == Alias.DISABLE
            and flg_input.old_name == OldName.DISABLE
            and flg_input.misuse == Misuse.DISABLE
        ):
            return text
        return self.__normalize_text(text=text, flg_input=flg_input)

    def __normalize_text(self, text: str, flg_input: FlgInput) -> str:
        """
        Normalize text by unifying spelling variations and synonyms（表記揺れと同義語を統一してテキストを正規化する）

        Args:
            text: Text to normalize（正規化するテキスト）
            flg_input: Normalization options（正規化オプション）

        Returns:
            Normalized text（正規化されたテキスト）

        Example:
            normalized_text = __normalize_text(text, flg_input)
        """
        morphemes = self.get_morphemes(text)
        normalized_parts = []
        for morpheme in morphemes:
            normalized_parts.append(self.normalize_word(morpheme, flg_input))
        return "".join(normalized_parts)

    def normalize_word(self, morpheme: Morpheme, flg_input: FlgInput) -> str:
        """
        Normalize a word by unifying spelling variations and synonyms（表記揺れと同義語を統一して単語を正規化する）

        Args:
            morpheme: Morpheme information（形態素情報）
            flg_input: Normalization options（正規化オプション）

        Returns:
            Normalized word（正規化された単語）

        Example:
            normalized_word = normalize_word(morpheme, flg_input)
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
            if not self.is_input_word_expansion_any_or_from_another(morpheme, synonym_group):
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
            synonym_group = self.get_represent_synonym_group_lexeme_id(flg_input, morpheme, synonym_group)
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
            synonym_group = self.get_represent_synonym_group_by_same_word_form(flg_input, morpheme, synonym_group)

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

    def is_input_word_expansion_any_or_from_another(self, morpheme: Morpheme, synonym_group: List[Synonym]) -> bool:
        """
        Judge whether the input word is expanded by synonyms（入力単語が同義語展開されるかどうかを判断する）

        Args:
            morpheme: Morpheme information（形態素情報）
            synonym_group: Synonym group（同義語グループ）

        Returns:
            True if the input word is expanded by synonyms, False otherwise（同義語展開される場合はTrue, されない場合はFalse）

        Example:
            is_expansion = is_input_word_expansion_any_or_from_another(morpheme, synonym_group)
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

    def get_represent_synonym_group_lexeme_id(
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
            synonym_group = get_represent_synonym_group_lexeme_id(flg_input, morpheme, synonym_group)
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

    def get_represent_synonym_group_by_same_word_form(
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
            synonym_group = get_represent_synonym_group_by_same_word_form(flg_input, morpheme, synonym_group)
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

    def normalize_word_by_custom_synonyms(self, word: str) -> Optional[str]:
        """
        Normalize a word by custom synonyms（カスタム同義語で単語を正規化する）

        Args:
            word: Word to normalize（正規化する単語）

        Returns:
            Normalized word（正規化された単語）

        Example:
            normalized_word = normalize_word_by_custom_synonyms(word)
        """
        for k, v in self.custom_synonyms.items():
            if word in v:
                return k
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
