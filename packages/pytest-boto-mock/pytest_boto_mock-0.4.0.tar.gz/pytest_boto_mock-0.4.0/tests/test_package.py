import boto3
import botocore
import pytest_boto_mock


def test_version():
    pytest_boto_mock.__version__


def test_boto3_version():
    boto3.__version__


def test_botocore_version():
    botocore.__version__
