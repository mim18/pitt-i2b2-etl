import os
'''

Usage: ncats_parse.py <ini_filename> <report_filename> <output_filename>
   ex: ncats_parse.py ncats_parse.ini reports.txt output.txt
'''

__author__ = 'JDL50'

import ConfigParser
import sys
import re

LAB_TEST_REGEXS = 'lab_test_name_regexs'
OPTIONS = 'options'

SECTION_LAB_TEST = "LabTest"
SECTION_OPTIONS = "Options"
KEY_SEP = "|"

#this just needs to be random enough to not delete-overwrite anyone's files
TMP_FILE_PREFIX = "jdltempX7N9Acb"


def read_config(filename):
    config = ConfigParser.ConfigParser()
    config.read(filename)

    cfg_options = {LAB_TEST_REGEXS: {}, OPTIONS: {}}
    for regex in config.options(SECTION_LAB_TEST):
        cfg_options[LAB_TEST_REGEXS][regex] = config.get(SECTION_LAB_TEST, regex)

    for option in config.options(SECTION_OPTIONS):
        cfg_options[OPTIONS][option] = config.get(SECTION_OPTIONS, option)

    return cfg_options


def read_reports(cfg, filename):
    column_delimiter = cfg[OPTIONS]['column_delimiter'].decode("string_escape")
    max_page_size = cfg[OPTIONS]['max_page_size']

    cur_page = 1
    cur_page_size = 0
    page_file = open("a-" + TMP_FILE_PREFIX + str(cur_page), "w+")

    reading_header = 0
    reading_report = 0
    with open(filename) as f:
        for line in f:
            if 'S_O_H' in line:
                reading_header = 1
                head = ""
                continue

            elif 'E_O_H' in line:
                reading_header = 0
                reading_report = 1
                report = ""
                continue

            elif 'E_O_R' in line:
                print_columns = str(cfg[OPTIONS]["output_header_fields"]).split(",")
                header_cols = head.split("|")
                header = ""
                for col in print_columns:
                    if ":" in col:
                        subsplit_info = col.split(":")
                        for i in range(1, len(subsplit_info)):
                            header += header_cols[int(subsplit_info[0])].split()[int(subsplit_info[i])]
                            if (i+1 != len(subsplit_info)):
                                header += " "

                        header += "|"
                    else:
                        header += header_cols[int(col)] + "|"
                header = header[:-1]

                page_file, cur_page, cur_page_size = process_report(cfg, page_file, cur_page, cur_page_size,
                                                                    max_page_size, column_delimiter, header, report)
                reading_report = 0

            if reading_header:
                head += line.rstrip()

            if reading_report:
                report += line

    return cur_page


def process_report(cfg, page_file, cur_page, cur_page_size, max_page_size, column_delimiter, header, report):
    acc = "";
    bats = {}
    cur_bat_name = ""

    #key = MRN, Ascension_Number,Test Name, Collect_date, Collect_time, PQNO?!
    for line in iter(report.splitlines()):
        if line.startswith("ACC:"):
            acc = line
            acc_cols = line.split();
            acc_num = acc.split()[1]
        elif line.startswith("BAT:"):
            bat = line
            bat_cols = line.split()
            cur_bat_name = bat_cols[1]
            cur_bat_collect_date = bat_cols[2]
            cur_bat_collect_time = bat_cols[3]
            pqno = bat_cols[4]
            bats[cur_bat_name] = {}
            bats[cur_bat_name]['data'] = bat_cols
        elif line.startswith("DAT:"):
            dat = line
            dat_cols = line.split(",")
            cur_dat_name = line.split()[1]
            for regex in cfg[LAB_TEST_REGEXS]:
                pattern = cfg[LAB_TEST_REGEXS][regex]
                m = re.match(pattern, cur_dat_name)
                if m and len(m.group(0)) == len(cur_dat_name):
                    bats[cur_bat_name][cur_dat_name] = {}
                    bats[cur_bat_name][cur_dat_name]['data'] = dat
                    bats[cur_bat_name][cur_dat_name]['text'] = ""
                    bats[cur_bat_name][cur_dat_name][
                        'key'] = acc_num + cur_dat_name + cur_bat_collect_date + cur_bat_collect_time + KEY_SEP + pqno

        elif (line.startswith("TXT:") and cfg[OPTIONS]["include_txt_lines"] == '1'):
            cur_dat_name = line.split()[1]
            cur_dat_name = cur_dat_name[:-1]
            if cur_dat_name in bats[cur_bat_name]:
                bats[cur_bat_name][cur_dat_name]['text'] += line

    for bat in bats:
        for dat in bats[bat]:
            if dat != 'data':
                if cur_page_size == max_page_size:
                    page_file.close()
                    cur_page += 1
                    cur_page_size = 1
                    page_file = open("a-" + TMP_FILE_PREFIX + str(cur_page), "w+")
                else:
                    cur_page_size = cur_page_size + 1
                page_file.write(
                    #bats[bat][dat]['key'] + "@@@@@" + header + column_delimiter + acc + column_delimiter + bats[bat][
                    #    "data"] + column_delimiter + bats[bat][dat]['data'] + column_delimiter + bats[bat][dat][
                    #    'text'] + "\n");
                    bats[bat][dat]['key'] + "@@@@@" + header + column_delimiter)
                for counter, col in enumerate(acc_cols):
                    if (counter == len(acc_cols)-1):
                        page_file.write(col.split(";")[0] + column_delimiter + col.split(";")[1] + column_delimiter)
                    elif (counter != 0):
                        page_file.write(col + column_delimiter)

                for counter, col in enumerate(bats[bat]["data"]):
                    if counter != 0:
                        page_file.write(col + column_delimiter)


                test_name = str(bats[bat][dat]['data'])[4:].split()[0]
                test_name_loc = findnth(str(bats[bat][dat]['data']), test_name, 0)
                page_file.write(test_name + column_delimiter)
                for counter, col in enumerate(str(bats[bat][dat]['data'][test_name_loc + len(test_name):]).strip().split(",")):
                        page_file.write(col + column_delimiter)
                if counter < 4:
                    while counter < 4:
                        page_file.write(column_delimiter)
                        counter += 1

                if not bats[bat][dat]['text'] == "":
                    nd_colon = findnth(bats[bat][dat]['text'], ":", 1)
                    page_file.write(bats[bat][dat]['text'][nd_colon+1:].strip())
                page_file.write("\n");
    return page_file, cur_page, cur_page_size

