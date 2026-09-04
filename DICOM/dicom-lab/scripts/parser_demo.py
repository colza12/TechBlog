from pathlib import Path
from datetime import datetime
import csv

import numpy as np
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid


OUTPUT_DIR = Path("data/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_pathological_metadata_dicom(output_path: Path) -> None:
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(
        str(output_path),
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )

    now = datetime.now()

    ds.PatientName = "ATTACK^LOG\nInjected-Log-Line: false status"
    ds.PatientID = "=HYPERLINK(\"http://example.invalid\",\"click\")"
    ds.StudyDate = now.strftime("%Y%m%d")
    ds.StudyTime = now.strftime("%H%M%S")
    ds.Modality = "OT"
    ds.StudyDescription = "<img src=x onerror=alert(1)>"
    ds.InstitutionName = "DICOM Parser Lab"
    ds.AccessionNumber = "LAB-PARSER-0001"

    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPClassUID = SecondaryCaptureImageStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 64
    ds.Columns = 64
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0

    pixel_array = np.zeros((64, 64), dtype=np.uint8)
    pixel_array[8:56, 8:56] = 120
    ds.PixelData = pixel_array.tobytes()

    ds.save_as(output_path, write_like_original=False)


def naive_export_to_csv(dicom_path: Path, csv_path: Path) -> None:
    import pydicom

    ds = pydicom.dcmread(dicom_path, stop_before_pixels=True)

    rows = [
        ["field", "value"],
        ["PatientName", str(getattr(ds, "PatientName", ""))],
        ["PatientID", str(getattr(ds, "PatientID", ""))],
        ["StudyDescription", str(getattr(ds, "StudyDescription", ""))],
        ["InstitutionName", str(getattr(ds, "InstitutionName", ""))],
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main() -> None:
    dicom_path = OUTPUT_DIR / "pathological_metadata.dcm"
    csv_path = OUTPUT_DIR / "naive_export.csv"

    create_pathological_metadata_dicom(dicom_path)
    naive_export_to_csv(dicom_path, csv_path)

    print(f"Created DICOM: {dicom_path}")
    print(f"Created CSV: {csv_path}")
    print("Inspect the CSV as text before opening it in spreadsheet software.")


if __name__ == "__main__":
    main()
