#!/usr/bin/env python2

# nfs4lib.py - NFS4 library for Python. 
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

# TODO: Exceptions.
# Implement buffering in NFS4OpenFile.
# Translation of error- and operation codes to enums.
# FIXME: Error when transferring large files?


NFS_PROGRAM = 100003
NFS_VERSION = 4
NFS_PORT = 2049

BUFSIZE = 4096

import rpc
from nfs4constants import *
from nfs4types import *
import nfs4packer
import random
import array
import socket
import os
try:
    import pwd
except ImportError:
    class pwdStub:
	def getpwuid(self, uid):
	    return "winuser"
    pwd = pwdStub()


# Stubs for Win32 systems
if not hasattr(os, "getuid"):
    os.getuid = lambda: 1

if not hasattr(os, "getgid"):
    os.getgid = lambda: 1

if not hasattr(os, "getgroups"):
    os.getgroups = lambda: []


# All NFS errors are subclasses of NFSException
class NFSException(Exception):
	pass

class BadCompoundRes(NFSException):
    def __init__(self, operation, errcode):
        self.operation = operation
        self.errcode = errcode

    def __str__(self):
        return "operation %d gave result %d" % (self.operation, self.errcode)

class DummyNcl:
    def __init__(self, packer=None, unpacker=None):
	self.packer = packer
	self.unpacker = unpacker

