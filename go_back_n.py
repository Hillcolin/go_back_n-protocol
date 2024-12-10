
import time
import threading
import queue

class GBN_sender:
    total =0
    def __init__(self, input_file, window_size, packet_len, nth_packet, send_queue, ack_queue, timeout_interval, logger):
        
        self.input_file = input_file #The file containing the data to be sent
        self.window_size = window_size #the size of the window for sending packets
        self.packet_len = packet_len #the length of each packet to be sent in bits
        self.nth_packet = nth_packet #An integer value representing the number of packets to be dropped
        self.send_queue = send_queue #A queuq to send packets to the reciever
        self.ack_queue = ack_queue #A queue to send acknowledgements to the reciever
        self.timeout_interval = timeout_interval #The timeout period for retransmitting packets if no acknowledgement is received
        self.logger = logger #A logging object to log events during the transmission

        self.base = 0 #The base of the sliding window
        self.packets = self.prepare_packets() #The list of packets to be sent
        self.acks_list = [False] * len(self.packets) #List that tracs which packets have been AWKed
        self.packet_timers = [0] * len(self.packets) #A list that tracks the timeout ofor each packet
        self.dropped_list = [] #A list that tracks which packets have been dropped

        self.logger.info(f"{len(self.prepare_packets())} packets created, Window size: {window_size}, Packet length: {packet_len}, Nth packet to be dropped: {self.nth_packet}, Timeout interval: {self.timeout_interval}")
        

###########################################################################################################################################

        """
        This method reads the data from the input file, converts it to binary, and
        then breaks it up into packets. The sequence number of each packet is
        appended to the packet as a 16-bit binary string.

        Returns
        list
            A list of binary strings, each representing a packet to be sent.
        """
    def prepare_packets(self):
        #READ
        with open(self.input_file, 'r') as file:
            data = file.read()

        #STR to BIN
        binary_data = ''
        for char in data:
            binary_data += format(ord(char), '08b')

        #NUM PACKS
        packet_len = self.packet_len
        data_len = len(binary_data)
        num_packets = (data_len + (packet_len - 16) - 1) // (packet_len - 16)
        
        #MAKE PACKS
        packets = []
        seq_num = 0
        for i in range(num_packets):
            packet = binary_data[i * (packet_len - 16): (i + 1) * (packet_len - 16)]
            packet += format(seq_num, '016b')
            packets.append(packet)
            seq_num += 1
        return packets
    
###########################################################################################################################################

    """
        Sends packets from the base index to the end of the packets list. If
        packet is one of the nth packets, it is dropped. The sequence number of
        each packet is logged. The packet is then put into the send queue.

    """
    def send_packets(self):
        
        for i in range(self.base, len(self.packets)):
            seq_num = int(self.packets[i][-16:], 2)
            self.logger.info(f"Sender: sending packet {seq_num}")
            
            if (self.total + 1) % self.nth_packet == 0 and seq_num not in self.dropped_list:
                self.logger.info(f"Sender: packet {seq_num} dropped")
                self.dropped_list.append(seq_num)
                self.total += 1
                self.packet_timers[i] = time.time()
                
            else:
                self.send_queue.put(self.packets[i])
                self.packet_timers[i] = time.time()
                self.total += 1


###########################################################################################################################################

        """
        Sends the next packet in the packets list if it is not one of the nth
        packets to be dropped. If the previous packet has been acknowledged,
        the packet is sent. Otherwise it is dropped.
        """
    def send_next_packet(self):
        self.base += 1
        packet_num = self.base + self.window_size - 1

        if packet_num < len(self.packets):
            packet = self.packets[packet_num]
            seq_num = int(packet[-16:], 2)

            if (seq_num + 1) % self.nth_packet == 0 and seq_num not in self.dropped_list:
                self.logger.info(f"Sender: packet {seq_num} dropped")
                self.dropped_list.append(seq_num)
                self.packet_timers[i] = time.time()
                
            else:
                
                if seq_num - 1 in [x for x in range(len(self.acks_list)) if self.acks_list[x]]: # has prev packet been acked, is seq num in ack list
                    self.send_queue.put(packet)
                    self.packet_timers[packet_num] = time.time()

###########################################################################################################################################

    """
    This method iterates over the packets in the current window, checks if the
    transmission time has exceeded the timeout interval, and if so, logs a
    timeout message, updates the base to the timed-out packet's index, and
    retransmits the packets starting from the base.

    Returns bool
        True if any packet has timed out and packets were retransmitted,
        other False.
    """
    def check_timers(self):
        for i in range(self.base, min(self.base + self.window_size, len(self.packets))):
            seq_num = int(self.packets[i][-16:], 2)
            
            if time.time() - self.packet_timers[i] > self.timeout_interval:
                self.logger.info(f"Sender: packet {seq_num} timed out")
                self.base = i
                self.send_packets()
                return True
            
        return False
    
