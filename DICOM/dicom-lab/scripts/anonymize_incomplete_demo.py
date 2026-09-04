import argparse
from pathlib import Path

import pydicom


def incomplete_anonymize(input_path: Path, output_path: Path) -> None:
    ds = pydicom.dcmread(input_path)

    if "PatientName" in ds:
        ds.PatientName = "ANONYMIZED"

    if "PatientID" in ds:
        ds.PatientID = "ANONYMIZED"

    ds.save_as(output_path, write_like_original=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    args = parser.parse_args()

    incomplete_anonymize(
        Path(args.input_file),
        Path(args.output_file),
    )

    print(f"Saved: {args.output_file}")
    print("Warning: this is intentionally incomplete anonymization")


if __name__ == "__main__":
    main()
