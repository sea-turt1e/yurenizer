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
    return next((getattr(item, synonym_attr.value) for item in synonym_group if item.lemma == morpheme.surface()), None)
