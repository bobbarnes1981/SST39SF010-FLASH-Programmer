import serial
import serial.tools.list_ports
import sys
import time

def helpScreen():
    print("Usage: prom.py <file>")
    print("Writes the binary content of <file> to FLASH.")
    print("All data is read back and verified.")
    print("Press Ctrl+C to exit.")

def getFirstComPort():
    for port in serial.tools.list_ports.comports():
        return f"/dev/{port.name}"
    return None

if __name__ == "__main__":
    # TODO: enable ANSI control sequences?
    print("\nSST39SF0x0A FLASH Programmer v2.1a")
    print("Written by C. Herting (slu4) 2023\n")
    print("Ported from C++ by R. Barnes 2024\n")
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
    com = serial.Serial(port, 115200, bytesize=8, parity='N', stopbits=1)
    # pyserial resets arduino with DTR, so wait for startup
    time.sleep(2)
    print(f"{com.name}")
    print("o Looking for programmer... ", end='', flush=True)
    com.write(b'a')
    rec = com.read(1)[0]
    if rec == ord('A'):
        print("OK")
        print("o Sending bytesize... ", end='', flush=True)
        com.write(bytes(str(bytesize), 'utf-8'))
        com.write(b'b')
        rec = 0
        recsize = 0
        while True:
            rec = com.read(1)[0]
            if rec == ord('B') or rec < ord('0') or rec > ord('9'):
                break
            recsize = recsize * 10 + rec - ord('0')
        if recsize == bytesize:
            print("OK")
            print("o Erasing FLASH... ", end='', flush=True)
            rec = com.read(1)[0]
            if rec == ord('C'):
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
                    com.read(1)[0]
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
                    rec = com.read(1)[0]
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

"""
------------------------------------------------------------------------------
This software is available under 2 licenses -- choose whichever you prefer.
------------------------------------------------------------------------------
ALTERNATIVE A - MIT License
Copyright (c) 2023 Carsten Herting
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
------------------------------------------------------------------------------
ALTERNATIVE B - Public Domain (www.unlicense.org)
This is free and unencumbered software released into the public domain.
Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.
In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
------------------------------------------------------------------------------
"""