###########################################################################################################################################

    """
    This method retrieves ACKs from the `ack_queue` in a loop. If an ACK is
    `None`, it breaks the loop, indicating the end of transmission. For valid
    ACKs within the range of packet indices, it checks if the packet has already
    been acknowledged. If not, it marks the packet as acknowledged and logs the
    receipt. It then triggers the sending of the next packet. If the ACK is out
    of range, it logs this information. Any exceptions encountered during the
    process are logged as errors.
    """
    def receive_acks(self):
        while True:
            try:
                ack = self.ack_queue.get()

                if ack is None:
                    break

                if ack < len(self.packets):
                    if self.acks_list[ack]:
                        self.logger.info(f"Sender: ack {ack} received, Ignoring")

                    else:
                        self.acks_list[ack] = True
                        self.logger.info(f"Sender: ack {ack} received")
                        self.send_next_packet()

                else:
                    self.logger.info(f"Sender: ack {ack} received, out of range")

            except Exception as e:
                self.logger.error(f"Sender: Error receiving ack: {e}")
            
###########################################################################################################################################

        """
        Start the sender by sending the first packet and starting a thread to receive
        acknowledgements. Then, loop until all packets have been sent and acknowledged.
        During each iteration of the loop, check if any packets have timed out and
        retransmit them if necessary. After all packets have been acknowledged, send
        a None packet to the receiver to signal the end of transmission and
        process any remaining acknowledgements. If an error occurs during the
        transmission, log the error and join the thread.
        """
    def run(self):
        self.send_packets()
        thread = threading.Thread(target=self.receive_acks)
        thread.start()

        try:
            while self.base < len(self.packets):
                self.check_timers()
                if self.check_timers():
                    self.send_packets()
                time.sleep(0.1)

            self.send_queue.put(None)
            self.logger.info("Sender: All packets have been sent and acknowledgments processed.")

        except Exception as e:
            self.logger.error(f"Sender: Error running sender: {e}")
            thread.join()
        
    
############################################################################################################
############################################################################################################

class GBN_receiver:
    def __init__(self, output_file, send_queue, ack_queue, logger):
        self.output_file = output_file
        self.send_queue = send_queue
        self.ack_queue = ack_queue
        self.logger = logger
        self.packet_list = []
        self.expected_seq_num = 0

###########################################################################################################################################

        """
        If the packet is in the correct order, it is added to the packet_list
        and its sequence number is sent back to the sender as an acknowledgement.
        If the packet is out of order, the sequence number of the last packet
        successfully processed is sent back to the sender as an acknowledgement.
        If an error occurs during processing, an error message is logged and
        False is returned.
        
        Parameters: packet - str
            The packet received from the sender

        Returns: bool
            True if the packet was successfully processed, False otherwise
        """
    def process_packet(self, packet):
        try:
            seq_num = int(packet[-16:], 2)
            
            if seq_num == self.expected_seq_num:
                self.packet_list.append(packet[:-16])
                self.ack_queue.put(seq_num)  
                self.logger.info(f"Receiver: packet {seq_num} received")
                self.expected_seq_num = seq_num + 1
                return True
            
            else:
                self.ack_queue.put(self.expected_seq_num - 1)
                self.logger.info(f"Receiver: packet {seq_num} received out of order")
                return False
            
        except Exception as e:
            self.logger.error(f"Receiver: Error processing packet: {e}")
            return False
        
###########################################################################################################################################

    """
    The packet_list is a list of binary strings, where each string represents
    a packet of data. This method converts each packet from binary to a string
    of characters and writes the resulting string to the output file.
    """
    def write_to_file(self):
        try:
            #binary format --> characters
            data = ''
            
            for packet in self.packet_list:
                #binary packet --> string of characters
                packet_str = ''.join(chr(int(packet[i:i+8], 2)) for i in range(0, len(packet), 8))
                data += packet_str
                
            with open(self.output_file, 'w') as file:
                file.write(data)
                
        except Exception as e:
            self.logger.error(f"Receiver: Error writing to file: {e}")

###########################################################################################################################################

    """
    This method runs an infinite loop where it retrieves packets from the send queue
    with a timeout. Each packet is processed using the `process_packet` method. If a
    `None` packet is received, it breaks the loop, indicating the end of transmission.
    After processing all packets, it writes the accumulated data to an output file and
    sends a `None` acknowledgment to signal completion. Handles any exceptions that
    may occur during packet processing or file writing and logs them. Also
    exits on a keyboard interrupt.
    """
    def run(self):
        try:
            while True:
                try:
                    packet = self.send_queue.get(timeout=1)

                    if packet is None:
                        break

                    self.process_packet(packet)

                except queue.Empty:
                    pass

                except Exception as e:
                    self.logger.error(f"Receiver: Error running receiver: {e}")
            
            self.write_to_file()
            self.ack_queue.put(None)

        except KeyboardInterrupt:
            self.logger.info("Receiver:Keyboard interrupt")

        except Exception as e:
            self.logger.error(f"Receiver: Unexpected error: {e}")