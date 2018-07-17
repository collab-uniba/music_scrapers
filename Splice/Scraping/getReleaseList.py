from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import csv
import os
import subprocess
import signal
import re
import sys
import multiprocessing
import concurrent.futures
import Queue as queue
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
# from pyvirtualdisplay import Display



def get_thread_pool_executor():
    num_cpus = multiprocessing.cpu_count()
    return concurrent.futures.ThreadPoolExecutor(max_workers=num_cpus)

COUNT = 0

def increment():
    global COUNT
    COUNT = COUNT + 1

releaseList = set()

def mining(url):
    # display = Display(visible=0, size=(1920, 1080)).start()
    options = Options()
    options.set_headless(headless=True)
    driver = webdriver.Firefox(firefox_options=options)
    try:
        driver.get("https://splice.com/" + (url.split(',')[0].replace('"', '')))
        delay = 3  # seconds
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.profile-sidebar-username')))

        for rel in driver.find_element_by_css_selector(".m-release-players").find_elements_by_tag_name("li"):
            releaseList.add(
                "https://splice.com" + rel.find_element_by_class_name("release-player-top-wrapper").get_attribute(
                    "href"))

        increment()
        if COUNT % 10 == 0:
            print COUNT

    except Exception as e:
        print e
        print "error at user: " + url
    finally:
        # display.stop()
        driver.quit()

songQueue = queue.Queue(0)

def main():
    with open (sys.argv[1]) as in_f:
        urls = {line.rstrip () for line in in_f}

    #mining from Splice
    with get_thread_pool_executor() as pool_executor:
        for url in urls:
            pool_executor.submit(mining, url)

    #writing to files
    fileSong = open (sys.argv[2], 'wt')
    try:
        writer = csv.writer (fileSong, csv.QUOTE_ALL)
        for song in releaseList:
            writer.writerow([song])
        print 'Printed CSV output file'
    finally:
        fileSong.close()
        in_f.close()

if __name__ == '__main__':
    main()
