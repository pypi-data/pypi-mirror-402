import logging
from datetime import datetime
from enum import Enum, unique
import pydicom

from qmenta.anon.time_utils import TimeAnonymise


def PatchedMultiString(val, valtype=str):
    """
    Split a bytestring by delimiters if there are any

    Parameters
    ----------
    val: str
        DICOM bytestring to split up
    valtype:
        default str, but can be e.g. UID to overwrite to a specific type
    """
    # Remove trailing blank used to pad to even length
    # 2005.05.25: also check for trailing 0, error made in PET files we are
    # converting

    if val and (val.endswith(" ") or val.endswith("\x00")):
        val = val[:-1]
    splitup = val.split("\\")
    if len(splitup) == 1:
        try:
            val = splitup[0]
            return valtype(val) if val else val
        except ValueError:
            if valtype in [str, pydicom.valuerep.PersonName, pydicom.uid.UID]:
                return valtype("XXXX") if val else val
            elif valtype is pydicom.valuerep.DSfloat:
                return valtype(0.0) if val else val
    else:
        return pydicom.multival.MultiValue(valtype, splitup)


# overwriting an existing method in order to prevent exceptions when
# tags annonymized with data of other type (e.g. float tag gets string)
pydicom.valuerep.MultiString = PatchedMultiString


@unique
class DicomAttribute(Enum):
    @property
    def tag(self):
        """
        The DICOM tag, represented as (group number, element number)
        """
        return self.value

    PatientName = (0x0010, 0x0010)
    PatientID = (0x0010, 0x0020)
    IssuerOfPatientID = (0x0010, 0x0021)
    PatientBirthTime = (0x0010, 0x0032)
    PatientSex = (0x0010, 0x0040)
    PatientBirthName = (0x0010, 0x1005)
    CountryOfResidence = (0x0010, 0x2150)
    RegionOfResidence = (0x0010, 0x2152)
    PatientTelephoneNumbers = (0x0010, 0x2154)
    CurrentPatientLocation = (0x0038, 0x0300)
    PatientInstitutionResidence = (0x0038, 0x0400)
    StudyDate = (0x0008, 0x0020)
    SeriesDate = (0x0008, 0x0021)
    AcquisitionDate = (0x0008, 0x0022)
    ContentDate = (0x0008, 0x0023)
    OverlayDate = (0x0008, 0x0024)
    CurveDate = (0x0008, 0x0025)
    AcquisitionDateTime = (0x0008, 0x002A)
    StudyTime = (0x0008, 0x0030)
    SeriesTime = (0x0008, 0x0031)
    AcquisitionTime = (0x0008, 0x0032)
    ContentTime = (0x0008, 0x0033)
    OverlayTime = (0x0008, 0x0034)
    CurveTime = (0x0008, 0x0035)
    InstitutionAddress = (0x0008, 0x0081)
    ReferringPhysicianName = (0x0008, 0x0090)
    ReferringPhysicianAddress = (0x0008, 0x0092)
    ReferringPhysicianTelephoneNumber = (0x0008, 0x0094)
    InstitutionalDepartmentName = (0x0008, 0x1040)
    OperatorsName = (0x0008, 0x1070)
    StudyID = (0x0020, 0x0010)
    DateTime = (0x0040, 0xA120)
    Date = (0x0040, 0xA121)
    Time = (0x0040, 0xA122)
    PersonName = (0x0040, 0xA123)
    AccessionNumber = (0x0008, 0x0050)
    InstitutionName = (0x0008, 0x0080)
    ReferringPhysicianIDSequence = (0x0008, 0x0096)
    PhysiciansOfRecord = (0x0008, 0x1048)
    PhysiciansOfRecordIDSequence = (0x0008, 0x1049)
    PerformingPhysicianName = (0x0008, 0x1050)
    PerformingPhysicianIDSequence = (0x0008, 0x1052)
    NameOfPhysicianReadingStudy = (0x0008, 0x1060)
    PhysicianReadingStudyIDSequence = (0x0008, 0x1062)
    PatientBirthDate = (0x0010, 0x0030)
    PatientInsurancePlanCodeSequence = (0x0010, 0x0050)
    PatientPrimaryLanguageCodeSeq = (0x0010, 0x0101)
    OtherPatientIDs = (0x0010, 0x1000)
    OtherPatientNames = (0x0010, 0x1001)
    OtherPatientIDsSequence = (0x0010, 0x1002)
    PatientAge = (0x0010, 0x1010)
    PatientAddress = (0x0010, 0x1040)
    PatientMotherBirthName = (0x0010, 0x1060)

    # File meta information used in _updateMetaInfo():
    ImplementationClassUID = (0x0002, 0x0012)
    MediaStorageSOPClassUID = (0x0002, 0x0002)
    MediaStorageSOPInstanceUID = (0x0002, 0x0003)


