#!/usr/bin/env python2

# nfs4st.py - NFS4 server tester
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
# Extend unittest with warnings.

# Note on docstrings: Each class inheriting NFSTestCase is referred to as a
# "test case". Each test* method is a "invocable component", sometimes called
# "component". 


import unittest
import time
import sys

from nfs4constants import *
from nfs4types import *
import nfs4lib

# Global variables
host = None
port = None
transport = "udp"


class NFSTestCase(unittest.TestCase):
    def connect(self):
        if transport == "tcp":
            self.ncl = nfs4lib.TCPNFS4Client(host, port)
        elif transport == "udp":
            self.ncl = nfs4lib.UDPNFS4Client(host, port)
        else:
            raise RuntimeError, "Invalid protocol"

        self.ncl.init_connection()
    
    def failIfRaises(self, excClass, callableObj, *args, **kwargs):
        try:
            apply(callableObj, args, kwargs)
        except excClass, e:
            self.fail(e)
        else:
            return


    def assert_OK(self, res):
        self.failIfRaises(nfs4lib.NFSException, nfs4lib.check_result, res)


class AccessTestCase(NFSTestCase):
    """Test ACCESS operation.

    Note: We do not examine if the "access" result actually corresponds to
    the correct rights. This is hard since the rights for a object can
    change at any time.
    """
    
    maxval = ACCESS4_DELETE + ACCESS4_EXECUTE + ACCESS4_EXTEND + ACCESS4_LOOKUP \
             + ACCESS4_MODIFY + ACCESS4_READ

    def valid_access_ops(self):
        result = []
        for i in range(AccessTestCase.maxval + 1):
            result.append(self.ncl.access_op(i))
        return result

    def invalid_access_ops(self):
        result = []
        for i in [64, 65, 66, 127, 128, 129]:
            result.append(self.ncl.access_op(i))
        return result
    
    def setUp(self):
        self.connect()
        self.putrootfhop = self.ncl.putrootfh_op()

    def testSanityOnDir(self):
        """All valid combinations of ACCESS arguments on directory

        The ACCESS operation takes an uint32_t as an argument, which is
        bitwised-or'd with zero or more of all ACCESS4* constants. This
        component tests all valid combinations of these constants. It also
        verifies that the server does not respond with an right in "access"
        but not in "supported". 
        """
        for accessop in self.valid_access_ops():
            res = self.ncl.compound([self.putrootfhop, accessop])
            self.assert_OK(res)
            
            supported = res.resarray[1].arm.arm.supported
            access = res.resarray[1].arm.arm.access

            # Server should not return an access bit if this bit is not in supported. 
            self.failIf(access > supported, "access is %d, but supported is %d" % (access, supported))


    def testSanityOnFile(self):
        """All valid combinations of ACCESS arguments on file

        Se testSanityOnDir.
        """
        path = nfs4lib.str2pathname("/README")
        lookupop = self.ncl.lookup_op(path)
        for accessop in self.valid_access_ops():
            res = self.ncl.compound([self.putrootfhop, lookupop, accessop])
            self.assert_OK(res)

            supported = res.resarray[2].arm.arm.supported
            access = res.resarray[2].arm.arm.access

            # Server should not return an access bit if this bit is not in supported. 
            self.failIf(access > supported, "access is %d, but supported is %d" % (access, supported))

    def testNoExecOnDir(self):
        """ACCESS4_EXECUTE should never be returned for directory

        ACCESS4_EXECUTE has no meaning for directories and should not be
        returned in "access" or "supported". 
        """
        for accessop in self.valid_access_ops():
            res = self.ncl.compound([self.putrootfhop, accessop])
            self.assert_OK(res)
            
            supported = res.resarray[1].arm.arm.supported
            access = res.resarray[1].arm.arm.access

            self.failIf(supported & ACCESS4_EXECUTE,
                        "server returned ACCESS4_EXECUTE for root dir (supported=%d)" % supported)

            self.failIf(access & ACCESS4_EXECUTE,
                        "server returned ACCESS4_EXECUTE for root dir (access=%d)" % access)

    def testInvalids(self):
        """ACCESS should fail on invalid arguments

        ACCESS should return with NFS4ERR_INVAL if called with an illegal
        access request (eg. an integer with bits set that does not correspond to
        any ACCESS4* constant).
        """
        for accessop in self.invalid_access_ops():
            res = self.ncl.compound([self.putrootfhop, accessop])
            self.failUnlessEqual(res.status, NFS4ERR_INVAL,
                                 "server accepts invalid ACCESS request with NFS4_OK, "
                                 "should be NFS4ERR_INVAL")

    def testWithoutFh(self):
        """ACCESS should fail without (cfh)

        ACCESS should return NFS4ERR_NOFILEHANDLE if called without filehandle.
        """
        accessop = self.ncl.access_op(ACCESS4_READ)
        res = self.ncl.compound([accessop])
        self.failUnlessEqual(res.status, NFS4ERR_NOFILEHANDLE)


