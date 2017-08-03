#! /usr/bin/env python
#
# The MIT License (MIT)
#
# Copyright (c) 2014-2017 Jason Stevens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import sys
if sys.version_info < (3, 0):
    import StringIO as io
else:
    import io

class grub2select():
    menuCount = 1
    menuData = {}
    newEntry = ''
    grub2cfgData = io.StringIO()
    grubEnvData = io.StringIO()
    grub2Path = "/boot/grub2/"
    grub2cfgFile = "grub.cfg"
    grub2cfgFileEFI = "grub2.cfg"
    grub2cfg = os.path.join(grub2Path, grub2cfgFile)
    grub2cfgEFI = os.path.join(grub2Path, grub2cfgFileEFI)
    grubDefault = str(None)
    grubDefaultMatch = None


    def parseGrubCfg(self):
        if os.path.exists(self.grub2cfgEFI):
            self.grub2cfg = self.grub2cfgEFI
        """read in 'grub.cfg' and 'grub2-editenv list' and parse data"""
        if not os.path.exists(self.grub2cfg):
            print("unable to locate %s, is grub2 installed?" % self.grub2cfg)
            sys.exit(0)

        # load grub.cfg menu data
        self.grub2cfgData = io.StringIO()
        f = open(self.grub2cfg, "r")
        self.grub2cfgData.write(f.read())
        f.close()
        del(f)
        self.grub2cfgData.seek(0)

        # load grub2 env data
        self.grubEnvData = io.StringIO()
        os.system("grub2-editenv list > /tmp/grub2-env.lst")
        f = open("/tmp/grub2-env.lst", "r")
        self.grubEnvData.write(f.read())
        f.close()
        del(f)
        self.grubEnvData.seek(0)

        # parse grub.cfg data
        self.menuData = {}
        self.menuCount = 1
        self.grub2cfgData.seek(0)
        for line in self.grub2cfgData:
            if line.strip().lower().startswith("menuentry "):
                menu = {"name": None, "id": None}
                menu["name"] = line.split("'")[1]
                menu["id"] = line.split("'")[3]
                self.menuData[self.menuCount] = menu
                self.menuCount +=1

        # parse grubEnv for default
        self.grubDefault = str(None)
        self.grubDefaultMatch = None
        for line in self.grubEnvData:
            if line.lower().startswith("saved_entry="):
                self.grubDefault = line.replace("saved_entry=", "").strip()

        # try to match default => menu["id"]
        #for item in sorted(self.menuData):
        #    if str(self.menuData[item]["id"]).count(self.grubDefault):
        #        self.grubDefaultMatch = self.menuData[item]
        #        break

        # try to match default => menu["name"]
        for item in sorted(self.menuData):
            try:
                grubDefaultSplit = self.grubDefault.split(">")
                matchData = grubDefaultSplit[len(grubDefaultSplit)-1]
            except:
                matchData = self.grubDefault
            if self.menuData[item]["name"].count(matchData):
                self.grubDefaultMatch = self.menuData[item]
                break

    def selectKernel(self):
        for item in sorted(self.menuData):
            grubMatch = " "
            if self.grubDefaultMatch is not None:
                if self.menuData[item]['name'] is self.grubDefaultMatch['name']:
                    grubMatch = "*"
            print("{0}:{2}:{1}".format(item, self.menuData[item]["name"], grubMatch))
        print("")
        self.showGrubDefault()
        if sys.version_info < (3, 0):
            selection = raw_input("select number: ")
        else:
            selection = input("select number: ")
            selection = "{0}".format(selection)
        if not selection.isdigit():
            print("Invalid selection")
            sys.exit(0)

        try:
            selection = int(selection)
        except:
            print("Invalid selection")
            sys.exit(0)
        if (selection < 1) or (selection >= self.menuCount):
            print("Invalid selection")
            sys.exit(0)
        print("valid selection!\n")

        self.newEntry = self.menuData[selection]

        os.system('grub2-set-default "{0}"'.format(self.newEntry["name"]))
        #os.system('grub2-set-default "{0}"'.format(self.newEntry["id"]))
        self.writeGrubCfg()

    def showGrubDefault(self):
        if self.grubDefaultMatch is not None:
            print("Current Default: {0}".format(self.grubDefaultMatch["name"]))
        else:
            print("Current Default: UNKNOWN")

    def writeGrubCfg(self):
        os.system('grub2-mkconfig -o %s > /dev/null 2>&1' % self.grub2cfg)

    def main(self):
        self.writeGrubCfg()
        self.parseGrubCfg()
        self.selectKernel()
        self.parseGrubCfg()
        self.showGrubDefault()

if __name__ == "__main__":
    try:
        program = grub2select()
        program.main()
    except KeyboardInterrupt:
        print("Bye!")
        sys.exit(0)
