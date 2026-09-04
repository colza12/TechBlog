import argparse

import pydicom


SENSITIVE_KEYWORDS = [
    "Patient",
    "Physician",
    "Institution",
    "Referring",
    "Operator",
    "Station",
    "Device",
    "Accession",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dicom_file")
    args = parser.parse_args()

    ds = pydicom.dcmread(args.dicom_file, stop_before_pixels=True)

    for elem in ds.iterall():
        keyword = elem.keyword or ""
        name = elem.name or ""

        if any(token in keyword or token in name for token in SENSITIVE_KEYWORDS):
            print(f"{elem.tag} {keyword}: {elem.value}")


if __name__ == "__main__":
    main()
