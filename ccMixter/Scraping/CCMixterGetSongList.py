import os
import subprocess
import signal

import sys
from selenium import webdriver

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


phantom_js_clean_up ()
# INSERT YOUR PATH TO PHANTOMJS EXECUTABLE
driver = webdriver.PhantomJS (executable_path='PATH TO phantomjs EXECUTABLE')
file = open (sys.argv[1], "w")

i = 0
for j in range(0,1837):
    driver.get ("http://ccmixter.org/view/media/remix/latest?offset="+str(i))
    song = driver.find_elements_by_xpath("/html/body/div[3]/div[3]/div/div[2]/div[1]/div/div[2]/a[2]")
    for s in song:
        file.write(s.get_attribute("href")+"\n")
    print j
    i += 15


file.close ()
