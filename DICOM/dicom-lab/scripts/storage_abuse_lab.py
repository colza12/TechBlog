import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid
from pynetdicom import AE
from pynetdicom.sop_class import SecondaryCaptureImageStorage as SC_STORAGE


PACS_HOST = "127.0.0.1"
PACS_PORT = 4242
PACS_AET = "ORTHANC"
CALLING_AET = "LABCLIENT"


def build_dicom(index: int, rows: int, columns: int) -> FileDataset:
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(
        None,
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )

    now = datetime.now()

    ds.PatientName = f"LOADTEST^{index:04d}"
    ds.PatientID = f"LOAD-{index:04d}"
    ds.StudyDate = now.strftime("%Y%m%d")
    ds.StudyTime = now.strftime("%H%M%S")
    ds.Modality = "OT"
    ds.StudyDescription = "LAB STORAGE LOAD TEST"
    ds.SeriesDescription = "Small generated images"
    ds.InstitutionName = "DICOM Cybersecurity Lab"

    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPClassUID = SecondaryCaptureImageStorage
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = rows
    ds.Columns = columns
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0

    pixel_array = np.zeros((rows, columns), dtype=np.uint8)
    pixel_array[:, :] = index % 256
    ds.PixelData = pixel_array.tobytes()

    return ds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--rows", type=int, default=64)
    parser.add_argument("--columns", type=int, default=64)
    args = parser.parse_args()

    if args.count > 100:
        raise ValueError("Safety limit: --count must be 100 or less")

    if args.rows * args.columns > 512 * 512:
        raise ValueError("Safety limit: image size must be 512x512 or less")

    ae = AE(ae_title=CALLING_AET)
    ae.add_requested_context(SC_STORAGE)

    assoc = ae.associate(PACS_HOST, PACS_PORT, ae_title=PACS_AET)

    if not assoc.is_established:
        print("Association failed")
        return

    for index in range(args.count):
        ds = build_dicom(index=index, rows=args.rows, columns=args.columns)
        status = assoc.send_c_store(ds)

        if status:
            print(f"[{index}] C-STORE status: 0x{status.Status:04X}")
        else:
            print(f"[{index}] C-STORE failed")

    assoc.release()


if __name__ == "__main__":
    main()