# Basic Application Level Confidentiality Profile Attributes
# ftp://medical.nema.org/medical/dicom/final/sup55_ft.pdf


@unique
class ActionCode(Enum):
    """
    See https://qmenta.atlassian.net/wiki/spaces/QTG/pages/1166409832
    /DICOM+de-identification for the list and references
    """

    X = "Remove tag"
    Z = (
        "Replace with a zero length value, or a non-zero length value that "
        "may be a dummy value and consistent with the Value Representations"
    )
    D = (
        "Replace with a non-zero length value that may be a dummy value and "
        "consistent with the Value Representations"
    )


DICOM_ANON_MIN_SUPP_55 = {
    DicomAttribute.PatientName: ActionCode.Z,
    DicomAttribute.PatientID: ActionCode.Z,
    DicomAttribute.IssuerOfPatientID: ActionCode.X,
    DicomAttribute.PatientBirthTime: ActionCode.X,
    DicomAttribute.PatientSex: ActionCode.Z,
    DicomAttribute.PatientBirthName: ActionCode.X,
    DicomAttribute.CountryOfResidence: ActionCode.X,
    DicomAttribute.RegionOfResidence: ActionCode.X,
    DicomAttribute.PatientTelephoneNumbers: ActionCode.X,
    DicomAttribute.CurrentPatientLocation: ActionCode.X,
    DicomAttribute.PatientInstitutionResidence: ActionCode.X,
    DicomAttribute.StudyDate: ActionCode.Z,
    DicomAttribute.SeriesDate: ActionCode.X,
    DicomAttribute.AcquisitionDate: ActionCode.X,
    DicomAttribute.ContentDate: ActionCode.Z,
    DicomAttribute.OverlayDate: ActionCode.X,
    DicomAttribute.CurveDate: ActionCode.X,
    DicomAttribute.AcquisitionDateTime: ActionCode.X,
    DicomAttribute.StudyTime: ActionCode.Z,
    DicomAttribute.SeriesTime: ActionCode.X,
    DicomAttribute.AcquisitionTime: ActionCode.X,
    DicomAttribute.ContentTime: ActionCode.Z,
    DicomAttribute.OverlayTime: ActionCode.X,
    DicomAttribute.CurveTime: ActionCode.X,
    DicomAttribute.InstitutionAddress: ActionCode.X,
    DicomAttribute.ReferringPhysicianName: ActionCode.Z,
    DicomAttribute.ReferringPhysicianAddress: ActionCode.X,
    DicomAttribute.ReferringPhysicianTelephoneNumber: ActionCode.X,
    DicomAttribute.InstitutionalDepartmentName: ActionCode.X,
    DicomAttribute.OperatorsName: ActionCode.X,
    DicomAttribute.StudyID: ActionCode.Z,
    DicomAttribute.DateTime: ActionCode.X,
    DicomAttribute.Date: ActionCode.X,
    DicomAttribute.Time: ActionCode.X,
    DicomAttribute.PersonName: ActionCode.D,
    DicomAttribute.AccessionNumber: ActionCode.Z,
    DicomAttribute.InstitutionName: ActionCode.X,
    DicomAttribute.ReferringPhysicianIDSequence: ActionCode.X,
    DicomAttribute.PhysiciansOfRecord: ActionCode.X,
    DicomAttribute.PhysiciansOfRecordIDSequence: ActionCode.X,
    DicomAttribute.PerformingPhysicianName: ActionCode.X,
    DicomAttribute.PerformingPhysicianIDSequence: ActionCode.X,
    DicomAttribute.NameOfPhysicianReadingStudy: ActionCode.X,
    DicomAttribute.PhysicianReadingStudyIDSequence: ActionCode.X,
    DicomAttribute.PatientBirthDate: ActionCode.Z,
    DicomAttribute.PatientInsurancePlanCodeSequence: ActionCode.X,
    DicomAttribute.PatientPrimaryLanguageCodeSeq: ActionCode.X,
    DicomAttribute.OtherPatientIDs: ActionCode.X,
    DicomAttribute.OtherPatientNames: ActionCode.X,
    DicomAttribute.OtherPatientIDsSequence: ActionCode.X,
    DicomAttribute.PatientAge: ActionCode.X,
    DicomAttribute.PatientAddress: ActionCode.X,
    DicomAttribute.PatientMotherBirthName: ActionCode.X,
}


