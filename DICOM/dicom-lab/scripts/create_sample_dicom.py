from pathlib import Path
from datetime import datetime

import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid, SecondaryCaptureImageStorage


OUTPUT_DIR = Path("data/generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_dicom(output_path: Path) -> None:
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

    ds.SpecificCharacterSet = "ISO_IR 100"
    ds.PatientName = "LAB^PATIENT"
    ds.PatientID = "LAB-0001"
    ds.PatientBirthDate = "19700101"
    ds.PatientSex = "O"

    ds.StudyDate = now.strftime("%Y%m%d")
    ds.StudyTime = now.strftime("%H%M%S")
    ds.AccessionNumber = "LAB-ACCESSION-0001"
    ds.Modality = "OT"
    ds.StudyDescription = "DICOM LAB SAMPLE"
    ds.SeriesDescription = "Generated sample"
    ds.InstitutionName = "DICOM Cybersecurity Lab"
    ds.ReferringPhysicianName = "LAB^DOCTOR"

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
    pixel_array[16:48, 16:48] = 180
    ds.PixelData = pixel_array.tobytes()

    ds.save_as(output_path, write_like_original=False)


if __name__ == "__main__":
    output = OUTPUT_DIR / "sample.dcm"
    create_sample_dicom(output)
    print(f"Created: {output}")
