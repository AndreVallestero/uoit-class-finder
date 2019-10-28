# for class in classes:
#   parser.feed(class)
#
# create parser.print()  // add print day to this function and remove from main
# create parser.sort()

import requests
from html.parser import HTMLParser
from datetime import datetime
import sys, getopt
import time

def main(argv):
    subjects = set(("SOFE", "CSCI", "ELEE"))
    if len(argv):
        subjects = set()

    apiParams = {
        "subject": "",
        "course": "dummy",
        "location": "UON",
        "day": curr_day().lower()
    }

    for i, arg in enumerate(argv):
        if not arg.startswith('-'):
            subjects.add(arg.upper())
        else:
            argv = argv[i:len(argv)+1]
            break

    try:
        opts, args = getopt.getopt(argv,  "h:s:c:l")
    except getopt.GetoptError:
        print('use "ucc.py -h" for manual')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("test.py -s <subject code>")
            sys.exit()
        elif opt in ("-s", "--subject"):
            splitSubjects = arg.split(',')
            for subject in splitSubjects:
                subjects.add(subject.upper())
        elif opt in ("-c", "--course"):
            apiParams["course"] = arg
        elif opt in ("-l", "--location"):
            apiParams["location"] = arg
        else:
            assert False, "unhandled option"

    if not len(subjects):
        print("subject cannot be empty")
        sys.exit(2)

    url = "http://ssbp.mycampus.ca/prod_uoit/bwckschd.p_get_crse_unsec"
    reqPayload = "TRM=U&term_in={termCode}&sel_subj=dummy&sel_day=dummy&sel_schd=dummy&sel_insm=dummy&sel_camp=dummy&sel_levl=dummy&sel_sess=dummy&sel_instr=dummy&sel_ptrm=dummy&sel_attr=dummy&sel_subj={subject}&sel_crse=&sel_title=&sel_schd=LEC&sel_insm=CLS&sel_from_cred=&sel_to_cred=&sel_camp={location}&begin_hh=0&begin_mi=0&begin_ap=a&end_hh=0&end_mi=0&end_ap=a&sel_day={day}"
    parser = ScheduleParser()
    
    now = datetime.now()
    termCode = now.year * 100 + (now.month - 1) // 4 * 4 + 1
    for subject in subjects:
        apiParams["termCode"] = termCode
        apiParams["subject"] = subject
        response = requests.post(url, reqPayload.format(**apiParams))
        with open("test.html", "wb+") as file:
            file.writelines(response)
        htmlData = response.content.decode("utf-8")
        parser.feed(htmlData)
        

    print("Subjects: ", ", ".join(subjects))
    parser.sort_schedule()
    parser.print_schedule()

    #for debugging
    #with open("debug.html", "w") as outfile: # open in binary mode
    #    outfile.write(htmlData)

def curr_day():
    return ("M","T","W","R","F","S","U")[datetime.today().weekday()]

class ScheduleParser(HTMLParser):
    def __init__(self):
        self.currDay = curr_day()

        self.headerScan = False
        self.timeSearch = False
        self.timeScan = False
        self.dayScan = False
        self.roomScan = False
        self.validDay = False
        self.timeRowCount = -1
        self.timeColumnCount = -1
        self.timeBuffer = ""

        self.schedule = []

        return super().__init__()

    def handle_starttag(self, tag, attrs):
        if (tag == "th" and ("class", "ddheader") in attrs):
            self.headerScan = True
        elif (tag == "table" and ("class", "bordertable") in attrs and ("summary", "This table lists the scheduled meeting times and assigned instructors for this class.") in attrs):
            self.timeSearch = True
            self.timeRowCount = -1
        elif (self.timeSearch and tag == "tr"):
            self.timeRowCount += 1
            self.timeColumnCount = -1
            self.validDay = False
        elif (self.timeSearch and self.timeRowCount > 0 and tag == "td"):
            self.timeColumnCount += 1
            if (self.timeColumnCount == 1):
                self.timeScan = True
            elif (self.timeColumnCount == 2):
                self.dayScan = True
            elif (self.timeColumnCount == 3):
                self.roomScan = True

    def handle_endtag(self, tag):
        if (tag == "th" and self.headerScan):
            self.headerScan = False
        elif (tag == "table" and self.timeSearch):
            self.timeSearch = False
        if (tag == "td"):
            if (self.timeScan):
                self.timeScan = False
            elif (self.dayScan):
                self.dayScan = False
            elif (self.roomScan):
                self.roomScan = False

    def handle_data(self, data):
        if (self.headerScan):
            courseData = data.split("-")
            #print(courseData)
            self.schedule.append(["{} - {}".format(courseData[2].strip(), courseData[0])])
        elif (self.timeScan):
            self.timeBuffer = data
        elif (self.dayScan):
            if(data == self.currDay):
                self.schedule[-1].append(self.timeBuffer)
                self.validDay = True
        elif (self.roomScan and self.validDay):
            self.schedule[-1].append(data)

    # DONT LOOK AT ME!, I'M UGLY!
    def sort_schedule(self):
        self.schedule = sorted(self.schedule, key=lambda timeSlot: time.mktime(time.strptime('00 ' + ' '.join(timeSlot[1].split()[3:5]), "%y %I:%M %p")))

    def print_schedule(self):
        print("Day: ", self.currDay)

        for timeSlot in self.schedule:
            print("{}\n\t{} @ {}".format(timeSlot[0], timeSlot[1], timeSlot[2]))

if __name__ == "__main__":
   main(sys.argv[1:])
