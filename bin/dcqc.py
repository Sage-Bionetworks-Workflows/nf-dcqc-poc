#!/usr/bin/env python3

import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile

import synapseclient


def main():
    mode = sys.argv[1]

    if mode == "prepare_targets":
        input_csv = sys.argv[2]
        output_dir = sys.argv[3]
        os.makedirs(output_dir, exist_ok=True)
        # TODO: Ensure no duplicate URIs
        targets = parse_csv(input_csv)
        for target in targets:
            target_dict = target.to_dict(expanded=False)
            target_path = os.path.join(output_dir, f"{target.name}.json")
            write_json(target_dict, target_path)

    elif mode == "stage_target":
        target_json = sys.argv[2]
        staging_dir = sys.argv[3]
        os.makedirs(staging_dir, exist_ok=True)
        target = parse_target_json(target_json)
        target.stage(staging_dir)

    elif mode == "prepare_tests":
        target_json = sys.argv[2]
        output_dir = sys.argv[3]
        os.makedirs(output_dir, exist_ok=True)
        target = parse_target_json(target_json)
        suite = prepare_suite_from_target(target)
        for test in suite.tests:
            test_dict = test.to_dict()
            test_path = os.path.join(output_dir, f"{target.name}.{test.name}.json")
            write_json(test_dict, test_path)

    elif mode == "prepare_cmd":
        test_json = sys.argv[2]
        command_path = sys.argv[3]
        test = parse_test_json(test_json)
        command_dict = test.prepare_cmd()
        write_json(command_dict, command_path)

    elif mode == "run_test":
        test_json = sys.argv[2]
        test_path = sys.argv[3]
        test = parse_test_json(test_json)
        test.run()
        test_dict = test.to_dict()
        write_json(test_dict, test_path)

    elif mode == "interpret_cmd":
        test_json = sys.argv[2]
        test_path = sys.argv[3]
        test = parse_test_json(test_json)
        test.interpret_cmd()
        test_dict = test.to_dict()
        write_json(test_dict, test_path)

    elif mode == "target_report":
        report_path = sys.argv[2]
        input_tests = sys.argv[3:]
        tests = [parse_test_json(t) for t in input_tests]
        suite = prepare_suite_from_tests(tests)
        report = JsonQcReport([suite], report_path)
        report.generate()

    elif mode == "compile_reports":
        compiled_report_path = sys.argv[2]
        input_reports = sys.argv[3:]
        reports = []
        for report_path in input_reports:
            report = read_json(report_path)
            reports.extend(report)
        write_json(reports, compiled_report_path)


