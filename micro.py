'''
Created on Oct 8, 2012

@author: gardnerga

@summary: Reformat a list of microbiology reports into spreadsheet/delimited format.  Parse lines to separate information.
'''

import mmap
import sys

SEP = "|"

def parse_date(dateStr):
    if len(dateStr) == 8:
        year = dateStr[:4]
        month = dateStr[4:6]
        day = dateStr[6:]
        return "{0}/{1}/{2}".format(month, day, year)
    else:
        raise ValueError("{0} does not appear to be a valid date".format(dateStr))
    
def parse_time(time):
    if not ":" in time:
        if len(time)==4:
            return ":".join([time[:2], time[2:]])
        else:
            raise ValueError("{0} does not appear to be a valid time".format(time))
    if len(time) == 5:
        return time
    else:
        raise ValueError("{0} does not appear to be a valid time".format(time))

class NonparsedLine(object):
    
    def __init__(self, line):
        if isinstance(line, ORG):
            self.data = {'ORG':[line]}
        else:
            data = line.split(": ", 1)[1].split(None, 1)
            attr = data[0].replace(":", "")
            val = data[1].strip()
            self.data = {attr : val}
        
    def add_data(self, line):
        data = line.split(": ", 1)[1].split(None, 1)
        if len(data) == 1:
            data.append("")
        self.data.update({data[0].replace(":", "") : data[1].strip()})
    
    def add_org(self, org):
        if 'ORG' in self.data:
            self.data['ORG'].append(org)
        else:
            self.data['ORG'] = [org]
    
    def __str__(self):
        out = []
        for k,v in self.data.items():
            out.extend([k,v])
        return SEP.join(out)

class ParsedLine(object):
    
    def __init__(self, line):
        data = line.split(": ", 1)[1]
        for i, d in enumerate(data.split()):
            self.set_attr_num(i+1, d)
        self._clean()
    
    def _clean(self):
        self.set_attr_num(2, parse_date(self.get_attr_num(2)))
        self.set_attr_num(3, parse_time(self.get_attr_num(3)))
    
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
        return SEP.join(self.get_attrs())

class ACC(ParsedLine):
    
    NUMATTRS = 6
    
    def __init__(self, line):
        super(ACC, self).__init__(line)
        
class BAT(ParsedLine):
    
    NUMATTRS = 4
    
    def __init__(self, line):
        super(BAT, self).__init__(line)
        
class DAT(NonparsedLine):
    def __init__(self, line):
        super(DAT, self).__init__(line)
        
class TXT(NonparsedLine):
    def __init__(self, line):
        super(TXT, self).__init__(line)

class ORG(object):
    def __init__(self, line):
        self.data = {'ORG' : " ".join(line.split()[2:])}
        
    def add_attr(self, line):
        data = line.split()
        attr = data[1].replace(":", "").strip()
        val = " ".join(data[2:])
        self.data.update({attr : val})
        
    def __str__(self):
        return self.data['ORG']
         
class ReportParser(object):
    
    SOH = "S_O_H"
    EOH = "E_O_H"
    EOR = "E_O_R"
    SEP = "|"
    
    def __init__(self, filename):
        self.filename = filename
        self.records = self.get_records(filename)
        self.numOrgs, self.orgattrs = self._inspect_orgs()
        self._inspect_reports()
        
    def get_header_vars(self, header):
        split = header.split("|")
        mrn = split[1].split()[0]
        datetime = [x.strip() for x in split[3].split()]
        print datetime
        date = parse_date(datetime[0])
        time = parse_time(datetime[1])
        return mrn, date, time
    
    def get_header(self):
        return SEP.join(self.structure) 
    
    def get_records(self, filename):
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
                    mrn, date, time = self.get_header_vars(line)
                elif sectionFlags[1]:
                    if line.strip():
                        data += line
                    else:
                        if data:
                            records.append(uBioReport(mrn, date, time, data.strip()))
                            data = ""
                elif sectionFlags[2]:
                    data = ""
            else:
                break
        fread.close()
        return records
    
    def _inspect_orgs(self):
        orgattrs = set()
        num = 0
        for report in self.records:
            if 'ORG' in report.DAT.data:
                orgData = report.DAT.data['ORG']
                orgCount = len(orgData)
                num = num if orgCount < num else orgCount
                for org in orgData:
                    orgattrs.update(org.data.keys())
        return num, orgattrs
    
    def _inspect_reports(self):
        self.structure = ["MRN", "DATE", "TIME"]
        for CLS in [ACC, BAT]:
            for i in xrange(1, CLS.NUMATTRS+1):
                self.structure.append("{0}{1}".format(CLS.__name__, i))
        for report in self.records:
            dat = report.DAT
            for type in dat.data:
                if type=='ORG' or type in self.orgattrs:
                    continue
                datField = "DAT_{0}".format(type)
                if datField not in self.structure:
                    self.structure.extend([datField, "TXT_{0}".format(type)])
        orgattrs = sorted(list(self.orgattrs))
        orgattrs.remove('ORG')
        orgattrs = ['ORG'] + orgattrs
        for i in xrange(0, self.numOrgs):
            for attr in orgattrs:
                self.structure.extend(["DAT_{0}{1}".format(attr, i+1), "TXT_{0}{1}".format(attr, i+1)])
                    
    def write_reports(self, filename):
        fwrite = open(filename, 'w')
        fwrite.write(self.get_header() + "\n")
        for report in self.records:
            entry = []
            types = []
            for attr in self.structure:
                if "_" in attr:
                    type, subtype = attr.split("_")
                    try:
                        entry.append(getattr(report, type).data[subtype])
                    except KeyError:
                        try:
                            subtype, num = subtype[:-1], subtype[-1]
                            entry.append(getattr(report, type).data['ORG'][int(num)-1].data[subtype])
                        except (KeyError, ValueError, IndexError):
                            entry.append("")
                else:
                    try:
                        entry.append(str(getattr(report, attr)))
                    except AttributeError:
                        type, num = attr[:-1], attr[-1]
                        if type not in types:
                            entry.append(str(getattr(report, type)))
                            types.append(type)
            fwrite.write(SEP.join(entry) + "\n")
        fwrite.close()
            
            
    
class uBioReport(object):
    
    ATTRS = ["ACC", "BAT", "DAT", "TXT"]
    
    def __init__(self, mrn, date, time, report):
        self.MRN = mrn
        self.DATE = date
        self.TIME = time
        self.report = report
        self.parse()
        
    def parse(self):
        org = None
        for line in self.report.splitlines():
            type = line[:3]
            subtype = line.split()[1].replace(":","")
            if subtype == "ORG":
                org = ORG(line)
            try:
                if org:
                    if subtype == "ORG":
                        getattr(self, type).add_org(org)
                    else:
                        getattr(self, type).data['ORG'][-1].add_attr(line)
                else:
                    getattr(self,type).add_data(line)
            except AttributeError:
                if org:
                    setattr(self,type,getattr(sys.modules[__name__], type)(org))
                else:
                    setattr(self,type,getattr(sys.modules[__name__], type)(line))
                
    def __str__(self):
        out = [SEP.join([self.mrn, self.date, self.time])]
        for attr in uBioReport.ATTRS:
            out.append(str(getattr(self, attr)))
        return SEP.join(out)
    
if __name__ == "__main__":
    inputfile = "pilotcult.out"
    outfile = "pilotcult_parsed.pipe"
    reportParser = ReportParser(inputfile)
    reportParser.write_reports(outfile)
    
