import io
import json

import botocore
import botocore.client
import pytest


class BotoMockerFixture:
    # Botocore
    _make_api_call = botocore.client.BaseClient._make_api_call

    def __init__(self, mocker):
        self.mocker = mocker

    def patch(self, new):
        self.mocker.patch('botocore.client.BaseClient._make_api_call', new=new)

    @staticmethod
    def build_make_api_call(service_table):
        def make_api_call(self, operation_name, kwarg):
            service_name = type(self).__name__.lower()

            operation_table = service_table.get(service_name)
            if operation_table is not None and operation_name in operation_table:
                operation = operation_table.get(operation_name)
                if isinstance(operation, Exception):
                    raise operation
                return operation(self, operation_name, kwarg) if callable(operation) else operation
            return BotoMockerFixture._make_api_call(self, operation_name, kwarg)

        return make_api_call

    @staticmethod
    def build_lambda_invoke_handler(response_table):
        def handle_lambda_invoke(self, operation_name, kwarg):
            function_name = kwarg.get('FunctionName')

            response = response_table.get(function_name)
            if response is not None:
                if callable(response):
                    response = response(self, operation_name, kwarg)

                payload = response.get('Payload')
                if isinstance(payload, Exception):
                    if 'FunctionError' in response:
                        payload = {'errorMessage': str(payload), 'errorType': type(payload).__name__}
                    else:
                        raise payload
                elif callable(payload):
                    payload = payload(self, operation_name, kwarg)

                if payload:
                    payload = json.dumps(payload)
                payload = payload.encode()
                return response | {
                    'Payload': botocore.response.StreamingBody(io.BytesIO(payload), len(payload))
                }
            return BotoMockerFixture._make_api_call(self, operation_name, kwarg)

        return handle_lambda_invoke


def _mocker(scope='function'):
    def _function(mocker):
        """
        Return a mocker for Boto. Life cycle is the same as `mocker`.
        """
        return BotoMockerFixture(mocker)

    def _class(class_mocker):
        """
        Return a mocker for Boto. Life cycle is the same as `class_mocker`.
        """
        return BotoMockerFixture(class_mocker)

    def _module(module_mocker):
        """
        Return a mocker for Boto. Life cycle is the same as `module_mocker`.
        """
        return BotoMockerFixture(module_mocker)

    def _package(package_mocker):
        """
        Return a mocker for Boto. Life cycle is the same as `package_mocker`.
        """
        return BotoMockerFixture(package_mocker)

    def _session(session_mocker):
        """
        Return a mocker for Boto. Life cycle is the same as `session_mocker`.
        """
        return BotoMockerFixture(session_mocker)

    return {
        'function': _function,
        'class': _class,
        'module': _module,
        'package': _package,
        'session': _session,
    }[scope]


# For all scopes.
boto_mocker = pytest.fixture()(_mocker())
class_boto_mocker = pytest.fixture(scope='class')(_mocker('class'))
module_boto_mocker = pytest.fixture(scope='module')(_mocker('module'))
package_boto_mocker = pytest.fixture(scope='package')(_mocker('package'))
session_boto_mocker = pytest.fixture(scope='session')(_mocker('session'))
