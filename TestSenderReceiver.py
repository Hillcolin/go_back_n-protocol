import unittest
from go_back_n import GBN_sender, GBN_receiver

class TestGBNSenderReceiver(unittest.TestCase):
    def test_successful_transmission(self):
        # Create a sender and receiver with the same parameters
        sender = GBN_sender(input_file='input_test.txt', window_size=4, packet_len=32, nth_packet=4, send_queue=None, ack_queue=None, timeout_interval=1, logger=None)
        receiver = GBN_receiver(output_file='output_test.txt', send_queue=None, ack_queue=None, logger=None)

        # Run the sender and receiver
        sender.run()
        receiver.run()

        # Check if all packets were sent and received successfully
        if sender.all_packets_sent() and receiver.all_packets_received():
            print("Test 1 passed")
        else:
            print("Test 1 failed")

    def test_packet_drop(self):
        # Create a sender and receiver with the same parameters
        sender = GBN_sender(input_file='input_test.txt', window_size=4, packet_len=32, nth_packet=2, send_queue=None, ack_queue=None, timeout_interval=1, logger=None)
        receiver = GBN_receiver(output_file='output_test.txt', send_queue=None, ack_queue=None, logger=None)

        # Run the sender and receiver
        sender.run()
        receiver.run()

        # Check if the dropped packet was retransmitted and received successfully
        if sender.all_packets_sent() and receiver.all_packets_received():
            print("Test 2 passed")
        else:
            print("Test 2 failed")

    def test_timeout(self):
        # Create a sender and receiver with the same parameters
        sender = GBN_sender(input_file='input_test.txt', window_size=4, packet_len=32, nth_packet=4, send_queue=None, ack_queue=None, timeout_interval=0.5, logger=None)
        receiver = GBN_receiver(output_file='output_test.txt', send_queue=None, ack_queue=None, logger=None)

        # Run the sender and receiver
        sender.run()
        receiver.run()

        # Check if the dropped packet was retransmitted and received successfully
        if sender.all_packets_sent() and receiver.all_packets_received():
            print("Test 3 passed")
        else:
            print("Test 3 failed")

if __name__ == '__main__':
    unittest.main()