def redact_dicom_attr(header, tag):
    value = header[tag].value
    if isinstance(value, str):
        header[tag].value = "XXXX"
    elif isinstance(value, pydicom.valuerep.PersonName):
        header[tag].value = "XXXX"
    elif isinstance(value, pydicom.valuerep.DSfloat):
        header[tag].value = 0.0
    elif isinstance(value, pydicom.uid.UID):
        header[tag].value = "XXXX"
    elif isinstance(value, pydicom.multival.MultiValue):
        header[tag].value = []
    else:
        raise RuntimeError(
            "Unknown type {} for tag {}".format(type(value), tag)
        )


def check_tag(header, tag):
    """
    Parameters
    ----------
    header:
        The DICOM header to check

    tag:
        DICOM tag ID to check
    """
    try:
        _ = header[tag].value
        return True
    except (NotImplementedError, Exception):
        return False


def check_meta_tag(header, tag):
    """
    Parameters
    ----------
    header:
        The DICOM header to check

    tag:
        DICOM meta tag ID to check
    """
    try:
        _ = header.file_meta[tag].value
        return True
    except (NotImplementedError, Exception):
        return False


def anonymise_header_attribute(header, attribute, action):
    """
    Redact or delete the attribute from the header as specified
    by the action.

    Parameters
    ----------
    header:
        The DICOM header to update

    attribute: DicomAttribute
        The DICOM attribute to update

    action: ActionCode
        The type of anonymisation to apply

    Raises
    ------
    NotImplementedError
        If the action is not in [Z, D, X]
    """
    if action not in [ActionCode.Z, ActionCode.D, ActionCode.X]:
        raise NotImplementedError("Only actions Z, D and X are supported.")

    if check_tag(header, attribute.tag):
        if action in [ActionCode.Z, ActionCode.D]:
            redact_dicom_attr(header, attribute.tag)
        elif action is ActionCode.X:
            try:
                del header[attribute.tag]
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(str(e))
                delattr(header, attribute.name)


def anonymise_dicom_dataset(dcm, actions=None):
    """
    Anonyise the given DICOM header using the specified profile.

    Parameters
    ----------
    dcm:
        The DICOM header to anonymise

    actions:
        The confidentiality profile to use when redacting the header.
        Default: DICOM_ANON_MIN_SUPP_55
    """
    actions = actions or DICOM_ANON_MIN_SUPP_55
    logger = logging.getLogger(__name__)
    node_queue = [dcm]
    while node_queue:
        header = node_queue.pop(0)

        # anonymisation
        for attribute in actions:
            logger.debug(
                f"Anonymizing {attribute} with action {actions[attribute]}."
            )
            anonymise_header_attribute(header, attribute, actions[attribute])

        # tail recursion
        tags_to_delete = []
        for tag in header.keys():
            if check_tag(header, tag):
                elem = header[tag]
                if isinstance(elem.value, pydicom.sequence.Sequence):
                    node_queue.extend(elem.value)
            else:
                template = (
                    "deleting key {!r} with invalid data from header "
                    "when anonymising dicom file"
                )
                logger.warning(template.format(tag))
                tags_to_delete.append(tag)

        for tag in tags_to_delete:
            try:
                del header[tag]
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(str(e))
                logger.error("Using delattr to delete the tag")
                delattr(header, tag)


