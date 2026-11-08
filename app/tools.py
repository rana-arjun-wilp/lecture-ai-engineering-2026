"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")

def make_quiz(lecture: int) -> str:
    """Pick one term from the given lecture and return a review question and its answer.

    Use when asked for review questions, such as "Give me a review question for Lecture 2"
    or "Quiz me on Lecture 1". Picks one term at random from the glossary for the given
    lecture number and returns a question asking what the term means along with its answer.
    """
    glossary = load_glossary()
    terms = [e for e in glossary if e["lecture"] == lecture]
    if not terms:
        available = sorted({e["lecture"] for e in glossary})
        return json.dumps({"error": f"No terms found for lecture {lecture}. Available lectures: {available}"}, ensure_ascii=False)
    entry = random.choice(terms)
    return json.dumps({
        "question": f'What does "{entry["term"]}" mean?',
        "answer": entry["definition"],
        "lecture": entry["lecture"],
    }, ensure_ascii=False)


def save_learning_log(note: str) -> str:
    """Save a learning note or record to the learning_log folder.

    Use when the user explicitly asks to save, record, or log something they have learned.
    Saves the note as a timestamped text file in learning_log/.
    Requires user confirmation before saving because this writes to disk and is hard to undo.
    """
    import datetime
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = LOG_DIR / f"log_{timestamp}.txt"
    path.write_text(note, encoding="utf-8")
    return json.dumps({"saved": str(path), "note": note}, ensure_ascii=False)
