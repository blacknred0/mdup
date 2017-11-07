'''
Created on Feb 28, 2017

@contact: Irving Duran
@author: irving.duran@gmail.com
@summary: Collect and send via SMS your current month data usage.
'''

# TODO: Rewrite to accept one high-level argument (instead of two separate)
#       python scripts to be used an an input in crontab
import os
import datetime
import sys
import mdup
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from pathlib import Path

prog_path = os.path.dirname(os.path.realpath(sys.argv[0])) #get python file path
os.chdir(prog_path) #change working directory
conf = pd.read_table('conf', sep='=', header=None) #store config file

# TODO: Better way to extract results and storing it
used, left, daysleft, dataused, datesnap, startday, datacap = mdup.get_data(prog_path, conf)
comb = used + ',' + left + ',' + daysleft + ',' + dataused + ',' + datesnap + '\n'

fp = Path('isp.log')
# file exists append new data, else create headers and dump data
if fp.is_file():
    ###############################################################################
    #    Convert strings to date and check if there is a newer snapshot from Mediacom
    #    if there if new snapshot, continue, else quit
    ###############################################################################
    dt_datesnap = datetime.datetime.strptime(datesnap, '%m/%d/%Y %H:%M')
    last_dt_datesnap = datetime.datetime.strptime(pd.read_csv('isp.log')['datesnap']
                                                  .tail(1).to_string(header=False, index=False),
                                                  '%m/%d/%Y %H:%M')
    if last_dt_datesnap >= dt_datesnap:
        print('No need to dump new data since latest version exist on the log file.',
              '\nWill still continue and run prediction.')
        #mdup.kill(dvr, disp) #try to started services
        ###############################################################################
        #    Gather date information to align with reporting month
        ###############################################################################
        today = datetime.date.today() #return today's date as a string
        #source http://stackoverflow.com/questions/37396329/finding-first-day-of-the-month-in-python
        if today.day > startday:
            today += datetime.timedelta(1)
            startdate = str(today.replace(day=startday)) #return XXth of the previous month
        else:
            #source http://stackoverflow.com/questions/36155332/how-to-get-the-first-day-and-last-day-of-current-month-in-python
            startdate = str(datetime.date(today.year, today.month - 1, startday)) #return XXth of the previous month
        enddate = mdup.add_months(datetime.datetime(*[int(item) for item in startdate.split('-')]), 1).strftime("%Y-%m-%d")
        ###############################################################################
        #    Build prediction model using linear regression
        ###############################################################################
        df = pd.read_csv('isp.log')
        df.replace(r'( \d:\d\d)|( \d\d:\d\d)', '', inplace=True, regex=True) #remove time
        df['datesnap'] = pd.to_datetime(df['datesnap'], format="%m/%d/%Y") #fix date issue
        df = df[df['datesnap'] > startdate] #select records on the current month
        X = df.as_matrix(columns=['daysleft']) # current days
        y = df.as_matrix(columns=['dataused']) # data usage to predict
        model = LinearRegression()
        model.fit(X, y)
        # create and sort descending order for days left
        # then predict data usage based on days left on the month by excluding
        # day zero from the selection
        X_predict = np.arange(np.min(X)); X_predict = X_predict[:0:-1]
        X_predict = X_predict[:, np.newaxis] #transpose
        y_predict = model.predict(X_predict) #predict data usage
        #fc = np.concatenate((X_predict, y_predict), axis=1) #forecast
        # calculate the over usage based on 50GB blocks at $10 a piece.
        f_msg = str('\n[Mediacom] With ' + str(np.min(X)) + ' days left, ' +
                    'your current ' + dataused + 'GB and projected ' +
                    str(np.max(np.round(y_predict, decimals=1))) + 'GB data usage.')
        b_msg = str(' That is ~' + str(np.round(np.max(y_predict)-datacap, decimals=0).astype(int)) +
                    'GB or ~$' + str(mdup.round10(((np.max(y_predict)-datacap)/50) * 10)) +
                    ' over.')
        # if over usage data prediction is less than zero,
        # don't append prediction over usage
        dta_msg = str(f_msg +
                      '' if np.round(np.max(y_predict)-datacap, decimals=0).astype(int) < 0
                      else f_msg + b_msg)
        ###############################################################################
        #    Email the prediction results
        ###############################################################################
        username = conf.iloc[2][1]
        password = conf.iloc[3][1]
        to = sys.argv[2].split(sep=',')
        mdup.email_msg(username, password, to, dta_msg)
        #mdup.kill(dvr, disp) #try to started services
        print('DONE processing the whole thing.')
        sys.exit(0)
    else:
        f = open('isp.log', mode='a')
        f.write(comb)
        f.close()
        ###############################################################################
        #    Gather date information to align with reporting month
        ###############################################################################
        today = datetime.date.today()  # return today's date as a string
        #source http://stackoverflow.com/questions/37396329/finding-first-day-of-the-month-in-python
        if today.day > startday:
            today += datetime.timedelta(1)
            startdate = str(today.replace(day=startday)) #return XXth of the previous month
        else:
            #source http://stackoverflow.com/questions/36155332/how-to-get-the-first-day-and-last-day-of-current-month-in-python
            startdate = str(datetime.date(today.year, today.month - 1, startday)) #return XXth of the previous month
        enddate = mdup.add_months(datetime.datetime(*[int(item) for item in startdate.split('-')]), 1).strftime("%Y-%m-%d")
        ###############################################################################
        #    Build prediction model using linear regression
        ###############################################################################
        df = pd.read_csv('isp.log')
        df.replace(r'( \d:\d\d)|( \d\d:\d\d)', '', inplace=True, regex=True) #remove time
        df['datesnap'] = pd.to_datetime(df['datesnap'], format="%m/%d/%Y") #fix date issue
        df = df[df['datesnap'] > startdate] #select records on the current month
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
        f_msg = str('\n[Mediacom] With ' + str(np.min(X)) + ' days left, ' +
                    'your current ' + dataused + 'GB and projected ' +
                    str(np.max(np.round(y_predict, decimals=1))) + 'GB data usage.')
        b_msg = str(' That is ~' + str(np.round(np.max(y_predict)-datacap, decimals=0).astype(int)) +
                    'GB or ~$' + str(mdup.round10(((np.max(y_predict)-datacap)/50) * 10)) +
                    ' over.')
        # if over usage data prediction is less than zero,
        # don't append prediction over usage
        dta_msg = str(f_msg +
                      '' if np.round(np.max(y_predict)-datacap, decimals=0).astype(int) < 0
                      else f_msg + b_msg)
        ###############################################################################
        #    Email the prediction results
        ###############################################################################
        username = conf.iloc[2][1]
        password = conf.iloc[3][1]
        to = sys.argv[2].split(sep=',')
        mdup.email_msg(username, password, to, dta_msg)
        #mdup.kill(dvr, disp) #try to started services
        print('DONE processing the whole thing.')
        sys.exit(0)
else:
    f = open('isp.log', 'w')
    f.write('used,left,daysleft,dataused,datesnap\n') #write header
    f.write(comb)
    f.close()
    print('Creating new file since it does not exist. Next run you should get a prediction.')
    #mdup.kill(dvr, disp) #try to started services
    sys.exit(0)