def findnth(haystack, needle, n):
    parts= haystack.split(needle, n+1)
    if len(parts)<=n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)


def merge_sort(items):
    """ Implementation of mergesort """
    if len(items) > 1:

        mid = len(items) / 2        # Determine the midpoint and split
        left = items[0:mid]
        right = items[mid:]

        merge_sort(left)            # Sort left list in-place
        merge_sort(right)           # Sort right list in-place

        l, r = 0, 0
        for i in range(len(items)):     # Merging the left and right list
            lstring = left[l]
            rstring = right[r]
            lval = str(left[l]).split("@@@@@")[0] if l < len(left) else None
            rval = str(right[r]).split("@@@@@")[0] if r < len(right) else None

            if (lval and rval and lval < rval) or rval is None:
                items[i] = lstring
                l += 1
            elif (lval and rval and lval >= rval) or lval is None:
                items[i] = rstring
                r += 1
            else:
                raise Exception('Could not merge, sub arrays sizes do not match the main array')


def mergeSort(alist):
    if len(alist) > 1:
        mid = len(alist) // 2
        lefthalf = alist[:mid]
        righthalf = alist[mid:]

        lefthalf = mergeSort(lefthalf)
        righthalf = mergeSort(righthalf)
        return merge(lefthalf, righthalf)
    else:
        return alist


def merge(lefthalf, righthalf):
    alist = [""] * (len(lefthalf) + len(righthalf))

    i = 0
    j = 0
    k = 0
    while i < len(lefthalf) and j < len(righthalf):
        lefthalfval = str(lefthalf[i]).split("@@@@@")[0]
        righthalfval = str(righthalf[j]).split("@@@@@")[0]

        if lefthalfval < righthalfval:
            alist[k] = lefthalf[i]
            i = i + 1
        else:
            alist[k] = righthalf[j]
            j = j + 1
        k = k + 1

    while i < len(lefthalf):
        alist[k] = lefthalf[i]
        i = i + 1
        k = k + 1

    while j < len(righthalf):
        alist[k] = righthalf[j]
        j = j + 1
        k = k + 1

    return alist


def merge(lefthalf, righthalf):
    alist = [""] * (len(lefthalf) + len(righthalf))

    i = 0
    j = 0
    k = 0
    while i < len(lefthalf) and j < len(righthalf):
        lefthalfval = str(lefthalf[i]).split("@@@@@")[0]
        righthalfval = str(righthalf[j]).split("@@@@@")[0]

        if lefthalfval < righthalfval:
            alist[k] = lefthalf[i]
            i = i + 1
        else:
            alist[k] = righthalf[j]
            j = j + 1
        k = k + 1

    while i < len(lefthalf):
        alist[k] = lefthalf[i]
        i = i + 1
        k = k + 1

    while j < len(righthalf):
        alist[k] = righthalf[j]
        j = j + 1
        k = k + 1

    return alist


def sort_all_files(num_pages):
    for i in range(1, num_pages):
        f = open("a-" + TMP_FILE_PREFIX + str(i), "r+")
        list = []
        for line in f:
            list.append(line)
            list = mergeSort(list)
        f.close()
        f = open("a-" + TMP_FILE_PREFIX + str(i), "w+")
        for line in list:
            f.write(line)
        f.close()


