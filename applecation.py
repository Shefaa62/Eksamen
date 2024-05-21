import argparse
import socket
import time
from struct import *

BUFFER_SIZE = 1024
RECEIVED_FILE_NAME = "received_file.jpg"  # Change the file extension to .jbg
TIMEOUT = 0.5  # Timeout in seconds for retransmission

header_format = '!HHH'  # sequence number 2 bytes, acknowledgment number 2 bytes, flags 2 bytes

# Create package
def create_packet(seq, ack, flags, data):
    header = pack(header_format, seq, ack, flags)
    packet = header + data
    return packet

# Parse header and return it
def parse_header(header):
    return unpack(header_format, header)

def parse_flags(flags):
    syn = (flags & (1 << 2)) >> 2
    ack = (flags & (1 << 1)) >> 1
    fin = flags & 1
    return syn, ack, fin

def receive_file(server_ip, server_port, discard_packet):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))

    print("Connection Establishment Phase:\n")

    # receive SYN-packet fra client
    syn_packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
    _, _, flags = parse_header(syn_packet[:6])
    syn, ack, fin = parse_flags(flags)
    if syn:
        print("SYN packet is received")
        # Send SYN-ACK-package to client
        server_socket.sendto(create_packet(0, 0, (1 << 2) | (1 << 1), b''), client_address)  # SYN-ACK flag
        print("SYN-ACK packet is sent")

        ack_packet, _ = server_socket.recvfrom(BUFFER_SIZE)
        _, _, flags = parse_header(ack_packet[:6])
        if flags & (1 << 1):  # ACK flag
            print("ACK packet is received")
            print("Connection established\n")
        else:
            print("ACK packet not received. Connection establishment failed.")
            return
    else:
        print("SYN packet not received. Connection establishment failed.")
        return

    print("Data Transfer:\n")

    start_time = time.time()
    with open(RECEIVED_FILE_NAME, "wb") as file:  # Open the file in binary write mode
        expected_seq_num = 0
        packet_timestamps = {}  # Store timestamps of received packets



        while True:
            packet, client_address = server_socket.recvfrom(BUFFER_SIZE)
            header = packet[:6]
            data = packet[6:]
            seq_num, ack_num, flags = parse_header(header)

            if flags & 1:  # FIN flag
                fin_ack_packet = create_packet(0, 0, (1 << 1), b'')  # FIN-ACK flag
                server_socket.sendto(fin_ack_packet, client_address)
                print("FIN ACK packet is sent")
                break

            # Check package must be thrown away
            if discard_packet is not None and seq_num == discard_packet:
                print(f"Discarding packet {seq_num}")
                discard_packet = None  # Discard only once
                continue

            if seq_num == expected_seq_num:
                file.write(data)
                packet_timestamps[seq_num] = time.time()  # Stor timestamp
                timestamp_str = time.strftime('%H:%M:%S') + f'.{int(time.time() * 1000) % 1000:06}'  # Format timestamp
                print(f"{timestamp_str} -- Packet {seq_num} is received")   # Time

                ack_packet = create_packet(0, seq_num, (1 << 1), b'')  # ACK flag
                server_socket.sendto(ack_packet, client_address)
                timestamp_str = time.strftime('%H:%M:%S') + f'.{int(time.time() * 1000) % 1000:06}'  # Format timestamp
                print(f"{timestamp_str} -- ACK for packet {seq_num} is sent")

                expected_seq_num += 1
            else:
                timestamp_str = time.strftime('%H:%M:%S') + f'.{int(time.time() * 1000) % 1000:06}'  # Format timestamp
                print(f"{timestamp_str} -- Out-of-order packet {seq_num} is received")  # Time

                ack_packet = create_packet(0, expected_seq_num - 1, (1 << 1), b'')  # ACK for the last correctly received packet
                server_socket.sendto(ack_packet, client_address)
                print(f"ACK for out-of-order packet {expected_seq_num - 1} is sent")

    end_time = time.time()
    duration = end_time - start_time
    throughput = (expected_seq_num * 1000) / (1024 * 1024 * duration)  # in Mbps

    print(f"\nData Transfer Finished\n")
    print(f"The throughput is {throughput:.2f} Mbps")
    print("Connection Closes")

    server_socket.close()

