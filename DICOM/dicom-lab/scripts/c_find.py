from pynetdicom import AE
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind
from pydicom.dataset import Dataset


PACS_HOST = "127.0.0.1"
PACS_PORT = 4242
PACS_AET = "ORTHANC"
CALLING_AET = "LABCLIENT"


def main() -> None:
    ae = AE(ae_title=CALLING_AET)
    ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

    assoc = ae.associate(PACS_HOST, PACS_PORT, ae_title=PACS_AET)

    if not assoc.is_established:
        print("Association failed")
        return

    query = Dataset()
    query.QueryRetrieveLevel = "STUDY"
    query.PatientName = "*"
    query.PatientID = ""
    query.StudyDate = ""
    query.StudyDescription = ""
    query.Modality = ""
    query.StudyInstanceUID = ""

    responses = assoc.send_c_find(
        query,
        StudyRootQueryRetrieveInformationModelFind,
    )

    for status, identifier in responses:
        if status is None:
            print("Connection timed out or invalid response")
            continue

        print(f"Status: 0x{status.Status:04X}")

        if identifier:
            print("---- Result ----")
            print(f"PatientName: {getattr(identifier, 'PatientName', '')}")
            print(f"PatientID: {getattr(identifier, 'PatientID', '')}")
            print(f"StudyDate: {getattr(identifier, 'StudyDate', '')}")
            print(f"Modality: {getattr(identifier, 'Modality', '')}")
            print(f"StudyDescription: {getattr(identifier, 'StudyDescription', '')}")
            print(f"StudyInstanceUID: {getattr(identifier, 'StudyInstanceUID', '')}")

    assoc.release()


if __name__ == "__main__":
    main()
