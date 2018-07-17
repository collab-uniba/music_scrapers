# coding=utf8
# -*- coding: utf8 -*-
import csv
import os
import subprocess
import signal
import re
import sys
from selenium import webdriver
import multiprocessing
import concurrent.futures
import Queue as queue

class CCMixterSong:
    def __init__(self, title, url, author, dateUpload, dateUpdate, isRemixed, featuring, samplesFrom, samplesIn, recommends, reviews):
        self.title = title
        self.url = url
        self.author = author
        self.dateUpload = dateUpload
        self.dateUpdate = dateUpdate
        self.isRemixed = isRemixed
        self.featuring = featuring
        self.samplesFrom = samplesFrom
        self.samplesIn = samplesIn
        self.recommends = recommends
        self.reviews = reviews

    def info(self):
        return self.title + " by " + self.author

    def toarray(self):
        return [self.title, self.url, self.author, self.dateUpload, self.dateUpdate, self.isRemixed, self.featuring, self.samplesFrom, self.samplesIn,
                self.recommends, self.reviews]

def get_thread_pool_executor():
    num_cpus = multiprocessing.cpu_count()
    return concurrent.futures.ThreadPoolExecutor(max_workers=num_cpus)

def phantom_js_clean_up():
    """Clean up Phantom JS.
    Kills all phantomjs instances, disregard of their origin.
    """
    processes = subprocess.Popen (['ps', '-A'], stdout=subprocess.PIPE)
    out, err = processes.communicate ()

    for line in out.splitlines ():
        if 'phantomjs' in line:
            pid = int (line.split (None, 1)[0])
            os.kill (pid, signal.SIGKILL)


def getTitle(link, driver1):
    driver1.get(link)
    if "/pools/" not in link:
        return (driver1.find_element_by_css_selector (".title").text + " by " + driver1.find_element_by_css_selector(".cc_breadcrumbs > a:nth-child(3) > span:nth-child(1)").text).encode('utf-8')
    else:
        return driver1.find_element_by_css_selector("span.cc_file_link").text.encode('utf-8') + " by " + \
               driver1.find_element_by_css_selector("#credit_info > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(2) > i:nth-child(1)").text.encode('utf-8')

def getNumReviews(link, driver1):
    driver1.get(link)
    if len(driver1.find_elements_by_css_selector(".upload_review_link"))>0:
        return driver1.find_element_by_css_selector(".upload_review_link").text

COUNT = 0
def increment():
    global COUNT
    COUNT = COUNT+1

