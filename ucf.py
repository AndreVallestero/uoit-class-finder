import requests
from html.parser import HTMLParser
from datetime import datetime
import sys, getopt

def main(argv):

    apiParams = {
        "subject": "",
        "course": "dummy",
        "location": "UON",
        "day": curr_day().lower()
    }

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
            apiParams["subject"] = arg.upper()
        elif opt in ("-c", "--course"):
            apiParams["course"] = arg
        elif opt in ("-l", "--location"):
            apiParams["location"] = arg
        else:
            assert False, "unhandled option"

    if (apiParams["subject"] == ""):
        print("subject cannot be empty")
        sys.exit(2)

    url = "http://ssbp.mycampus.ca/prod_uoit/bwckschd.p_get_crse_unsec"
    reqPayload = "TRM=U&term_in=201901&sel_subj=dummy&sel_day=dummy&sel_schd=dummy&sel_insm=dummy&sel_camp=dummy&sel_levl=dummy&sel_sess=dummy&sel_instr=dummy&sel_ptrm=dummy&sel_attr=dummy&sel_subj={subject}&sel_crse=&sel_title=&sel_schd=LEC&sel_insm=CLS&sel_from_cred=&sel_to_cred=&sel_camp={location}&begin_hh=0&begin_mi=0&begin_ap=a&end_hh=0&end_mi=0&end_ap=a&sel_day={day}".format(**apiParams)
    response = requests.post(url, reqPayload)
    htmlData = response.content.decode("utf-8")

    print("Day: ", curr_day())

    parser = ScheduleParser()
    parser.feed(htmlData)

    #for debugging
    #with open("debug.html", "w") as outfile: # open in binary mode
    #    outfile.write(htmlData)

def curr_day():
    return ("M","T","W","R","F","S","U")[datetime.today().weekday()]

class ScheduleParser(HTMLParser):
    def __init__(self):
        self.headerScan = False
        self.timeSearch = False
        self.timeScan = False
        self.dayScan = False
        self.roomScan = False
        self.validDay = False
        self.timeRowCount = -1
        self.timeColumnCount = -1
        self.timeBuffer = ""
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
            print(courseData[2][1:len(courseData)+1], "-", courseData[0])
        elif (self.timeScan):
            self.timeBuffer = data
        elif (self.dayScan):
            if(data == curr_day()):
                print("\t", self.timeBuffer, end=' @ ')
                self.validDay = True
        elif (self.roomScan and self.validDay):
            print(data.split()[-1])

if __name__ == "__main__":
   main(sys.argv[1:])
