import uuid

import boto3
import pytest


# SQS
@pytest.fixture
def setup_sqs(boto_mocker):
    """
    Setup Amazon SQS client.
    """
    message_list = {}

    def _send_message(self, operation_name, kwarg):
        queue_url = kwarg['QueueUrl']
        message = {
            'Body': kwarg['MessageBody'],
            'ReceiptHandle': str(uuid.uuid4()),
        }

        if queue_url in message_list:
            message_list[queue_url].append(message)
        else:
            message_list[queue_url] = [message]

        return {
            'ResponseMetadata': {'HTTPStatusCode': 200},
        }

    def _receive_message(self, operation_name, kwarg):
        queue_url = kwarg['QueueUrl']
        max_number_of_messages = kwarg.get('MaxNumberOfMessages', 1)

        ret = {
            'ResponseMetadata': {'HTTPStatusCode': 200},
        }
        messages = message_list[queue_url][:max_number_of_messages]
        if messages:
            ret['Messages'] = messages
        return ret

    def _delete_message(self, operation_name, kwarg):
        queue_url = kwarg['QueueUrl']
        receipt_handle = kwarg['ReceiptHandle']

        message_list[queue_url] = [message for message in message_list[queue_url] if message['ReceiptHandle'] != receipt_handle]
        return {
            'ResponseMetadata': {'HTTPStatusCode': 200},
        }

    def _get_queue_url(self, operation_name, kwarg):
        queue_name = kwarg['QueueName']
        queue_owner_aws_account_id = kwarg.get('QueueOwnerAWSAccountId', 'ACCOUNT_ID')
        return {
            'QueueUrl': f"https://sqs.REGION.amazonaws.com/{queue_owner_aws_account_id}/{queue_name}",
            'ResponseMetadata': {'HTTPStatusCode': 200},
        }

    boto_mocker.patch(new=boto_mocker.build_make_api_call({
        'sqs': {
            'SendMessage': _send_message,
            'ReceiveMessage': _receive_message,
            'DeleteMessage': _delete_message,
            'GetQueueUrl': _get_queue_url,
        },
    }))


def test_sqs_sequence(setup_sqs):
    queue_name = 'QueueName.fifo'

    sqs = boto3.client('sqs')
    response = sqs.get_queue_url(QueueName=queue_name)
    queue_url = response['QueueUrl']
    response = sqs.send_message(QueueUrl=queue_url, MessageBody='Body', MessageGroupId='GroupId', MessageDeduplicationId='DeduplicationId')
    response = sqs.receive_message(QueueUrl=queue_url)
    receipt_handle = response['Messages'][0]['ReceiptHandle']
    response = sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
