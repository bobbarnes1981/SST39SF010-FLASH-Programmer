import serial
import sys
import time

def helpScreen():
    print("Usage: prom <file>")
    print("Writes the binary content of <file> to FLASH.")
    print("All data is read back and verified.")
    print("Press Ctrl+C to exit.")

def getFirstComPort():
    return "/dev/ttyUSB0"

if __name__ == "__main__":
    # TODO: enable ANSI control sequences?
    print("\nSST39SF0x0A FLASH Programmer v0.0")
    print("Written by <author> 2024\n")
    if len(sys.argv) != 2:
        helpScreen()
        exit()
    print("o Loading image file... ", end='', flush=True)
    try:
        file = open(sys.argv[1], 'rb')
    except:
        print(f"\nERROR: Can't open file '{sys.argv[1]}'")
        exit()
    filebuf = file.read()
    file.close()
    bytesize = len(filebuf)
    print(f"{bytesize} bytes")
    print("o Opening serial port... ", end='', flush=True)
    port = getFirstComPort()
    com = serial.Serial(port, 115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
    time.sleep(3)
    print(f"{com.name}")
    print("o Looking for programmer... ", end='', flush=True)
    com.write(b'a')
    rec = com.read(1)
    if rec == b'A':
        print("OK")
        print("o Sending bytesize... ", end='', flush=True)
        com.write(bytes(str(bytesize), 'utf-8'))
        com.write(b'b')
        rec = 0
        recsize = 0
        while True:
            rec = com.read(1)
            if rec == b'B' or rec < b'0' or rec > b'9':
                break
            recsize = recsize * 10 + rec[0] - b'0'[0]
        if recsize == bytesize:
            print("OK")
            print("o Erasing FLASH... ", end='', flush=True)
            rec = com.read(1)
            if rec == b'C':
                print("OK")

                print("\r[Go Writing... ", end='', flush=True)
                pos=0
                oldper = -1
                while pos < bytesize:
                    chunk = 32; # max buffersize of Arduino UART is 64 bytes
                    if pos + chunk > bytesize:
                        chunk = bytesize - pos
                    com.write(filebuf[pos:pos+chunk])
                    pos += chunk
                    com.read(1)
                    per = int(100*(pos)/bytesize)
                    if per != oldper:
                        print(f"\r[Go Writing... {per}%", end='', flush=True)
                        oldper = per
                print(" OK")
                print("\r[Go Verifying...", end='', flush=True)
                nowticks = lastticks = time.time()
                errors = 0
                pos = 0
                oldper = -1
                while True:
                    nowticks = time.time()
                    rec = com.read(1)
                    if rec != filebuf[pos]:
                        errors+=1
                    pos+=1
                    lastticks = nowticks
                    per = int(100*(pos)/bytesize)
                    if per != oldper:
                        print(f"\r[Go Verifying... {per}%", end='', flush=True)
                        oldper = per
                    if nowticks - lastticks >= 1000 or pos >= bytesize:
                        break
                if pos == bytesize: # check for size mismatch
                    print(" OK\n")
                    if errors == 0:
                        print("SUCCESS")
                    else:
                        print(f"{errors} ERRORS")
                else:
                    print("\nERROR: File size mismatch.")
            else:
                print("\nERROR: Programmer can't erase FLASH.")
        else:
            print("\nERROR: Programmer doesn't confirm bytesize.")
    else:
        print("\nERROR: Programmer doesn't respond.")
    com.close()