def anonymise(filename, actions=None):
    header = pydicom.read_file(filename)

    actions = actions or DICOM_ANON_MIN_SUPP_55
    anonymise_dicom_dataset(header, actions)
    _updateMetaInfo(header)

    header.save_as(filename)
    return {"OK": True, "error_tags": []}


def _updateMetaInfo(header):
    """
    Set DICOM meta information if needed.
    """
    if not check_meta_tag(header, DicomAttribute.ImplementationClassUID.tag):
        header.file_meta.ImplementationClassUID = "1.2.3.4"
    if not check_meta_tag(header, DicomAttribute.MediaStorageSOPClassUID.tag):
        header.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    if not check_meta_tag(header,
                          DicomAttribute.MediaStorageSOPInstanceUID.tag):
        header.file_meta.MediaStorageSOPInstanceUID = "1.2.3"


def check_anonymised_file(input_file, options={}):
    _options = {"return_lines": False, "not_found_as_error": False}

    _options.update(options)

    lines = []
    not_anonymised_attr = []

    try:
        hd = pydicom.read_file(input_file)
        n_errors = 0
        for attribute in DICOM_ANON_MIN_SUPP_55:
            if check_tag(hd, attribute.tag):
                val = hd[attribute.tag].value

                if _options["return_lines"]:
                    lines.append((attribute.name, str(val)))

                try:
                    if not check_anonym_dicom_attr(hd, attribute.tag):
                        not_anonymised_attr.append(attribute.name)
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(str(e))
                    pass

            else:
                if _options["return_lines"]:
                    lines.append((attribute.name, "!!!"))
                if _options["not_found_as_error"]:
                    n_errors += 1
    except Exception as e:
        return {"OK": False, "error": str(e)}

    ret = {
        "OK": True,
        "n_errors": n_errors,
        "not_anonymised_attr": not_anonymised_attr
    }

    if _options["return_lines"]:
        ret["lines"] = lines

    return ret


def check_anonym_dicom_attr(header, tag):
    value = header[tag].value
    if isinstance(value, str):
        return str(value) == "XXXX"
    elif isinstance(value, pydicom.valuerep.PersonName):
        return value == "XXXX"
    elif isinstance(value, pydicom.valuerep.DSfloat):
        return value == 0.0
    elif isinstance(value, pydicom.uid.UID):
        return value == "XXXX"

    return True


