import time
from pathlib import Path,PosixPath
from . import encrypt
from .file_server import web_server
import hashlib
import json
import os,sys
import re
import numpy as np
import threading
import getpass
import subprocess
import socket #导入socket模块
import threading
import math as _math
import array as _array
from urllib.request import quote
try:
    from . import songziviewer,get_input_ui
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except:
    pass

import click
# import shutil 
ENCODE_CODE = b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
CODE_SET=bytearray(256)
for i,j in enumerate(ENCODE_CODE):
    CODE_SET[j]=i

global_dict = {'db':None,'passwd':None,'version':1,'replace':False,'gui':False}

def toN(b,base=36):
    nb = len(b) 
    n = int.from_bytes(b,'big')
    t = bytearray(int(nb*(_math.log(256)/_math.log(base))+2))
    ii = 0
    while n!=0:
        n,y = divmod(n,base)
        t[ii] = y
        ii += 1
    s = t[:ii][::-1]
    return s 


def spencode3(cryptor,b,str_set=b''):
    if not b:return b
    b=cryptor.encrypt(pad(b,16))
    ns=len(str_set)
    x=_array.array('L')
    w=_math.ceil(8*_math.log(256)/_math.log(ns))
    x.frombytes(b)
    y=bytearray(len(x)*w)
    t=0
    for i in x:
        for j in range(w-1,-1,-1):
            i,m = divmod(i,ns)
            y[t+j]=str_set[m]
        t+=w
    return y

