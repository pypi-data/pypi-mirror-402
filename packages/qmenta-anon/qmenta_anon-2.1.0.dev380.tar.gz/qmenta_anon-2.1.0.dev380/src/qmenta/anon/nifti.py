import os
import shutil
from tempfile import TemporaryDirectory

import nibabel


def anonymise(filename):
    try:
        nifti_file = nibabel.load(filename)

        hdr = nifti_file.header
        if "db_name" in hdr:
            hdr["db_name"] = "XXXX"

        with TemporaryDirectory() as tmp_dir:
            new_image_path = os.path.join(tmp_dir, os.path.basename(filename))
            new_image = nibabel.Nifti1Image(
                nifti_file.get_fdata(), nifti_file.affine, hdr
            )
            nibabel.save(new_image, new_image_path)
            shutil.copyfile(new_image_path, filename)

        return {"OK": True}
    except Exception as e:
        return {
            "OK": False,
            "error": "Some NIFTI files are not accepted or are corrupted. "
                     f"\n{str(e)}"
        }


def check_anonymised_file(filename):
    try:
        nifti_file = nibabel.load(filename)
        hdr = nifti_file.header
        if "db_name" in hdr and (
            str(hdr["db_name"].astype(str)) not in ["XXXX", ""]
        ):
            return {"OK": False}
        else:
            return {"OK": True}
    except Exception as e:
        return {
            "OK": False,
            "error": "Some NIFTI files are not accepted or are corrupted. "
                     f"\n{str(e)}"
        }
