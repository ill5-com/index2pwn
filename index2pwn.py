import re
import requests
import threading
import random
from tqdm import tqdm
from bs4 import BeautifulSoup
from queue import Queue
import warnings
warnings.filterwarnings("ignore", message=".*")

numberOfThreads = 250
timeOut = 5
#interestingRegex = ( "passwd", "backup", "\.sql$", "c99\.php$", "shell\.php$", "\.csv$", "\.xsls$", "\.xls$", "\.doc$", "\.docx$", "\.vhd$" )
interestingRegex = ( "password", "wallet", "c99\.php$", "shell\.php$" )
#interestingRegex = re.compile("(wallet\.dat$|c99\.php$|shell\.php$)")

ipsToScan = Queue()

def GetSoupFromResponse(response):
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        return soup
    except Exception:
        pass

    return None

def GetResponseOfIP(ip):
    try:
        response = requests.get("http://" + ip, timeout=timeOut)
        return response
    except Exception:
        pass

    return None

def CheckIfNameIsInteresting(title):
    for regex in interestingRegex:
        if re.search(regex, title.lower()):
            return True
    
    return False
    
    #return re.search(interestingRegex, title.lower())

def GetFileNamesFromSoup(soup):
    names = []

    try:
        namesTable = soup.find("table")

        for a in namesTable.find_all('a'):
            names.append(a["href"])
    except Exception:
        pass

    return names

def QueueLoaderThread():
    global ipsToScan

    print("Started loader thread...")

    with open("ips.txt") as f:
        for line in f:
            ipsToScan.queue.insert(random.randint(0, len(ipsToScan.queue)), line.strip())

    return

def ThreadMain(threadId):
    global ipsToScan

    print("Started thread #", threadId, sep='')

    while ipsToScan.qsize() > 0:
        currentIp = ipsToScan.get()

        #print("DIALING:", currentIp)

        indexResponse = GetResponseOfIP(currentIp)
        if not indexResponse:
            #print("no indexResponse")
            continue

        if indexResponse.status_code != 200:
            #print("not 200")
            continue

        indexSoup = GetSoupFromResponse(indexResponse)
        if not indexSoup:
            #print("no soup")
            continue

        if not indexSoup.title or not indexSoup.title.string or "Index of" not in indexSoup.title.string:
            #print("no index")
            continue

        #print("INDEX AT", currentIp)

        fileNames = GetFileNamesFromSoup(indexSoup)

        for name in fileNames:
            if CheckIfNameIsInteresting(name):
                print("INTERESTING! -->", currentIp, '|', name)

    return

def Main():
    global ipsToScan

    print("Loading IPs into memory, please wait...")

    loaderThread = threading.Thread(target=QueueLoaderThread)
    loaderThread.start()

    print("Loaded, creating threads!")

    threads = []

    for i in range(numberOfThreads):
        threads.append(threading.Thread(target=ThreadMain, args=(i,)))

    print("Starting threads!")

    for thread in threads:
        thread.start()

    print("Waiting for threads to exit...")

    for thread in threads:
        thread.join()

    loaderThread.join()

    return

if __name__ == "__main__":
    Main()
