from __future__ import annotations

import argparse
from pathlib import Path

import pydicom


def main() -> None:
    parser = argparse.ArgumentParser(
        description="検証用のSuspicious DICOMを作成します。"
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="data/suspicious.dcm")
    args = parser.parse_args()

    src = Path(args.input)
    out = Path(args.out)

    if not src.exists():
        raise SystemExit(f"input not found: {src}")

    ds = pydicom.dcmread(str(src))

    ds.BurnedInAnnotation = "YES"
    ds.ImageComments = "LAB_ONLY_METADATA_PADDING:" + ("X" * 4096)

    ds.add_new((0x0011, 0x0010), "LO", "LAB_PRIVATE_CREATOR")
    ds.add_new(
        (0x0011, 0x1001),
        "LT",
        "LAB_ONLY_PRIVATE_TAG_MARKER: this simulates hidden metadata, not exploit code.",
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    ds.save_as(str(out), write_like_original=False)

    print(f"created: {out}")


if __name__ == "__main__":
    main()