class PartialNFS4Client:
    def __init__(self):
        # Client state variables
        self.clientid = None
        self.verifier = None
        # Current directory. A string, like /doc/foo.
	# FIXME: Consider using a list of components instead. 
        self.cwd = "/"
        # Last seqid
        self.seqid = 0

    
    def addpackers(self):
 	# Pass a reference to ourself to NFS4Packer and NFS4Unpacker. 
        self.packer = nfs4packer.NFS4Packer(self)
        self.unpacker = nfs4packer.NFS4Unpacker(self, '')

    #
    # RPC procedures
    #

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

    def get_seqid(self):
        self.seqid += 1
        self.seqid = self.seqid % 2**32L
        return self.seqid

    def get_pathname(self, filename):
	if filename[0] == os.sep:
            # Absolute path
            # Remove slash, begin from root. 
            filename = filename[1:]
            pathname = []
        else:
            # Relative path. Begin with cwd.
            pathname = str2pathname(self.cwd)

	return str2pathname(filename, pathname)

    # 
    # Operations. These come in two flawors: <operation>_op and <operation>.
    #
    # <operation>_op: This is just a wrapper which creates a
    # nfs_argop4.  The arguments for the method <operation>_op should
    # be the same as the arguments for <operation>4args. No default
    # arguments or any other kind of intelligent handling should be
    # done in the _op methods.
    #
    # <operation>: This is a convenience method. It can have default arguments 
    # and operation-specific arguments. Not all operations have <operation>
    # methods. It's pretty useless for operations without arguments, for example.
    # Eg., if the <operation> method doesn't do anything, it should not exist. 
    #
    # The _op method should be defined first. Look at read_op and read for an
    # example.
    #
    # 
    def access_op(self, access):
	args = ACCESS4args(self, access)
	return nfs_argop4(self, argop=OP_ACCESS, opaccess=args)

    def close_op(self, seqid, stateid):
        args = CLOSE4args(self, seqid, stateid)
        return nfs_argop4(self, argop=OP_CLOSE, opclose=args)

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

    def getattr_op(self, attr_request):
	args = GETATTR4args(self, attr_request)
        return nfs_argop4(self, argop=OP_GETATTR, opgetattr=args)

    def getattr(self, attrlist=[]):
	# The argument to GETATTR4args is a list of integers. 
	attr_request = []
	for attr in attrlist:
	    # Lost? Se section 2.2 in RFC3010. 
	    arrintpos = attr / 32
	    bitpos = attr % 32
	    
	    while (arrintpos+1) > len(attr_request):
		attr_request.append(0)

	    arrint = attr_request[arrintpos]
	    arrint = arrint | (1L << bitpos)
	    attr_request[arrintpos] = arrint

	return self.getattr_op(attr_request)

    def getfh_op(self):
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

    def lookup_op(self, path):
	args = LOOKUP4args(self, path)
	return nfs_argop4(self, argop=OP_LOOKUP, oplookup=args)

    def lookupp(self):
        # FIXME
        raise NotImplementedError()

    def nverify(self):
        # FIXME
        raise NotImplementedError()

    def open_op(self, claim, openhow, owner, seqid, share_access, share_deny):
	args = OPEN4args(self, claim, openhow, owner, seqid, share_access, share_deny)
        return nfs_argop4(self, argop=OP_OPEN, opopen=args)

    def open(self, claim=None, how=UNCHECKED4, owner=None, seqid=None,
             share_access=OPEN4_SHARE_ACCESS_READ, share_deny=OPEN4_SHARE_DENY_NONE,
             clientid=None, file=None, opentype=OPEN4_NOCREATE):
        
        if not claim:
            claim = open_claim4(self, claim=CLAIM_NULL, file=file)

        if not owner:
	    # FIXME: Change to PID?
	    # FIXME: variable clashing: owner. 
            owner = pwd.getpwuid(os.getuid())[0]

        if not clientid:
            clientid = self.clientid

        if not seqid:
            seqid = self.get_seqid()

        openhow = openflag4(self, opentype=opentype, how=how)
        owner = nfs_lockowner4(self, clientid=clientid, owner=owner)

        return self.open_op(claim, openhow, owner, seqid, share_access, share_deny)

    def openattr(self):
        # FIXME
        raise NotImplementedError()

    def open_confirm(self):
        # FIXME
        raise NotImplementedError()

    def open_downgrade(self):
        # FIXME
        raise NotImplementedError()

    def putfh_op(self, object):
        args = PUTFH4args(self, object)
        return nfs_argop4(self, argop=OP_PUTFH, opputfh=args)

    def putpubfh(self, fh):
        # FIXME
        raise NotImplementedError()

    def putrootfh_op(self):
        return nfs_argop4(self, argop=OP_PUTROOTFH)

    def read_op(self, stateid, offset, count):
	args = READ4args(self, stateid, offset, count)
	return nfs_argop4(self, argop=OP_READ, opread=args)

    def read(self, stateid=0, offset=0, count=0):
	return self.read_op(stateid, offset, count)

    def readdir_op(self, cookie, cookieverf, dircount, maxcount, attr_request):
	args = READDIR4args(self, cookie, cookieverf, dircount, maxcount, attr_request)
	return nfs_argop4(self, argop=OP_READDIR, opreaddir=args)

    def readdir(self, cookie=0, cookieverf="", dircount=2, maxcount=4096, attr_request=[]):
	return self.readdir_op(cookie, cookieverf, dircount, maxcount, attr_request)

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

    def setclientid_op(self, client, callback):
	args = SETCLIENTID4args(self, client, callback)
        return nfs_argop4(self, argop=OP_SETCLIENTID, opsetclientid=args)

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

	return self.setclientid_op(client_id, callback)

    def setclientid_confirm_op(self, setclientid_confirm):
	args = SETCLIENTID_CONFIRM4args(self, setclientid_confirm)
        return nfs_argop4(self, argop=OP_SETCLIENTID_CONFIRM, opsetclientid_confirm=args)

    def verify(self):
        # FIXME
        raise NotImplementedError()

    def write_op(self, stateid, offset, stable, data):
	args = WRITE4args(self, stateid, offset, stable, data)
	return nfs_argop4(self, argop=OP_WRITE, opwrite=args)

    def write(self, data, stateid, offset=0, stable=UNSTABLE4):
        return self.write_op(stateid, offset, stable, data)

    def cb_getattr(self):
        # FIXME
        raise NotImplementedError()

    def cb_recall(self):
        # FIXME
        raise NotImplementedError()
    
    #
    # NFS convenience methods. Calls server. 
    #
    def init_connection(self):
        # SETCLIENTID
        setclientidop = self.setclientid()
        res =  self.compound([setclientidop])

        check_result(res)
        
        self.clientid = res.resarray[0].arm.resok4.clientid
        setclientid_confirm = res.resarray[0].arm.resok4.setclientid_confirm

        # SETCLIENTID_CONFIRM
        setclientid_confirmop = self.setclientid_confirm_op(setclientid_confirm)
        res =  self.compound([setclientid_confirmop])

        check_result(res)
        

    def do_read(self, fh, offset=0, size=None):
        putfhop = self.putfh_op(fh)
        data = ""

        while 1:
            readop = self.read(count=BUFSIZE, offset=offset)
            res = self.compound([putfhop, readop])
            check_result(res)
            data += res.resarray[1].arm.arm.data
            
            if res.resarray[1].arm.arm.eof:
                break

            # Have we got as much as we were asking for?
            if size and (len(data) >= size):
                break

            offset += BUFSIZE

        if size:
            return data[:size]
        else:
            return data

    def do_write(self, fh, data, stateid, offset=0, stable=UNSTABLE4):
        putfhop = self.putfh_op(fh)
	writeop = self.write(data, stateid, offset=offset, stable=stable)
	res = self.compound([putfhop, writeop])
	check_result(res)

    def do_close(self, fh, stateid):
        seqid = self.get_seqid()
        putfhop = self.putfh_op(fh)
        closeop = self.close_op(seqid, stateid)
        res = self.compound([putfhop, closeop])
        check_result(res)

        return res.resarray[1].arm.stateid

    def do_readdir(self, fh, attr_request=[]):
	# Since we may not get whole directory listing in one readdir request,
	# loop until we do. For each request result, create a flat list
	# with <entry4> objects. 
	cookie = 0
	cookieverf = ""
	entries = []
	while 1:
	    putfhop = self.putfh_op(fh)
	    readdirop = self.readdir(cookie, cookieverf, attr_request=attr_request)
	    res = self.compound([putfhop, readdirop])
	    check_result(res)

	    entry = res.resarray[1].arm.arm.reply.entries[0]

	    while 1:
		entries.append(entry)
		cookie = entry.cookie
		if not entry.nextentry:
		    break
		entry = entry.nextentry[0]
	    
	    if res.resarray[1].arm.arm.reply.eof:
		break
	    
	    cookieverf = res.resarray[1].arm.arm.cookieverf

	return entries
	
        