def spdecode3(cryptor,b,str_set=b'',t_set=None):
    if not b:return b
    nb,ns=len(b),len(str_set)
    x=_array.array('L',[0])
    w=_math.ceil(8*_math.log(256)/_math.log(ns))
    x*=nb//w
    t=0
    for i in range(nb//w):
        s=0
        for j in range(t,t+w):
            s=s*ns+t_set[b[j]]
        t+=w
        x[i]=s
    b=x.tobytes()
    if(len(b)%16 == 0):
        b=unpad(cryptor.decrypt(b),16)
    else:
        b = b''
    return b

class yxs_encrypt:
    def __init__(self,passwd):
        m = hashlib.md5(passwd.encode()).digest()
        self.lenp = 101 + m[10] % 71
        for _ in range(10):
            m += hashlib.md5(passwd.encode()+m).digest()
        self.passwd_md5 = np.frombuffer(m[:self.lenp],dtype='uint8')
        self.passwd_arr = self.passwd_md5.copy()
    def encode(self,bs,start_pos):
        data = np.frombuffer(bs,dtype='uint8').copy()
        lenp = self.lenp
        istart = start_pos % lenp
        passwd_arr = self.passwd_arr
        passwd_arr[:lenp-istart] = self.passwd_md5[istart:]
        passwd_arr[lenp-istart:] = self.passwd_md5[:istart]
        nrows = data.size // lenp 
        left = data.size - nrows*lenp 
        if nrows>0:
            m = data[:nrows*lenp].reshape(nrows,-1)
            m += passwd_arr
        if left>0:
            data[-left:] += passwd_arr[:left]
        return data.tobytes()
    def decode(self,bs,start_pos):
        data = np.frombuffer(bs,dtype='uint8').copy()
        lenp = self.lenp
        istart = start_pos % lenp
        passwd_arr = self.passwd_arr
        passwd_arr[:lenp-istart] = self.passwd_md5[istart:]
        passwd_arr[lenp-istart:] = self.passwd_md5[:istart]
        nrows = data.size // lenp 
        left = data.size - nrows*lenp 
        if nrows>0:
            m = data[:nrows*lenp].reshape(nrows,-1)
            m -= passwd_arr
        if left>0:
            data[-left:] -= passwd_arr[:left]
        return data.tobytes()

class file_database:
    def __init__(self,dirname=None,database_name='.yxs_file_database.xdb'):
        if global_dict['db'] is not None:
            database_name = global_dict['db']
        self.dirname = dirname 
        if self.dirname:
            self.database = Path(self.dirname) / database_name
        else:
            self.dirname = './'
            self.database = Path(database_name)
        self.database_data = None
        self.file_info = dict()
    def create(self):
        dict2str = lambda x:'{'+','.join([f'{k}:{v}' for k,v in x.items()])+'}'
        fmt = '{zonename}{ftype}{is_link}__:{data}//{info}\n'
        fp = open(self.database,'w')
        fp.write('''#{zonename}{ftype}{is_link}__:{data}//{dict_info}\n''')
        for root,dirs,fs in os.walk(self.dirname,followlinks=True):
            proot = Path(root)
            l = 'l' if proot.is_symlink() else '_'
            info = {'size':0,'st_mtime':int(proot.stat().st_mtime)}
            fp.write(fmt.format(zonename='z',ftype='d',is_link=l,data=root,info=dict2str(info)))
            for d in dirs:
                kf = proot/d
                if kf.exists():
                    l = 'l' if kf.is_symlink() else '_'
                    info = {'size':0,'st_mtime':int(kf.stat().st_mtime)}
                    fp.write(fmt.format(zonename='_',ftype='d',is_link=l,data=d,info=dict2str(info)))
            for f in fs:
                kf = proot/f
                l = 'l' if kf.is_symlink() else '_'
                if kf.exists():
                    info = {'size':kf.stat().st_size,'st_mtime':int(kf.stat().st_mtime)}
                    fp.write(fmt.format(zonename='_',ftype='f',is_link=l,data=f,info=dict2str(info)))
        fp.close()
    def read(self):
        fp = open(self.database)
        result = {}

        for it in fp:
            kk = it.split('//{')
            i = kk[0]
            ztype = i[0]
            if ztype == '#':
                continue 
            elif ztype == 'z':
                files = list()
                zone_name = Path(i[6:])
                dt = kk[1].rstrip()[:-1]
                dd = dict([i.split(':') for i in dt.split(',')])
                dd['files'] = files
                dd['attribute'] = i[:5]
                self.file_info[str(zone_name)] = dd
                result[i[6:]] = dd
            elif ztype == '_':
                dt = kk[1].rstrip()[:-1]
                dd = dict([i.split(':') for i in dt.split(',')])
                dd['attribute'] = i[:5]
                self.file_info[str(zone_name/i[6:])] = dd
                files.append((i[:5],i[6:],dd))
        self.database_data = result 
        return self.database_data
    def write(self,oname=None):
        if oname is None:
            oname = self.database
        fp = open(oname,'w')
        fmt = '{attribute}:{data}//{{{info}}}\n'
        fp.write('''#{zonename}{ftype}{is_link}__:{data}//{dict_info}\n''')

        for k,v in self.database_data.items():
            if v is None:
                continue
            stat = ','.join([f'{kk}:{val}' for kk,val in v.items() if kk!='files' and kk!='attribute'])
            fp.write(fmt.format(attribute=v['attribute'],data=k,info=stat))
            for att,f,dt in v['files']:
                stat=','.join([f'{kk}:{val}' for kk,val in dt.items() if kk!='attribute'])
                fp.write(fmt.format(attribute=att,data=f,info=stat))
    def _update_key(self,zdd,xdb):
        if zdd in xdb:
            return 
        p = Path(zdd)
        files = list()
        xdb[zdd] = {'size':0,'st_mtime':int(p.stat().st_mtime),'attribute':'zd___','files':files}
        for i in p.glob('*'):
            print('update',str(i))
            l = 'l' if i.is_symlink() else '_'
            f = 'f' if i.is_file() else 'd'
            stat = i.stat()
            att = f'_{f}{l}__'
            info = {'size':stat.st_size,'st_mtime':int(stat.st_mtime)}
            ss = att,i.name,info
            files.append(ss)

            pdd = f'./{i}'
            if f == 'd':
                self._update_key(pdd,xdb)
    def update(self):
        rr = dict()
        database_data = self.database_data
        dirs = [root+os.sep+d for root,ds,_ in os.walk('.',followlinks=True) for d in ds]
        dirs.append('./')
        dirs = set(dirs)
        for k,v in database_data.items():
            if k in dirs:
                p = Path(k)
                new_mtime = p.stat().st_mtime
                if new_mtime > int(v['st_mtime']):
                    files = list()
                    v_names = {ii[1]:ii for ii in  v['files']}
                    database_data[k] = {'size':0,'st_mtime':int(new_mtime),'attribute':'zd___','files':files}
                    for i in p.glob('*'):
                        namet = i.name
                        if namet in v_names:
                            files.append(v_names[namet])
                        else:
                            if i.exists():
                                print('update',str(i))
                                l = 'l' if i.is_symlink() else '_'
                                f = 'f' if i.is_file() else 'd'
                                stat = i.stat()
                                att = f'_{f}{l}__'
                                info = {'size':stat.st_size,'st_mtime':int(stat.st_mtime)}
                                ss = att,namet,info
                                files.append(ss)

                                pdd = f'./{i}'
                                if f == 'd' and pdd not in database_data:
                                    self._update_key(pdd,rr)
            else:
                database_data[k] = None
        database_data.update(rr)

    def find(self,find_str):
        if self.database_data is None:
            self.read()
        find_str = find_str.lower()
        fmt = '{} -> {}'
        db = self.database_data
        rr = []
        for zone_name in db:
            rootp = Path(zone_name)
            nad = yxsFile(rootp.name).decode_filename().name
            if nad.lower().find(find_str) != -1:
                print('dirname:',fmt.format(nad,zone_name))
                rr.append(('d',zone_name))
            for ftt in db[zone_name]['files']:
                attri,i = ftt[:2]
                rp = rootp / i 
                if attri[1] == 'f' and attri[2] == '_':
                    t = str(yxsFile(i).decode_filename())
                    if t.lower().find(find_str) != -1:
                        tname = rootp / t
                        iname = rootp / i
                        if t != i:
                            tname = [yxsFile(i).decode_filename().name for i in tname.parts]
                            tname = os.sep.join(tname)
                            print(fmt.format(tname,iname))
                            
                        else:
                            print(iname)
                        rr.append(('f',iname))
        return rr
    def to_name_list(self):
        if self.database_data is None:
            self.read()
        rr = []
        db = self.database_data
        for zone_name in db:
            rootp = Path(zone_name)
            
            for ftt in db[zone_name]['files']:
                attri,i = ftt[:2]
                if attri[1] == 'f' and attri[2] == '_':
                    t = str(yxsFile(i).decode_filename())
                    rr.append(t.upper())
        return rr
mysuffix_dict = {'.xsd':'.0f','.xsf':'.0f','.jpxs':'.0g','.mpxs':'.0h'}
class yxsFile:
    t = ['.jpg','.jpeg','.png','.webp','.gif','.bmp']
    jpg_suffix = set(t+[i.upper() for i in t])
    XS_SUFFIX = set(('.xsd','.xsf','.mpxs','.jpxs','.0g','.0h','.0d','.0f'))
    passwd_v1 = encrypt.get_default_passwd()
    def __init__(self,filename,workdir=None,passwd=None,version=None):
        if not version:
            version = global_dict['version']
        self.version = version
        self.encode_func = None 
        self.decode_func = None
        if not passwd and global_dict['passwd']:
            passwd = global_dict['passwd']
        if not passwd:
            passwd = self.passwd_v1
        self.filename = Path(str(filename))
        self.title_size = 2048
        self.passwd = passwd
        # self.file_suffix = '.mpxs','.jpxs','.xsf'
        if self.filename.suffix in self.XS_SUFFIX:
            self.is_pureFile = False
        else:
            self.is_pureFile = True
        self.workdir = workdir 
        if workdir is None:
            self.workdir = self.filename.parent
        self._fp = None 
        self._pos = 0
        self._offset = 0
        self._aes_crypto = None
        self._head_info = None

        self.file_name_origin = self.filename
        self.check_origin_filename = False
        
    def get_origin_filename(self):
        if self.check_origin_filename:
            return self.file_name_origin
        if self.filename.suffix == '.0h':
            if self.filename.stat().st_size < 2048*2:
                fp = open(self.filename,'rb')
                t = fp.read(2048*2)
                if t.startswith(b'yxslink:'):
                    sf = t.decode('utf8')
                    self.file_name_origin = Path(sf[8:].strip())
        self.check_origin_filename = True 
        return self.file_name_origin
    def to_pureFile(self,to_dir = None,output=None,force=False):
        if not self.is_pureFile:
            fp   = open(self.get_origin_filename(),'rb')
            tts = fp.read(self.title_size)
            info = parse_header(tts,self.passwd)
            title = output
            if not title:
                title = info['name']
            if not title:
                title = self.filename.stem + '.pure_xs'
            new_name = self.filename.parent/title
            if to_dir:
                new_name = Path(to_dir)/new_name.name
            if new_name.is_file():
                if force or global_dict['replace']:
                    os.remove(new_name)
                else:
                    print('File already exists!',new_name)
                    return None
            tempfn = new_name.with_suffix('.temp_YXS')
            fpp = open(tempfn,'wb')
            bsize = 1024*1024*8
            t = self.read(bsize)
            while t != b'':
                fpp.write(t)
                t = self.read(bsize)
            fpp.close()
            os.rename(tempfn,new_name)
        else: 
            new_name = None 
        return new_name

    def to_encrypt(self,bs):
        if self.version == 2:
            if self.encode_func is None:
                self.encode_func = yxs_encrypt(self.passwd)
                self.ipos = 0 
            bn = self.encode_func.encode(bs,self.ipos)
            self.ipos += len(bs)
            bs = bn 
        if self.version == 3:
            if len(bs) % 16 != 0:
                bs = pad(bs,16)
            return self._aes_encode(bs)
        return bs

    def to_yxsFile(self,to_dir=None,force=False,fp=None,xs_name = None,st_size=None):
        if self.is_pureFile or xs_name:
            yxs_filenme = self.encode_filename()
            if to_dir:
                yxs_filenme = Path(to_dir) / yxs_filenme.name 
            print(force,global_dict['replace'])
            if yxs_filenme.is_file() and not xs_name:
                if force or global_dict['replace']:
                    
                    os.remove(yxs_filenme)
                else:
                    print('File already exists!',yxs_filenme)
                    return None
            if xs_name:
                yxs_filenme = Path(xs_name)

            tempfn = yxs_filenme.with_suffix('.temp_YXS')
            fpxs = open(tempfn,'wb',buffering=1024*1024*1024)
            if not fp:
                fp   = open(self.filename,'rb')
                length = self.filename.stat().st_size
            else:
                length = st_size 
            info = {'name':self.filename.name,'ver':self.version}
            info['len'] = length
            jds = json.dumps(info,ensure_ascii=False).encode()
            if self.version == 3:
                tbytes = bytes([0]*(self.title_size-16-len(jds)))
                t = jds+tbytes 
                t = b'/3'+b'_'*14 + self._aes_encode(t)
            else:
                tbytes = bytes([0]*(self.title_size-9-len(jds)))
                t = jds+tbytes
                t = b'/_______'+encrypt.encode(t,self.passwd)
                self.encode_func = None 

            while t != b'':
                fpxs.write(t)
                t = fp.read(1024*1024*32)
                t = self.to_encrypt(t)
            fpxs.close()
            os.rename(tempfn,yxs_filenme)
        else:
            yxs_filenme = None 
        return yxs_filenme

    def play_video(self):
        os.chdir(self.get_origin_filename().absolute().parent)
        url = 'http://0.0.0.0:9090/file_downloader/x./'+quote(self.get_origin_filename().name)
        td = threading.Thread(target=web_server.main,args=(9090,False))
        td.setDaemon(True)
        td.start()
        stat,_ = subprocess.getstatusoutput('which vlc')
        if stat == 0:
            os.system(f'vlc {url} > /dev/null')
        else:
            print(f'You can also copy the url to browser to play the video: {url}')
            td.join()
    def view_image(self):
        songziviewer.main(self.get_origin_filename())
    def encode_filename(self,filename=None):
        if not filename:
            filename = self.filename
        else:
            filename = Path(filename)
        name = filename.name
        suffix = filename.suffix 
        if suffix in self.XS_SUFFIX:
            return filename

        if suffix in self.jpg_suffix:
            mysuffix = '.jpxs'
            name = filename.stem
        elif suffix == '.mp4':
            mysuffix = '.mpxs'
            name = filename.stem
        else:
            mysuffix = '.xsf'
        length= len(name)
        name1 = name[:length]
        version = self.version
        while True:
            if version == 3:
                if not self._aes_crypto:
                    self.aeskey()
                spname = spencode3(self._aes_crypto,name1.encode(),str_set=ENCODE_CODE).decode()
            else:
                spname = encrypt.spencode(name1.encode(),self.passwd,str_set=ENCODE_CODE).decode()
            if len(spname)< 250:
                break 
            else:
                length = int(length / 2)
                name1 = name[:length] + str(hash(name))[-4:]
        if version == 3:
            mysuffix = mysuffix_dict[mysuffix]
        if self.version != 1:
            mysuffix = f'.{self.version}'+mysuffix
        spname = spname + mysuffix 
        return filename.parent/ spname
    def decode_filename(self):
        suffix = self.filename.suffix 
        if self.passwd != 'nopasswd' and suffix in self.XS_SUFFIX:
            stem = self.filename.stem
            if stem[-2] == '.':
                version = int(stem[-1])
                stem = stem[:-2]
            else:
                version = 1 
            if version == 1:
                passwd_temp = self.passwd_v1
            else: 
                passwd_temp = self.passwd
            if version != self.version and self.version == 3:
                return self.filename
            if version == 3:
                if not self._aes_crypto:
                    self.aeskey()
                spname = spdecode3(self._aes_crypto,stem.encode(),str_set=ENCODE_CODE,t_set=CODE_SET).decode()
            else:
                spname = encrypt.spdecode(stem.encode(),passwd_temp,str_set=ENCODE_CODE).decode()
            if not spname:
                spname = self.filename.stem
            if suffix == '.mpxs' or suffix == '.0h':
                mysuffix = '.mp4'
            elif suffix == '.jpxs' or suffix == '.0g':
                mysuffix = '.jpg'
            else: 
                mysuffix = ''

            return self.filename.parent / (spname+mysuffix)
        else:
            return self.filename

    def get_md5(self):
        fp = open(self.get_origin_filename(),'rb')
        if not self.is_pureFile:
            fp.read(self.title_size)
        md5 = hashlib.md5()
        while True:
            t = fp.read(1024*1024*4)
            if t == b'':
                break
            md5.update(t)
        return md5
    def get_data(self):
        return self.read()
    def read(self,BUFFER_SIZE=-1):
        if not self._fp:
            self._fp = open(self.get_origin_filename(),'rb')
            if not self.is_pureFile:
                self._offset = self.title_size
                tts = self._fp.read(self.title_size)
                if self.filename.stem[-2] != '.':
                    self.passwd = self.passwd_v1
                self._head_info = parse_header(tts,self.passwd)
                self._version = self._head_info['ver']
                if self._version == 2:
                    self.decodef = yxs_encrypt(self.passwd)
        if self.is_pureFile:
            self._fp.seek(self._pos,0)
            rbytes = self._fp.read(BUFFER_SIZE)
        else:
            version = self._version
            if version <= 2:
                self._fp.seek(self._pos+self._offset,0)
                rbytes = self._fp.read(BUFFER_SIZE)
                if version == 2:
                    rbytes = self.decodef.decode(rbytes,self._pos) 
            elif version == 3:
                length = self._head_info['len']
                if BUFFER_SIZE < 0:
                    BUFFER_SIZE = length
                tail1 = self._pos % 16
                opos = self._pos
                self._pos -= tail1
                lth = BUFFER_SIZE+tail1
                tail2 = lth % 16
                if tail2 != 0:
                    lth += 16 - tail2
                self._fp.seek(self._pos+self._offset,0)
                rbytes = self._fp.read(lth)
                rbytes = self._aes_decode(rbytes)
                bias = (self._pos + len(rbytes)) - length
                if bias>0:
                    rbytes = rbytes[:-bias]
                rbytes = rbytes[tail1:tail1+BUFFER_SIZE]
                self._pos = opos
            else:
                raise Exception('version error',self._version)
        self._pos += len(rbytes)
        return rbytes
    def seek(self,pos,where):
        assert where == 0
        self._pos = pos
    def close(self):
        if self._fp:
            self._fp.close()
    def file_size(self):
        if self.is_pureFile:
            return self.get_origin_filename().stat().st_size
        else:
            stem = self.get_origin_filename().stem
            if stem.endswith('.3'):
                t = open(self.get_origin_filename(),'rb').read(self.title_size)
                head_info = parse_header(t,self.passwd)
                size = head_info['len']
            else:
                size = self.get_origin_filename().stat().st_size - self.title_size
            return size
    
    def aeskey(self):
        key = self.passwd.encode()
        if len(key) != 24:
            key = (key*(24//len(key)+1))[:24]
        self._aes_crypto = AES.new(key,AES.MODE_ECB)
    def _aes_encode(self,data):
        if self._aes_crypto is None:
            self.aeskey()
        return self._aes_crypto.encrypt(data)
    def _aes_decode(self,data):
        if self._aes_crypto is None:
            self.aeskey()
        return self._aes_crypto.decrypt(data)
    def get_head_info(self):
        if self._head_info is None:
            tts = open(self.get_origin_filename(),'rb').read(self.title_size)
            if self.get_origin_filename().stem[-2] != '.':
                self.passwd = self.passwd_v1
            self._head_info = parse_header(tts,self.passwd)
        return self._head_info

def parse_header(hd,passwd=None):
    if not passwd:
        passwd = yxsFile.passwd_v1 
    ht = hd[:2]
    if ht == b'/_':
        jds = encrypt.decode(hd[8:],passwd)
        jds = jds.replace(bytes([0]),b'').decode()
        info = json.loads(jds)
    elif ht == b'/3':
        jds = encrypt.decode_AES(hd[16:],passwd)
        jds = jds.replace(bytes([0]),b'').decode()
        info = json.loads(jds)
    else:
        info = dict()
        t = hd.replace(bytes([0]),b'').decode()
        if len(t) > 2000:
            t = None 
        info['name'] = t
        info['ver'] = 1
    return info
def listdir(dirname):
    result = []
    igetp = True
    for i in os.listdir(dirname):
        if Path(i).stem[-2] == '.' and igetp:
            igetp = False
            global_dict['passwd'] = get_passwd()
        t = str(yxsFile(i).decode_filename())
        result.append((t,len(t),i))
    result.sort(key = lambda x:x[0])
    max_length = max([i[1] for i in result])
    f = '{:'+str(max_length+2)+'s}-> {}'
    for dname,_,ename in result:

        if dname != ename:
            print(f.format(dname,ename))
        else:
            print(dname)
class SPath(PosixPath):
    global_xdb = {}
    def glob(self,ftype):
        xdb_key,xp = self.get_xdb_ps()
        xdb_data = self.global_xdb[xdb_key].database_data
        parent = './'+str(xp)
        if parent == './.':
            parent = './'
        pp = Path(xdb_key) / parent
        if parent not in xdb_data:
            return []
        if ftype == '*':
            return [SPath(pp/ft[1],parent=self) for ft in xdb_data[parent]['files']]
        else:
            rr = []
            kre = re.compile(ftype.replace('*','.*'))
            for ft in xdb_data[parent]['files']:
                if kre.match(ft[1]):
                    rr.append(SPath(pp/ft[1],parent=self))
            return rr

    def is_file(self):
        if not self.global_xdb:
            return super().is_file()
        rr = self._is_core('f',1)
        return rr
    def is_dir(self):
        if not self.global_xdb:
            return super().is_dir()
        rr = self._is_core('d',1)
        return rr

    def is_file_abs(self):
        return super().is_file()
    def is_dir_abs(self):
        return super().is_dir()

    def is_symlink(self):
        if not self.global_xdb:
            return super().is_symlink()
        rr = self._is_core('l',2)
        return rr
    def _is_core(self,ftype,ind):
        xdb_key,xp = self.get_xdb_ps()
        if xdb_key is None:
            return False
        xdb_data = self.global_xdb[xdb_key].database_data
        parent = './'+str(xp.parent )
        if parent == './.':
            parent = './'
        fname = xp.name 
        if parent not in xdb_data:
            return False 
        else:
            for ft in xdb_data[parent]['files']:
                if ft[0][ind] == ftype and ft[1] == fname:
                    return True 
            return False

    def get_xdb_ps(self):
        abspath_str = str(self.absolute())
        for key in self.global_xdb.keys():
            if abspath_str.startswith(key):
                return key,Path(abspath_str[len(key)+1:])
        return None,None
    def add_xdb(self,xdb_name):
        xdb_key = str(Path(xdb_name).absolute().parent)
        if xdb_key in self.global_xdb:
            return None 
        else:
            self.global_xdb[xdb_key] = file_database(database_name=xdb_name)
            self.global_xdb[xdb_key].read() 
            return True
    def add_path(self):
        xdb_key,xp = self.get_xdb_ps()
        xdb_data = self.global_xdb[xdb_key].database_data
        parent = './'+str(xp.parent )
        if parent == './.':
            parent = './'
        fname = xp.name 
        xdb_data[parent]['files']

def find_file(find_str):
    if not global_dict['passwd']:
        global_dict['passwd'] = get_passwd()
    find_str = find_str.lower()
    db = file_database()
    if not db.database.exists():
        db.create()
    db.find(find_str)

def to_yxs_dir(dname,suffix_list,encode_dir):
    yxs_suffix = {'.jpxs','.mpxs','.xsf','.temp_YXS'}
    dir_list = [Path(dname)]
    for root,ds,fs in os.walk(dname):
        pr = Path(root)
        if encode_dir:
            dir_list.extend([pr/d for d in ds if not d.endswith('.xsd')])
        for f in fs:
            t = pr/f
            suffix = t.suffix
            if suffix in yxs_suffix or t.is_symlink():
                continue
            if suffix in suffix_list or suffix_list == '*':
                pf = yxsFile(t)
                ename = pf.encode_filename()
                print(t,'->',ename)
                pf.to_yxsFile()
                if global_dict['delete'] and ename.name != t.name:
                    os.remove(t)
    if encode_dir:
        dir_list.sort(key=lambda x:-len(x.parts))
        for d in dir_list:
            yname = yxsFile(d).encode_filename()
            print(d,'->',yname)
            os.rename(d,yname)

def to_pure_dir(dname):
    yxs_suffix = {'.jpxs','.mpxs','.xsf'}
    dir_list = []
    for root,ds,fs in os.walk(dname):
        pr = Path(root)
        dir_list.extend([pr/d for d in ds if d.endswith('.xsd')])
        for f in fs:
            suffix = Path(f).suffix
            if suffix in yxs_suffix:
                t = pr/f
                if t.is_symlink():
                    continue
                pf = yxsFile(t)
                print(t,'->',pf.decode_filename())
                pf.to_pureFile()
                if global_dict['delete'] and pf.decode_filename().name != t.name:
                    os.remove(t)
  
    dir_list.sort(key=lambda x:-len(x.parts))
    for d in dir_list:
        yname = yxsFile(d).decode_filename()
        print(d,'->',yname)
        os.rename(d,yname)

def get_passwd(server=False,server_only=False):
    def md5_passwd(pad):
        md = hashlib.md5()
        md.update(pad.encode()+b'__s__')
        return md.hexdigest()
    if server_only:
        if is_server_running():
            return passwd_client('getpasswd')
        else:
            raise Exception('Server is not running!')
    if server:
        while True:
            passwd = getpass.getpass('Password:')
            if md5_passwd(passwd)[:2] != '54':
                print('Password error.')
            else:
                break
        if is_server_running():
            passwd_client('stop')
            time.sleep(0.01)
        td = threading.Thread(target=passwd_server,args=(passwd,))
        td.setDaemon(True)
        td.start()
        print('server is running ...')
        time.sleep(3600)
        print('stop')
        return 
    if is_server_running():
        passwd = passwd_client('getpasswd')
    elif global_dict['gui']:
        while True:
            passwd,ok = get_input_ui.main('密码输入','请输入',True)
            if ok:
                if md5_passwd(passwd)[:2] != '54':
                    print('Password error.')
                else:
                    break
            else:
                sys.exit(0)
    else:
        while True:
            passwd = getpass.getpass('Password:')
            if md5_passwd(passwd)[:2] != '54':
                print('Password error.')
            else:
                break
            
    return passwd

def passwd_server(passwd):
    HOST = '' #定义变量HOST的初始值
    PORT = 10000  #定义变量PORT的初始值
    #创建socket对象s，参数分别表示地址和协议类型
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT)) #将套接字与地址绑定
    data = True #设置变量data的初始值
    stt = time.time()
    while data: #如果有数据
        data,address = s.recvfrom(1024) #实现对话操作（接收/发送）
        minfo = data.decode()
        print(minfo)
        itype,info = minfo[0],minfo[1:]
        if itype == 'p':
            passwd = info
        if itype == 'g':
            s.sendto(passwd.encode(),address) #发送信息
        if itype == 's':
            break 
        if time.time() - stt > 3600*5:
            break
    s.close() #关闭连接

def is_server_running():

    HOST = '' #定义变量HOST的初始值
    PORT = 10000  #定义变量PORT的初始值
    #创建socket对象s，参数分别表示地址和协议类型
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((HOST, PORT)) #将套接字与地址绑定
        s.close()
        stat = False 
    except:
        stat = True 
    return stat 

def passwd_client(pstr):
    HOST = 'localhost' #定义变量HOST的初始值
    PORT = 10000 #定义变量PORT的初始值
    #创建socket对象s，参数分别表示地址和协议类型
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(pstr.encode('utf-8'),(HOST,PORT)) #发送数据信息
    if pstr[0] == 'g':
        data,addr = s.recvfrom(512) #读取数据信息
        # print("从服务器接收信息：\n",data.decode('utf-8')) #显示从服务器端接收的信息
    else:
        data = b''
    s.close() #关闭连接
    return data.decode()

@click.command()
@click.argument('args',nargs=-1)
@click.option('--filename','-i',default=None,help="输入文件名或者文件夹名称")
@click.option('--output','-o',default='',help="输出")
@click.option('--pure','-p',default=False,is_flag=True,help="转化为原始文件")
@click.option('--xfile','-x',default=False,is_flag=True,help="加密该文件")
@click.option('--find','-f',default='',help="查找文件")
@click.option('--update_db','-u',default=False,is_flag=True,help="更新文件名数据库")
@click.option('--db',default=None,help="设置数据库名称")
@click.option('--decode','-d',default=False,is_flag=True,help="单独显示原文件名,不转码文件,文件名后缀改为._tt")
@click.option('--encode','-e',default=False,is_flag=True,help="加密显示文件名(._tt)")
@click.option('--encode_dir',default=False,help='是否加密文件夹名',is_flag=True)
@click.option('--transfer','-t',default='',help='转换文件名')
@click.option('--suffix',default='*',help='需要转换文件的类型')
@click.option('--delete',default=False,is_flag=True,help="删除原始文件")
@click.option('--passwd', default=False,is_flag=True)
@click.option('--gui', default=False,is_flag=True)
@click.option('--replace', default=False,is_flag=True)
@click.option('--server', default=False,is_flag=True)
@click.option('--passwd_str', default='',help='设置密码')
@click.option('--version',default=1,help="设置版本")
def main(args=None,filename=None,pure=False,xfile=False,find=None,decode=False,encode=False,update_db=False,db=None,delete=False,transfer='',
        suffix='*',encode_dir=False,passwd=None,version=None,passwd_str=None,gui=False,server=False,replace=False,
        output=''):
    suffix_list = suffix
    key_option = 0
    global_dict['db'] = db
    global_dict['gui'] = gui
    global_dict['replace'] = replace
    global_dict['delete'] = delete
    if passwd_str:
        global_dict['passwd'] = passwd_str 
    else:
        if passwd:
            global_dict['passwd'] = get_passwd()
    if server:
        get_passwd(server)
        return
    if not global_dict['passwd']:
        global_dict['passwd'] = get_passwd()
        
    if passwd and version == 1:
        global_dict['version'] = 2
    else:
        global_dict['version'] = version
    if update_db:
        md = file_database()
        if md.database.is_file():
            md.read()
            md.update()
            md.write()
        else:
            md.create()
    if find:
        key_option += 1
        find_file(find)
        return
    if transfer:
        key_option += 1
        df = yxsFile(transfer)
        print(df.decode_filename().name)
        print(df.encode_filename().name)
        return
    if decode:
        for i in os.listdir('./'):
            try:
                if not i.endswith('._tt'):
                    df = yxsFile(i).decode_filename().name
                    if df != i:
                        suffix = Path(i).suffix
                        os.rename(i,df+suffix+'._tt')
                        time.sleep(0.01)
            except:
                print('error file',i)
    if encode:
        for i in os.listdir('./'):
            try:
                if i.endswith('._tt'):
                    istem = i[:-4]
                    suffix = Path(istem).suffix
                    ef = yxsFile(istem[:-len(suffix)]).encode_filename().name
                    os.rename(i,Path(ef).with_suffix(suffix))
                    time.sleep(0.01)
            except:
                print('error file',i)
                
    if 'ls' in args:
        listdir('./')
        return
    if not filename:
        return
    p = Path(filename)
    if p.is_file():
        filename_list = [p,]
    else:
        filename_list = list(p.glob('*'))
    

    if len(filename_list) == 1:
        t = Path(filename_list[0])
        
    for fn in filename_list:
        if pure:
            if Path(fn).is_dir():
                to_pure_dir(fn)
            else:
                pf = yxsFile(fn)
                pf.to_pureFile(output)
                print(pf.decode_filename())
        elif xfile:
            if Path(fn).is_dir():
                to_yxs_dir(fn,suffix_list,encode_dir)
            else:
                pf = yxsFile(fn)
                pf.to_yxsFile(output)
                print(fn,'->',pf.encode_filename())
        elif len(filename_list) == 1:
            pf = yxsFile(fn)
            suffix = Path(fn).suffix
            if suffix in ('.mpxs','.0h'):

                pf.play_video()
            if suffix in ('.jpxs','.0g'):
                pf.view_image()
        if delete and Path(fn).is_file():
            os.remove(fn)

if __name__=='__main__':
    main()