def merge_files(f1, f2, output_filename):
    of = open(output_filename, "w+")

    usedLeft = 1
    usedRight = 1
    while True:
        if usedLeft:
            lefthalf = f1.readline()
        if usedRight:
            righthalf = f2.readline()
        if not lefthalf:
            break
        if not righthalf:
            break

        lefthalfval = lefthalf.split("@@@@@")[0]
        righthalfval = righthalf.split("@@@@@")[0]

        if lefthalfval < righthalfval:
            of.write(lefthalf)
            usedRight = 0
            usedLeft = 1
        else:
            of.write(righthalf)
            usedLeft = 0
            usedRight = 1

    while True:

        if not lefthalf:
            break
        of.write(lefthalf)
        lefthalf = f1.readline()

    while True:
        if not righthalf:
            break
        of.write(righthalf)
        righthalf = f2.readline()

    of.close()


def merge_all_files(num_pages):
    i = 1;
    on_a = 1
    a_or_b = "a-"
    exit = 0
    while True:
        num_files_found = 0
        while i <= num_pages:

            if on_a:
                output_filename = "b-"
            else:
                output_filename = "a-"

            fn1 = a_or_b + TMP_FILE_PREFIX + str(i)
            fn1_i = str(i)
            if os.path.isfile(fn1):
                num_files_found += 1
                while True:
                    if i > num_pages:
                        if (num_files_found > 1):
                            output_filename = output_filename + TMP_FILE_PREFIX + fn1_i
                            os.rename(fn1, output_filename)
                        else:
                            if os.path.exists(TMP_FILE_PREFIX + "sorted.txt"):
                                os.remove(TMP_FILE_PREFIX + "sorted.txt")
                            os.rename(fn1, TMP_FILE_PREFIX + "sorted.txt")
                            exit = 1
                        process = 0
                        break;

                    i = i + 1
                    fn2 = a_or_b + TMP_FILE_PREFIX + str(i)
                    if os.path.isfile(fn2):
                        process = 1
                        break

                if process:
                    f1 = open(fn1, "r+")
                    f2 = open(fn2, "r+")

                    output_filename = output_filename + TMP_FILE_PREFIX + str(fn1_i)
                    merge_files(f1, f2, output_filename)

                    f1.close()
                    f2.close()
                    os.remove(fn1)
                    os.remove(fn2)
            i = i + 1

        if not exit:
            i = 1;
            if on_a:
                on_a = 0
                a_or_b = "b-"
            else:
                on_a = 1
                a_or_b = "a-"
        else:
            break


def filter_out_old_tests(cfg, output_filename):
    print "Opening output file for writing: " + output_filename
    of = open(output_filename, "w+")
    delim = cfg[OPTIONS]['column_delimiter'].decode("string_escape")
    header_field_titles = cfg[OPTIONS]['header_field_titles'].split(",")
    for title in header_field_titles:
        of.write(title + delim)
    of.write("accession_number" +delim+ "rec_date" +delim+"rec_time" +delim+"acct#" +delim+"location" +delim+"docno" +delim+"hosp" +delim+"battery_name" +delim+"collect_date" +delim+"collect_time" +delim+"pqno" +delim+"test_name" +delim+"test_result" +delim+"test_units" +delim+"normal_range" +delim+"indicator" +delim+"status" +delim+"test_comment"+"\n")
    prev_key = None
    prev_pqno = None
    prev_data = None
    for line in open(TMP_FILE_PREFIX + "sorted.txt"):
        metadata = line.split("@@@@@")[0]
        data = line.split("@@@@@")[1]
        md_cols = metadata.split("|")
        key = md_cols[0]
        pqno = md_cols[1]
        #if (prev_key != None):
        #    print prev_key + " / " + key
        if not prev_key:
            prev_key = key
            prev_pqno = pqno
            prev_data = data
        else:
            if prev_key != key:

                of.write(prev_data)
                prev_key = key
                prev_pqno = pqno
                prev_data = data
            else:
                print "Excluding out-of-date test: " + prev_key + "@" + prev_pqno
                prev_key = key
                prev_pqno = pqno
                prev_data = data
    if prev_data:
        of.write(prev_data)

    os.remove(TMP_FILE_PREFIX + "sorted.txt")
    print "Output file written."


if len(sys.argv) != 4:
    print 'Usage: ncats_parse.py <ini_filename> <report_filename> <output_filename>'
    print 'No actions were performed.'
else:
    config_filename = sys.argv[1];
    report_filename = sys.argv[2];
    output_filename = sys.argv[3];

    cfg = read_config(config_filename)
    num_pages = read_reports(cfg, report_filename)
    sort_all_files(num_pages)
    merge_all_files(num_pages)
    filter_out_old_tests(cfg, output_filename)