#
# Misc. helper functions. 
#
def check_result(compoundres):
    if not compoundres.status:
        return

    for resop in compoundres.resarray:
        if resop.arm.status:
            raise BadCompoundRes(resop.resop, resop.arm.status)

def str2pathname(str, pathname=[]):
    pathname = pathname[:]
    for component in str.split("/"):
        if (component == "") or (component == "."):
            pass
        elif component == "..":
            pathname = pathname[:-1]
        else:
            pathname.append(component)
    return pathname

def opaque2long(data):
    import struct
    result = 0L
    # Decode 4 bytes at a time. 
    for intpos in range(len(data)/4):
	integer = data[intpos*4:intpos*4+4]
	val = struct.unpack(">L", integer)[0]
	shiftbits = (len(data)/4 - intpos - 1)*64
	result = result | (val << shiftbits)

    return result

def get_attrbitpos():
    # Get dictionary with attribute bit positions
    import nfs4constants
    attrbitpos = {}
    for name in dir(nfs4constants):
	if name.startswith("FATTR4_"):
	    attrname = name[7:].lower()
	    attrbitpos[attrname] = eval("nfs4constants." + name)
	    
    return attrbitpos

def get_attrunpackers(unpacker):
    # Get dictionaries with attribute unpackers
    import nfs4packer
    attrunpackers = {}
    for name in dir(nfs4packer.NFS4Unpacker):
	if name.startswith("unpack_fattr4"):
	    attrname = name[14:]
	    attrunpackers[attrname] = eval("unpacker.unpack_fattr4_" + attrname)

    return attrunpackers

def fattr2dict(obj):
    # Convert a fattr4 object to a dictionary like
    # {"size": 4711}

    attrbitpos = get_attrbitpos()

    # Construct a dictionary with the attributes to unpack.
    # Example: {53: 'time_modify', 4: 'size', 8: 'fsid'}
    unpack_these = {}
    for intpos in range(len(obj.attrmask)):
	integer = obj.attrmask[intpos]
	
	for attr in attrbitpos.keys():
	    bitnum = attrbitpos[attr]

	    if bitnum in range(intpos * 32, (intpos+1) * 32):
		bitpos = bitnum % 32
		bitvalue = 1L << bitpos

		if integer & bitvalue:
		    unpack_these[bitnum] = attr

    # Construct a dummy Client. 
    ncl = DummyNcl()
    # Construct a Unpackar with our object data. 
    unpacker = nfs4packer.NFS4Unpacker(ncl, obj.attr_vals)
    ncl.unpacker = unpacker

    result = {}
    attrunpackers = get_attrunpackers(unpacker)
    bitnums_to_unpack = unpack_these.keys()
    # The data on the wire is ordered according to attribute bit number. 
    bitnums_to_unpack.sort()
    for bitnum in bitnums_to_unpack:
	attrname = unpack_these[bitnum]
	unpack_method = attrunpackers[attrname]
	result[attrname] = unpack_method()

    return result


