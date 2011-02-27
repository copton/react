#!/usr/bin/env python3.2

import os
import os.path
from pyinotify import WatchManager, IN_DELETE, IN_CREATE, IN_CLOSE_WRITE, ProcessEvent, Notifier
import subprocess
import sys
import re
import argparse

parser = argparse.ArgumentParser(description='Launch a script if specified files change.')
parser.add_argument('directory', help='the directory which is recursively monitored')
parser.add_argument('-p', '--pattern', required=False, default=".*", help='files only trigger the reaction if therir name matches this regular expression')
parser.add_argument("script", help="the script that is executed upon reaction")
parser.add_argument("parameters", nargs="*", help="paramemters which are passed to the reaction script. $p is expanded to the full path and $f to the file name of the modified file")

class Options:
    __slots__=["directory", "pattern", "script", "parameters"]

options = Options()
args = parser.parse_args(namespace=options)

class Reload (Exception):
    pass

class Process(ProcessEvent):
    def __init__(self,  options):
        self.pattern = re.compile(options.pattern)
        self.parameters = options.parameters
        self.script = options.script

    def process_IN_CREATE(self, event):
        target = os.path.join(event.path, event.name)
        if os.path.isdir(target):
            raise Reload()

    def process_IN_DELETE(self, event):
        raise Reload()

    def process_IN_CLOSE_WRITE(self, event):
        target = os.path.join(event.path, event.name)
        if self.pattern.match(target):
            args = [self.script]
            params2 = map (lambda s: s.replace("$p", event.path), self.parameters)
            params3 = map (lambda s: s.replace("$f", event.name), params2)
            args += params3
            sys.stdout.write("executing script:" + " ".join(args) + "\n")
            subprocess.call(args)
            sys.stdout.write("------------------------\n")

while True:
    wm = WatchManager()
    process = Process(options)
    notifier = Notifier(wm, process)
    mask = IN_DELETE | IN_CREATE | IN_CLOSE_WRITE
    wdd = wm.add_watch(options.directory, mask, rec=True)
    try:
        while True:
            notifier.process_events()
            if notifier.check_events():
                notifier.read_events()
    except Reload:
        pass
    except KeyboardInterrupt:
        notifier.stop()
        break
