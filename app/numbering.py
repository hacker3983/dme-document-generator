import json
from pathlib import Path
from datetime import date


def _get_prefix_and_key(doc_type: str, year: int) -> tuple[str, str]:
    mapping = {
        "invoice": ("DME-INV", f"invoice_{year}"),
        "pro_forma": ("DME-PF", f"proforma_{year}"),
        "quote": ("DME-QT", f"quote_{year}"),
    }
    return mapping.get(doc_type, ("DME-INV", f"invoice_{year}"))


def peek_next_invoice_number(data_dir: Path, doc_type: str = "invoice") -> str:
    """Determine the next sequential document number without committing it."""
    counter_file = data_dir / "numbering.json"
    year = date.today().year
    prefix, key = _get_prefix_and_key(doc_type, year)

    if counter_file.exists():
        try:
            state = json.loads(counter_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}
    else:
        state = {}

    sequence = int(state.get(key, 0)) + 1
    return f"{prefix}-{year}-{sequence:03d}"


def commit_invoice_number(data_dir: Path, doc_type: str = "invoice") -> str:
    """Persist and increment the sequential document number upon success."""
    counter_file = data_dir / "numbering.json"
    year = date.today().year
    prefix, key = _get_prefix_and_key(doc_type, year)

    if counter_file.exists():
        try:
            state = json.loads(counter_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}
    else:
        state = {}

    sequence = int(state.get(key, 0)) + 1
    state[key] = sequence
    counter_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return f"{prefix}-{year}-{sequence:03d}"