class UDPNFS4Client(PartialNFS4Client, rpc.RawUDPClient):
    def __init__(self, host, port=NFS_PORT):
        rpc.RawUDPClient.__init__(self, host, NFS_PROGRAM, NFS_VERSION, port)
        PartialNFS4Client.__init__(self)

    def mkcred(self):
	if self.cred == None:
            hostname = socket.gethostname()
            uid = os.getuid()
            gid = os.getgid()
            groups = os.getgroups()
	    self.cred = (rpc.AUTH_UNIX, rpc.make_auth_unix(1, hostname, uid, gid, groups))
	return self.cred

    def mkverf(self):
	if self.verf == None:
	    self.verf = (rpc.AUTH_NULL, rpc.make_auth_null())
	return self.verf


class TCPNFS4Client(PartialNFS4Client, rpc.RawTCPClient):
    def __init__(self, host, port=NFS_PORT):
        rpc.RawTCPClient.__init__(self, host, NFS_PROGRAM, NFS_VERSION, port)
        PartialNFS4Client.__init__(self)

        

class NFS4OpenFile:
    """Emulates a Python file object.
    """
    # BUGS: If pos is set beyond file size and data is later written,
    # we should fill in zeros. 
    def __init__(self, ncl):
        self.ncl = ncl
        self.__set_priv("closed", 1)
        self.__set_priv("mode", "")
        self.__set_priv("name", "")
        self.softspace = 0
        self.pos = 0L
        # NFS4 file handle. 
        self.fh = None
        # NFS4 stateid
        self.stateid = None

    def __setattr__(self, name, val):
        if name in ["closed", "mode", "name"]:
            raise TypeError("read only attribute")
        else:
            self.__set_priv(name, val)

    def __set_priv(self, name, val):
        self.__dict__[name] = val

    def open(self, filename, mode="r", bufsize=BUFSIZE):
	pathname = self.ncl.get_pathname(filename)

        putrootfhop = self.ncl.putrootfh_op()

	if mode == "r":
	    share_access = OPEN4_SHARE_ACCESS_READ
	elif mode == "w":
	    share_access = OPEN4_SHARE_ACCESS_WRITE
	else:
	    # FIXME: More modes allowed. 
	    raise TypeError("Invalid mode")
	
        openop = self.ncl.open(file=pathname, share_access=share_access)
        getfhop = self.ncl.getfh_op()
        res =  self.ncl.compound([putrootfhop, openop, getfhop])

        check_result(res)
        
        self.__set_priv("closed", 0)
        self.__set_priv("mode", mode)
        self.__set_priv("name", os.path.join(os.sep, *pathname))
        self.stateid = res.resarray[1].arm.arm.stateid
        self.fh = res.resarray[2].arm.arm.object
        

    def close(self):
        if not self.closed:
            self.__set_priv("closed", 1)
            self.ncl.do_close(self.fh, self.stateid)

    def flush(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        raise NotImplementedError()

    # isatty() should not be implemented.

    # fileno() should not be implemented.

    def read(self, size=None):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        data = self.ncl.do_read(self.fh, self.pos, size)
        self.pos += len(data)
        return data

    def readline(self, size=None):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        data = self.ncl.do_read(self.fh, self.pos, size)
        
        if data:
            line = data.split("\n", 1)[0] + "\n"
            self.pos += len(line)
            return line
        else:
            return ""

    def readlines(self, sizehint=None):
        if self.closed:
            raise ValueError("I/O operation on closed file")
        data = self.ncl.do_read(self.fh, self.pos)

        self.pos += len(data)

        lines = data.split("\n")
        if lines[len(lines)-1] == "":
            lines = lines[:-1]
        
        # Append \n on all lines.
        return map(lambda line: line + "\n", lines)

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
	    putfhop = self.ncl.putfh_op(self.fh)
	    getattrop = self.ncl.getattr([FATTR4_SIZE])
	    res =  self.ncl.compound([putfhop, getattrop])
	    check_result(res)
	    size = opaque2long(res.resarray[1].arm.arm.obj_attributes.attr_vals)
	    newpos = size + offset
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
        # FIXME: SETATTR can probably be used. 
        raise NotImplementedError()
        
    def write(self, data):
        if self.closed:
            raise ValueError("I/O operation on closed file")

	self.ncl.do_write(self.fh, data, stateid=self.stateid, offset=self.pos)
	self.pos += len(data)

    def writelines(self, list):
        if self.closed:
            raise ValueError("I/O operation on closed file")
    
	for line in list:
	    self.write(line)

if __name__ == "__main__":
    # Demo
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
    print "Root filehandles is", repr(fh)


# Local variables:
# py-indent-offset: 4
# tab-width: 8
# End:
