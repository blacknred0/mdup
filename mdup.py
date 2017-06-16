import os, platform, sys, re, smtplib, datetime, calendar, math, time
from selenium import webdriver
from pyvirtualdisplay import Display

def get_data(proj_dir, conf):
    ###############################################################################
    #    Gather data from provider
    ###############################################################################
    if sys.platform == 'darwin':
        chromedvr = proj_dir + '/chromedriver_mac'
        display = ''
    elif sys.platform.startswith('linux'):
        chromedvr = proj_dir + '/chromedriver_linux64'
        display = ''
        #source http://stackoverflow.com/questions/26070834/how-to-fix-selenium-webdriverexception-the-browser-appears-to-have-exited-befor/34650348
        if ('DISPLAY' in os.environ) == False | ('moby' in str(platform.uname())) == True:
            display = Display(visible=0, size=(1024, 768))
            display.start() #create virtual display
            os.environ["webdriver.chrome.driver"] = chromedvr
        elif ('DISPLAY' in os.environ) == False | ('moby' in str(platform.uname())) == False:
            display = Display(visible=0, size=(1024, 768))
            display.start() #create virtual display
            os.environ["webdriver.chrome.driver"] = chromedvr
        else:
            print('Need to install Xvfb or something is wrong with the docker image.',
                  '\nIn Ubuntu you can do -> `apt -y install xvfb`\n')
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
    time.sleep(5) # wait
    #cookie = driver.get_cookies()
    driver.get('http://www.mediacomtoday.com/usagemeter/usagemeter.php')
    html = driver.page_source
    try: # clean up data, if fails, quit
        print('Cleaning up data...')
        used, left, daysleft, dataused, datesnap = cln_structure(html)
        return(used, left, daysleft, dataused, datesnap)
    finally:
        kill(driver, display) #kill started services

def cln_structure(txt):
    used = re.search(r'(\d% used)|(\d\d% used)|(\d\d\d% used)', txt).group(0) #pct. used
    left = re.search(r'(\d% left)|(\d\d% left)|(\d\d\d% left)', txt).group(0) #pct. left
    daysleft = re.search(r'(with \d days remaining this month)|(with \d\d days remaining this month)', txt).group(0) #days left in the month
    dataused = re.search(r'(\d GB of 400 GB used)|(\d.\d GB of 400 GB used)|(\d\d.\d GB of 400 GB used)|(\d\d\d.\d GB of 400 GB used)|(\d\d GB of 400 GB used)|(\d\d\d GB of 400 GB used)', txt).group(0) #data used
    datesnap = re.search(r'(Data usage above as measured by Mediacom as of \d/\d\d/\d\d\d\d \d\d:\d\d)|(Data usage above as measured by Mediacom as of \d\d/\d\d/\d\d\d\d \d\d:\d\d)|(Data usage above as measured by Mediacom as of \d/\d/\d\d\d\d \d\d:\d\d)', txt).group(0) #data snapshot
    used = re.sub(r'[^0-9]', '', used)
    left = re.sub(r'[^0-9]', '', left)
    daysleft = re.sub(r'[^0-9]', '', daysleft)
    dataused = re.sub(r'( GB of 400 GB used)', '', dataused)
    datesnap = re.sub(r'(Data usage above as measured by Mediacom as of )', '', datesnap)

    return(used, left, daysleft, dataused, datesnap)

def kill(driver, display):
    print('An attempt to kill driver.')
    driver.quit() #driver
    if isinstance(display, Display) == True:
        print('An attempt to kill display.')
        display.stop() #display
    else:
        print('Did not kill display since it did not exist.')

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
