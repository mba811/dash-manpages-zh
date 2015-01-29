#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: garcia.wul
@contact: garcia.wul@alibaba-inc.com
@date: 2014/06/23
"""

import os
import sqlite3
import urllib2
import shutil
import tarfile
import hashlib
import codecs

from mako.template import Template
from pyquery import PyQuery

currentPath = os.path.join(os.path.dirname(os.path.realpath(__file__)))
name = "manpages"

baseName = "manpages-zh"
output = baseName + ".docset"
appName = "dash-" + baseName
tarFileName = baseName + ".tgz"
feedName = baseName + ".xml"
version = "1.5.0"


docsetPath = os.path.join(currentPath, output, "Contents", "Resources", "Documents")
# Step 2: Copy the HTML Documentation
fin = codecs.open(os.path.join(docsetPath, "index.html"), "r", "utf-8")
content = fin.read()
fin.close()
jQuery = PyQuery(content)
jQuery.find("body").empty()

fileNames = []
itemTemplate = Template("<a href='html/${fileName}'>${name}</a><br />\n")
for fileName in os.listdir(os.path.join(docsetPath, "html")):
    fileNames.append({
        "name": fileName.split(".")[0],
        "fileName": fileName
    })
    jQuery.find("body").append(itemTemplate.render(name = fileName.split(".")[0], fileName = fileName))
fin = codecs.open(os.path.join(docsetPath, "index.html"), "w", "utf-8")
newContent = jQuery.html()
fin.write(newContent)
fin.close()

# Step 3: create the Info.plist file
infoTemplate = Template('''<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
<key>CFBundleIdentifier</key>
<string>${name}</string>
<key>CFBundleName</key>
<string>${name}</string>
<key>DocSetPlatformFamily</key>
<string>${name}</string>
<key>dashIndexFilePath</key>
<string>index.html</string>
<key>dashIndexFilePath</key>
<string>index.html</string>
<key>isDashDocset</key><true/>
<key>isJavaScriptEnabled</key><true/>
</dict>
</plist>''')
infoPlistFile = os.path.join(currentPath, output, "Contents", "Info.plist")
fin = open(infoPlistFile, "w")
fin.write(infoTemplate.render(name = name))
fin.close()

# Step 4: Create the SQLite Index
dbFile = os.path.join(currentPath, output, "Contents", "Resources", "docSet.dsidx")
if os.path.exists(dbFile):
    os.remove(dbFile)
db = sqlite3.connect(dbFile)
cursor = db.cursor()

try:
    cursor.execute("DROP TABLE searchIndex;")
except Exception:
    pass

cursor.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
cursor.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

insertTemplate = Template("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('${name}', '${type}', '${path}');")

# Step 5: Populate the SQLite Index
for result in fileNames:
    sql = insertTemplate.render(name = result["name"], type = "Builtin", path = "html/" + result["fileName"])
    print sql
    cursor.execute(sql)
db.commit()
db.close()

# Step 6: copy icon
shutil.copyfile(os.path.join(currentPath, "icon.png"),
    os.path.join(currentPath, output, "icon.png"))
shutil.copyfile(os.path.join(currentPath, "icon@2x.png"),
    os.path.join(currentPath, output, "icon@2x.png"))

# Step 7: 打包
if not os.path.exists(os.path.join(currentPath, "dist")):
    os.makedirs(os.path.join(currentPath, "dist"))
tarFile = tarfile.open(os.path.join(currentPath, "dist", tarFileName), "w:gz")
for root, dirNames, fileNames in os.walk(output):
    for fileName in fileNames:
        fullPath = os.path.join(root, fileName)
        tarFile.add(fullPath)
tarFile.close()

# Step 8: 更新feed url
feedTemplate = Template('''<entry>
    <version>${version}</version>
    <sha1>${sha1Value}</sha1>
    <url>https://raw.githubusercontent.com/magicsky/${appName}/master/dist/${tarFileName}</url>
</entry>''')
fout = open(os.path.join(currentPath, "dist", tarFileName), "rb")
sha1Value = hashlib.sha1(fout.read()).hexdigest()
fout.close()
fin = open(os.path.join(currentPath, feedName), "w")
fin.write(feedTemplate.render(sha1Value = sha1Value, appName = appName, tarFileName = tarFileName, version = version))
fin.close()
