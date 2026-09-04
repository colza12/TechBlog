from pynetdicom import AE
from pynetdicom.sop_class import Verification


PACS_HOST = "127.0.0.1"
PACS_PORT = 4242
PACS_AET = "ORTHANC"
CALLING_AET = "LABCLIENT"


def main() -> None:
    ae = AE(ae_title=CALLING_AET)
    ae.add_requested_context(Verification)

    assoc = ae.associate(PACS_HOST, PACS_PORT, ae_title=PACS_AET)

    if not assoc.is_established:
        print("Association failed")
        return

    status = assoc.send_c_echo()

    if status:
        print(f"C-ECHO status: 0x{status.Status:04X}")
    else:
        print("C-ECHO failed")

    assoc.release()


if __name__ == "__main__":
    main()