def parse_csv(path):
    targets = []
    with open(path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            uri = row.pop("uri")
            target = FileQcTarget(uri, row)
            targets.append(target)
    return targets


def parse_target_dict(target_dict):
    target_class_name = target_dict.pop("type")
    target_class = getattr(sys.modules[__name__], target_class_name)
    target = target_class(target_dict["uri"], target_dict["metadata"])
    return target


def parse_target_json(target_json):
    target_dict = read_json(target_json)
    target = parse_target_dict(target_dict)
    return target


def parse_test_dict(test_dict):
    test_class_name = test_dict.pop("type")
    test_class = getattr(sys.modules[__name__], test_class_name)
    # Implement function that can selectively pick what's needed
    target = parse_target_dict(test_dict["target"])
    test = test_class(target, test_dict["config"])
    if test_dict["status"] is not None:
        test.status = test_dict["status"]
    return test


def parse_test_json(test_path):
    test_dict = read_json(test_path)
    test = parse_test_dict(test_dict)
    return test


def prepare_suite_from_target(target):
    file_type = target.get_metadata("file_type")
    assert file_type != "N/A"
    qc_suite_class = QC_SUITE_MAP.get(file_type, FileQcSuite)
    qc_suite = qc_suite_class(target)
    return qc_suite


def prepare_suite_from_tests(tests):
    target = tests[0].target
    # Ensure that all tests share the same target
    for test in tests:
        assert test.target.name == target.name
    qc_suite = prepare_suite_from_target(target)
    qc_suite.tests = tests
    return qc_suite


def prepare_suites_from_targets(targets):
    suites = []
    for target in targets:
        qc_suite = prepare_suite_from_target(target)
        suites.append(qc_suite)
    return suites


def read_json(path):
    with open(path, "r") as fp:
        return json.load(fp)


def write_json(obj, path):
    with open(path, "w") as fp:
        json.dump(obj, fp, indent=2)
        fp.write("\n")


class BaseFile(object):
    def __init__(self, uri):
        assert uri.startswith(self.prefix)
        self.uri = uri

    def __str__(self):
        return str(self.to_dict())

    @property
    def type(self):
        return self.__class__.__name__

    def save(self, path):
        file_dict = self.to_dict()
        write_json(file_dict, path)

    def to_dict(self):
        file_dict = {
            "uri": self.uri,
            "type": self.type,
            "version": self.get_version(),
            "filename": self.get_filename(),
        }
        return file_dict


class SynapseFile(BaseFile):
    prefix = "syn://"

    def __init__(self, uri):
        super().__init__(uri)
        self.synid = uri.replace("syn://", "")
        self.name = self.synid
        self.syn = synapseclient.Synapse(silent=True)
        self.syn.login()
        self.entity = self.syn.get(self.synid, downloadFile=False)

    def get_version(self):
        version = self.entity.properties.get("versionNumber", "N/A")
        return version

    def get_filename(self):
        filename = self.entity.properties.get("name", "N/A")
        return filename

    def get_staging_location(self, staging_dir):
        return os.path.join(staging_dir, self.get_filename())

    def stage(self, staging_dir="./"):
        staging_location = self.get_staging_location(staging_dir)
        if os.path.exists(staging_location):
            return staging_location
        with tempfile.TemporaryDirectory() as tmpdirname:
            downloaded = self.syn.get(self.synid, downloadLocation=tmpdirname)
            shutil.move(downloaded.path, staging_location)
        return staging_location

    def to_dict(self):
        file_dict = super().to_dict()
        file_dict["synapse_id"] = self.synid
        return file_dict


class BaseQcTarget(object):
    def __init__(self, uri, metadata):
        self.uri = uri
        self.files = [SynapseFile(uri)]
        self.metadata = metadata

    def __str__(self):
        return str(self.to_dict())

    @property
    def type(self):
        return self.__class__.__name__

    def get_metadata(self, key=None):
        if key:
            result = self.metadata.get(key, None)
        else:
            result = self.metadata
        return result

    def stage(self, staging_dir):
        for file in self.files:
            file.stage(staging_dir)

    def to_dict(self, expanded=True):
        target_dict = {
            "type": self.type,
            "uri": self.uri,
            "metadata": self.get_metadata(),
        }
        if expanded:
            target_dict["files"] = [f.to_dict() for f in self.files]
        return target_dict


class FileQcTarget(BaseQcTarget):
    def __init__(self, uri, metadata):
        super().__init__(uri, metadata)
        self.file = self.files[0]
        self.name = self.file.name


class BaseQcTest(object):
    is_internal_test = None

    def __init__(self, target, config=None):
        self.target = target
        self.status = None
        self.config = config or {}

    def __str__(self):
        return str(self.to_dict())

    @property
    def type(self):
        return self.name

    def to_dict(self, expanded=True, with_target=True):
        test_dict = {
            "type": self.type,
            "config": self.config,
        }
        if expanded:
            test_dict["tier"] = self.tier
            test_dict["is_internal_test"] = self.is_internal_test
            test_dict["status"] = self.status
        if with_target:
            test_dict["target"] = self.target.to_dict(expanded=False)
        return test_dict


class BaseInternalQcTest(BaseQcTest):
    is_internal_test = True

    def run(self):
        NotImplementedError()


class FileExtensionQcTest(BaseInternalQcTest):
    name = "FileExtensionQcTest"
    tier = 1

    def run(self):
        assert (
            "file_extensions" in self.config
        ), f"Configure {self.name} with `file_extensions`."
        file_extensions = tuple(self.config["file_extensions"])
        filename = self.target.file.get_filename()
        self.status = filename.endswith(file_extensions)
        return self.status


class Md5ChecksumQcTest(BaseInternalQcTest):
    name = "Md5ChecksumQcTest"
    tier = 1

    def __init__(self, target, config=None):
        super().__init__(target, config)
        self.expected_md5 = self.target.get_metadata("md5_checksum")

    def run(self):
        staged_path = self.target.file.stage()
        hash_md5 = hashlib.md5()
        with open(staged_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        actual_md5 = hash_md5.hexdigest()
        self.status = actual_md5 == self.expected_md5
        return self.status


class BaseExternalQcTest(BaseQcTest):
    is_internal_test = False
    outpath = "std_out.txt"
    errpath = "std_err.txt"
    codepath = "exit_code.txt"

    def prepare_cmd(self):
        NotImplementedError()

    def load_log_files(self):
        file_paths = {
            "stdout": self.outpath,
            "stderr": self.errpath,
            "exit_code": self.codepath,
        }
        logs = {}
        for name, path in file_paths.items():
            assert os.path.exists(path)
            with open(path, "r") as fp:
                logs[name] = fp.read()
        return logs

    def interpret_cmd(self):
        NotImplementedError()


class LibTiffInfoQcTest(BaseExternalQcTest):
    name = "LibTiffInfoQcTest"
    tier = 2

    def prepare_cmd(self):
        container = "autamus/libtiff:4.4.0"
        target_path = self.target.file.get_filename()
        command = f'tiffinfo "{target_path}"'
        return {"container": container, "command": command}

    def interpret_cmd(self):
        logs = self.load_log_files()
        self.status = logs["exit_code"] == 0
        return self.status


class BioFormatsInfoQcTest(BaseExternalQcTest):
    name = "BioFormatsInfoQcTest"
    tier = 2

    def prepare_cmd(self):
        container = "openmicroscopy/bftools:latest"
        target_path = self.target.file.get_filename()
        command = (
            f'export PATH="/opt/bftools:$PATH"; '
            f'showinf -nopix -novalid -nocore "{target_path}"'
        )
        return {"container": container, "command": command}

    def interpret_cmd(self):
        logs = self.load_log_files()
        self.status = logs["exit_code"] == 0
        return self.status


class OmeXmlSchemaQcTest(BaseExternalQcTest):
    name = "OmeXmlSchemaQcTest"
    tier = 2

    def prepare_cmd(self):
        container = "openmicroscopy/bftools:latest"
        target_path = self.target.file.get_filename()
        command = f'export PATH="/opt/bftools:$PATH"; xmlvalid "{target_path}"'
        return {"container": container, "command": command}

    def interpret_cmd(self):
        logs = self.load_log_files()
        self.status = logs["exit_code"] == 0
        return self.status


class BaseQcSuite(object):
    name = "BaseQcSuite"

    def __init__(self, target, required_tests=None):
        self.target = target
        self.required_tests = required_tests
        self.tests = []
        self.init_tests()

    def __str__(self):
        return str(self.to_dict())

    def init_tests(self):
        return

    def list_tests(self):
        test_names = []
        for test in self.tests:
            test_name = test.get_name()
            test_names.append(test_name)
        return test_names

    def get_status(self):
        summary_status = True
        new_required_tests = []
        for test in self.tests:
            if self.required_tests is None:
                is_required = test.tier <= 2
            else:
                is_required = test.name in self.required_tests
            if is_required and test.status is not None:
                summary_status = summary_status and test.status
                new_required_tests.append(test.name)
        if self.required_tests is None:
            self.required_tests = new_required_tests
        return summary_status

    def to_dict(self):
        summary_status = self.get_status()
        suite_dict = {
            "target": self.target.to_dict(),
            "summary_status": {
                "required_tests": self.required_tests,
                "status": summary_status,
            },
            "tests": [t.to_dict(with_target=False) for t in self.tests],
        }
        return suite_dict


class FileQcSuite(BaseQcSuite):
    file_type = "txt"
    file_extensions = (".txt",)

    def init_tests(self):
        super().init_tests()
        new_tests = [
            FileExtensionQcTest(self.target, {"file_extensions": self.file_extensions}),
            Md5ChecksumQcTest(self.target),
        ]
        self.tests.extend(new_tests)


class TiffQcSuite(FileQcSuite):
    file_type = "tif"
    file_extensions = (".tif", ".tiff")

    def init_tests(self):
        super().init_tests()
        new_tests = [
            LibTiffInfoQcTest(self.target),
        ]
        self.tests.extend(new_tests)


class OmeTiffQcSuite(TiffQcSuite):
    file_type = "ome.tif"
    file_extensions = (".ome.tif", ".ome.tiff")

    def init_tests(self):
        super().init_tests()
        new_tests = [
            OmeXmlSchemaQcTest(self.target),
        ]
        self.tests.extend(new_tests)


class JsonQcReport(object):
    def __init__(self, suites, local_path):
        self.suites = suites
        self.local_path = local_path

    def generate(self):
        report = []
        for suite in self.suites:
            suite_dict = suite.to_dict()
            report.append(suite_dict)
        write_json(report, self.local_path)


QC_SUITE_MAP = {
    "txt": FileQcSuite,
    "tif": TiffQcSuite,
    "ome.tif": OmeTiffQcSuite,
}


if __name__ == "__main__":
    main()
