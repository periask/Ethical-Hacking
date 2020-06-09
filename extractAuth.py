#!/usr/bin/env python3
import sys
import os
import re
import time
import argparse
import pprint
from pathlib import Path
from tqdm import tqdm

def myArgParger():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", type=str,
                        help="Data path")
    parser.add_argument("-o", "--output", type=str,
                        help="Where to store the output")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    args = parser.parse_args()
    return args

def getAllFiles(dirPath):
    files = []

    p = Path(dirPath)
    files = [x for x in p.iterdir() if not x.is_dir()]
    dirs  = [x for x in p.iterdir() if x.is_dir()]
    for d in dirs:
        files = files + getAllFiles(d)
    return files

def writeToFiles(filename, matched, output):
    progress_bar = tqdm(total=len(matched.keys()), leave=False)
    progress_bar.set_description(f'{str(filename)[-30:]} Writing output : ')

    p = re.compile("[^a-z0-9_-]")

    for domain in matched.keys():
        for k in ["matched", "users", "passwds"]:
            try:
                with open(os.path.join(output, p.subn('_', domain)[0] + "_" + k + ".txt"),
                          "a", errors='replace') as fp:
                    for line in matched[domain][k]:
                        fp.write(line + "\n")
            except KeyboardInterrupt:
                sys.exit()
            except:
                progress_bar.write("Exception: ignoring...{} {} {}".foramt(output, domain, k))

        progress_bar.update(1)
    progress_bar.close()

def extractDomains(filename, output):
    lines = []
    matched = {}

    with open(str(filename), "r", errors='replace') as fp:
        lines = fp.readlines()

    progress_bar = tqdm(total=len(lines), leave=False)
    progress_bar.set_description(f'{str(filename)[-30:]} Extracting : ')

    pattern = re.compile("([^@]*@([^:]*)):(.*)")
    for line in lines:
        line = line.strip()
        f = pattern.match(line)
        if f and f.group(1) and f.group(2) and f.group(3):
            domain = f.group(2).strip().lower()
            if domain and ((domain[0] >= 'a' and domain[0] <= 'z') or (domain[0] >= '0' and domain[0] <= '9')):
                if domain not in matched.keys():
                    matched[domain] = {}
                    matched[domain]["matched"] = [line]
                    matched[domain]["users"] = [f.group(1)]
                    matched[domain]["passwds"] = [f.group(3)]
                else:
                    matched[domain]["matched"].append(line)
                    matched[domain]["users"].append(f.group(1))
                    matched[domain]["passwds"].append(f.group(3))

        progress_bar.update(1)

    writeToFiles(filename, matched, output)
    progress_bar.close()

    return matched

def extractDomain(filename, domain):
    lines = []
    matched = []
    users = []
    passwd = []

    with open(str(filename), "r", errors='replace') as fp:
        lines = fp.readlines()

    pattern = re.compile("([^@]*@([^:]*)):(.*)")
    for line in lines:
        f = pattern.match(line)
        if f and domain in f.group(2):
            matched.append(line)
            users.append(f.group(1))
            passwd.append(f.group(3))

    return (matched, users, passwd, len(lines))

def main_concurrent(args):
    files = getAllFiles(args.path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
        data_returned = {executor.submit(extractDomain, filename, "gmail.com"): filename for filename in files}

        for data in concurrent.futures.as_completed(data_returned):
            filename = data_returned[data]
            try:
                (matched, total_lines) = data.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (str(filename), exc))
            else:
                print('File: %s Matched: %d / %d ' % (str(filename), matched, total_lines))

            data_returned[data] = None
            data = None

def main(args):
    total = 0
    totalMatched = 0

    files = getAllFiles(args.path)

    progress_bar = tqdm(total=len(files))
    for f in files:
        progress_bar.set_description(f'Processing ...{str(f)[-30:]} : ')
        matched = extractDomains(str(f), args.output)
        progress_bar.set_description(f'Processing ...{str(f)[-30:]} : ')
        progress_bar.update(1)

if __name__ == "__main__":
    args = myArgParger()
    main(args)
