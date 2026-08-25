#!/usr/bin/env python3
"""Print a non-sensitive summary of the ESP-IDF PHY NVS namespace."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


def find_parser_dir(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())

    idf_path = os.environ.get("IDF_PATH")
    if idf_path:
        candidates.append(
            Path(idf_path) / "components/nvs_flash/nvs_partition_tool"
        )

    candidates.extend(
        sorted(
            Path.home().glob(
                ".espressif/*/esp-idf/components/nvs_flash/nvs_partition_tool"
            ),
            reverse=True,
        )
    )

    for candidate in candidates:
        if (candidate / "nvs_parser.py").is_file():
            return candidate.resolve()

    raise RuntimeError(
        "nvs_parser.py was not found; pass --parser-dir with the ESP-IDF "
        "components/nvs_flash/nvs_partition_tool directory"
    )


def written_entries(nvs: Any) -> Iterable[Any]:
    for page in nvs.pages:
        for entry in page.entries:
            if entry.state == "Written":
                yield entry


def entry_payload(entry: Any) -> bytes:
    payload = b"".join(bytes(child.raw) for child in entry.children)
    size = entry.data["size"]
    if len(payload) < size:
        raise RuntimeError(
            f"{entry.key}: chunk has {len(payload)} bytes, expected {size}"
        )
    return payload[:size]


def assemble_blob(entries: list[Any], key: str) -> bytes:
    indexes = [
        entry
        for entry in entries
        if entry.key == key and entry.metadata["type"] == "blob_index"
    ]
    if len(indexes) != 1:
        raise RuntimeError(f"{key}: expected one blob index, found {len(indexes)}")

    index = indexes[0]
    chunk_start = index.data["chunk_start"]
    chunk_count = index.data["chunk_count"]
    chunks: dict[int, bytes] = {}

    for entry in entries:
        if entry.key != key or entry.metadata["type"] != "blob_data":
            continue
        relative_index = (entry.metadata["chunk_index"] - chunk_start) % 256
        if relative_index >= chunk_count:
            raise RuntimeError(
                f"{key}: chunk index {entry.metadata['chunk_index']} is out of range"
            )
        if relative_index in chunks:
            raise RuntimeError(f"{key}: duplicate chunk {relative_index}")
        chunks[relative_index] = entry_payload(entry)

    missing = [index for index in range(chunk_count) if index not in chunks]
    if missing:
        raise RuntimeError(f"{key}: missing chunks {missing}")

    payload = b"".join(chunks[index] for index in range(chunk_count))
    expected_size = index.data["size"]
    if len(payload) != expected_size:
        raise RuntimeError(
            f"{key}: assembled size {len(payload)}, expected {expected_size}"
        )
    return payload


def scalar_value(entries: list[Any], key: str, expected_type: str) -> int:
    matches = [
        entry
        for entry in entries
        if entry.key == key and entry.metadata["type"] == expected_type
    ]
    if len(matches) != 1:
        raise RuntimeError(f"{key}: expected one {expected_type}, found {len(matches)}")
    return int(matches[0].data["value"])


def parse_mac(value: str) -> bytes:
    compact = value.replace(":", "").replace("-", "")
    if len(compact) != 12:
        raise argparse.ArgumentTypeError("MAC must contain exactly 12 hex digits")
    try:
        return bytes.fromhex(compact)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("MAC contains non-hex characters") from exc


def format_mac(value: bytes) -> str:
    return ":".join(f"{byte:02x}" for byte in value)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def build_summary(nvs_file: Path, nvs_parser: Any, expected_mac: bytes | None) -> dict:
    partition = nvs_parser.NVS_Partition(
        nvs_file.name, bytearray(nvs_file.read_bytes())
    )
    entries = list(written_entries(partition))
    namespaces = {
        entry.data["value"]: entry.key
        for entry in entries
        if entry.metadata["namespace"] == 0
    }
    phy_entries = [
        entry
        for entry in entries
        if namespaces.get(entry.metadata["namespace"]) == "phy"
    ]
    if not phy_entries:
        raise RuntimeError("the phy namespace is missing or empty")

    cal_version = scalar_value(phy_entries, "cal_version", "uint32_t")
    cal_mac = assemble_blob(phy_entries, "cal_mac")
    cal_data = assemble_blob(phy_entries, "cal_data")
    embedded_mac = cal_data[4:10] if len(cal_data) >= 10 else b""

    summary = {
        "source": str(nvs_file.resolve()),
        "cal_version": cal_version,
        "cal_version_hex": f"0x{cal_version:08X}",
        "cal_mac": format_mac(cal_mac),
        "cal_mac_length": len(cal_mac),
        "cal_mac_sha256": sha256(cal_mac),
        "cal_data_length": len(cal_data),
        "cal_data_sha256": sha256(cal_data),
        "cal_data_embedded_mac": format_mac(embedded_mac),
        "cal_data_mac_matches_cal_mac": embedded_mac == cal_mac,
    }
    if expected_mac is not None:
        summary["expected_mac"] = format_mac(expected_mac)
        summary["cal_mac_matches_expected_mac"] = cal_mac == expected_mac
    return summary


def validate_summary(summary: dict, expected_mac: bytes | None) -> list[str]:
    errors: list[str] = []
    if summary["cal_mac_length"] != 6:
        errors.append(f"cal_mac length is {summary['cal_mac_length']}, expected 6")
    if summary["cal_data_length"] != 1904:
        errors.append(
            f"cal_data length is {summary['cal_data_length']}, expected 1904"
        )
    if not summary["cal_data_mac_matches_cal_mac"]:
        errors.append("cal_data embedded MAC does not match cal_mac")
    if expected_mac is not None and not summary["cal_mac_matches_expected_mac"]:
        errors.append("cal_mac does not match the expected device MAC")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize only phy:cal_version, cal_mac, and cal_data without "
            "printing raw calibration data or other NVS namespaces."
        )
    )
    parser.add_argument("nvs_file", type=Path)
    parser.add_argument("--parser-dir", help="Directory containing nvs_parser.py")
    parser.add_argument("--expected-mac", type=parse_mac)
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail unless MAC relationships and expected PHY blob lengths are valid",
    )
    args = parser.parse_args()

    if not args.nvs_file.is_file():
        parser.error(f"NVS file does not exist: {args.nvs_file}")

    try:
        parser_dir = find_parser_dir(args.parser_dir)
        sys.path.insert(0, str(parser_dir))
        nvs_parser = importlib.import_module("nvs_parser")
        summary = build_summary(args.nvs_file, nvs_parser, args.expected_mac)
        validation_errors = (
            validate_summary(summary, args.expected_mac) if args.strict else []
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=True))
    else:
        for key, value in summary.items():
            print(f"{key}: {value}")
    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
