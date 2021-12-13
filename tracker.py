from socket import *
import threading
import os
import random
import math

save_path = "chunks/"
file_name = "Chapter_2_v8.1.zip"
CLIENT_NUM = 2


def break_file(file):
    num = 0
    with open(file, 'rb') as infile:
        chunk = infile.read(10000)
        while chunk:

            # We then open the save path and save the chunks as chunkn
            filename = os.path.join(save_path, ("chunk_" + str(num)))
            with open(filename, "wb") as f:
                f.write(chunk)
                f.close()
            num += 1
            chunk = infile.read(10000)
        infile.close()
        return num


def open_peer_connection(server_port, total_chunks, chunks):
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', server_port))
    serverSocket.listen(1)
    responseSocket, addr = serverSocket.accept()

    while True:
        response = responseSocket.recv(1024).decode()
        print("recieved: " + response)
        if response == "send chunks":
            responseSocket.send(file_name.encode())
            print("sent: filename=", file_name)
            for chunk_name in chunks:
                responseSocket.send(chunk_name.encode())  # sending "chunk_NUM"
                print("sent: ", chunk_name)
                ok = responseSocket.recv(1024)
                print("okrecv")
                with open(save_path + chunk_name, "rb") as f:
                    bytes_read = f.read()
                    responseSocket.send(bytes_read)  # sending chunk data
                    f.close()
                    print("sent data: ", chunk_name)
            responseSocket.send(str(total_chunks).encode())
            print("sent: total_chunks=", total_chunks)
            break
        responseSocket.close()


def tracker_main():
    serverPort = 12000
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen(1)

    print("The server is ready to receive.")

    num_chunks = break_file(file_name)

    cur_client = 0
    peers = []
    chunks = [f"chunk_{x}" for x in range(0, num_chunks)]
    random.shuffle(chunks)
    while cur_client < CLIENT_NUM:
        mainSocket, addr = serverSocket.accept()
        message = mainSocket.recv(10000).decode()

        if message == "send port":
            # recieve connection, reply with port #
            port = 12001 + cur_client
            mainSocket.send(str(port).encode())

            start_ind = cur_client*math.ceil(num_chunks/CLIENT_NUM)
            end_ind = min(
                start_ind + math.ceil(num_chunks/CLIENT_NUM), num_chunks)
            print()
            print("@@@@@@@@@@")
            print(start_ind, end_ind, len(chunks[start_ind:end_ind]))

            # open_peer_conn with sent port number
            peers.append(threading.Thread(target=open_peer_connection,
                                          args=(port, num_chunks, chunks[start_ind:end_ind])))

            peers[cur_client].start()
            cur_client += 1


if __name__ == '__main__':
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    main = threading.Thread(target=tracker_main)
    main.start()
# sdasda
