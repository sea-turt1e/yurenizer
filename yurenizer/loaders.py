import csv
import json
from collections import defaultdict
from typing import Dict, List, Set

from .entities import Synonym


def load_sudachi_synonyms(synonym_file: str) -> Dict[str, List[Synonym]]:
    """
    Load synonym information from SudachiDict's synonyms.txt.

    Args:
        synonym_file: Path to the SudachiDict synonym file

    Returns:
        Synonym information dictionary
    """
    try:
        with open(synonym_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            data = [row for row in reader if row]

        synonyms = defaultdict(list)
        for line in data:
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
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Failed to load Sudachi synonyms: {e}")
    except ValueError as e:
        raise ValueError(f"Failed to load Sudachi synonyms: {e}")


def load_custom_synonyms(file_path: str) -> Dict[str, Set[str]]:
    """
    Load custom synonym definition JSON/CSV file.

    Args:
        file_path: Path to the custom synonym definition JSON/CSV file

    Returns:
        Custom synonym definition
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith((".csv", ".tsv")):
                delimiter = "," if file_path.endswith(".csv") else "\t"
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
