import json
import logging

import boto.logs
from boto.logs.exceptions import (DataAlreadyAcceptedException,
                                  InvalidSequenceTokenException,
                                  ResourceAlreadyExistsException)


class CloudWatchHandler(logging.StreamHandler):
    def __init__(self, region, log_group_name, log_stream_name, level=logging.INFO):
        logging.StreamHandler.__init__(self)
        self.region = region
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self.connection = None
        self.sequence_token = None

    def create_group_and_stream(self, log_group_name, log_stream_name):
        try:
            self.connection.create_log_group(log_group_name)
        except ResourceAlreadyExistsException:
            pass
        try:
            self.connection.create_log_stream(log_group_name, log_stream_name)
        except ResourceAlreadyExistsException:
            pass

    def _lazy_connect(self):
        if self.connection:
            return
        self.connection = boto.logs.connect_to_region(self.region)
        self.create_group_and_stream(self.log_group_name, self.log_stream_name)

    def _put_message(self, message, timestamp):
        self._lazy_connect()
        event = {"message": message, "timestamp": timestamp}
        result = self.connection.put_log_events(
            self.log_group_name,
            self.log_stream_name,
            [event],
            self.sequence_token)
        self.sequence_token = result.get("nextSequenceToken", None)

    def put_message(self, message, timestamp):
        try:
            self._put_message(message, timestamp)
        except (DataAlreadyAcceptedException, InvalidSequenceTokenException) as e:
            if e.status != 400:
                raise
            next_sequence_token = e.body.get("expectedSequenceToken", None)
            if next_sequence_token:
                self.sequence_token = next_sequence_token
                self._put_message(message, timestamp)
            else:
                raise

    def emit(self, record):
        timestamp = int(record.created * 1000)
        message = json.dumps(vars(record))
        self.put_message(message, timestamp)
