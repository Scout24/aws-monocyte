#!/usr/bin/env python
import logging

from mock import patch
import unittest

import boto

from monocyte.loghandler import CloudWatchHandler


class CloudWatchHandlerTest(unittest.TestCase):

    def setUp(self):
        self.boto_mock = patch("monocyte.loghandler.boto").start()
        self.connection = self.boto_mock.logs.connect_to_region.return_value
        self.logger = logging.getLogger("Test")
        self.logger.setLevel(logging.WARN)
        # # do you want a console output, too? use this...
        # console_handler = logging.StreamHandler(sys.stdout)
        # console_handler.setFormatter(logging.Formatter('%(levelname)-8s %(message)s'))
        # self.logger.addHandler(console_handler)

    def myAssertIn(self, a, b):
        self.assertTrue(a in b)

    def test_cloudwatch_logging(self):
        cloudwatch_handler = CloudWatchHandler("eu-central-1", "monocyte", "test")
        self.logger.addHandler(cloudwatch_handler)

        self.connection.create_log_group.assert_called_with("monocyte")
        self.connection.create_log_stream.assert_called_with("monocyte", "test")

        self.logger.debug("aha")
        self.logger.info("aha")
        self.assertFalse(self.connection.put_log_events.called)

        self.logger.warn("aha")
        call_args = self.connection.put_log_events.call_args[0]
        self.assertEqual("monocyte", call_args[0])
        self.assertEqual("test", call_args[1])
        log_event = call_args[2][0]
        self.myAssertIn("timestamp", log_event)
        self.myAssertIn("message", log_event)
        self.myAssertIn("WARNING", log_event["message"])
        self.myAssertIn("aha", log_event["message"])

    def test_log_group_already_exists(self):
        e = boto.logs.exceptions.ResourceAlreadyExistsException(400, "binschonda")
        self.connection.create_log_group.side_effect = e
        self.connection.create_log_stream.side_effect = e
        CloudWatchHandler("eu-central-1", "monocyte", "test")

    def test_response_with_invalid_sequence_token(self):
        e = boto.logs.exceptions.InvalidSequenceTokenException(400, "foo")
        e.body = {"expectedSequenceToken": "correct_token"}
        self.connection.put_log_events.side_effect = e

        handler = CloudWatchHandler("eu-central-1", "monocyte", "test")
        self.assertRaises(boto.logs.exceptions.InvalidSequenceTokenException,
                          handler.put_message, "message", "timestamp")

    def test_invalid_response(self):
        e = boto.logs.exceptions.InvalidSequenceTokenException(500, "completelybroken")
        self.connection.put_log_events.side_effect = e

        handler = CloudWatchHandler("eu-central-1", "monocyte", "test")
        self.assertRaises(boto.logs.exceptions.InvalidSequenceTokenException,
                          handler.put_message, "message", "timestamp")

    def test_response_with_missing_sequence_token(self):
        e = boto.logs.exceptions.InvalidSequenceTokenException(400, "foo")
        e.body = {}
        self.connection.put_log_events.side_effect = e

        handler = CloudWatchHandler("eu-central-1", "monocyte", "test")
        self.assertRaises(boto.logs.exceptions.InvalidSequenceTokenException,
                          handler.put_message, "message", "timestamp")


if __name__ == "__main__":
    unittest.main()
