import time

import boto3
import pytest


# CloudWatchLogs
@pytest.fixture
def setup_logs(boto_mocker):
    """
    Setup Amazon CloudWatch Logs client.
    """
    logs = boto3.client('logs')
    log_groups = {}

    def _create_log_group(self, operation_name, kwarg):
        log_group_name = kwarg['logGroupName']
        if log_group_name in log_groups:
            raise logs.exceptions.ResourceAlreadyExistsException({}, 'CreateLogGroup')
        log_groups[log_group_name] = {}
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}

    def _delete_log_group(self, operation_name, kwarg):
        log_group_name = kwarg['logGroupName']
        if log_group_name not in log_groups:
            raise logs.exceptions.ResourceNotFoundException({}, 'DeleteLogGroup')
        del log_groups[log_group_name]
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}

    def _create_log_stream(self, operation_name, kwarg):
        log_group_name = kwarg['logGroupName']
        log_stream_name = kwarg['logStreamName']
        if log_group_name not in log_groups:
            raise logs.exceptions.ResourceNotFoundException({}, 'CreateLogStream')
        log_group = log_groups[log_group_name]
        if log_stream_name in log_group:
            raise logs.exceptions.ResourceAlreadyExistsException({}, 'CreateLogStream')
        log_group[log_stream_name] = {}
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}

    def _delete_log_stream(self, operation_name, kwarg):
        log_group_name = kwarg['logGroupName']
        log_stream_name = kwarg['logStreamName']
        if log_group_name not in log_groups:
            raise logs.exceptions.ResourceNotFoundException({}, 'DeleteLogStream')
        log_group = log_groups[log_group_name]
        if log_stream_name not in log_group:
            raise logs.exceptions.ResourceNotFoundException({}, 'DeleteLogStream')
        del log_group[log_stream_name]
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}

    def _put_log_events(self, operation_name, kwarg):
        log_group_name = kwarg['logGroupName']
        log_stream_name = kwarg['logStreamName']
        log_events = kwarg['logEvents']
        if log_group_name not in log_groups:
            raise logs.exceptions.ResourceNotFoundException({}, 'PutLogEvents')
        log_group = log_groups[log_group_name]
        if log_stream_name not in log_group:
            raise logs.exceptions.ResourceNotFoundException({}, 'PutLogEvents')
        log_stream = log_group[log_stream_name]
        for log_event in log_events:
            if log_event['timestamp'] in log_stream:
                log_stream[log_event['timestamp']] += [log_event]
            else:
                log_stream[log_event['timestamp']] = [log_event]
        return {'nextSequenceToken': 'next', 'ResponseMetadata': {'HTTPStatusCode': 200}}

    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'cloudwatchlogs': {
            'CreateLogGroup': _create_log_group,
            'DeleteLogGroup': _delete_log_group,
            'CreateLogStream': _create_log_stream,
            'DeleteLogStream': _delete_log_stream,
            'PutLogEvents': _put_log_events,
        },
    }))


def test_logs_sequence(setup_logs):
    log_group_name = 'Test.LogGroupName'
    log_stream_name = 'Test.LogStreamName'

    logs = boto3.client('logs')
    try:
        logs.create_log_group(logGroupName=log_group_name)
        logs.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)

        logs.put_log_events(logGroupName=log_group_name, logStreamName=log_stream_name, logEvents=[{
            'timestamp': int(time.time() * 1000),
            'message': 'log message.',
        }])
    finally:
        try:
            logs.delete_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
        except logs.exceptions.ResourceNotFoundException:
            pass
        try:
            logs.delete_log_group(logGroupName=log_group_name)
        except logs.exceptions.ResourceNotFoundException:
            pass
        logs.close()
