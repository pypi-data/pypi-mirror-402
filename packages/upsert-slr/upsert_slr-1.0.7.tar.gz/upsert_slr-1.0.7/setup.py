import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "upsert-slr",
    "version": "1.0.7",
    "description": "Manage AWS service-linked roles in a better way.",
    "license": "MIT",
    "url": "https://github.com/tmokmss/upsert-slr.git",
    "long_description_content_type": "text/markdown",
    "author": "tmokmss<tmokmss@users.noreply.github.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/tmokmss/upsert-slr.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "upsert_slr",
        "upsert_slr._jsii"
    ],
    "package_data": {
        "upsert_slr._jsii": [
            "upsert-slr@1.0.7.jsii.tgz"
        ],
        "upsert_slr": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.1.0, <3.0.0",
        "constructs>=10.0.5, <11.0.0",
        "jsii>=1.125.0, <2.0.0",
        "publication>=0.0.3",
        "typeguard==2.13.3"
    ],
    "classifiers": [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
