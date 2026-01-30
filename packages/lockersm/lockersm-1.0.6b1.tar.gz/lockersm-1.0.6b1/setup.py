import json
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


with open('locker/__about__.json', 'r') as fd:
    _about_data = json.load(fd)
    __version__ = _about_data.get("version")
    binary_version = _about_data.get("binary_version")


def _requirements():
    # download_binary()
    with open('requirements.txt', 'r') as f:
        return [name.strip() for name in f.readlines()]


def _requirements_test():
    # download_binary()
    with open('requirements-test.txt', 'r') as f:
        return [name.strip() for name in f.readlines()]


def _classifiers():
    classifiers = [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
    if "b1" in __version__ or "b2" in __version__:
        classifiers += ["Development Status :: 3 - Alpha"]
    else:
        classifiers += ["Development Status :: 5 - Production/Stable"]
    return classifiers


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


with open('README.md', 'r') as f:
    long_description = f.read()


def main():
    setup(
        name="lockersm",
        version=__version__,
        author="CyStack",
        author_email="contact@locker.io",
        url="https://locker.io",
        download_url="",
        description="Locker Secret Python SDK",
        long_description=long_description,
        long_description_content_type="text/markdown",
        keywords=[
            "django",
            "vault management",
            "security"
        ],
        # license = BSD-3-Clause  # Example license
        include_package_data=True,
        packages=find_packages(
            exclude=[
                "docs",
                "examples",
                "tests",
                "tests.*",
                "venv",
                "projectenv",
                "*.sqlite3"
            ]
        ),
        python_requires=">=3.8",
        install_requires=_requirements(),
        tests_require=_requirements_test(),
        cmdclass={
            'test': PyTest,
        },
        classifiers=_classifiers(),
    )


if __name__ == "__main__":
    main()
