import argparse
import random
import socket
import threading
import hashlib
import time
import struct

timeout = 1
retransmit = False
firstKarn = True

# Calcula el checksum de un mensaje en string
def calculate_checksum(message):
    checksum = hashlib.md5(message.encode()).hexdigest()
    return checksum

# Envía el paquete con datos al servidor
def send_packet(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (ip, port)

    try:
        sock.sendto(message.encode(), server_address)
    finally:
        sock.close()


def main(ip, filename, window, packsize, seqsize, sendport, ackport):
    global timeout
    # El archivo que queremos mandar.
    f = open(filename, "r")
    content = f.read()
    sent_time = []
    # El texto dividido en chunks de packsize caracteres.
    parts = [content[i:i + packsize] for i in range(0, len(content), packsize)]

    # Número de secuencia inicial. Debe ser cero. Ojo con el ACK que se manda si es
    # que el servidor está esperando el primer paquete. ¿Qué valor debiese tener? Maxseq
    # Hint: revisen lo que les tira el servidor si el paquete 0 no llega.
    seq_num = 0

    # Crea un mensaje concatenándole su seqnum y checksum.
    def create_message(message, seq_num):
        seq_num_padded = str(seq_num).zfill(seqsize)
        checksum = calculate_checksum(message)

        return "%s%s%s" % (str(seq_num_padded), str(checksum), message)


    # Funcion anidada para leer el input.
    # Espera el paquete ack de parte del servidor. Esta versión no hace nada
    # distinto a publicar ese valor.
    def receive_ack():
        global firstKarn
        global timeout
        global retransmit
        EstimatedRTT = None
        DevRTT = None

        running = True
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sock.bind((ip, ackport))
        sock.settimeout(90)

        while running:
            data, address = sock.recvfrom(1024)
            if data:
                seq,chksum = struct.unpack(str(seqsize)+'s32s', data)
                seq = seq.decode('utf-8')
                chksum = chksum.decode('utf-8')
                if calculate_checksum(seq) == chksum:
                    print("Checksum correcto de seq: "+seq)
                    if not retransmit:
                        ack_time = time.time()
                        if firstKarn:
                            firstKarn = False
                            EstimatedRTT = ack_time-sent_time[int(seq)]
                            DevRTT = EstimatedRTT/2.0
                            timeout = EstimatedRTT + max(1,4*DevRTT) # Segun RFC6298 Pag 2
                            print('Calculated timeout: '+str(timeout))
                            if timeout < 1: # Whenever RTO is computed, if it is less than 1 second, then the
                                            # RTO SHOULD be rounded up to 1 second.
                                timeout = 1
                        else:
                            SampleRTT = ack_time-sent_time[int(seq)]
                            EstimatedRTT = (1-0.125)*EstimatedRTT+0.125*SampleRTT
                            DevRTT = (1-0.25)*DevRTT+0.25*abs(SampleRTT-EstimatedRTT)
                            timeout = EstimatedRTT + 4*DevRTT
                            print('Calculated timeout: ' + str(timeout))
                            if timeout < 1:
                                timeout = 1
                else:
                    print("Checksum con errores")

    # Thread de recepción de acks.
    ack_thread = threading.Thread(target=receive_ack)
    ack_thread.start()

    # Enviamos cada paquete. ¿Llegan siempre? No
    while seq_num < len(parts):
        message = create_message(parts[seq_num], seq_num)
        sent_time.append(time.time())
        send_packet(ip, sendport, message)
        time.sleep(0.1)
        seq_num += 1

    send_packet(ip, sendport, '') # Paquete vacio para terminar la conexion


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="IP to send the data", default='127.0.0.1', type=str)
    parser.add_argument("--filename", help="File to send", default='mandela.txt', type=str)
    parser.add_argument("--window", help="Window size", default=30, type=int)
    parser.add_argument("--packsize", help="Size of the package", default=30, type=int)
    parser.add_argument("--seqsize", help="Max sequence numbers", default=2, type=int)
    parser.add_argument("--sendport", help='Port to send the data', default=8989, type=int)
    parser.add_argument('--ackport', help="Port to receive ACKs", default=9090, type=int)
    args = parser.parse_args()
    main(args.ip, args.filename, args.window, args.packsize, args.seqsize, args.sendport, args.ackport)
