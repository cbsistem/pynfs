#!/usr/bin/env python2

# nfs4lib.py - NFS4 library for Python. 
#
# Copyright (C) 2001  Peter �strand <peter@cendio.se>
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

# TODO: Exceptions.
# Remove self.rootfh?

NFS_PROGRAM = 100003
NFS_VERSION = 4
NFS_PORT = 2049

import rpc
from nfs4constants import *
from nfs4types import *
import nfs4packer
import random
import array
import socket
import os
import pwd

class PartialNFS4Client:
    def __init__(self):
        # Client state variables
        self.clientid = None
        self.verifier = None
        # Current directory. A string, like /doc/foo. 
        self.cwd = "/"
        # Root directory
        self.rootfh = None

    
    def addpackers(self):
        self.packer = nfs4packer.NFS4Packer()
        self.unpacker = nfs4packer.NFS4Unpacker('')

    def null(self):
	return self.make_call(0, None, None, None)

    def compound(self, argarray, tag="", minorversion=0):
        """A Compound call"""
        compoundargs = COMPOUND4args(self, argarray=argarray, tag=tag, minorversion=minorversion)
        res = COMPOUND4res(self)
        
        self.make_call(1, None, compoundargs.pack, res.unpack)
        return res

    #
    # Utility methods
    #
    def gen_random_64(self):
        a = array.array('I')
        for turn in range(4):
            a.append(random.randrange(2**16))
        return a.tostring()

    def gen_uniq_id(self):
        # Use FQDN and pid as ID.
        return socket.gethostname() + str(os.getpid())

    #
    # Operations. Creates complete operations. Does not send them to the server. 
    #
    def access(self):
        # FIXME
        raise NotImplementedError()

    def close(self):
        # FIXME
        args = CLOSE4args(self, seqid=, stateid)
        return nfs_argop4(self, argop=OP_CLOSE, opputfh=args)
        raise NotImplementedError()

    def commit(self):
        # FIXME
        raise NotImplementedError()

    def create(self):
        # FIXME
        raise NotImplementedError()

    def delegpurge(self):
        # FIXME
        raise NotImplementedError()

    def delegreturn(self):
        # FIXME
        raise NotImplementedError()

    def getattr(self):
        # FIXME
        raise NotImplementedError()

    def getfh(self):
        return nfs_argop4(self, argop=OP_GETFH)

    def link(self):
        # FIXME
        raise NotImplementedError()

    def lock(self):
        # FIXME
        raise NotImplementedError()

    def lockt(self):
        # FIXME
        raise NotImplementedError()

    def locku(self):
        # FIXME
        raise NotImplementedError()

    def lookup(self):
        # FIXME
        raise NotImplementedError()

    def lookupp(self):
        # FIXME
        raise NotImplementedError()

    def nverify(self):
        # FIXME
        raise NotImplementedError()

    def open(self, claim=None, how=UNCHECKED4, owner=None, seqid=0,
             share_access=OPEN4_SHARE_ACCESS_READ, share_deny=OPEN4_SHARE_DENY_NONE,
             clientid=None, file=None, opentype=OPEN4_NOCREATE):
        
        if not claim:
            claim = open_claim4(self, claim=CLAIM_NULL, file=file)

        if not owner:
            owner = pwd.getpwuid(os.getuid())[0]

        if not clientid:
            clientid = self.clientid

        openhow = openflag4(self, opentype=opentype, how=how)
        owner = nfs_lockowner4(self, clientid=clientid, owner=owner)

        args = OPEN4args(self, claim, openhow, owner, seqid, share_access, share_deny)
        return nfs_argop4(self, argop=OP_OPEN, opopen=args)

    def openattr(self):
        # FIXME
        raise NotImplementedError()

    def open_confirm(self):
        # FIXME
        raise NotImplementedError()

    def open_downgrade(self):
        # FIXME
        raise NotImplementedError()

    def putfh(self, fh):
        args = PUTFH4args(self, object=fh)
        return nfs_argop4(self, argop=OP_PUTFH, opputfh=args)

    def putpubfh(self, fh):
        # FIXME
        raise NotImplementedError()

    def putrootfh(self):
        return nfs_argop4(self, argop=OP_PUTROOTFH)

    def read(self, stateid=0, offset=0, count=0):
        args = READ4args(self, stateid=stateid, offset=offset, count=count)
        return nfs_argop4(self, argop=OP_READ, opread=args)

    def readdir(self):
        # FIXME
        raise NotImplementedError()

    def readlink(self):
        # FIXME
        raise NotImplementedError()

    def remove(self):
        # FIXME
        raise NotImplementedError()

    def rename(self):
        # FIXME
        raise NotImplementedError()

    def renew(self):
        # FIXME
        raise NotImplementedError()

    def restorefh(self):
        # FIXME
        raise NotImplementedError()

    def savefh(self):
        # FIXME
        raise NotImplementedError()

    def secinfo(self):
        # FIXME
        raise NotImplementedError()

    def setattr(self):
        # FIXME
        raise NotImplementedError()

    def setclientid(self, verifier=None, id=None, cb_program=None, r_netid=None, r_addr=None):
        if not verifier:
            self.verifier = self.gen_random_64()
        else:
            self.verifier = verifier

        if not id:
            id = self.gen_uniq_id()

        if not cb_program:
            # FIXME
            cb_program = 0

        if not r_netid:
            # FIXME
            r_netid = "udp"

        if not r_addr:
            # FIXME
            r_addr = socket.gethostname()
        
        client_id = nfs_client_id4(self, verifier=self.verifier, id=id)
        cb_location = clientaddr4(self, r_netid=r_netid, r_addr=r_addr)
        callback = cb_client4(self, cb_program=cb_program, cb_location=cb_location)
        args = SETCLIENTID4args(self, client=client_id, callback=callback)

        return nfs_argop4(self, argop=OP_SETCLIENTID, opsetclientid=args)

    def setclientid_confirm(self, setclientid_confirm):
        args = SETCLIENTID_CONFIRM4args(self, setclientid_confirm=setclientid_confirm)
        
        return nfs_argop4(self, argop=OP_SETCLIENTID_CONFIRM, opsetclientid_confirm=args)

    def verify(self):
        # FIXME
        raise NotImplementedError()

    def write(self):
        # FIXME
        raise NotImplementedError()

    def cb_getattr(self):
        # FIXME
        raise NotImplementedError()

    def cb_recall(self):
        # FIXME
        raise NotImplementedError()
    
    #
    # NFS convenience methods
    #
    def init_connection(self):
        # SETCLIENTID
        op = self.setclientid()
        res =  self.compound([op])
        if res.status:
            raise "SETCLIENTID failed with status", res.status
        
        self.clientid = res.resarray[0].arm.resok4.clientid
        setclientid_confirm = res.resarray[0].arm.resok4.setclientid_confirm

        # SETCLIENTID_CONFIRM
        op = self.setclientid_confirm(setclientid_confirm)
        res =  self.compound([op])
        if res.status:
            raise "SETCLIENTID_CONFIRM failed with status", res.status

        # Fetch root filehandle.
        self.fetch_root()

    def fetch_root(self):
        putrootfhoperation = self.putrootfh()
        getfhoperation = self.getfh()
        res =  self.compound([putrootfhoperation, getfhoperation])
        if res.status:
            raise "failed with status", res.status

        self.rootfh = res.resarray[1].arm.arm.object
    

