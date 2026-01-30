#!/usr/bin/env python3

import os
import sys

import yaml
from avocado.core.job import Job
from avocado.core.suite import TestSuite
from avocado.utils import process
from avocado.utils.podman import Podman

CONTAINER_IMAGE_MAPPING = {
    "CentOS_Stream_9": ("redhat_based", "centos:stream9"),
    "Fedora_36": ("redhat_based", "fedora:36"),
    "Fedora_37": ("redhat_based", "fedora:37"),
}


def read_metadata(metadata_path):
    """
    Reads metadata yaml files from the directory.

    It recursively reads metadata from given path and returns a dictionary with the
    supported platforms and the tests that should be run on each platform.

    :param metadata_path: Path to the directory containing metadata files.
    :type metadata_path: str
    :return: Dictionary with supported platforms and tests.
    :rtype: dict

    """

    def read_yaml(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                metadata = yaml.load(f, Loader=yaml.SafeLoader)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except yaml.YAMLError as e:
            print(f"YAML parsing error in {file_path}: {e}")
        for supported_platform in metadata["supported_platforms"]:
            supported_platform = supported_platform.replace(" ", "_")
            if supported_platform not in supported_platforms:
                supported_platforms[supported_platform] = []
            supported_platforms[supported_platform].extend(metadata["tests"])

    supported_platforms = {}
    if os.path.isdir(metadata_path):
        for root, _, files in os.walk(metadata_path):
            for file in files:
                if file.endswith(".yml"):
                    read_yaml(os.path.join(root, file))
    else:
        read_yaml(metadata_path)
    return supported_platforms


METADATA_PATH = sys.argv[1]
COVERAGE = False
if len(sys.argv) > 2:
    COVERAGE = sys.argv[2] == "--coverage"

platforms = read_metadata(METADATA_PATH)

images = []
test_suites = []

for platform, tests in platforms.items():
    try:
        containerfile, image_version = CONTAINER_IMAGE_MAPPING.get(platform)
    except TypeError:
        print(f"platform {platform} is not in known container images")
    if COVERAGE:
        _, result, _ = Podman().execute(
            "build",
            "--no-cache",
            "--from",
            image_version,
            "--env",
            "COVERAGE_RUN=1",
            "-f",
            os.path.join("tests", "containerfiles", containerfile),
            ".",
        )
    else:
        _, result, _ = Podman().execute(
            "build",
            "--no-cache",
            "--from",
            image_version,
            "-f",
            os.path.join("tests", "containerfiles", containerfile),
            ".",
        )
    image = result.splitlines()[-1].decode()
    images.append(image)
    config = {"run.spawner": "podman", "spawner.podman.image": image}

    config["resolver.references"] = tests
    test_suites.append(TestSuite.from_config(config, platform))


with Job(test_suites=test_suites) as j:
    rc = j.run()
    if COVERAGE:
        for image in images:
            _, result, _ = Podman().execute(
                "ps", "-qa", "--noheading", f"--filter=ancestor={image}"
            )
            for container in result.splitlines():
                Podman().execute(
                    "cp", f"{container.decode()}:/tmp/autils_coverage/", "./"
                )
        process.run("coverage combine ./autils_coverage")
        process.run("coverage xml")
        print(process.run("coverage report").stdout_text)

    for image in images:
        Podman().execute("image", "rm", "-f", image)
    sys.exit(rc)
