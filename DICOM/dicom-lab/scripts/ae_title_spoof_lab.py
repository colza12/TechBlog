import argparse

from pynetdicom import AE
from pynetdicom.sop_class import Verification


PACS_HOST = "127.0.0.1"
PACS_PORT = 4242
PACS_AET = "ORTHANC"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--calling-aet",
        default="CT_ROOM_01",
        help="Calling AE Title to present to the PACS",
    )
    args = parser.parse_args()

    ae = AE(ae_title=args.calling_aet)
    ae.add_requested_context(Verification)

    assoc = ae.associate(PACS_HOST, PACS_PORT, ae_title=PACS_AET)

    if not assoc.is_established:
        print("Association failed")
        return

    status = assoc.send_c_echo()

    if status:
        print(f"Calling AE Title: {args.calling_aet}")
        print(f"C-ECHO status: 0x{status.Status:04X}")
    else:
        print("C-ECHO failed")

    assoc.release()


if __name__ == "__main__":
    main()
