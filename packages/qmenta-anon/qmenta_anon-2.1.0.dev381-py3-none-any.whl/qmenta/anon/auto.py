import pydicom
from enum import Enum
from pydicom.errors import InvalidDicomError

from qmenta.anon.dicom import anonymise as anonymise_dicom
from qmenta.anon.nifti import anonymise as anonymise_nifti


class Format(Enum):
    """
    Enum with the following options:
    UNKNOWN, DICOM, NIFTI
    """
    UNKNOWN = 0
    DICOM = 1
    NIFTI = 2


def recognise_file_format(file):
    """
    Detects whether a file is DICOM or NifTI.

    Parameters
    ----------
    file : str
        The path of the file.

    Returns
    -------
    str
        Either 'dicom' or 'nifti'.
    """

    try:
        if pydicom.read_file(file):
            return Format.DICOM
        else:
            raise InvalidDicomError
    except InvalidDicomError:
        if file.endswith(".nii") or file.endswith(".nii.gz"):
            return Format.NIFTI
        else:
            return Format.UNKNOWN


def anonymise(file):
    """
    Anonymise DICOM and NifTI files.
    This function will replace the given file with the anonymised version.

    Parameters
    ----------
    file : str
        The path of the file

    Returns
    -------
    dict
        The boolean return status in the value for the key "OK" and,
        optionally the list of errors on the value for the key "error_tags".
    """
    format = recognise_file_format(file)
    if format == Format.DICOM:
        return anonymise_dicom(file)
    elif format == Format.NIFTI:
        return anonymise_nifti(file)
    elif format == Format.UNKNOWN:
        return {
            "error": "Some files are not accepted or are corrupted.",
            "OK": False
        }
    else:
        raise RuntimeError(
            'This format is not properly handled by the anonymise function.'
        )
