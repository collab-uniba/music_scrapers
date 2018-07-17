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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def getdate(s):
    if s.__contains__("hours"):
        n = int(s.replace(" hours ago", ""))
        return (datetime.now() - timedelta(hours=n)).strftime(("%d/%m/%Y"))
    elif s.__contains__("a day"):
        return (datetime.now() - timedelta(days=1)).strftime(("%d/%m/%Y"))
    elif s.__contains__("days"):
        n = int(s.replace(" days ago", ""))
        return (datetime.now() - timedelta(days=n)).strftime(("%d/%m/%Y"))
    elif s.__contains__("a month"):
        return (datetime.now() - timedelta(days=30)).strftime(("%d/%m/%Y"))
    elif s.__contains__("months"):
        n = int(s.replace(" months ago", ""))
        return (datetime.now() - timedelta(days=30 * n)).strftime(("%d/%m/%Y"))
    elif s.__contains__("a year"):
        return (datetime.now() - timedelta(days=365)).strftime(("%d/%m/%Y"))
    elif s.__contains__("years"):
        n = int(s.replace(" years ago", ""))
        return (datetime.now() - timedelta(days=365 * n)).strftime(("%d/%m/%Y"))
    else:
        return (datetime.now()).strftime(("%d/%m/%Y"))


class SpliceSong:
    def __init__(self, id, title, url, author, coauthor, isSpliced, plays, splices, relSplices, likes, date, comments):
        self.id = id
        self.title = title
        self.url = url
        self.author = author
        self.coauthor = coauthor
        self.isSpliced = isSpliced
        self.plays = plays
        self.splices = splices
        self.relSplices = relSplices
        self.likes = likes
        self.date = date
        self.comments = comments

    def info(self):
        return self.title + " by " + self.author

    def toarray(self):
        return [self.id, self.title, self.url, self.author, self.coauthor, self.isSpliced, self.plays,
                self.splices, self.relSplices, self.likes, self.date, self.comments]


def get_thread_pool_executor():
    num_cpus = multiprocessing.cpu_count()
    return concurrent.futures.ThreadPoolExecutor(max_workers=num_cpus)


COUNT = 0

def increment():
    global COUNT
    COUNT = COUNT + 1

options = Options()
options.set_headless(headless=True)

def mining(url):
    # display = Display(visible=0, size=(1920, 1080)).start()
    driver = webdriver.Firefox(firefox_options=options)

    try:
        driver.get(url.split(',')[0].replace ('"', ''))
        delay = 3  # seconds
        # time.sleep(delay)
        WebDriverWait(driver, delay).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.creator')))

        author = driver.find_element_by_css_selector("a.creator").text

        isContestSong = False
        if driver.find_element_by_css_selector(".release-player-featured").text == "Official Contest":
            isContestSong = True

        title = driver.find_element_by_class_name("dna-player-title").text

        coauthor = "-"
        coauthors = driver.find_element_by_css_selector(
            ".dna-player-artist-expanded-users").find_elements_by_tag_name("a")
        if len(coauthors) > 0:
            l = list()
            for c in coauthors:
                l.append(c.get_attribute("data-original-title"))
            coauthor = '-'.join(l)

        plays = driver.find_element_by_css_selector(
            "div.dna-info-stats-wrapper:nth-child(2) > span:nth-child(1)").get_attribute(
            'data-original-title')
        plays = re.sub("[a-zA-Z\s]", "", plays)

        splices = driver.find_element_by_css_selector(
            "div.dna-info-stats-wrapper:nth-child(2) > span:nth-child(2)").get_attribute(
            'data-original-title')
        splices = re.sub("[a-zA-Z\s]", "", splices)

        likes = driver.find_element_by_css_selector(
            "span.ng-isolate-scope:nth-child(3)").get_attribute(
            'data-original-title')
        likes = re.sub("[a-zA-Z\s]", "", likes)

        date = driver.find_element_by_css_selector("div.dna-player-title-timestamp:nth-child(4)").text
        date = getdate(date)
        if isContestSong:
            comments = driver.find_element_by_css_selector("h3.ng-binding").text
        else:
            comments = driver.find_element_by_css_selector(
                "div.col-sm-6:nth-child(2) > h3:nth-child(1)").text

        comments = re.sub("[a-zA-Z()\s]", "", comments)
        if comments == "":
            comments = 0

        released_splices = "0"
        if not isContestSong:
            released_splices = driver.find_element_by_css_selector(
                ".dna-social-splices > h3:nth-child(1)").text
            released_splices = re.sub("[a-zA-Z()\s]", "", released_splices)
        if released_splices == "":
            released_splices = "0"

        isSpliced = "Contest"
        if not isContestSong:
            splice = driver.find_element_by_css_selector(
                "a.release-player-spliced-from-link:nth-child(2)")
            if splice.text != "":
                isSpliced = splice.get_attribute("href")
            else:
                isSpliced = False

        song = SpliceSong(COUNT, title.encode('utf-8'), url, author.encode('utf-8'),
                          coauthor.encode('utf-8'),
                          str(isSpliced), plays, splices, released_splices, likes, date, comments)
        songQueue.put(song)
        increment()
        if COUNT % 10 == 0:
            print COUNT
    except Exception as e:
        print e
        print "error at song: " + relLink
    finally:
        # display.stop()
        driver.quit()


songQueue = queue.Queue(0)

def main():
    with open(sys.argv[1]) as in_f:
        urls = {line.rstrip() for line in in_f}

    # mining from Splice
    with get_thread_pool_executor() as pool_executor:
        for url in urls:
            pool_executor.submit(mining, url)

    # writing to files
    fileSong = open(sys.argv[2], 'wt')
    try:
        writer = csv.writer(fileSong, quoting=csv.QUOTE_NONNUMERIC)
        # writer.writerow(
        #     ('Id', 'Title', 'URL', 'Author', 'Co-Author', 'IsSpliced?', 'Plays', 'Splices', 'Released Splices', 'Likes',
        #      'Date', 'Comments'))
        songQueue.put("STOP")
        for song in iter(songQueue.get, "STOP"):
            writer.writerow(song.toarray())
        print 'Printed CSV output file'
    finally:
        fileSong.close()
        in_f.close()


if __name__ == '__main__':
    main()
