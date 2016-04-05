'''
Created on Oct 1, 2012

@author: gardnerga

@summary: Parse MARS pharmacy reports, output to CSV
'''

import mmap
from optparse import OptionParser
import sys
import time
import re

def parse_date(dateStr):
        year = dateStr[:4]
        month = dateStr[4:6]
        day = dateStr[6:]
        return "{0}/{1}/{2}".format(month, day, year)

class NonparsedPharmLine(object):
    
    SEP = "|"
    
    def __init__(self, data):
        split = data.split()
        self.data = " ".join(split[1:])
        
    def __str__(self):
        return self.data
    
    def add_data(self, data):
        self.__init__(data)
    
    def get_attrs(self):
        return [self.data]   
                 
class ParsedPharmLine(NonparsedPharmLine):
    
    def __init__(self, data):
        super(ParsedPharmLine, self).__init__(data)
        num = self.__class__.NUMATTRS
        for i, s in enumerate(data.split()):
            if i > 0:
                if i > num:
                    self.set_attr_num(i, self.get_attr_num(num) + s)
                else:
                    self.set_attr_num(i, s)
        self._clean()
                        
    
    def _clean(self):
        for i in xrange(1,self.__class__.NUMATTRS+1):
            try:
                self.get_attr_num(i)
            except AttributeError:
                self.set_attr_num(i, "")
    
    def get_attr_num(self, num):
        return getattr(self, "data{0}".format(num))
    
    def get_attrs(self):
        attrs = []
        for i in xrange(1,self.__class__.NUMATTRS+1):
            attrs.append(self.get_attr_num(i))
        return attrs
    
    def set_attr_num(self, num, val):
        setattr(self, "data{0}".format(num), val)
    
    def __str__(self):
        try:
            return ParsedPharmLine.SEP.join(self.get_attrs())
        except AttributeError:
            return super(ParsedPharmLine, self).__str__()
                
class ORD1(ParsedPharmLine):
    
    NUMATTRS = 10
    
    def __init__(self, data):
        super(ORD1, self).__init__(data)
        self._modify_dates()
        
    def _modify_dates(self):
        for i in [2,4]:
            self.set_attr_num(i,parse_date(self.get_attr_num(i)))
        
class DOC2(NonparsedPharmLine):
    
    NUMATTRS = 1
    
    def __init__(self, data):
        super(DOC2, self).__init__(data)
        
class OCN3(NonparsedPharmLine):
    
    NUMATTRS = 1
    
    def __init__(self, data):
        super(OCN3, self).__init__(data)
        
    def add_data(self, data):
        split = data.split()
        self.data += "\n" + " ".join(split[1:])
  
class COM4(ParsedPharmLine):
    
    NUMATTRS = 4
    
    def __init__(self, data):
        super(COM4, self).__init__(data)

class COM5(ParsedPharmLine):
    
    NUMATTRS = 6
    ALPHACONVERSION = ['A', 'B', 'C', 'D', 'E', 'F']
    
    def __init__(self, data):
        super(COM5, self).__init__(data)
        
    def _clean(self):
        currentVals = []
        for i in xrange(1, COM5.NUMATTRS+1):
            try:
                val = self.get_attr_num(i)
                currentVals.append(val)
            except AttributeError:
                pass
        for val in currentVals:
            self.set_attr_num(COM5.ALPHACONVERSION.index(val[0])+1, val)
        for i in xrange(1, COM5.NUMATTRS+1):
            try:
                val = self.get_attr_num(i)
                if val[0] != COM5.ALPHACONVERSION[i-1]:
                    self.set_attr_num(i, "")
            except AttributeError:
                self.set_attr_num(i, "")

