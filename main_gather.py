'''
Created on Feb 28, 2017

@contact: Irving Duran
@author: irving.duran@gmail.com
@summary: Collect and send via SMS your current month data usage.
'''

import os, datetime, sys, mdup
import pandas as pd
from pathlib import Path

prog_path = os.path.dirname(os.path.realpath(sys.argv[0])) #get python file path
os.chdir(prog_path) #change working directory
conf = pd.read_table('conf', sep='=', header=None) #store config file

used, left, daysleft, dataused, datesnap = mdup.get_data(prog_path, conf)
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
        print('No need to run, since latest version exist on the log file.')
        #mdup.kill(dvr, disp) #try to started services
        sys.exit(0)
    else:
        f = open('isp.log', mode='a')
        f.write(comb)
        f.close()
        print('DONE processing the whole thing.')
        #mdup.kill(dvr, disp) #try to started services
        sys.exit(0)
else:
    f = open('isp.log', 'w')
    f.write('used,left,daysleft,dataused,datesnap\n') #write header
    f.write(comb)
    f.close()
    print('Creating new file since it does not exist. Next run you should get a prediction.')
    #mdup.kill(dvr, disp) #try to started services
    sys.exit(0)