class UDPNFS4Client(PartialNFS4Client, rpc.RawUDPClient):
    def __init__(self, host):
        rpc.RawUDPClient.__init__(self, host, NFS_PROGRAM, NFS_VERSION, NFS_PORT)

    def mkcred(self):
	if self.cred == None:
            # FIXME. 
	    self.cred = (rpc.AUTH_UNIX, rpc.make_auth_unix(1, "maggie.lkpg.cendio.se", 0, 0, [0, 1, 2, 3, 4, 6, 10]))
	return self.cred

    def mkverf(self):
	if self.verf == None:
	    self.verf = (rpc.AUTH_NULL, rpc.make_auth_null())
	return self.verf


class TCPNFS4Client(PartialNFS4Client, rpc.RawTCPClient):
    def __init__(self, host):
        rpc.RawTCPClient.__init__(self, host, NFS_PROGRAM, NFS_VERSION, NFS_PORT)
        PartialNFS4Client.__init__(self)



        

class NFS4OpenFile:
    """Emulates a Python file object.
    """
    # TODO: Implement buffering. 
    def __init__(self, ncl):
        self.ncl = ncl
        self.__set_priv("closed", 1)
        self.__set_priv("mode", "")
        self.__set_priv("name", "")
        self.softspace = 0
        self.pos = 0
        # NFS4 file handle. 
        self.fh = None

    def __setattr__(self, name, val):
        if name in ["closed", "mode", "name"]:
            raise TypeError("read only attribute")
        else:
            self.__set_priv(name, val)

    def __set_priv(self, name, val):
        self.__dict__[name] = val

        # FIXME: bufsize from system default. 
    def open(self, filename, mode="r", bufsize=1024):
        if filename[0] != os.sep:
            # Only absolute file names now. 
            raise NotImplementedError()
        else:
            # Remove slash.
            filename = filename[1:]

        components = filename.split(os.sep)

        putrootfhoperation = self.ncl.putrootfh()
        op = self.ncl.open(file=components)
        getfhoperation = self.ncl.getfh()
        res =  self.ncl.compound([putrootfhoperation, op, getfhoperation])
        # FIXME: Intelligent error handling: In this app: Print error message.
        # In nfs4lib: Raise exception. 
        if res.status:
            raise " failed with status", res.status
            
        self.fh = res.resarray[2].arm.arm.object
        

    def close(self):
        if not self.closed:
            self.__set_priv("closed", 1)
            # FIXME: NFS close. 
            raise NotImplementedError()

    def flush(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        raise NotImplementedError()

    # isatty() should not be implemented.

    # fileno() should not be implemented.

    def read(self, size=None):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        # FIXME
        pass

    def readline(self, size=None):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        # FIXME
        pass

    def readlines(self, sizehint=None):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        # FIXME
        pass

    def xreadlines(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        import xreadlines
        return xreadlines.xreadlines(self)

    def seek(self, offset, whence=0):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        if whence == 0:
            # absolute file positioning)
            newpos = offset
        elif whence == 1:
            # seek relative to the current position
            newpos = self.pos + offset
        elif whence == 2:
            # seek relative to the file's end
            #offset += self.len
            # FIXME: Fetch len via NFS. 
            raise NotImplementedError()
        else:
            raise IOError("[Errno 22] Invalid argument")
        self.pos = max(0, newpos)

    def tell(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        return self.pos

    def truncate(self, size=None):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        if not size:
            size = self.pos
        # FIXME
        raise NotImplementedError()
        
    def write(self, str):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        # FIXME
        raise NotImplementedError()
        

    def writelines(self, list):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        # (writelines() does not add line separators)
        # FIXME
        raise NotImplementedError()
        


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print "Usage: %s <protocol> <host>" % sys.argv[0]
        sys.exit(1)
    
    proto = sys.argv[1]
    host = sys.argv[2]
    if proto == "tcp":
        ncl = TCPNFS4Client(host)
    elif proto == "udp":
        ncl = UDPNFS4Client(host)
    else:
        raise RuntimeError, "Wrong protocol"

    # PUTROOT & GETFH
    putrootfhoperation = nfs_argop4(ncl, argop=OP_PUTROOTFH)
    getfhoperation = nfs_argop4(ncl, argop=OP_GETFH)
    
    res =  ncl.compound([putrootfhoperation, getfhoperation])

    fh = res.resarray[1].opgetfh.resok4.object
    print "fh is", repr(fh)



