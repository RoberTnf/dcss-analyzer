from bs4 import BeautifulSoup
import urllib.request
import re
import os
import sys

def download_morgues(base_url, base_folder):
    # get link to each user morgue's folder
    print("Indexing each user morgue's folder for {}".format(base_url))
    resp_base = urllib.request.urlopen(base_url)
    soup_base = BeautifulSoup(
        resp_base, "html5lib",
        from_encoding=resp_base.info().get_param('charset'))

    # get links to each morgue for user
    for user in soup_base.find_all('a', href=True):
        # avoid the parent directory link and the order links
        if user["href"] != "/crawl/" and user["href"][0] != "?":
            print("Indexing {} morgue's folder".format(user["href"]))
            print("Link : {}".format(base_url + user["href"]))
            resp_user = urllib.request.urlopen(base_url + user["href"])
            soup_user = BeautifulSoup(
                resp_user, "html5lib",
                from_encoding=resp_user.info().get_param('charset'))

            # create directory for user
            directory = base_folder + user["href"]
            if not os.path.exists(directory):
                os.makedirs(directory)
            for morgue in re.findall(re.compile(
                    "morgue.*\.txt"), soup_user.text):
                # check if we already downloaded the file to avoid redownloads
                if not os.path.isfile(directory + morgue):
                    print("Downloading {}: ".format(
                        base_url + user["href"] + morgue))
                    text = urllib.request.urlopen(
                        base_url + user["href"] + morgue).read()
                    with open(directory + morgue, "wb") as f:
                        f.write(text)
                else:
                    print("{} already exists".format(directory + morgue))


url = "http://crawl.xtahua.com/crawl/morgue/"
folder = "morgues/crawl-xtahua/"


if len(sys.argv) == 2:
    if sys.argv[1] == "download":
        download_morgues(url, folder)