class CommitTestCase(NFSTestCase):
    """Test COMMIT operation.

    Note: We do not examine the writeverifier in any way. It's hard
    since it can change at any time.
    """

    def setUp(self):
        self.connect()
        self.putrootfhop = self.ncl.putrootfh_op()

        # Filenames
        self.linkfile = "/dev/floppy"
        self.blockfile = "/dev/fd0"
        self.charfile = "/dev/ttyS0"
        self.socketfile = "/dev/log"
        self.fifofile = "/dev/initctl"
        self.dirfile = "/doc"
        self.normfile = "/doc/README"

    def testOnLink(self):
        """COMMIT should fail with NFS4ERR_INVAL on Links"""

        path = nfs4lib.str2pathname(self.linkfile)
        lookupop = self.ncl.lookup_op(path)
        commitop = self.ncl.commit_op(0, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.failUnlessEqual(res.status, NFS4ERR_INVAL)

    def testOnBlock(self):
        """COMMIT should fail with NFS4ERR_INVAL on block device"""

        path = nfs4lib.str2pathname(self.blockfile)
        lookupop = self.ncl.lookup_op(path)
        commitop = self.ncl.commit_op(0, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.failUnlessEqual(res.status, NFS4ERR_INVAL)

    def testOnBlock(self):
        """COMMIT should fail with NFS4ERR_INVAL on character device"""

        path = nfs4lib.str2pathname(self.charfile)
        lookupop = self.ncl.lookup_op(path)
        commitop = self.ncl.commit_op(0, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.failUnlessEqual(res.status, NFS4ERR_INVAL)

    def testOnSocket(self):
        """COMMIT should fail with NFS4ERR_INVAL on socket"""
        
        path = nfs4lib.str2pathname(self.socketfile)
        lookupop = self.ncl.lookup_op(path)
        commitop = self.ncl.commit_op(0, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.failUnlessEqual(res.status, NFS4ERR_INVAL)

    def testOnFifo(self):
        """COMMIT should fail with NFS4ERR_INVAL on FIFOs"""

        path = nfs4lib.str2pathname(self.fifofile)
        lookupop = self.ncl.lookup_op(path)
        commitop = self.ncl.commit_op(0, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.failUnlessEqual(res.status, NFS4ERR_INVAL)
        
    def testOnDir(self):
        """COMMIT should fail with NFS4ERR_ISDIR on directories

        COMMIT should fail with NFS4ERR_ISDIR if called with an filehandle
        that corresponds to a directory. 
        """

        path = nfs4lib.str2pathname(self.dirfile)
        lookupop = self.ncl.lookup_op(path)
        commitop = self.ncl.commit_op(0, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.failUnlessEqual(res.status, NFS4ERR_ISDIR)

    def testOffsets(self):
        """Simple COMMIT on file with offset 0, 1 and 2**64 - 1

        This component tests boundary values for the offset parameter in the
        COMMIT operation. All values are legal. 
        """
        path = nfs4lib.str2pathname(self.normfile)
        lookupop = self.ncl.lookup_op(path)

        # offset = 0
        commitop = self.ncl.commit_op(0, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.assert_OK(res)

        # offset = 1
        commitop = self.ncl.commit_op(1, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.assert_OK(res)

        # offset = 2**64 - 1
        commitop = self.ncl.commit_op(-1, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.assert_OK(res)


    def testCounts(self):
        """COMMIT on file with count 0, 1 and 2**64 - 1

        This component tests boundary values for the count parameter in the
        COMMIT operation. All values are legal. 
        """
        path = nfs4lib.str2pathname(self.normfile)
        lookupop = self.ncl.lookup_op(path)
        
        # count = 0
        commitop = self.ncl.commit_op(0, 0)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.assert_OK(res)

        # count = 1
        commitop = self.ncl.commit_op(0, 1)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.assert_OK(res)

        # count = 2**64 - 1
        commitop = self.ncl.commit_op(0, -1)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.assert_OK(res)

    def testOverflow(self):
        """COMMIT on file with  offset+count >= 2**64

        If the COMMIT operation is called with an offset plus count
        that is larger than 2**64, the server should return NFS4ERR_INVAL
        """
        
        path = nfs4lib.str2pathname(self.normfile)
        lookupop = self.ncl.lookup_op(path)
        
        commitop = self.ncl.commit_op(-1, -1)
        res = self.ncl.compound([self.putrootfhop, lookupop, commitop])
        self.failUnlessEqual(res.status, NFS4ERR_INVAL)


class CreateTestCase(NFSTestCase):
    """Test CREATE operation.
    """
    
    def setUp(self):
        self.connect()
        self.putrootfhop = self.ncl.putrootfh_op()
        self.obj_dir = "/tmp"
        self.obj_name = "object1"

        # Make sure the object to create does not exist.
        # This tests at the same time the REMOVE operation. Not much
        # we can do about it. 
        operations = [self.ncl.putrootfh_op()]

        pathname = nfs4lib.str2pathname(self.obj_dir)
        self.lookup_dir_op = self.ncl.lookup_op(pathname)
        operations.append(self.lookup_dir_op)

        operations.append(self.ncl.remove_op(self.obj_name))

        res = self.ncl.compound(operations)
        self.failIf(res.status not in [NFS4_OK, NFS4ERR_NOENT],
                    "cannot remove test object in preparation for CREATE test")

    def testLink(self):
        """CREATE link

        Create an (symbolic) link.
        """
        
        objtype = createtype4(self.ncl, type=NF4LNK, linkdata="/etc/X11")
        operations = [self.putrootfhop]
        operations.append(self.lookup_dir_op)

        createop = self.ncl.create_op(self.obj_name, objtype)
        operations.append(createop)

        res = self.ncl.compound(operations)
        self.assert_OK(res)
        

class TestProgram(unittest.TestProgram):
    USAGE = """\
Usage: %(progName)s host[:port] [options] [test] [...]

Options:
  -u, --udp        use UDP as transport (default)
  -t, --tcp        use TCP as transport
  -h, --help       Show this message
  -q, --quiet      Minimal output

Examples:
  %(progName)s                               - run default set of tests
  %(progName)s MyTestSuite                   - run suite 'MyTestSuite'
  %(progName)s MyTestCase.testSomething      - run MyTestCase.testSomething
  %(progName)s MyTestCase                    - run all 'test*' test methods
                                               in MyTestCase
"""
    def parseArgs(self, argv):
        import getopt
        import re
        global host, port, transport

        self.verbosity = 2

        # Reorder arguments, so we can add options at the end 
        ordered_args = []
        for arg in sys.argv[1:]:
            if arg.startswith("-"):
                ordered_args.insert(0, arg)
            else:
                ordered_args.append(arg)
        
        try:
            options, args = getopt.getopt(ordered_args, 'uthq',
                                          ['help', 'quiet', 'udp', 'tcp'])
        except getopt.error, msg:
            self.usageExit(msg)
            
        for opt, value in options:
            if opt in ("-u", "--udp"):
                transport = "udp"
            if opt in ("-t", "--tcp"):
                transport = "tcp"
            if opt in ('-h','--help'):
                self.usageExit()
            if opt in ('-q','--quiet'):
                self.verbosity = 0

        if len(args) < 1:
            self.usageExit()

        match = re.search(r'^(?P<host>([a-zA-Z][\w\.]*|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))'
                          r'(?::(?P<port>\d*))?$', args[0])

        if not match:
            self.usageExit()

        host = match.group("host")
        portstring = match.group("port")

        if portstring:
            port = int(portstring)
        else:
            port = nfs4lib.NFS_PORT

        args = args[1:]
                    
        if len(args) == 0 and self.defaultTest is None:
            self.test = self.testLoader.loadTestsFromModule(self.module)
            return
        if len(args) > 0:
            self.testNames = args
        else:
            self.testNames = (self.defaultTest,)

        self.createTests()


main = TestProgram

if __name__ == "__main__":
    main()