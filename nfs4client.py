#!/usr/bin/env python2

# nfs4client.py - NFS4 client. 
#
# Written by Peter �strand <peter@cendio.se>
# Copyright (C) 2001 Cendio Systems AB (http://www.cendio.se)
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License. 
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# TODO:
# completion: should not complete commands as arguments. 

from nfs4constants import *
from nfs4types import *
import nfs4lib
import readline
import cmd
import sys
import getopt
import re
import os


SYNTAX = """\
Syntax:
nfs4client host[:[port]]<directory> [-u|-t] [-d debuglevel]

-u --udp (default)
-t --tcp

-d --debuglevel debuglevel
"""

VERSION = "0.0"
BUFSIZE = 4096

# Load readline & completer
try:
    import pynfs_completer
except ImportError:
    print "Module readline not available."
else:
    import __builtin__
    import __main__
    class Completer(pynfs_completer.Completer):
        def __init__(self):
            self.pythonmode = 0
        
        commands = [
            "help", "cd", "rm", "dir", "ls", "exit", "quit", "get",
            "put", "mkdir", "md", "rmdir", "rd", "cat", "page",
            "debug", "ping", "version", "pythonmode"]

        def complete(self, text, state):
            """Return the next possible completion for 'text'.

            This is called successively with state == 0, 1, 2, ... until it
            returns None.  The completion should begin with 'text'.

            """
            if state == 0:
                if "." in text and self.pythonmode:
                    self.matches = self.attr_matches(text)
                else:
                    self.matches = self.global_matches(text)
            try:
                return self.matches[state]
            except IndexError:
                return None

            
        def global_matches(self, text):
            """Compute matches when text is a simple name.

            Return a list of all keywords, built-in functions and names
            currently defines in __main__ that match.

            """
            import keyword
            matches = []
            n = len(text)

            searchlist = [Completer.commands]
            if self.pythonmode:
                searchlist.append(keyword.kwlist)
                searchlist.append(__builtin__.__dict__.keys())
                searchlist.append(__main__.__dict__.keys())

            for list in searchlist:
                for word in list:
                    if word[:n] == text and word != "__builtins__":
                        matches.append(word)

            return matches


    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(' \t\n`~!@#$%^&*()-=+{}\\|;:\'",<>/?')

# Save history upon exit
import os
histfile = os.path.join(os.environ["HOME"], ".nfs4client")
try:
    readline.read_history_file(histfile)
except IOError:
    pass
import atexit
atexit.register(readline.write_history_file, histfile)
del histfile


class ClientApp(cmd.Cmd):
    def __init__(self, transport, host, port, directory, pythonmode):
        self.transport = transport
        self.host = host
        self.port = port
        self.directory = directory
        self.ncl = None

        self.completer = Completer()
        self.completer.pythonmode = pythonmode
        readline.set_completer(self.completer.complete)

        # FIXME: show current directory. 
        self.prompt = "nfs4: >"
        # FIXME
        #self.intro = ""
        #self.doc_header = ""
        #self.misc_header
        #self.undoc_header

        self._connect()


    def _connect(self):
        if transport == "tcp":
            self.ncl = nfs4lib.TCPNFS4Client(self.host, self.port)
        elif transport == "udp":
            self.ncl = nfs4lib.UDPNFS4Client(self.host, self.port)
        else:
            raise RuntimeError, "Invalid protocol"
        self.ncl.init_connection()
        

    #
    # Commands
    #
    def do_EOF(self, line):
        print
        sys.exit(0)
    
    def do_cd(self, line):
        # FIXME
        print "not implemented"

    def do_rm(self, line):
        # FIXME
        print "not implemented"

    def do_dir(self, line):
        # FIXME
        print "not implemented"

    do_ls = do_dir

    do_exit = do_EOF

    do_quit = do_EOF

    def do_get(self, line):
        filenames = line.split()

        if not filenames:
            print "get <filename>..."
            return
        
        for file in filenames:
            basename = os.path.basename(file)
            remote = nfs4lib.NFS4OpenFile(ncl)
            try:
                remote.open(file)
                local = open(basename, "w")
                while 1:
                    data = remote.read(BUFSIZE)
                    if not data:
                        break
                    
                    local.write(data)
                
                remote.close()
                local.close()
            except nfs4lib.BadCompondRes, r:
                print "Error fetching file: operation %d returned %d" % (r.operation, r.errcode)
        print


    def do_put(self, line):
        # FIXME
        print "not implemented"

    def do_mkdir(self, line):
        # FIXME
        print "not implemented"

    do_md = do_mkdir

    def do_rmdir(self, line):
        # FIXME
        print "not implemented"

    do_rd = do_rmdir

    def do_cat(self, line):
        filenames = line.split()

        if not filenames:
            print "cat <filename>..."
            return
        
        for file in filenames:
            f = nfs4lib.NFS4OpenFile(self.ncl)
            try:
                f.open(file)
                print f.read(),
                f.close()
            except nfs4lib.BadCompondRes, r:
                print "Error fetching file: operation %d returned %d" % (r.operation, r.errcode)
        print
        
    do_page = do_cat

    def do_debug(self, line):
        # FIXME
        print "not implemented"

    def do_ping(self, line):
        # FIXME
        print "not implemented"

    def do_version(self, line):
        print "nfs4client.py version", VERSION

    def do_shell(self, line):
        os.system(line)

    def do_pythonmode(self, line):
        self.completer.pythonmode = (not self.completer.pythonmode)
        print "pythonmode is now",
        if self.completer.pythonmode:
            print "on"
        else:
            print "off"

    #
    # Misc. 
    #
    def help_cd(self):
        print "Change current directory"
    
    def help_overview(self):
        print SYNTAX

    def emptyline(self):
        pass

    def default(self, line):
        if line[:1] == '@':
            line = line[1:]

        try:
            code = compile(line + '\n', '<stdin>', 'single')
            exec code in globals()
        except:
            t, v = sys.exc_info()[:2]
            if type(t) == type(''):
                exc_type_name = t
            else: exc_type_name = t.__name__
            print '***', exc_type_name + ':', v



def usage():
    print "Usage: %s host[:[port]]<directory> [-u|-t] [-d debuglevel]" % sys.argv[0]
    print "options:"
    print "-h, --help                   display this help and exit"
    print "-u, --udp                    use UDP as transport (default)"
    print "-t, --tcp                    use TCP as transport"
    print "-d level, --debuglevel level set debuglevel"
    print "-p, --pythonmode             enable Python interpreter mode"
    sys.exit(2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hutdp", ["help", "udp", "tcp", "debuglevel", "pythonmode"])
    except getopt.GetoptError:
        print "invalid option"
        usage()
        sys.exit(2)

    transport = "udp"
    debuglevel = 0
    pythonmode = 0

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-u", "--udp"):
            transport = "udp"
        if o in ("-t", "--tcp"):
            transport = "tcp"
        if o in ("-d", "--debuglevel"):
            debuglevel = a
        if o in ("-p", "--pythonmode"):
            pythonmode = 1


    # By now, there should only be one argument left.
    if len(args) != 1:
        usage()
    else:
        # Parse host/port/directory part. 
        match = re.search(r'(?P<host>\w*)(?::(?P<port>\d*))?(?P<dir>[\w/]*)', args[0])
        if not match:
            usage()
        host = match.group("host")
        portstring = match.group("port")
        directory = match.group("dir")

        if portstring:
            port = int(portstring)
        else:
            port = nfs4lib.NFS_PORT

        if not directory:
            directory = "/"

    c = ClientApp(transport, host, port, directory, pythonmode)
    c.cmdloop()
    
