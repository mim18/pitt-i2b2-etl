'''
 To run, simply pass the input file as the only parameter, for example:
    python cath.py cath_examples.txt
'''

import re
import sys

matches = dict()
matches['Enoxaparin'] = ['all']
matches['Lovenox'] = ['all']
matches['Bivalirudin'] = ['all']
matches['Angiomax'] = ['all']
matches['Eptifiatide'] = ['all']
matches['Integrilin'] = ['all']
matches['Unfractionated'] = ['all']
matches['Abciximab'] = ['all']
matches['Reopro'] = ['all']
matches['Smoker'] = ['all']
matches['Height'] = ['all']
matches['Weight'] = ['all']




#f = open("cathrpt_itemsneeded.txt");
#for line in f:
#    m = re.search("\\w*@@([A-Za-z_0-9]*)", line)
#    if m != None:
#        print "matches['" + m.group(1) +"'] = ['all']"

def isMatch(line):
    f = open("cathrpt_itemsneeded.txt")
    for masterSearchTerm in matches:
        m = re.search("^\\W*("+masterSearchTerm+")\\W", line, re.IGNORECASE)
        if m != None:
            for subSearchTerm in matches[masterSearchTerm]:
                if subSearchTerm == "all":
                    return 1
                else:
                    m2 = re.search(subSearchTerm, line, re.IGNORECASE)
                    if m2 != None:
                       return 1
    return 0

f = open(sys.argv[1])
reading_header = 0
reading_body = 0
header = ""
for line in f:
    if line.__contains__("S_O_H"):
        header = ""
        reading_body = 0
        reading_header = 1
    elif line.__contains__("E_O_H"):
        reading_header = 0
        reading_body = 1
    elif line.__contains__("E_O_R"):
        reading_body = 0
    elif (reading_header):
        header = line.rstrip()


    if isMatch(line):
        print header + " | " + line.rstrip()

