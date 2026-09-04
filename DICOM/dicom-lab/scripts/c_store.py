from pathlib import Path

import pydicom
from pynetdicom import AE
from pynetdicom.sop_class import SecondaryCaptureImageStorage


PACS_HOST = "127.0.0.1"
PACS_PORT = 4242
PACS_AET = "ORTHANC"
CALLING_AET = "LABCLIENT"

DICOM_FILE = Path("data/generated/sample.dcm")


def main() -> None:
    ds = pydicom.dcmread(DICOM_FILE)

    ae = AE(ae_title=CALLING_AET)
    ae.add_requested_context(SecondaryCaptureImageStorage)

    assoc = ae.associate(PACS_HOST, PACS_PORT, ae_title=PACS_AET)

    if not assoc.is_established:
        print("Association failed")
        return

    status = assoc.send_c_store(ds)

    if status:
        print(f"C-STORE status: 0x{status.Status:04X}")
    else:
        print("C-STORE failed")

    assoc.release()


if __name__ == "__main__":
    main()
