import argparse
import random
import socket
import threading
import hashlib
import time
import struct

current_milli_time = lambda: int(round(time.time() * 1000))

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
    total_parts = len(parts)

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
    ackCount = [0 for el in parts]
    lastReceived = [-1]

    # Timeout para la ventana calculado con el algoritmo de Karn
    timeout = 30000 # millis

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
                try:
                    seq,chksum = struct.unpack(str(seqsize)+'s32s', data)
                    seq = seq.decode('utf-8')
                    chksum = chksum.decode('utf-8')
                    # Si el checksum es correcto y el numero de secuencia esta en los limites
                    if calculate_checksum(seq) == chksum and int(seq) < total_parts:
                        print("Checksum correcto de seq: "+seq)
                        ackCount[int(seq)] = ackCount[int(seq)] + 1
                        # Si el numero de secuencia es mayor que el ultimo recibido actualizar
                        if lastReceived[0] < int(seq):
                            lastReceived[0] = int(seq)
                            print(lastReceived[0])
                    else:
                        print("Checksum con errores")
                        ackCount[int(seq)] = ackCount[int(seq)] + 1
                except Exception as e:
                    print("Exception en unpack",e)

    # Thread de recepción de acks.
    ack_thread = threading.Thread(target=receive_ack)
    ack_thread.start()

    # Enviamos cada paquete. ¿Llegan siempre? No
    window_bottom = seq_num
    window_top = seq_num + window

    while seq_num < total_parts:

        # Enviar dentro de la ventana
        if seq_num < window_top:
            message = create_message(parts[window_bottom], window_bottom)
            send_packet(ip, sendport, message)
            seq_num += 1

        # Si es el primero de la ventana poner el timeout
        if seq_num == window_bottom:
            timeToQuit = current_milli_time() + timeout

        # Si el timeout se acabo reiniciar ventana
        if timeToQuit < current_milli_time():
            seq_num = window_bottom

        # Actualizar variables de la ventana
        if window_bottom != lastReceived[0]:
            window_bottom = lastReceived[0]
            if window_top + window < total_parts: 
                window_top = window_bottom + window
            else:
                window_top = total_parts

    # Estadisticas finales de ejecucion
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