def mining(url):
    # INSERT YOUR PATH TO PHANTOMJS EXECUTABLE
    driver = webdriver.PhantomJS (executable_path='/usr/local/bin/phantomjs',
                                  service_args=['--cookies-file=/tmp/cookies.txt'])


    try:
        driver.get (url)
        # time.sleep(2)

        # 	Title
        title = driver.find_element_by_css_selector (".title").text.encode('utf-8')
        # 	Author
        author = driver.find_element_by_css_selector (".cc_breadcrumbs > a:nth-child(3)")
        authorName = author.text.encode('utf-8')
        authorLink = author.get_attribute ("href")
        authorSet.add (authorLink)
        # 	Date of upload
        dateUpload = driver.find_element_by_css_selector ("#date_box").text.encode('utf-8')
        dateUpload = dateUpload[15:].replace (" @", "")
        # 	Date of last update (if present)
        dateUpdate = "-"
        if len (driver.find_elements_by_css_selector ("#modified_date")) > 0:
            dateUpdate = driver.find_element_by_css_selector ("#modified_date").text.encode('utf-8')
            dateUpdate = re.sub ("M\s.*$", "M", dateUpdate[20:]).replace (" @", "")
            dateUpload = re.sub ("M\s.*$", "M", dateUpload)
        # Remixed (Yes/No)
        remixed = False
        samplesFrom = "-"
        listaSampleFrom = list ()
        for k in range(1,5):
            if len(driver.find_elements_by_css_selector("#upload_sidebar_td > div:nth-child("+str(k)+") > h2:nth-child(2)")) > 0 \
                    and driver.find_element_by_css_selector("#upload_sidebar_td > div:nth-child("+str(k)+") > h2:nth-child(2)").text == "Uses samples from:":
                    remixed = True
                    for r in driver.find_element_by_css_selector ("#upload_sidebar_td > div:nth-child("+str(k)+")").find_elements_by_class_name("remix_links"):
                        link = r.get_attribute ("href")
                        if link.strip() != url.strip():
                            listaSampleFrom.append (link)
                            sampleSet.add (link)
                    break

        samplesIn = "-"
        listaSampleIn = list ()
        for k in range (1, 5):
            if len (driver.find_elements_by_css_selector ("#upload_sidebar_td > div:nth-child(" + str (k) + ") > h2:nth-child(2)")) > 0 \
                    and driver.find_element_by_css_selector ("#upload_sidebar_td > div:nth-child(" + str (
                        k) + ") > h2:nth-child(2)").text == "Samples are used in:":
                for r in driver.find_element_by_css_selector ("#upload_sidebar_td > div:nth-child(" + str (
                            k) + ")").find_elements_by_class_name ("remix_links"):
                        link = r.get_attribute ("href")
                        if link.strip () != url.strip ():
                            listaSampleIn.append (link)
                break

        # Featuring
        featuring = "-"
        if (driver.find_element_by_css_selector (
                "#credit_info > tbody:nth-child(1) > tr:nth-child(2) > th:nth-child(1)").text == "featuring"):
            featuring = driver.find_element_by_css_selector (
                "#credit_info > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(2)").text.encode('utf-8')
        # Recommends (likes)
        recommends = driver.find_element_by_xpath (
            "/html/body/div[3]/div[3]/div/div[2]/table/tbody/tr/td[2]/div[1]/table/tbody/tr/td/div/span").text.encode('utf-8')
        recommends = re.sub ("[()]", "", recommends)

        # Review
        reviews = 0

        if len(driver.find_element_by_css_selector("#requested_reviews").find_elements_by_class_name("cc_gen_button"))>0:
            reviews = getNumReviews(driver.find_element_by_css_selector("#requested_reviews").find_element_by_class_name("cc_gen_button").get_attribute("href"), driver)
            reviews = re.sub("[()]","", reviews)

        if len(listaSampleFrom) > 0:
            # listaTitoliSampleFrom = list ()
            # for samples in listaSampleFrom:
            #     listaTitoliSampleFrom.append (getTitle (samples, driver))
            samplesFrom = '\n'.join (listaSampleFrom)

        if len(listaSampleIn) > 0:
            # listaTitoliSampleIn = list ()
            # for samples in listaSampleIn:
            #     listaTitoliSampleIn.append (getTitle (samples, driver))
            samplesIn = '\n'.join (listaSampleIn)

        song = CCMixterSong(title, url, authorName, dateUpload, dateUpdate, remixed, featuring, samplesFrom, samplesIn, recommends, reviews)
        songQueue.put(song)
        increment()
        if(COUNT % 20 == 0):
            print COUNT

    except Exception as e:
        print e
        print "error at song: " + url
    finally:
        driver.close()
        driver.quit ()

songQueue = queue.Queue(0)
authorSet = set()
sampleSet = set()

def main():
    phantom_js_clean_up ()

    with open (sys.argv[1]) as in_f:
        urls = {line.rstrip () for line in in_f}

    #mining from CCMixter
    with get_thread_pool_executor() as pool_executor:
        for url in urls:
            pool_executor.submit(mining, url)

    #writing to files
    fileSong = open (sys.argv[2], 'wt')
    fileAuthor = open (sys.argv[3], "w")
    fileSample = open (sys.argv[4], "w")
    try:
        writer = csv.writer (fileSong, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow (('Title', 'URL', 'Author', 'dateUpload', 'dateUpdate', 'isRemixed', 'featuring', 'samplesFrom', 'samplesIn', 'recommends', 'reviews' ))
        songQueue.put("STOP")
        for song in iter (songQueue.get, "STOP"):
            writer.writerow(song.toarray())
        print 'Printed CSV output file'
        for auth in authorSet:
            fileAuthor.write (auth.encode('utf-8') + "\n")
        print 'Printed Author list'
        for samples in sampleSet:
            fileSample.write (samples + "\n")
        print 'Printed Samples list'
    finally:
        fileAuthor.close()
        fileSample.close()
        fileSong.close()
        in_f.close()

if __name__ == '__main__':
    main()
