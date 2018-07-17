# coding=utf8
# -*- coding: utf8 -*-
import csv
import os
import subprocess
import signal
import sys
from selenium import webdriver
import multiprocessing
import concurrent.futures
import queue

class CCMixterAuthor:
    def __init__(self, username, uploads, hasavatar, signupdate, remixdone, remixreceived, playlistwithauthor, forummsg, reviewleft, reviewreceived):
        self.username = username
        self.uploads = uploads
        self.hasavatar = hasavatar
        self.signupdate = signupdate
        self.remixdone = remixdone
        self.remixreceived = remixreceived
        self.playlistwithauthor = playlistwithauthor
        self.forummsg = forummsg
        self.reviewleft = reviewleft
        self.reviewreceived = reviewreceived

    def toarray(self):
        return [self.username, self.uploads, self.hasavatar, self.signupdate, self.remixdone, self.remixreceived, self.playlistwithauthor,
                    self.forummsg, self.reviewleft, self.reviewreceived]

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

COUNT = 0

def increment():
    global COUNT
    COUNT = COUNT+1

def mining(url):
    #INSERT YOUR PATH TO PHANTOMJS EXECUTABLE
    driver = webdriver.PhantomJS (executable_path='PATH TO phantomjs executable', service_args=['--cookies-file=/tmp/cookies.txt'])
    try:
        driver.get (url+"/uploads")
        # time.sleep(2)

        #  Number of uploads
        uploads = 0
        if len(driver.find_elements_by_css_selector(".page_viewing"))>0:
            uploads = driver.find_element_by_css_selector(".page_viewing").text.split("of ")[1]
        elif len(driver.find_elements_by_css_selector("#upload_listing"))>0:
            uploads = len(driver.find_elements_by_css_selector(".upload"))

        driver.get (url+"/profile")
        # Username
        username = driver.find_element_by_css_selector (".title").text.encode('utf-8')
        # HasAvatar
        hasavatar = False
        if len (driver.find_elements_by_css_selector("#avatar > img:nth-child(1)")) > 0:
            if driver.find_element_by_css_selector("#avatar > img:nth-child(1)").get_attribute("src") != "http://ccmixter.org/mixter-files/images/mixter-default.gif":
                hasavatar = True
        # 	Date of sign up
        signupdate = driver.find_element_by_css_selector("div.ufc:nth-child(3) > div:nth-child(2)").text[5:]
        # 	Number of remixes done
        remixStat = driver.find_element_by_css_selector("#user_num_remixes").text
        remixDoneTxt = remixStat.split (" and has ")[0]
        remixReceivedTxt = remixStat.split (" and has ")[1]
        if not " no " in remixDoneTxt:
           if "one" in remixDoneTxt:
                remixDone = 1
           else:
            remixDone = [int (s) for s in remixDoneTxt.split () if s.isdigit ()][-1]
        else:
            remixDone = 0
        # 	Number of remixes received
        if not "not " in remixReceivedTxt:
            if "once" in remixReceivedTxt:
                remixReceived = 1
            else:
                remixReceived = [int (s) for s in remixReceivedTxt.split () if s.isdigit ()][-1]
        else:
            remixReceived = 0
        # 	Number of playlists with author’s song
        playlists = 0
        if len(driver.find_elements_by_css_selector("div.ufc:nth-child(5)")) > 0:
            playlistText = driver.find_element_by_css_selector("div.ufc:nth-child(5)").text
            if "playlists" in playlistText:
                if "once" in playlistText:
                    playlists = 1
                else:
                    playlists = [int (s) for s in playlistText.split () if s.isdigit ()][-1]
        # 	Number of forum messages
        forumMsg = 0
        if len (driver.find_elements_by_css_selector ("#user_post_stats")) > 0:
            forumText = driver.find_element_by_css_selector ("#user_post_stats").text
            forumMsg = [int (s) for s in forumText.split () if s.isdigit ()][0]
        # 	Number of reviews left
        reviewLeft = 0
        reviewReceived = 0
        if len (driver.find_elements_by_css_selector("#user_review_stats")) > 0:
            reviewStat = driver.find_element_by_css_selector("#user_review_stats").text
            reviewLeftTxt = reviewStat.split (" and has ")[0]
            reviewReceivedTxt = reviewStat.split (" and has ")[1]
            if not " not " in reviewLeftTxt:
                reviewLeft = [int (s) for s in reviewLeftTxt.split () if s.isdigit ()][-1]
            # 	Number of reviews received
            if not "not " in reviewReceivedTxt:
                if not " once" in reviewReceivedTxt:
                    reviewReceived = [int (s) for s in reviewReceivedTxt.split () if s.isdigit ()][-1]
                else:
                    reviewReceived = 1

        author = CCMixterAuthor( username, uploads, hasavatar, signupdate, remixDone, remixReceived, playlists, forumMsg, reviewLeft, reviewReceived)
        authorQueue.put(author)
        increment()
        if(COUNT % 20 == 0):
            print COUNT

    except Exception as e:
        print e
        print "error at profile: " + url
    finally:
        driver.close()
        driver.quit ()

authorQueue = queue.Queue(0)
def main():

    phantom_js_clean_up ()

    with open (sys.argv[1]) as in_f:
        urls = {line.rstrip () for line in in_f}

    #mining from CCMixter
    with get_thread_pool_executor() as pool_executor:
        for url in urls:
            pool_executor.submit(mining, url)

    #writing to files
    fileauthor = open (sys.argv[2], 'wt')
    try:
        writer = csv.writer (fileauthor, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow (('Username', 'Uploads', 'HasAvatar', 'SignUpDate', 'remixDone', 'remixReceived', 'PlaylistsWithAuthor', 'forumMessage', 'reviewLeft', 'reviewReceived'))
        authorQueue.put("STOP")
        for author in iter (authorQueue.get, "STOP"):
            writer.writerow(author.toarray())
        print 'Printed CSV output file'
    finally:
        fileauthor.close()
        in_f.close()

if __name__ == '__main__':
    main()
