from dataclasses import dataclass


@dataclass
class NormalizerConfig:
    unify_level: str = "lexeme"
    taigen: bool = True
    yougen: bool = False
    expansion: str = "from_another"
    other_language: bool = True
    alias: bool = True
    old_name: bool = True
    misuse: bool = True
    alphabetic_abbreviation: bool = True
    non_alphabetic_abbreviation: bool = True
    alphabet: bool = True
    orthographic_variation: bool = True
    missspelling: bool = True
    custom_synonym: bool = True

    """
    NormalizerConfigクラスは正規化の設定を保持するクラスです。
    このクラスのインスタンスを生成し、normalizeメソッドに引数として渡すことで、正規化の設定を変更することができます。
    このクラスの各フィールドは、正規化の設定を表すフラグを保持します。

    Args:
        unify_level（default="lexeme"）:統一レベルを指定するフラグ。デフォルト"lexeme"はlexeme（語彙素）番号が同じもので統一。"word_form"オプションはwor_form（語形）番号が同じものでの統一。"abbreviation"オプションはabbreviation（略語）番号が同じものでの統一。
        taigen（default=True）: 統一するのに体言を含むかどうかのフラグ。デフォルトは含む。含まない場合はFalseを指定。
        yougen（default=False）: 統一するのに用言を含むかどうかのフラグ。デフォルトは含まない。含む場合はTrueを指定。ただし用言は
        expansion（default="from_another"）: 同義語展開の制御フラグ。デフォルトは同義語辞書の展開制御フラグが0のもののみ展開。"ANY"を指定すると展開制御フラグが常に展開する。
        other_language（default=True）: 日本語以外の言語を日本語に正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        alias（default=True）: 別称を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        old_name（default=True）: 旧称を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        misuse（default=True）: 誤用を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        alphabetic_abbreviation（default=True）: アルファベットの略語を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        non_alphabetic_abbreviation（default=True）: 日本語の略語を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        alphabet（default=True）: アルファベットの表記揺れを正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        orthographic_variation（default=True）: 異表記を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        missspelling（default=True）: 誤表記を正規化するかどうかのフラグ。デフォルトは正規化する。正規化しない場合はFalseを指定。
        custom_synonym（default=True）: ユーザーが設定したcustom_synonymを使用するかどうかのフラグ。デフォルトは使用する。使用しない場合はFalseを指定。

    例:
        ```
        config = NormalizerConfig(taigen=0, yougen=1)
        normalizer = SynonymNormalizer(config)
        result = normalizer.normalize("テストを実行する")
        ```

    See Also:
        SudachiDictの同義語辞書ソース:
        https://github.com/WorksApplications/SudachiDict/blob/develop/docs/synonyms.md#%E5%90%8C%E7%BE%A9%E8%AA%9E%E8%BE%9E%E6%9B%B8%E3%82%BD%E3%83%BC%E3%82%B9-%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88
    """