class ReportParser(object):
    
    START = "1ORD"
    PHARMATTRS = ["ORD1", "DOC2", "OCN3", "COM4", "COM5"]
    headers = ["1ORD", "2DOC", "3OCN", "4COM", "5COM"]
    SOH = "S_O_H"
    EOH = "E_O_H"
    EOR = "E_O_R"
    SEP = "|"
    
    def __init__(self, filename, atOnce=False, outfile=None):
        self.filename = filename
        if atOnce:
            if outfile is None:
                print "Please specify an output filename to parse the file while it's read"
                sys.exit(1)
            else:
                self.parse_at_once(outfile)
        else:
            self.pharmObjects = self.get_records()
        
    def _check_pharm_objects(self):
        print "Total Records: {0}".format(len(self.pharmObjects))
        counts = [0,0,0,0,0]
        coms = [0,0]
        for pharmObject in self.pharmObjects:
            com4, com5 = 0,0
            for i, attr in enumerate(ReportParser.PHARMATTRS):
                if not hasattr(pharmObject, attr):
                    counts[i] += 1
            if hasattr(pharmObject, "COM4"):
                com4 = len(pharmObject.COM4)
                coms[0] += com4
            if hasattr(pharmObject, "COM5"):
                com5 = len(pharmObject.COM5)
                coms[1] += com5
            if com4 != com5:
                print pharmObject.ORD1
        print counts
        print coms
    
    def get_header(self):
        max4coms = 0
        for obj in self.pharmObjects:
            if hasattr(obj, 'COM4'):
                com4 = len(obj.COM4)
                if com4 > max4coms:
                    max4coms = com4
            else:
                print "Warning: the following record did not contain all required attributes (i.e. 2DOC, 4COM, etc.):" + str(obj)
        
        
        comString = ReportParser.SEP.join("4COM" for x in xrange(COM4.NUMATTRS)) + ReportParser.SEP + ReportParser.SEP.join("5COM" for x in xrange(COM5.NUMATTRS))
        header = ReportParser.SEP.join(["MRN","ADMISSION_DATE","DISCHARGE_DATE"]) + ReportParser.SEP
        header += self.get_header_piece("1ORD", ORD1.NUMATTRS) + ReportParser.SEP
        header += self.get_header_piece("2DOC", DOC2.NUMATTRS) + ReportParser.SEP
        header += self.get_header_piece(comString, max4coms)
            
#        for attr in ReportParser.PHARMATTRS:
#            name = attr[-1] + attr[:-1]
#            if header:
#                header += "," + ",".join(name for x in xrange(getattr(sys.modules[__name__], attr).NUMATTRS))
#            else:
#                header += ",".join(name for x in xrange(getattr(sys.modules[__name__], attr).NUMATTRS))
        return self.make_header_unique(header)
    
    def get_header_at_once(self):
        header = ReportParser.SEP.join(["MRN","ADMISSION_DATE","DISCHARGE_DATE"]) + ReportParser.SEP
        header += self.get_header_piece("1ORD", ORD1.NUMATTRS) + ReportParser.SEP
        header += self.get_header_piece("2DOC", DOC2.NUMATTRS) + ReportParser.SEP
        header += self.get_header_piece("4COM", COM4.NUMATTRS) + ReportParser.SEP
        header += self.get_header_piece("5COM", COM5.NUMATTRS)
        return self.make_header_unique(header)
    
    def get_header_piece(self, name, num):
        return ReportParser.SEP.join(name for x in xrange(num))
    
    def get_header_vars(self, header):
        split = header.split("|")
        mrn = split[11].split()[0]
        admitDate = parse_date(split[3])
        dischargeDate = parse_date(split[26])
        return mrn, admitDate, dischargeDate
    
    def get_records(self):
        records = []
        fread = open(self.filename, 'r+')
        buf = mmap.mmap(fread.fileno(), 0)
        readline = buf.readline
        data = ""
        sectionFlags = [False, False, False]
        while True:
            line = readline()
            if line:
                if line.startswith(ReportParser.SOH):
                    sectionFlags = [True, False, False]
                    continue
                elif line.startswith(ReportParser.EOH):
                    sectionFlags = [False, True, False]
                    continue
                elif line.startswith(ReportParser.EOR):
                    sectionFlags = [False, False, True]
                    continue
                if sectionFlags[0]:
                    mrn, admitDate, dischargeDate = self.get_header_vars(line)
                elif sectionFlags[1]:
                    if line.strip():
                        data += line
                    else:
                        if data:
                            records.append(PharmData(mrn, admitDate, dischargeDate, data.strip()))
                            data = ""
                elif sectionFlags[2]:
                    data = ""
            else:
                break
        fread.close()
        return records
    
    def make_header_unique(self, header):
        counts = {}
        header = header.split(ReportParser.SEP)
        for i in xrange(len(header)):
            if header[i] in ReportParser.headers:
                if header[i] in counts:
                    counts[header[i]] += 1
                else:
                    counts[header[i]] = 1
                header[i] = header[i] + str(counts[header[i]])
        return ReportParser.SEP.join(header)
    
    def parse_at_once(self, outfile):
        """Lower memory footprint by parsing each record as it is read, writing it, and reusing
        memory for the next record"""
        records = []
        fread = open(self.filename, 'r+')
        buf = mmap.mmap(fread.fileno(), 0)
        readline = buf.readline
        data = ""
        sectionFlags = [False, False, False]
        max4coms = 0
        fwrite = open(outfile, 'w')
        fwrite.write(self.get_header_at_once() + "\n")
        while True:
            line = readline()
            if line:
                if line.startswith(ReportParser.SOH):
                    sectionFlags = [True, False, False]
                    continue
                elif line.startswith(ReportParser.EOH):
                    sectionFlags = [False, True, False]
                    continue
                elif line.startswith(ReportParser.EOR):
                    sectionFlags = [False, False, True]
                    continue
                if sectionFlags[0]:
                    mrn, admitDate, dischargeDate = self.get_header_vars(line)
                elif sectionFlags[1]:
                    if line.strip():
                        data += line
                    else:
                        if data:
                            fwrite.write(str(PharmData(mrn, admitDate, dischargeDate, data.strip())) + "\n")
                            data = ""
                elif sectionFlags[2]:
                    data = ""
            else:
                break
        fread.close()
        fwrite.close()
        return records
    
    def write_records(self, filename):
        fwrite = open(filename, 'w')
        fwrite.write(self.get_header() + "\n")
        for pharmObject in self.pharmObjects:
            fwrite.write(str(pharmObject))
            fwrite.write("\n")
        fwrite.close()
                    
        
