import argparse
import random
import socket
import threading
import hashlib
import time


# Calcula el checksum de un mensaje en string (sí, es así de simple)
def calculate_checksum(message):
    checksum = hashlib.md5(message.encode()).hexdigest()
    print("hash is " + checksum)
    return checksum


# Crea un mensaje concatenándole su seqnum y checksum.
def create_message(message, seq_num):
    seq_num_padded = str(seq_num).zfill(2)
    checksum = calculate_checksum(message)

    return "%s%s%s" % (str(seq_num_padded), str(checksum), message)


# Envía el paquete con datos al servidor
def send_packet(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (ip, port)

    try:
        sock.sendto(message.encode(), server_address)
    finally:
        sock.close()


# Espera el paquete ack de parte del servidor. Esta versión no hace nada
# distinto a publicar ese valor.
def receive_ack():
    running = True
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind(('0.0.0.0', 9090))
    sock.settimeout(90)

    while running:
        data, address = sock.recvfrom(1024)

        if data:
            print("ACK recibido: " + data.decode())


# TODO Cambiar nuumeros hardcodeados
def main(ip, filename, window, packsize, seqsize, sendport, ackport):
    # El texto que queremos mandar. La biografía de Nelson Mandela.
    f = open(filename, "r")
    content = f.read()
    # El texto dividido en chunks de 30 caracteres.
    parts = [content[i:i + 30] for i in range(0, len(content), 30)]
    # Número de secuencia inicial. Debe ser cero. Ojo con el ACK que se manda si es
    # que el servidor está esperando el primer paquete. ¿Qué valor debiese tener?
    # Hint: revisen lo que les tira el servidor si el paquete 0 no llega.
    seq_num = 0

    # Thread de recepción de acks.
    ack_thread = threading.Thread(target=receive_ack)
    ack_thread.start()

    # Enviamos cada paquete. ¿Llegan siempre?
    while seq_num < len(parts):
        message = create_message(parts[seq_num], seq_num)
        send_packet('0.0.0.0', sendport, message)  # Estos deberían ser parámetros configurables de lso usuarios
        time.sleep(0.1)
        seq_num += 1

    send_packet('localhost', sendport, '') # Paquete vacio para terminar la conexion


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="IP to send the data", default='127.0.0.1', type=str)
    parser.add_argument("--filename", help="File to send", default='mandela.txt', type=str)
    parser.add_argument("--window", help="Window size", default=30, type=int)
    parser.add_argument("--packsize", help="Size of the package", default=30, type=int)
    parser.add_argument("--seqsize", help="Max sequence numbers", default=30, type=int)
    parser.add_argument("--sendport", help='Port to send the data', default=8989, type=int)
    parser.add_argument('--ackport', help="Port to receive ACKs", default=9090, type=int)
    args = parser.parse_args()
    main(args.ip, args.filename, args.window, args.packsize, args.seqsize, args.sendport, args.ackport)
