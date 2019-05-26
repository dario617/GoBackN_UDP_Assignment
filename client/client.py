import argparse
import random
import socket
import threading
import hashlib
import time
import struct

# Calcula el checksum de un mensaje en string
def calculate_checksum(message):
    checksum = hashlib.md5(message.encode()).hexdigest()
    print("hash is " + checksum)
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

    # El archivo que queremos mandar.
    f = open(filename, "r")
    content = f.read()

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

    # Crear lista para manejar los Ack recibidos
    # y listas para manejo de errores
    acks = [False for el in parts]
    ackCount = [0 for el in parts]
    flags = [0]
    lastAck = 0

    # Timeout para la ventana calculado con el algoritmo de Karn
    timeout = 0.9

    # Funcion anidada para leer el input.
    # Espera el paquete ack de parte del servidor. Esta versión no hace nada
    # distinto a publicar ese valor.
    def receive_ack():
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
                    acks[int(seq)] = True
                    ackCount[int(seq)] = ackCount[int(seq)] + 1
                else:
                    print("Checksum con errores")
                # Si se recibe el elemento de la ventana muchas veces entonces 
                # el checksum estaba corrupto pero el servidor obtuvo la info
                # entonces podemos mover el seqnum
                if ackCount[int(seq)] > 3 :
                    print("Moviendo el numero de ACK a {}".format(int(seq)))
                    flags[0] = int(seq)

    # Thread de recepción de acks.
    ack_thread = threading.Thread(target=receive_ack)
    ack_thread.start()

    # Enviamos cada paquete. ¿Llegan siempre? No
    while seq_num < len(parts):

        window_bottom = seq_num
        if seq_num + window < len(parts):
            window_top = seq_num + window
        else:
            window_top = len(parts)

        # Enviar los paquetes en la ventana
        print("Ventana actual",window_bottom, window_top)
        while window_bottom < window_top:
            message = create_message(parts[window_bottom], window_bottom)
            send_packet(ip, sendport, message)
            window_bottom += 1

        # Esperar el timeout
        time.sleep(timeout)

        # Tomar ultimo valor True
        while lastAck < len(parts) and acks[lastAck]:
            lastAck += 1

        # Compararlo con el valor de ack mas grande
        if lastAck < flags[0]:
            lastAck = flags[0]
        
        seq_num = lastAck

    # Estadisticas finales de ejecucion
    print("Acks recibidos sin problemas")
    print(acks)
    print("Conteo de acks")
    print(ackCount)
    send_packet(ip, sendport, '') # Paquete vacio para terminar la conexion


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="IP to send the data", default='127.0.0.1', type=str)
    parser.add_argument("--filename", help="File to send", default='mandela.txt', type=str)
    parser.add_argument("--window", help="Window size", default=5, type=int)
    parser.add_argument("--packsize", help="Size of the package", default=30, type=int)
    parser.add_argument("--seqsize", help="Max sequence numbers", default=2, type=int)
    parser.add_argument("--sendport", help='Port to send the data', default=8989, type=int)
    parser.add_argument('--ackport', help="Port to receive ACKs", default=9090, type=int)
    args = parser.parse_args()
    main(args.ip, args.filename, args.window, args.packsize, args.seqsize, args.sendport, args.ackport)
