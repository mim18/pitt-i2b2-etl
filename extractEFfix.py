__author__ = 'jdl50'

import sys
import re


p = re.compile("(([A-Z][^><0-9\)\(]*))(?=((\d+.\d+\s*[a-z]*\s\([\w\.\- ]+\))|>?<? ?\d+[\-\d%\(]*\)))")

reading_header = 0
reading_body = 0
printed_header = 0
echo_section = 0
need_eor = 0
header = ""

with open(sys.argv[1]) as f:
    for line in f:
        if line.find("S_O_H") != -1:
            reading_header = 1
            header = ""
            echo_section = 0
        elif line.find("E_O_H") != -1:
            reading_header = 0
            reading_body = 1
        elif line.find("E_O_R") != -1:
            reading_body = 0
        else:
            if reading_header:
                header += line.strip()
            elif reading_body:
                if echo_section:
                    m = p.findall(line)
                    if m:
                        for i in m:
                            print header + i[0].strip().replace(":", "") + ": " + i[2].strip()
                            need_eor = 1
                else:
                    if line.upper().find("ECHOCARDIOGRAPHIC MEASUREMENTS") != -1:
                        echo_section = 1

