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

    sock.bind(('0.0.0.0', 2040))
    sock.settimeout(90)

    while running:
        data, address = sock.recvfrom(1024)

        if data:
            print("ACK recibido: " + data.decode())


# TODO Cambiar nuumeros hardcodeados
def main(ip, filename, window, packsize, seqsize, sendport, ackport):
    # El texto que queremos mandar. La biografía de Nelson Mandela.
    mandela = "A Xhosa, Mandela was born to the Thembu royal family in Mvezo, British South Africa. He studied law at the University of Fort Hare and the University of Witwatersrand before working as a lawyer in Johannesburg. There he became involved in anti-colonial and African nationalist politics, joining the ANC in 1943 and co-founding its Youth League in 1944. After the National Party's white-only government established apartheid, a system of racial segregation that privileged whites, he and the ANC committed themselves to its overthrow. Mandela was appointed President of the ANC's Transvaal branch, rising to prominence for his involvement in the 1952 Defiance Campaign and the 1955 Congress of the People. He was repeatedly arrested for seditious activities and was unsuccessfully prosecuted in the 1956 Treason Trial. Influenced by Marxism, he secretly joined the banned South African Communist Party (SACP). Although initially committed to non-violent protest, in association with the SACP he co-founded the militant Umkhonto we Sizwe in 1961 and led a sabotage campaign against the government. He was arrested and imprisoned in 1962, and subsequently sentenced to life imprisonment for conspiring to overthrow the state following the Rivonia Trial."

    # El texto dividido en chunks de 30 caracteres.
    parts = [mandela[i:i + 30] for i in range(0, len(mandela), 30)]
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
        send_packet('0.0.0.0', 2030, message)  # Estos deberían ser parámetros configurables de lso usuarios
        time.sleep(0.1)
        seq_num += 1

    send_packet('localhost', 2030, '')


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", help="IP to send the data", default='127.0.0.1', type=str)
    parser.add_argument("--filename", help="File to send", type=str)
    parser.add_argument("--window", help="Window size", default=30, type=int)
    parser.add_argument("--packsize", help="Size of the package", default=100, type=int)
    parser.add_argument("--seqsize", help="Max sequence numbers", default=30, type=int)
    parser.add_argument("--sendport", help='Port to send the data', default=8989, type=int)
    parser.add_argument('--ackport', help="Port to receive ACKs", default=9090, type=int)
    args = parser.parse_args()
    main(args.ip, args.filename, args.window, args.packsize, args.seqsize, args.sendport, args.ackport)
