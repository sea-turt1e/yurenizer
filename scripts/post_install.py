import subprocess
from pathlib import Path


def post_install():
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    url = "https://raw.githubusercontent.com/WorksApplications/SudachiDict/develop/src/main/text/synonyms.txt"
    output_path = data_dir / "synonyms.txt"

    # curlを使用してファイルをダウンロード
    subprocess.run(["curl", "-o", str(output_path), url], check=True)


if __name__ == "__main__":
    post_install()