# Client function
def send_data(server_ip, server_port, file_path, window_size):   # Send data
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)

    print("Connection Establishment Phase:\n")

    # Send SYN-package to server
    client_socket.sendto(create_packet(0, 0, 1 << 2, b''), (server_ip, server_port))  # SYN flag
    print("SYN packet is sent")

    # Receive SYN-ACK-package fra server
    syn_ack_packet, _ = client_socket.recvfrom(BUFFER_SIZE)
    _, _, flags = parse_header(syn_ack_packet[:6])
    syn, ack, fin = parse_flags(flags)
    if syn and ack:
        print("SYN-ACK packet is received")
        client_socket.sendto(create_packet(0, 0, 1 << 1, b''), (server_ip, server_port))  # ACK flag
        print("ACK packet is sent")
        print("Connection established\n")
    else:
        print("SYN-ACK packet not received. Connection establishment failed.")
        client_socket.close()
        return

    print("Data Transfer:\n")

    with open(file_path, "rb") as file:
        seq_num = 0
        base = 0
        data_buffer = []


        while chunk := file.read(994):  # Read chunks of 994 bytes
            data_buffer.append(chunk)

        while base < len(data_buffer):
            while seq_num < len(data_buffer) and seq_num < base + window_size:
                packet = create_packet(seq_num, 0, 0, data_buffer[seq_num])
                client_socket.sendto(packet, (server_ip, server_port))
                timestamp_str = time.strftime('%H:%M:%S') + f'.{int(time.time() * 1000) % 1000:06}'  # Format timestamp
                print(f"{timestamp_str} -- packet with seq = {seq_num} is sent, sliding window = {set(range(base, seq_num + 1))}")
                seq_num += 1

            try:
                while base < seq_num:
                    ack_packet, _ = client_socket.recvfrom(BUFFER_SIZE)
                    _, ack_num, flags = parse_header(ack_packet[:6])
                    if flags & (1 << 1):  # ACK flag
                        timestamp_str = time.strftime('%H:%M:%S') + f'.{int(time.time() * 1000) % 1000:06}'  # Format timestamp
                        print(f"{timestamp_str} -- ACK for packet = {ack_num} is received")
                        if ack_num >= base:
                            base = ack_num + 1
                            break  # Move out of the while loop to send the next set of packets
            except socket.timeout:
                timestamp_str = time.strftime('%H:%M:%S') + f'.{int(time.time() * 1000) % 1000:06}'  # Format timestamp
                print(f"{timestamp_str} -- RTO occurred")
                for i in range(base, min(seq_num, base + window_size)):
                    packet = create_packet(i, 0, 0, data_buffer[i])
                    client_socket.sendto(packet, (server_ip, server_port))
                    timestamp_str = time.strftime('%H:%M:%S') + f'.{int(time.time() * 1000) % 1000:06}'  # Format timestamp
                    print(f"{timestamp_str} -- retransmitting packet with seq = {i}")

    print("\nData Transfer Finished\n")

    print("Connection Teardown:\n")
    fin_packet = create_packet(0, 0, 1, b'')  # FIN flag
    client_socket.sendto(fin_packet, (server_ip, server_port))
    print("FIN packet is sent")

    fin_ack_packet, _ = client_socket.recvfrom(BUFFER_SIZE)
    _, _, flags = parse_header(fin_ack_packet[:6])
    if flags & (1 << 1):  # FIN-ACK flag
        print("FIN ACK packet is received\n")
    else:
        print("FIN ACK packet not received.")

    print("Connection Closes.")
    client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Transfer using GBN Protocol")
    parser.add_argument("-s", "--server", action="store_true", help="Invoke server")
    parser.add_argument("-c", "--client", action="store_true", help="Invoke client")
    parser.add_argument("-i", "--ip", type=str, required=True, help="IP address")
    parser.add_argument("-p", "--port", type=int, required=True, help="Port number")
    parser.add_argument("-f", "--file", type=str, help="File path (required for client)")
    parser.add_argument("-w", "--window", type=int, default=3, help="Sliding window size (default is 3)")
    parser.add_argument("-d", "--discard", type=int, help="Packet number to discard (server only)")
    args = parser.parse_args()

    if args.server:
        receive_file(args.ip, args.port, args.discard)
    elif args.client:
        if args.file:
            send_data(args.ip, args.port, args.file, args.window)
        else:
            print("File path is required for client mode.")
    else:
        print("Please specify whether to run as server (-s) or client (-c).")

