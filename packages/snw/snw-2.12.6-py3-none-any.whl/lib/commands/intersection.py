import client.launcher as launcher
import os
import requests
import sys


class Intersection:
    def __init__(self, options, auth):
        self.options = options
        self.auth = auth
        self.is_json = self.options.display == "JSON"

    def inter(self, options):
        file_path = self.options.file
        storage_path = self.options.storage_path
        search_side = self.options.search_side

        if not os.path.exists(file_path):
            raise ValueError("'%s' file does not exist" % file_path)
        basename = os.path.basename(file_path)
        file_data = [("file", (basename, open(file_path, "rb")))]
        payload = {
            "path": self.options.storage_path,
            "service": self.options.service,
            "source_language": self.options.source_lang,
            "target_language": self.options.target_lang,
            "search_side": search_side,
            **options,
        }
        r = requests.post(
            os.path.join(self.options.url, "search/intersection"),
            auth=self.auth,
            data=payload,
            files=file_data,
        )
        if r.status_code != 200:
            raise RuntimeError(
                "incorrect result from 'intersection' service: %s" % r.text
            )

        intersection = r.json()["intersection"]
        intersection_length = intersection.count("\n")
        path_inter = file_path + f"-{self.options.subcmd}-inter"
        path_diff = file_path + f"-{self.options.subcmd}-diff"
        with open(path_inter, "w") as fo:
            fo.write(intersection)
        with open(path_diff, "w") as fo:
            fo.write(r.json()["difference"])
        launcher.LOGGER.info(
            f"With {self.options.subcmd} method, {intersection_length} line(s) of {file_path}"
            f" are present in {storage_path}.\nFind:\n   "
            f"- the intersection at {path_inter}\n   - the difference at {path_diff}"
        )

        sys.exit(0)

    def execute_command(self):
        result = None
        if self.options.subcmd == "exact":
            result = self.inter({})
        elif self.options.subcmd == "partial":
            result = self.inter({"partial": True})
        elif self.options.subcmd == "nearmatch":
            result = self.inter({"nearmatch": True})
        elif self.options.subcmd == "nearpartial":
            result = self.inter({"partial": True, "nearmatch": True})
        return result
