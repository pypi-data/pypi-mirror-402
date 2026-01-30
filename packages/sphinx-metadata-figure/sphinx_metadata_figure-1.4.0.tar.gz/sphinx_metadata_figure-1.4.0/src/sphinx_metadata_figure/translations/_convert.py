import json
import os
from pathlib import Path
import subprocess

MESSAGE_CATALOG_NAME = "sphinx_metadata_figure"

def convert_json(folder=None):
    folder = folder or Path(__file__).parent

    # remove exising
    for path in (folder / "locales").glob(f"**/{MESSAGE_CATALOG_NAME}.po"):
        path.unlink()

    # compile po and create untranslate json
    untranslate_data = {}
    for path in (folder / "jsons").glob("*.json"):
        data = json.loads(path.read_text("utf8"))
        assert data[0]["symbol"] == "en"
        english = data[0]["text"]
        for item in data:
            if item["text"] not in untranslate_data:
                 untranslate_data.update({item["text"]: english})
        for item in data[1:]:
            language = item["symbol"]
            out_path = folder / "locales" / language / "LC_MESSAGES" / f"{MESSAGE_CATALOG_NAME}.po"
            if not out_path.parent.exists():
                out_path.parent.mkdir(parents=True)
            if not out_path.exists():
                header = f"""
msgid ""
msgstr ""
"Project-Id-Version: Sphinx-Metadata-Figure\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Language: {language}\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"
"""
                out_path.write_text(header)

            with out_path.open("a", encoding="utf8") as f:
                f.write("\n")
                f.write(f'msgid "{english}"\n')
                text = item["text"].replace('"', '\\"')
                f.write(f'msgstr "{text}"\n')

    # write untranslate json
    untranslate_path = folder / "untranslate.json"
    untranslate_path.write_text(json.dumps(untranslate_data, ensure_ascii=False, indent=2), encoding="utf8")

    # compile mo
    for path in (folder / "locales").glob(f"**/{MESSAGE_CATALOG_NAME}.po"):
        print(path)
        subprocess.check_call(
            [
                "msgfmt",
                os.path.abspath(path),
                "-o",
                os.path.abspath(path.parent / f"{MESSAGE_CATALOG_NAME}.mo"),
            ]
        )


if __name__ == "__main__":
    convert_json()