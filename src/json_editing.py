"""Batch-update JSON files in this folder.

If a JSON file has a ``Source`` value that includes ``Lene Voigt``, ensure
``Origin`` contains ``Leipzig``.
"""

from __future__ import annotations

import json
from pathlib import Path


def ensure_origin(json_path: Path, source_value: str, origin_value: str) -> bool:
	"""Update one JSON file in place.

	Returns True when the file was changed.
	"""
	with json_path.open("r", encoding="utf-8") as handle:
		data = json.load(handle)

	if not isinstance(data, dict):
		return False

	source = data.get("Source", "")
	if source_value not in str(source):
		return False

	origin = data.get("Origin", "")
	if isinstance(origin, list):
		if origin_value in origin:
			return False
		origin.append(origin_value)
	elif isinstance(origin, str):
		if origin == origin_value:
			return False
		origin = origin.strip()
		origin = origin_value if not origin else f"{origin}, {origin_value}"
	else:
		origin = origin_value

	data["Origin"] = origin

	with json_path.open("w", encoding="utf-8") as handle:
		json.dump(data, handle, ensure_ascii=False, indent=2)
		handle.write("\n")

	return True


if __name__ == "__main__":
	base_dir = Path("webpages/lieder_anton_guenther/json")
	changed_files = 0

	for json_path in sorted(base_dir.glob("*.json")):
		if ensure_origin(json_path, "Anton Günther", "Erzgebirge"):
			changed_files += 1

	print(f"Updated {changed_files} JSON file(s).")