class PharmData(object):
    
    PHARMATTRS = ["ORD1", "DOC2", "COM4", "COM5"]
    multipleLines = {'ORD1' : False, 'DOC2' : False, 'OCN3' : False, 'COM4' : True, 'COM5' : True}
    SEP = "|"
        
    def __init__(self, mrn, admitDate, dischargeDate, text):
        self.mrn = mrn
        self.admitDate = admitDate
        self.dischargeDate = dischargeDate
        self.text = text
        self.parse()
    
    def add_blanks(self, out, num):
        for i in xrange(num):
            out += PharmData.SEP
        return out
            
    def add_output(self, out, obj):
        if out:
            out += PharmData.SEP + str(obj)
        else:
            out += str(obj)
        return out
    
    def count_attr(self, attr):
        val = getattr(self, attr)
        if isinstance(val, list):
            return len(val)
        return 1
    
    def parse(self):
        for line in self.text.splitlines():
            if not line.isspace():
                data = line.split()
                attr = data[0][1:] + data[0][0]
                if PharmData.multipleLines[attr]:
                    try:
                        getattr(self, attr).append(getattr(sys.modules[__name__], attr)(line))
                    except AttributeError:
                        setattr(self, attr, [getattr(sys.modules[__name__], attr)(line)])
                else:
                    try:
                        getattr(self,attr).add_data(line)
                    except AttributeError:
                        setattr(self, attr, getattr(sys.modules[__name__], attr)(line))
                
    def __str__(self):
        out = PharmData.SEP.join([self.mrn, self.admitDate, self.dischargeDate])
        for attr in PharmData.PHARMATTRS[:-1]:
            try:
                lineObject = getattr(self, attr)
                if isinstance(lineObject, list):
                    for i, obj in enumerate(lineObject):
                        out = self.add_output(out, obj)
                        if isinstance(obj, COM4):
                            try:
                                out = self.add_output(out,self.COM5[i])
                            except (AttributeError, IndexError):
                                out = self.add_blanks(out, COM5.NUMATTRS)
                else:
                    out = self.add_output(out, lineObject)
            except AttributeError:
                out = self.add_blanks(out, getattr(sys.modules[__name__], attr).NUMATTRS)
        return out
            
def parse_options():
    parser = OptionParser()
    parser.add_option("-i", dest="inputfile", help="File to parse")
    parser.add_option("-o", dest="outputfile", help="Write output to file")
    parser.add_option("-m", dest="mode", action="store_true", default=False,
                      help="Use low memory mode with no data introspection (e.g. no formatted header)")
    (options, args) = parser.parse_args()
    errors = []
    if not options.inputfile:
        errors.append("You must specify an input file")
    if not options.outputfile:
        errors.append("You must specify an output file")
    if errors:
        for error in errors:
            print error
        parser.print_help()
        sys.exit(1)
    return options, args

def main():
    options, args = parse_options()
    start = time.time()
    if options.mode:
        ReportParser(options.inputfile, True, options.outputfile)
    else:
        reportParser = ReportParser(options.inputfile)
        reportParser.write_records(options.outputfile)
    print "Parsed file in {0} seconds".format(time.time()-start)

if __name__ == "__main__":
    main()
            
    
            
            
