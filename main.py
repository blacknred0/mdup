'''
Created on Feb 28, 2017

@contact: Irving Duran
@author: irving.duran@gmail.com
@summary: Collect and send via SMS your current month data usage.
'''

import os, time, re, smtplib, datetime, calendar, sys, math
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from pathlib import Path
from selenium import webdriver
from pyvirtualdisplay import Display

prog_path = os.path.dirname(os.path.realpath(sys.argv[0])) #get python file path
#os.chdir(prog_path) #get program path
conf = pd.read_table(prog_path + '/conf', sep='=', header=None) #store config file

#source http://stackoverflow.com/questions/29779155/converting-string-yyyy-mm-dd-into-datetime-python
def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12)
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year, month)[1])
    return datetime.date(year,month,day)

def email_msg(username, password, to, dta_msg):
    msg = """From: %s
    To: %s
    %s""" % (username, ", ".join(to), dta_msg)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(username, password)
    server.sendmail(username, to, msg)
    server.quit()
    print('Email sent!!!')

#source http://stackoverflow.com/questions/26454649/python-round-up-to-the-nearest-ten
def round10(x):
    return int(math.ceil(x / 10.0)) * 10

chromedvr = prog_path + '/' + sys.argv[1]
###############################################################################
#    Gather data from provider
###############################################################################
if sys.platform == "linux" or sys.platform == "linux2":
    #source http://stackoverflow.com/questions/26070834/how-to-fix-selenium-webdriverexception-the-browser-appears-to-have-exited-befor/34650348
    disp = Display(visible=0, size=(1024, 768))
    disp.start() #create virtual display
    os.environ["webdriver.chrome.driver"] = chromedvr
else:
    pass

print('Starting driver to gather data...')
dvr = webdriver.Chrome(chromedvr)  # create driver
dvr.get('http://www.mediacomtoday.com/usagemeter')
search_box = dvr.find_element_by_name('pf.username')
search_box.send_keys(conf.iloc[0][1])
search_box = dvr.find_element_by_name('pf.pass')
search_box.send_keys(conf.iloc[1][1])
time.sleep(5) # wait
search_box.submit()
time.sleep(5) # wait
cookie = dvr.get_cookies()
dvr.get('http://www.mediacomtoday.com/usagemeter/usagemeter.php')
html = dvr.page_source

# clean up data
print('Cleaning up data...')
used = re.search(r'(\d% used)|(\d\d% used)|(\d\d\d% used)', html).group(0) #pct. used
left = re.search(r'(\d% left)|(\d\d% left)|(\d\d\d% left)', html).group(0) #pct. left
daysleft = re.search(r'(with \d days remaining this month)|(with \d\d days remaining this month)', html).group(0) #days left in the month
dataused = re.search(r'(\d\d\d.\d GB of 400 GB used)|(\d\d\d GB of 400 GB used)', html).group(0) #data used
datesnap = re.search(r'(Data usage above as measured by Mediacom as of \d/\d\d/\d\d\d\d \d\d:\d\d)|(Data usage above as measured by Mediacom as of \d\d/\d\d/\d\d\d\d \d\d:\d\d)|(Data usage above as measured by Mediacom as of \d/\d/\d\d\d\d \d\d:\d\d)', html).group(0) #data snapshot
used = re.sub(r'[^0-9]', '', used)
left = re.sub(r'[^0-9]', '', left)
daysleft = re.sub(r'[^0-9]', '', daysleft)
dataused = re.sub(r'( GB of 400 GB used)', '', dataused)
datesnap = re.sub(r'(Data usage above as measured by Mediacom as of )', '', datesnap)

try: #try to started services
    print('An attempt to kill driver and display.')
    dvr.quit()
    disp.stop()
except Exception:
    pass

fp = Path(prog_path + "/isp.log")
comb = used + ',' + left + ',' + daysleft + ',' + dataused + ',' + datesnap + '\n'
# file exists append new data, else create headers and dump data
if fp.is_file():
    ###############################################################################
    #    Convert strings to date and check if there is a newer snapshot from Mediacom
    #    if there if new snapshot, continue, else quit
    ###############################################################################
    dt_datesnap = datetime.datetime.strptime(datesnap, '%d/%m/%Y %I:%M')
    last_dt_datesnap = datetime.datetime.strptime(pd.read_csv(prog_path + '/isp.log')['datesnap']
                                                  .tail(1).to_string(header=False, index=False),
                                                  '%d/%m/%Y %I:%M')
    if last_dt_datesnap >= dt_datesnap:
        print('No need to run, since latest version exist on the log file.')
        sys.exit(0)
    else:
        f = open(prog_path + "/isp.log", mode='a')
        f.write(comb)
        f.close()
        ###############################################################################
        #    Gather date information to align with reporting month
        ###############################################################################
        #source http://stackoverflow.com/questions/36155332/how-to-get-the-first-day-and-last-day-of-current-month-in-python
        today = str(datetime.date.today()) #return today's date as a string
        startdate = str(datetime.date(datetime.date.today().year,
                        datetime.date.today().month - 1, 11)) #return 11th of the previous month
        enddate = add_months(datetime.datetime(*[int(item) for item in startdate.split('-')]), 1).strftime("%Y-%m-%d")
        ###############################################################################
        #    Build prediction model using linear regression
        ###############################################################################
        df = pd.read_csv(prog_path + '/isp.log')
        df.replace(r'( \d:\d\d)|( \d\d:\d\d)', '', inplace=True, regex=True) #remove time
        df['datesnap'] = pd.to_datetime(df['datesnap'], format="%m/%d/%Y") #fix date issue
        df = df[df['datesnap'] >= startdate] #select records on the current month
        X = df.as_matrix(columns=['daysleft']) # current days
        y = df.as_matrix(columns=['dataused']) # data usage to predict
        model = LinearRegression()
        model.fit(X, y)
        # create and sort descending order for days left
        # then predict data usage based on days left on the month
        X_predict = np.arange(np.min(X)); X_predict = X_predict[::-1]
        X_predict = X_predict[:, np.newaxis] #transpose
        y_predict = model.predict(X_predict) #predict data usage
        #fc = np.concatenate((X_predict, y_predict), axis=1) #forecast
        # calculate the over usage based on 50GB blocks at $10 a piece.
        dta_msg = str('\n[Mediacom] there are ' + str(np.min(X)) + ' days left on the month ' +
                      'and you are projected to use ' + str(np.max(np.round(y_predict, decimals=1))) +
                      'GB. That is ~' + str(np.round(np.max(y_predict)-400, decimals=0).astype(int)) +
                      'GB or ~$' + str(round10(((np.max(y_predict)-400)/50) * 10)) +
                      ' over.')
        ###############################################################################
        #    Email the prediction results
        ###############################################################################
        username = conf.iloc[2][1]
        password = conf.iloc[3][1]
        to = sys.argv[2].split(sep=',')
        email_msg(username, password, to, dta_msg)
        print('DONE processing the whole thing.')
        sys.exit(0)
else:
    f = open(prog_path + "/isp.log", "w")
    f.write('used,left,daysleft,dataused,datesnap\n') #write header
    f.write(comb)
    f.close()
    print('Creating new file since it does not exist. Next run you should get a prediction.')
    sys.exit(0)