class RelativeTimeAnonymiser:
    """
    Anonymise multiple DICOM files, while keeping the relative time/date
    differences for (AcquisitionDate, AcquisitionTime) and
    (ContentDate, ContentTime) tuples intact between all the files that
    are anonymised by the same instance of RelativeTimeAnonymiser.

    The confidentiality profile is not configurable. It will always use
    DICOM_ANON_MIN_SUPP_55, with the exception that for the tags
    [AcquisitionDate, AcquisitionTime, ContentDate, ContentTime], the original
    action as specified in DICOM_ANON_MIN_SUPP_55 will only be applied if
    anonymisation that keeps the original relative times preserved fails.
    """

    def __init__(self):
        self._time_anonymise = TimeAnonymise()
        self._original_actions = DICOM_ANON_MIN_SUPP_55

        # Note: We currently do not support a single AquisitionDateTime or
        #   ContentDateTime tag. Two tags must be used to store date and time.
        self._datetime_attributes = [
            (DicomAttribute.AcquisitionDate, DicomAttribute.AcquisitionTime),
            (DicomAttribute.ContentDate, DicomAttribute.ContentTime),
        ]

        # The confidentiality profile that is used as a fallback when no
        # pair of date, time can be found. In the case where only one of
        # them exists, it will be anonymised as specified in the original
        # confidentiality profile.
        self._restricted_actions = dict(self._original_actions)
        attributes_to_remove = [
            # Flatten the _datetime_attributes list.
            atr
            for atr_pair in self._datetime_attributes
            for atr in atr_pair
        ]
        for atr in attributes_to_remove:
            self._restricted_actions.pop(atr, None)

    @staticmethod
    def _time_to_TM(time):
        """
        Convert the time component of a Python datetime object into
        DICOM time (TM) value representation.
        """
        return "{:02}{:02}{:02}.{:06}".format(
            time.hour, time.minute, time.second, time.microsecond
        )

    @staticmethod
    def _date_to_DA(date):
        """
        Convert the date component of a Python datetime object into
        DCIOM date (DA) value representation.
        """
        return "{:04}{:02}{:02}".format(date.year, date.month, date.day)

    def anonymise_datetime(self, header):
        """
        Anonymise the datetime values for AcquisitionDate, AcquisitionTime,
        ContentDate and ContentTime tags, while keeping the relative time
        differences of different dates/times for different calls of this
        function intact.

        Parameters
        ----------
        header:
            The DICOM header containing the datetime tags to anonymise

        Raises
        ------
        time_utils.TooLargeDeltaError
            when trying to anonymise multiple DICOM headers of which the
            datetimes to anonymise span more than 24h.
        """
        # Date and time must be stored in two separate tags
        for date_atr, time_atr in self._datetime_attributes:
            date_ok = check_tag(header, date_atr.tag)
            time_ok = check_tag(header, time_atr.tag)
            if not (date_ok and time_ok):
                # A full datetime cannot be reconstructed. If one of the tags
                #   exists, anonymise it as specified in the original
                #   confidentiality profile to ensure proper anonymisation.
                if time_ok:
                    action = self._original_actions[time_atr]
                    anonymise_header_attribute(header, time_atr, action)
                elif date_ok:
                    action = self._original_actions[date_atr]
                    anonymise_header_attribute(header, date_atr, action)
                continue  # Go to the next (date_atr, time_atr) pair

            date_element = header[date_atr.tag]
            time_element = header[time_atr.tag]

            assert date_element.VR == "DA"
            assert time_element.VR == "TM"

            # If date_element not a date string, then set to null to be
            # anonymized
            try:
                in_date = pydicom.valuerep.DA(date_element.value)
            except ValueError:
                in_date = None

            # If time_element not a date string, then set to null to be
            # anonymized
            try:
                in_time = pydicom.valuerep.TM(time_element.value)
            except ValueError:
                in_time = None

            if not (in_date and in_time):
                # One of the input values was an empty string
                anonymise_header_attribute(
                    header, time_atr, self._original_actions[time_atr])
                anonymise_header_attribute(
                    header, date_atr, self._original_actions[date_atr])
                continue  # Go to the next (date_atr, time_atr) pair

            in_datetime = datetime.combine(in_date, in_time)

            # Compute the target datetime
            out_datetime = self._time_anonymise.anonymise_datetime(in_datetime)

            header[date_atr.tag].value = self._date_to_DA(out_datetime)
            header[time_atr.tag].value = self._time_to_TM(out_datetime)

    def anonymise(self, filename, actions=None):
        """
        Anonymise the DICOM dataset using the
        restricted_actions profile, and replace
        the date/time elements with an anonymised date/time that keeps
        the relative date and time of different DICOM datasets intact.

        Parameters
        ----------
        filename: str
            The file to anonymise
        actions: dict, optional

        Raises
        ------
        time_utils.TooLargeDeltaError
            when trying to anonymise multiple DICOM headers of which the
            datetimes to anonymise span more than 24h.
        """
        header = pydicom.read_file(filename)
        self.anonymise_datetime(header)

        actions = actions or DICOM_ANON_MIN_SUPP_55
        restricted_actions = actions.copy()
        restricted_actions.pop(DicomAttribute.AcquisitionDate)
        restricted_actions.pop(DicomAttribute.ContentDate)
        restricted_actions.pop(DicomAttribute.AcquisitionTime)
        restricted_actions.pop(DicomAttribute.ContentTime)

        anonymise_dicom_dataset(header, restricted_actions)
        _updateMetaInfo(header)

        header.save_as(filename)
