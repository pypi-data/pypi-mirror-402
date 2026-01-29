import io
import json

import boto3
import botocore.exceptions
import pytest


# S3
def test_s3_call_native(boto_mocker):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
    }))

    with pytest.raises(botocore.exceptions.ParamValidationError):
        boto3.client('s3').copy_object()


@pytest.mark.parametrize('expected', [
    None,
    'Test',
    {},
    {'ResponseMetadata': {'HTTPStatusCode': 200}},
])
def test_s3_value(boto_mocker, expected):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        's3': {'CopyObject': expected}
    }))

    actual = boto3.client('s3').copy_object(Bucket='bucket')
    assert actual == expected


@pytest.mark.parametrize('expected', [
    None,
    'Test',
    {},
    {'ResponseMetadata': {'HTTPStatusCode': 200}},
])
def test_s3_callable(boto_mocker, expected):
    def _callable(self, operation_name, kwarg):
        return expected

    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        's3': {'CopyObject': _callable}
    }))

    actual = boto3.client('s3').copy_object(Bucket='bucket')
    assert actual == expected


@pytest.mark.parametrize('expected', [
    Exception(),
    botocore.exceptions.ClientError({}, 'CopyObject'),
])
def test_s3_exception(boto_mocker, expected):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        's3': {'CopyObject': expected},
    }))

    with pytest.raises(Exception) as ex:
        boto3.client('s3').copy_object(Bucket='bucket')
        assert ex == expected


@pytest.mark.parametrize('count', [
    0,
    2,
])
def test_s3_resource(boto_mocker, count):
    def _list_objects(self, operation_name, kwarg):
        ret = {
            'ResponseMetadata': {'HTTPStatusCode': 200},
            'IsTruncated': False,
            'Name': 'bucket',
            'Prefix': 'test',
            'MaxKeys': 1000,
        }
        if count:
            ret['Contents'] = [{'Key': f"test_{i}.txt"} for i in range(count)]
        return ret

    def _delete_objects(self, operation_name, kwarg):
        ret = {
            'ResponseMetadata': {'HTTPStatusCode': 200},
        }
        if count:
            ret['Deleted'] = [{'Key': f"test_{i}.txt"} for i in range(count)]
        return ret

    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        's3': {
            'ListObjects': _list_objects,
            'DeleteObjects': _delete_objects,
        },
    }))

    boto3.resource('s3').Bucket('bucket').objects.filter(Prefix='test').delete()


@pytest.fixture
def setup_read_json(boto_mocker):
    def _get_object(self, operation_name, kwarg):
        key = kwarg.get('Key')
        if key == 'not_exist.json':
            client = boto3.client('s3')
            raise client.exceptions.NoSuchKey({}, 'GetObject')
        else:
            body = json.dumps({
                'key': key,
            }).encode()
            return {
                'ResponseMetadata': {'HTTPStatusCode': 200},
                'Body': botocore.response.StreamingBody(io.BytesIO(body), len(body)),
            }

    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        's3': {
            'GetObject': _get_object,
        },
    }))


@pytest.mark.parametrize('key, has', [
    ('test.json', True),
    ('not_exist.json', False),
])
def test_s3_client_read_json(setup_read_json, key, has):
    client = boto3.client('s3')
    try:
        response = client.get_object(Bucket='bucket', Key=key)
        body = response.get('Body').read()
        json_data = json.loads(body)
    except client.exceptions.NoSuchKey:
        json_data = None

    if has:
        assert json_data is not None
    else:
        assert json_data is None


@pytest.mark.parametrize('key, has', [
    ('test.json', True),
    ('not_exist.json', False),
])
def test_s3_resource_read_json(setup_read_json, key, has):
    resource = boto3.resource('s3')
    try:
        response = resource.Bucket('bucket').Object(key).get()
        body = response.get('Body').read()
        json_data = json.loads(body)
    except resource.meta.client.exceptions.NoSuchKey:
        json_data = None

    if has:
        assert json_data is not None
    else:
        assert json_data is None
