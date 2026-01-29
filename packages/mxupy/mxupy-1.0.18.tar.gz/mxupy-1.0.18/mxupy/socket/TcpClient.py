import socket
import time
import errno


class TcpClient:

    def __init__(this, host, port, maxBytes=4096, onReceive=None, onError=None, onClose=None):

        this.host = host
        this.port = port
        this.maxBytes = maxBytes
        this.onReceive = onReceive
        this.onError = onError
        this.onClose = onClose

        this.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        this.client.settimeout(30)

    def send(this, data):
        this.client.send(data.encode())

    def connect(this):
        this.client.connect((this.host, this.port))

    def receive(this):
        try:

            recvData = this.client.recv(this.maxBytes)

            if not recvData:
                if this.onClose is not None:
                    this.onClose()
            else:
                if this.onReceive is not None:
                    this.onReceive(recvData.decode())

        except socket.error as e:

            if this.onError is not None:
                this.onError(e)

    def close(this):
        this.client.close()
