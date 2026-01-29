#!/usr/bin/env python3
import logging
from dataclasses import replace

from logikal_browser.chrome import ChromeBrowser
from logikal_browser.scenarios import desktop

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

browser = ChromeBrowser(settings=replace(desktop.settings, headless=False))
browser.get('https://slab.logikal.io')
input('Press <ENTER> to stop the program... ')
