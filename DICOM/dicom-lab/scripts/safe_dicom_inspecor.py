from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import pydicom
from pydicom.errors import InvalidDicomError


PHI_KEYWORDS = [
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "AccessionNumber",
    "StudyDate",
    "StudyTime",
    "InstitutionName",
    "ReferringPhysicianName",
    "StudyDescription",
    "SeriesDescription",
    "ProtocolName",
    "StationName",
    "DeviceSerialNumber",
]


def safe_text(value: Any, limit: int = 160) -> str:
    text = str(value)

    if len(text) > limit:
        return text[:limit] + "...<truncated>"

    return text


def value_length(value: Any) -> int | None:
    if isinstance(value, bytes):
        return len(value)

    if isinstance(value, str):
        return len(value)

    try:
        return len(value)
    except TypeError:
        return None


def inspect_dicom(
    path: Path,
    force: bool,
    max_file_mb: int,
    max_text_len: int,
    max_elements: int,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "file": str(path),
        "size_bytes": path.stat().st_size,
        "flags": [],
        "phi_like_metadata": [],
        "private_tags": [],
        "large_text_elements": [],
        "summary": {},
    }

    max_bytes = max_file_mb * 1024 * 1024

    if result["size_bytes"] > max_bytes:
        result["flags"].append(
            f"file_size_exceeds_limit: {result['size_bytes']} > {max_bytes}"
        )

    try:
        ds = pydicom.dcmread(
            str(path),
            stop_before_pixels=True,
            force=force,
        )
    except InvalidDicomError as exc:
        result["flags"].append(f"invalid_dicom: {exc}")
        return result

    result["summary"]["SOPClassUID"] = safe_text(getattr(ds, "SOPClassUID", ""))
    result["summary"]["TransferSyntaxUID"] = safe_text(
        getattr(getattr(ds, "file_meta", None), "TransferSyntaxUID", "")
    )
    result["summary"]["Modality"] = safe_text(getattr(ds, "Modality", ""))
    result["summary"]["StudyInstanceUID"] = safe_text(
        getattr(ds, "StudyInstanceUID", "")
    )

    for keyword in PHI_KEYWORDS:
        value = getattr(ds, keyword, None)

        if value is not None and str(value) != "":
            result["phi_like_metadata"].append(
                {
                    "keyword": keyword,
                    "value": safe_text(value),
                }
            )

    burned_in = str(getattr(ds, "BurnedInAnnotation", "")).upper()

    if burned_in == "YES":
        result["flags"].append("burned_in_annotation_yes")

    element_count = 0

    for elem in ds.iterall():
        element_count += 1

        if element_count > max_elements:
            result["flags"].append(f"too_many_elements: > {max_elements}")
            break

        if elem.tag.is_private:
            result["private_tags"].append(
                {
                    "tag": str(elem.tag),
                    "name": elem.name,
                    "vr": elem.VR,
                    "value_preview": safe_text(elem.value),
                }
            )

        length = value_length(elem.value)

        if isinstance(elem.value, str) and length is not None and length > max_text_len:
            result["large_text_elements"].append(
                {
                    "tag": str(elem.tag),
                    "keyword": elem.keyword,
                    "name": elem.name,
                    "vr": elem.VR,
                    "length": length,
                    "value_preview": safe_text(elem.value),
                }
            )

    result["summary"]["metadata_element_count"] = element_count
    result["summary"]["private_tag_count"] = len(result["private_tags"])
    result["summary"]["phi_like_metadata_count"] = len(result["phi_like_metadata"])

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DICOMを安全寄りに検査し、PHI残存や異常属性を確認します。"
    )
    parser.add_argument("file")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-file-mb", type=int, default=32)
    parser.add_argument("--max-text-len", type=int, default=512)
    parser.add_argument("--max-elements", type=int, default=5000)
    args = parser.parse_args()

    path = Path(args.file)

    if not path.exists():
        raise SystemExit(f"file not found: {path}")

    result = inspect_dicom(
        path=path,
        force=args.force,
        max_file_mb=args.max_file_mb,
        max_text_len=args.max_text_len,
        max_elements=args.max_elements,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
