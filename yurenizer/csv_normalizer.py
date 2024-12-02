import csv
from typing import Optional

from .entities import SudachiDictType
from .normalizer import NormalizerConfig, SynonymNormalizer


class CsvSynonymNormalizer(SynonymNormalizer):
    def __init__(
        self,
        synonym_file_path: str,
        sudachi_dict: SudachiDictType = SudachiDictType.FULL.value,
        custom_synonyms_file: Optional[str] = None,
    ) -> None:
        super().__init__(synonym_file_path, sudachi_dict, custom_synonyms_file)

    def normalize_csv(
        self,
        input_file_path: str,
        output_file_path: str,
        config: NormalizerConfig = NormalizerConfig(),
    ) -> None:
        with open(input_file_path, "r") as f, open(output_file_path, "w") as w:
            reader = csv.reader(f)
            writer = csv.writer(w)
            header = ["raw", "normalized"]
            writer.writerow(header)
            for row in reader:
                print([row[0], self.normalize(row[0], config)])
                writer.writerow([row[0], self.normalize(row[0], config)])
