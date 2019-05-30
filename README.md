# GoBackN_UDP_Assignment

Made by Dario Palma and Cristian Tamblay

## Prerequisites

 * Python3

## Running the code

First, start the server running
```shell
$ ./server 2 8989 9090 127.0.0.1
```

To start the client run (depending on your plaform)
```shell
$ python3 client.py
```
This will make the client query the *ip 127.0.0.1* and send the file *mandela.txt*, with a window size of 5, a package size of 30 bytes, maximum sequence numbers of 2, sending the data through *port 8989* and receiving acks through *port 9090*. You can type `$ python3 client.py -h` to get help.
In case you want to use custom values for a server running on other ip or ports, or for different package sizes, you can run (all parameters are optional and will use the default explained above):
```shell
$ python3 client.py --ip [IP] --filename [FILENAME] --window [WINDOW SIZE] --packsize [PACKAGE SIZE] --seqsize [MAX SEQNUM] --sendport [SEND PORT] --ackport [ACK PORT]
```

## Contact

In case of fire, git commit and send email to dpalma@dcc.uchile.cl and cristian.tamblay@ing.uchile.cl
