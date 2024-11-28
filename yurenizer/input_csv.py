from yurenizer import SynonymNormalizer
from .entities import SudachiDictType
from typing import Optional


class CsvSynonymNormalizer(SynonymNormalizer):
    def __init__(
        self,
        synonym_file_path: str,
        sudachi_dict: SudachiDictType = SudachiDictType.FULL.value,
        custom_synonyms_file: Optional[str] = None,
    ) -> None:
        super().__init__()

    def normalize_csv(self, text: str) -> str:
        return text
