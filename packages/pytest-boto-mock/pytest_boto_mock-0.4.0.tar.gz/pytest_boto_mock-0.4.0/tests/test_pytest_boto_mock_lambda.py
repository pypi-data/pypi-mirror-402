import json

import boto3
import botocore.exceptions
import pytest


# Lambda
def test_lambda_call_native(boto_mocker):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
    }))

    with pytest.raises(botocore.exceptions.ParamValidationError):
        boto3.client('lambda').invoke()


@pytest.mark.parametrize('expected', [
    None,
    'Test',
    {},
    {'StatusCode': 200, 'Payload': json.dumps({}).encode()},
])
def test_lambda_value(boto_mocker, expected):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {'Invoke': expected}
    }))

    actual = boto3.client('lambda').invoke(FunctionName='FunctionName')
    assert actual == expected


@pytest.mark.parametrize('expected', [
    None,
    'Test',
    {},
    {'StatusCode': 200, 'Payload': json.dumps({}).encode()},
])
def test_lambda_callable(boto_mocker, expected):
    def _callable(self, operation_name, kwarg):
        return expected

    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {'Invoke': _callable}
    }))

    actual = boto3.client('lambda').invoke(FunctionName='FunctionName')
    assert actual == expected


@pytest.mark.parametrize('expected', [
    Exception(),
    botocore.exceptions.ClientError({}, 'Invoke'),
])
def test_lambda_exception(boto_mocker, expected):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {'Invoke': expected}
    }))

    with pytest.raises(Exception) as ex:
        boto3.client('lambda').invoke(FunctionName='FunctionName')
        assert ex == expected


@pytest.mark.parametrize('expected', [
    # lambda_handler return value format.
    {'statusCode': 200, 'body': json.dumps('Hello from Lambda!')},
    '',
])
def test_lambda_invoke_value(boto_mocker, expected):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {
            'Invoke': boto_mocker.build_lambda_invoke_handler({
                'FunctionName': {
                    'StatusCode': 200,
                    'Payload': expected,
                }
            })
        }
    }))

    response = boto3.client('lambda').invoke(FunctionName='FunctionName')
    assert response.get('StatusCode') == 200
    actual = response.get('Payload').read().decode()
    if actual:
        actual = json.loads(actual)
    assert actual == expected


@pytest.mark.parametrize('expected', [
    # lambda_handler return value format.
    {'statusCode': 200, 'body': json.dumps('Hello from Lambda!')},
    '',
])
def test_lambda_invoke_callable(boto_mocker, expected):
    def _callable(self, operation_name, kwarg):
        return {
            'StatusCode': 200,
            'Payload': expected,
        }

    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {
            'Invoke': boto_mocker.build_lambda_invoke_handler({
                'FunctionName': _callable,
            })
        }
    }))

    response = boto3.client('lambda').invoke(FunctionName='FunctionName')
    assert response.get('StatusCode') == 200
    actual = response.get('Payload').read().decode()
    if actual:
        actual = json.loads(actual)
    assert expected == actual


@pytest.mark.parametrize('expected', [
    # lambda_handler return value format.
    {'statusCode': 200, 'body': json.dumps('Hello from Lambda!')},
    '',
])
def test_lambda_invoke_payload_callable(boto_mocker, expected):
    def _callable(self, operation_name, kwarg):
        return expected

    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {
            'Invoke': boto_mocker.build_lambda_invoke_handler({
                'FunctionName': {
                    'StatusCode': 200,
                    'Payload': _callable,
                }
            })
        }
    }))

    response = boto3.client('lambda').invoke(FunctionName='FunctionName')
    assert response.get('StatusCode') == 200
    actual = response.get('Payload').read().decode()
    if actual:
        actual = json.loads(actual)
    assert expected == actual


@pytest.mark.parametrize('expected', [
    botocore.exceptions.ClientError({}, 'Invoke'),
])
def test_lambda_invoke_payload_exception(boto_mocker, expected):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {
            'Invoke': boto_mocker.build_lambda_invoke_handler({
                'FunctionName': {
                    'StatusCode': 200,
                    'Payload': expected,
                }
            })
        }
    }))

    with pytest.raises(Exception) as ex:
        boto3.client('lambda').invoke(FunctionName='FunctionName')
        assert ex == expected


@pytest.mark.parametrize('expected', [
    Exception('error in lambda function'),
])
def test_lambda_invoke_function_error(boto_mocker, expected):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {
            'Invoke': boto_mocker.build_lambda_invoke_handler({
                'FunctionName': {
                    'StatusCode': 200,
                    'FunctionError': 'Unhandled',
                    'Payload': expected,
                }
            })
        }
    }))

    response = boto3.client('lambda').invoke(FunctionName='FunctionName')
    assert response.get('StatusCode') == 200
    payload = json.loads(response.get('Payload').read())
    actual = payload.get('errorMessage')
    assert actual == str(expected)


def test_lambda_invoke_event(boto_mocker):
    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'lambda': {
            'Invoke': boto_mocker.build_lambda_invoke_handler({
                'FunctionName': {
                    'ResponseMetadata': {'HTTPStatusCode': 202},
                    'StatusCode': 202,
                    'Payload': '',
                }
            })
        }
    }))

    response = boto3.client('lambda').invoke(FunctionName='FunctionName', InvocationType='Event')
    assert response.get('StatusCode') == 202
    response.get('Payload').read()
