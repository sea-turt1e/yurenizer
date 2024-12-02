import pytest

from yurenizer.csv_normalizer import CsvSynonymNormalizer


class TestCsvSynonymNormalizer:
    @pytest.fixture
    def csv_synonym_normalizer(self):
        return CsvSynonymNormalizer(synonym_file_path="yurenizer/data/synonyms.txt")

    def test_normalize(self, csv_synonym_normalizer):
        input_file_path = "tests/data/test.csv"
        output_file_path = "tests/data/normalized_test.csv"
        gold_output_file_path = "tests/data/gold_normalized_test.csv"
        csv_synonym_normalizer.normalize_csv(input_file_path, output_file_path)
        # output_csv should be the same as gold_output_csv
        with open(output_file_path, "r") as f1, open(gold_output_file_path, "r") as f2:
            assert f1.read() == f2.read()
