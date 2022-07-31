#!/usr/bin/python
from scrapy import cmdline
import sys
import time

arg = ''
if len(sys.argv) == 3:
   arg = sys.argv[2].replace('-', '')

timestr = 'Outputs-' + time.strftime("%Y%m%d-%H%M%S")

name = 'retailmenot'
if __name__ == '__main__':
    if arg == '':
        command = "scrapy crawl {0} -o {1}.csv".format(name, timestr).split()
    else:
        command = "scrapy crawl {0} -o best_seller_data.csv -a download_delay={1}".format(name, arg).split()

    cmdline.execute(command)

