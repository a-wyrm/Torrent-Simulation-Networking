from socket import *
import os
import threading

save_path = "peer_chunks/"
# tracker
trackerPort = 12000
trackerIP = "127.0.0.1"

# send port
sendPort = 12003

# recieve port
recievePort = 12002
recieveIP = "127.0.0.1"

def requestMissing(id_list, socket):
    # get the list parts
    list_parts = getIdList()
    # for each item in id_list
    for file_name in id_list:
        # check if it is in local, if not request it by name; call requestFile
        if (file_name not in list_parts):
            requestFile(file_name, socket)


def sendFile():
    # The port we're running our server on
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', sendPort))
    serverSocket.listen(1)
    print("The server is ready to receive. ")

    recieveConnectionSocket, addr = serverSocket.accept()

    # server for recieving files
    while True:
        message = recieveConnectionSocket.recv(1024).decode()
        if "sendfile" in message:
            # isolate filename
            filename = message.split(" ")[1]
            print(f"Received: request for {filename} from the client.\n")
            # read file from local dir
            # RB = READ BYTES
            filepath = os.path.join(save_path, filename)
            file = open(filepath, 'rb')
            FILESIZE = os.path.getsize(filepath)
            f = file.read(FILESIZE)

            # serverSocket.send("filename " + filename)

            # send file to client
            recieveConnectionSocket.send(f)
            print("sent: " + filename)

        elif ("idlist" in message):
            parts_to_send = getIdList()
            ids = parts_to_send[0]
            for id in parts_to_send[1:]:
                ids += f",{id}"
            recieveConnectionSocket.send(ids.encode())
            print("sent: idlist")

        elif (message == "close"):
            # close connection
            serverSocket.close()
            break


# function to recieve a file to a client on an open socket

def requestFile(chunk_name, socket):

    request = f"sendfile {chunk_name}"
    print(f"Sending request for {chunk_name}.\n")
    # request filename from server
    socket.send(request.encode())
    # recieve file from server
    file = socket.recv(100000)
    # save file locally
    saveFile(chunk_name, file)
    print(f"Received {chunk_name}.\n")
    # write to summary file
    with open('summary_file.txt', 'a') as file:
        file.write(chunk_name + '\n')


def getFilesFromPair(filename, num_of_chunks):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((recieveIP, recievePort))
    while True:

        # get the id list
        clientSocket.send("idlist".encode())
        id_list = clientSocket.recv(100000).decode()
        id_list = id_list.split(",")
        print("chunk ID list received.\n")

        # call request_missing
        requestMissing(id_list, clientSocket)

        # check if all chunks are recieved, break while loop
        # num_of_chunks is the amount of chunks that the tracker sends out
        list_parts = os.listdir(save_path)
        if (len(list_parts) == num_of_chunks):
            clientSocket.send("close".encode())
            clientSocket.close()
            break

    # construct file
    assemChunks("new_" + filename, num_of_chunks)



def getIdList():
    # open summary file
    # read summary file by line into list
    with open('summary_file.txt') as file:
        list_parts = file.readlines()
        list_parts = [line.rstrip() for line in list_parts]

    #list_parts = os.listdir(save_path)
    # list_parts.sort(key=len)

    return (list_parts)


def saveFile(filename, file):
    with open(save_path + filename, "wb") as f:
        f.write(file)
    f.close()
    return f


# asks and receives chunks, then assembles the file


def assemChunks(filename, num_of_chunks):
    print("assembling chunks")
    # filepath = os.path.join(save_path, filename)

    with open(filename, "ab") as f:
        for chunk in range(num_of_chunks):
            chunkpath = os.path.join(
                save_path, ("chunk_" + str(chunk)))
            o = open(chunkpath, "rb")
            bytes_read = o.read()
            f.write(bytes_read)
            o.close()
        f.close()


def getFilename():
    fn = input("What is the name of the file? ")
    return fn


def get_file_from_tracker():

    mainSocket = socket(AF_INET, SOCK_STREAM)
    mainSocket.connect((trackerIP, trackerPort))

    req_main = "send port"
    # request a port# from server
    mainSocket.send(req_main.encode())
    # recieve port# from server
    peer_port = int(mainSocket.recv(1024).decode())
    # close initial conneciton
    mainSocket.close()
    # connect to new port
    peerSocket = socket(AF_INET, SOCK_STREAM)
    peerSocket.connect((trackerIP, peer_port))
    # request file
    req_peer = "send chunks"
    print("sent: " + req_peer)
    peerSocket.send(req_peer.encode())
    file_name = peerSocket.recv(1024).decode()
    print("file_name: ", file_name)

    # get chunk name and bits
    chunk_name = "chunk"
    while "chunk" in chunk_name:
        chunk_name = peerSocket.recv(1024)
        chunk_name = chunk_name.decode()

        if "chunk" not in chunk_name:
            break

        print("recieved: " + chunk_name)
        peerSocket.send("ok".encode())
        print("sent: ok")

        chunk = peerSocket.recv(10000)
        print("recieved data: " + chunk_name)
        # save chunk
        saveFile(chunk_name, chunk)
        with open('summary_file.txt', 'a') as the_file:
            the_file.write(chunk_name + '\n')

    total_chunks = chunk_name
    print("total chunks: ", total_chunks)
    # close connection
    peerSocket.close()
    return int(total_chunks), file_name


if __name__ == '__main__':
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    total_chunks, file_name = get_file_from_tracker()

    upload = threading.Thread(target=sendFile)
    download = threading.Thread(
        target=getFilesFromPair, args=[file_name, total_chunks])

    upload.start()
    input("press enter to start...")
    download.start()
