"""Main function of  data gathering, cleanup and processing."""

import os
import platform
import sys
import re
import smtplib
import datetime
import calendar
import math
import time
from selenium import webdriver
from pyvirtualdisplay import Display

def get_data(proj_dir, conf):

    """
    Data gathering by activating Selenium with chromedriver.  This function also
    grabs configuration file from host along with executing whether is on
    docker or not.
    source (http://stackoverflow.com/questions/26070834/\
    how-to-fix-selenium-webdriverexception-the-browser-\
    appears-to-have-exited-befor/34650348)

    Arguments:
    proj_dir = get current python code main execution location
    conf = import username and password from config file
    """
    ###############################################################################
    #    Gather data from provider
    ###############################################################################
    if sys.platform == 'darwin':
        chromedvr = proj_dir + '/chromedriver_mac'
        display = ''
    elif sys.platform.startswith('linux'):
        chromedvr = proj_dir + '/chromedriver_linux64'
        display = ''
        # check that is running on docker image
        os.environ['PWD'] = '/src/mdup'
        if 'DISPLAY' in os.environ and os.environ['PWD'] == '/src/mdup':
            display = Display(visible=0, size=(1024, 768))
            display.start()  # create virtual display
            os.environ["webdriver.chrome.driver"] = chromedvr
        else:
            try:
                os.environ['DISPLAY'] = ':99'
                display = Display(visible=0, size=(1024, 768))
                display.start()  # create virtual display
                os.environ["webdriver.chrome.driver"] = chromedvr
            except Exception as e:
                print('Need to install Xvfb or something is wrong with the',
                      'docker image. \nIn Ubuntu you can do ->',
                      '`apt -y install xvfb` to successfully create virtual\n',
                      'display for selenium.\n')
    else:
        sys.exit('OS Not supported or recognized')
    print('Starting driver to gather data...')
    driver = webdriver.Chrome(chromedvr)  # create driver
    driver.get('http://www.mediacomtoday.com/usagemeter')
    search_box = driver.find_element_by_name('pf.username')
    search_box.send_keys(conf.iloc[0][1])
    search_box = driver.find_element_by_name('pf.pass')
    search_box.send_keys(conf.iloc[1][1])
    search_box.submit()
    time.sleep(5)  # wait
    # cookie = driver.get_cookies()
    driver.get('http://www.mediacomtoday.com/usagemeter/usagemeter.php')
    html = driver.page_source
    try:  # clean up data, if fails, quit
        print('Cleaning up data...')
        used, left, daysleft, dataused, datesnap, startday, datacap = cln_structure(html)
        return(used, left, daysleft, dataused, datesnap, startday, datacap)
    finally:
        kill(driver, display) #kill started services

def cln_structure(txt):
    """
    Function cleans up HTML source by gathering key pieces of data to be logged
    and to be able to perform prediction.

    Arguments:
    txt = HTML source to be cleaned and parsed
    """
    used = re.search(r'(\d+(?:\.\d+)?% used)', txt).group(0) #pct. used
    left = re.search(r'(\d+(?:\.\d+)?% left)', txt).group(0) #pct. left
    daysleft = re.search(r'(with \d+(?:\d+)? days remaining this month)',
                         txt).group(0) #days left in the month
    dataused = re.search(r'(\d+(?:\.\d+)? GB of \d+(?:\d+) GB used)',
                         txt).group(0) #data used
    datesnap = re.search(r'(Data usage above as measured by Mediacom as of ' +
                         r'\d+(?:\d+)?/\d+(?:\d+)?/\d\d\d\d \d\d:\d\d)',
                         txt).group(0) #data snapshot
    startday = re.search(r'(<tspan x="100">[a-zA-Z]{3} \d, \d{4} -)|(<tspan x="100">[a-zA-Z]{3} \d{2}, \d{4} -)', txt).group(0) #start day of plan
    datacap = re.search(r'(\d+(?:\.\d+)? GB monthly usage allowance)', txt).group(0) #data cap
    used = re.sub(r'[^0-9]', '', used)
    left = re.sub(r'[^0-9]', '', left)
    daysleft = re.sub(r'[^0-9]', '', daysleft)
    dataused = re.sub(r'( GB of \d+(?:\d+) GB used)', '', dataused)
    datesnap = re.sub(r'(Data usage above as measured by Mediacom as of )',
                      '', datesnap)
    startday = int(re.sub(r'(<.*[a-zA-z] )|(,.*)', '', startday))
    datacap = int(re.sub(r'[^0-9]', '', datacap))

    return(used, left, daysleft, dataused, datesnap, startday, datacap)

def kill(driver, display):
    """
    With somewhat intelligence, kill Selenium driver and/or Xvfb display.
    This will depend on the OS that the application has been executed.

    Arguments:
    driver = Selenium driver
    display = Xvfb display
    """
    print('An attempt to kill driver.')
    driver.quit() #driver
    if isinstance(display, Display) is True:
        print('An attempt to kill display.')
        display.stop() #display
    else:
        print('Did not kill display since it did not exist.')

def add_months(sourcedate, months):
    """
    Perform math in order to figure out what day of the month
    will the report end.

    Arguments:
    sourcedate = input the start date of your monthly report
    months = increase it by one month
    """
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12)
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])

    return datetime.date(year, month, day)

def email_msg(username, password, to_msg, dta_msg):
    """
    Send email status of predictions to phone number.

    Arguments:
    username = Gmail username from config file
    password = Gmail password from config file
    to_msg = phone number(s) to send message to
    dta_msg = what to say on the message
    """
    msg = """From: %s
    To: %s
    %s""" % (username, ", ".join(to_msg), dta_msg)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(username, password)
    server.sendmail(username, to_msg, msg)
    server.quit()
    print('Email sent!!!')

def round10(num_rnd):
    """
    Round to the nearest tenth.  This is specifically used to round up the
    dollar amount to pay extra on their bill.
    source (http://stackoverflow.com/questions/26454649/\
    python-round-up-to-the-nearest-ten)

    Arguments:
    num_rnd = input of Mediacom max prediction minus GB limit divided
    by monthly gig allocation/blocks
    """

    return int(math.ceil(num_rnd / 10.0)) * 10
