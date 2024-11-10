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
    Missspelling,
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
        synonyms = self.load_sudachi_synonyms(synonym_file_path)
        self.synonyms = {int(k): v for k, v in synonyms.items()}

        # カスタム同義語の読み込み
        self.custom_synonyms = {}
        if custom_synonyms_file:
            self.custom_synonyms = self.load_custom_synonyms(custom_synonyms_file)

    def load_sudachi_synonyms(self, synonym_file: str) -> Dict[int, List[Synonym]]:
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
        # グループ辞書から同義語グループを探す
        synonym_group = self.get_synonym_group(morpheme)
        if synonym_group:
            if expansion == Expansion.ANY:
                return synonym_group[0].lemma
            elif expansion == Expansion.FROM_ANOTHER:
                if {s.lemma: s.flg_expansion for s in synonym_group}.get(morpheme.normalized_form()) == 0:
                    return synonym_group[0].lemma
        return morpheme.surface()

    def get_custom_synonym(self, morpheme: Morpheme) -> Optional[str]:
        # カスタム同義語定義を使用
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
        テキストの表記ゆれと同義語を統一する

        Args:
            config: 正規化のオプション

        Returns:
            正規化された文字列
        """
        if not text:
            raise ValueError("テキストが空です")
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
            missspelling=Missspelling.from_int(config.missspelling),
            custom_synonym=CusotomSynonym.from_int(config.custom_synonym),
        )
        # 条件が階層的になっているので、下位の条件が正だった場合は上位の条件は正とする
        if (
            flg_input.alphabet == Alphabet.ENABLE
            or flg_input.orthographic_variation == OrthographicVariation.ENABLE
            or flg_input.missspelling == Missspelling.ENABLE
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
        # カスタム同義語定義を使用
        custom_representation = self.get_custom_synonym(morpheme)
        if custom_representation:
            return custom_representation
        # 用言、体言の判定
        is_yougen = self.yougen_matcher(morpheme)
        is_taigen = self.taigen_matcher(morpheme)
        if (flg_input.yougen == Yougen.INCLUDE and is_yougen) or (flg_input.taigen == Taigen.INCLUDE and is_taigen):
            pass
        else:
            return morpheme.surface()

        # 体言ごと、または用言ごとの同義語グループを取得
        synonym_group = self.get_synonym_group(morpheme, is_yougen, is_taigen)
        if not synonym_group:
            return morpheme.surface()

        # 展開制御フラグによってのちの処理を変える
        if flg_input.expansion == Expansion.ANY:
            if not self.is_input_word_expansion_any_or_from_another(morpheme, synonym_group):
                return morpheme.surface()
        elif flg_input.expansion == Expansion.FROM_ANOTHER:
            if not self.is_input_word_expansion_from_another(morpheme, synonym_group):
                return morpheme.surface()
        else:
            return morpheme.surface()

        # 同一語彙素の同義語グループを絞り込む
        if (
            flg_input.other_language == OtherLanguage.ENABLE
            or flg_input.alias == Alias.ENABLE
            or flg_input.old_name == OldName.ENABLE
            or flg_input.misuse == Misuse.ENABLE
        ):
            synonym_group = self.get_represent_synonym_group_lexeme_id(flg_input, morpheme, synonym_group)
        if not synonym_group:
            return morpheme.surface()

        # 同じ語形の同義語グループを取得
        if (
            flg_input.alphabetic_abbreviation == AlphabeticAbbreviation.ENABLE
            or flg_input.non_alphabetic_abbreviation == NonAlphabeticAbbreviation.ENABLE
            or flg_input.alphabet == Alphabet.ENABLE
            or flg_input.orthographic_variation == OrthographicVariation.ENABLE
            or flg_input.missspelling == Missspelling.ENABLE
        ):
            synonym_group = self.get_represent_synonym_group_by_same_word_form(flg_input, morpheme, synonym_group)

        if not synonym_group:
            return morpheme.surface()

        # 同じ略語・略称の同義語グループを取得
        if (
            flg_input.alphabet == Alphabet.ENABLE
            or flg_input.orthographic_variation == OrthographicVariation.ENABLE
            or flg_input.missspelling == Missspelling.ENABLE
        ):
            synonym_group = self.get_represent_synonym_group_by_same_abbreviation(flg_input, morpheme, synonym_group)
        if not synonym_group:
            return morpheme.surface()

        # 同義語グループから代表表記を取得。展開制御フラグによって絞り込む
        represent_synonym = synonym_group[0]
        if represent_synonym:
            return represent_synonym.lemma
        return morpheme.surface()

    def is_input_word_expansion_any_or_from_another(self, morpheme: Morpheme, synonym_group: List[Synonym]) -> bool:
        """
        入力単語が同義語展開されるかどうかを判断する

        Args:
            morpheme: 形態素情報
            synonym_group: 同義語グループ
        Returns:
            同義語展開される場合はTrue, されない場合はFalse
        """
        flg_expansion = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.FLG_EXPANSION)
        if flg_expansion in (FlgExpantion.ANY.value, FlgExpantion.FROM_ANOTHER.value):
            return True
        return False

    def is_input_word_expansion_from_another(self, morpheme: Morpheme, synonym_group: List[Synonym]) -> bool:
        """
        入力単語が同義語展開されるかどうかを判断する

        Args:
            morpheme: 形態素情報
            synonym_group: 同義語グループ
        Returns:
            同義語展開される場合はTrue, されない場合はFalse
        """
        flg_expansion = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.FLG_EXPANSION)
        if flg_expansion == FlgExpantion.ANY.value:
            return True
        return False

    def get_represent_synonym_group_lexeme_id(
        self, flg_input: FlgInput, morpheme: Morpheme, synonym_group: List[Synonym]
    ) -> List[Synonym]:
        """
        同一語彙素の同義語グループを絞り込む

        Args:
            morpheme: 形態素情報
            synonym_group: 同義語グループ
        Returns:
            Synonymオブジェクトのリスト
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
        同じ語形の同義語グループを取得

        Args:
            morpheme: 形態素情報
            synonym_group: 同義語グループ
        Returns:
            Synonymオブジェクトのリスト
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
        同じ略語・略称の同義語グループを取得

        Args:
            morpheme: 形態素情報
            synonym_group: 同義語グループ

        Returns:
            Synonymオブジェクトのリスト
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
            flg_input.missspelling == Missspelling.ENABLE
            and spelling_inconsistency == SpellingInconsistency.MISSPELLING.value
        ):
            is_expansion = True
        if is_expansion:
            if flg_input.unify_level in (UnifyLevel.LEXEME, UnifyLevel.WORD_FORM):
                return synonym_group
            elif flg_input.unify_level == UnifyLevel.ABBREVIATION:
                filtered_synonym_group = [s for s in synonym_group if s.abbreviation == abbreviation]
        return filtered_synonym_group

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
            synonym_group = self.get_synonym_group(morpheme)
            flg_expansion = self.get_synonym_value_from_morpheme(morpheme, synonym_group, SynonymField.FLG_EXPANSION)
            if flg_expansion == FlgExpantion.ANY.value:
                return True
        return False

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

    def get_synonym_group(self, morpheme: Morpheme, is_yougen: bool, is_taigen: bool) -> Optional[List[Synonym]]:
        synonym_group_ids = morpheme.synonym_group_ids()
        if synonym_group_ids:
            # 同義語グループのIDが1つの場合のみ。複数ある場合は判定できないので、Noneで返す。IDがない場合もNoneで返す
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
