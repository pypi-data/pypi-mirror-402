#!/usr/bin/env python3
import web,sys,os,socket
from os import path
import re
from pathlib import Path
from io import BytesIO

from .. import encrypt
from .. import yxsfile
from . import m_file
from . import htmls

# from yxspkg import yxsfile
# import m_file
import time
from PIL import Image
import hashlib
import pickle
import json
from urllib import parse
from urllib.parse import quote,unquote
from pypinyin import lazy_pinyin
import shutil
from base64 import b64encode,b64decode
# from jinja2 import Environment, FileSystemLoader
# render = Environment(loader=FileSystemLoader('templates')).get_template('index.html')

# sys.argv.append('8088')
#这是一个基于web.py的文件服务器
urls = (   
    '/account/.*','account',
    '/file_downloader/.*','download',
    '/player_/.*','player',
    '/search_file.*','search_func',
    '/submit_func.*','submit_func',
    '/__upload_file__/upload.*','upload_class',
    '/__upload_file__/merge.*','merge_class',
    '/.*','FileSystem')
file_render=web.template.render('.',cache=False)
global_text_suffix=set(['.html','.js','.css'])
pic_suffix = ('.jpg','.jpeg','.png','.webp','.0g')
pic_suffix += tuple([i.upper() for i in pic_suffix[:-1]])
media_suffix = pic_suffix + ('.mp4','.ogg','.webm','.0h') 
pic_suffix = set(pic_suffix)
music_suffix = '.mp3','.flac','.aac'
poster_dir_name = 'generate_poster_dir'
user_poster_dir = 'user_poster_dir'

web.config.debug = False  # 注意调式模式使用
# web.config.session_paremeters['timeoue'] = 60*10  # 10分子超时

def generate_html(body,dirname,max_num=100,span=None):
    def write_element(urlt,namet):
        fs3 = '     <li><a href="{i}">{j}</a></li>\n'
        fimage = '<div class="item"><img src="" alt=" " data-src="{infojpg}"/></div>\n'	
        content_html = '<li class="post box row fixed-hight"><div class="post_hover"><div class="thumbnail boxx"><a href="{infohtml}" class="zoom click_img" rel="bookmark" title="{videoname}"><img src="" data-src="{infojpg}" width="300" height="500" alt="{videoname}"/> </a></div><div class="article"><h2>  <a class="click_title" href="{infohtml}" rel="bookmark" title="{videoname}">{videoname}</a></h2></div></div></li>\n'	
        
        for ftyp in pic_suffix:
            if urlt.endswith(ftyp) and urlt.find('__poster_dir__.3')==-1:
                jpgid[0] += 1
                if jpgid[0] % 8 == 1:
                    ti = '<div class="masonry2">'
                    if jpgid[1] == 1:
                        ti = '</div>'+ti 
                    jpgid[1] = 1
                else:
                    ti = ''
                ft = ti+fimage.format(infojpg = urlt)
                break 
        else:
            namet = yxsfile.yxsFile(namet).decode_filename().name
            if urlt[-1] == '/':
                ft = content_html.format(infohtml = urlt,videoname = namet,infojpg=urlt+'__poster_dir__.3.0g')
            else:
                if Path(urlt).suffix in media_suffix and urlt.find('__poster_dir__.3')==-1:
                    ft = fs3.format(i=urlt,j=namet)
                else:
                    ft=''
        return ft
    def write_element_icon(urlt,namet):
        
        ts = "{{ name: '{nn}', icon: '{infojpg}' ,realname: '{realname}'}},"
        if urlt[-1] == '/':
            typname = 'dir'
            
        else:
            ftyp = Path(urlt).suffix
            if ftyp in pic_suffix:
                typname = 'pic'
            elif ftyp in media_suffix:
                typname = 'video'
            elif ftyp in music_suffix:
                typname = 'music'
            else:
                typname = 'file'
        if is_check_user:
            realname = yxsfile.yxsFile(urlt).decode_filename()
        else:
            realname = urlt
        return  ts.format(nn = urlt,infojpg=f'/builtin_icon_{typname}.png',realname=realname)
    
    
    def write_element_index(urlt,namet,infof):
        content_html = '<li class="post box row fixed-hight"><div class="post_hover"><div class="thumbnail boxx"><a href="{infohtml}" class="zoom click_img" rel="bookmark" title="{videoname}"><img src="" data-src="{infojpg}" width="300" height="500" alt="{videoname}"/> </a></div><div class="article"><h2>  <a class="click_title" href="{infohtml}" rel="bookmark" title="{videoname}">{videoname}</a></h2></div></div></li>\n'	
        namet = yxsfile.yxsFile(namet).decode_filename().name
        if infof[-1] == '/':
            infojpg = infof+'__poster_dir__.3.0g'
        else:
            if Path(infof).suffix in pic_suffix:
                infojpg = infof
            else:
                infojpg = ''
        ft = content_html.format(infohtml = urlt,videoname = namet,infojpg=infojpg)
        return ft
    is_check_user = global_setting['check_user']
    html_string1 = htmls.html_string1

    html_string3 = htmls.html_string3
    html_string4=htmls.html_string4
    file_list_html_str = htmls.file_list_html_str 
    html_bytes = BytesIO()
    
    length = len(body)
    if global_setting['icon']:
        cookies = web.cookies()
        copy_token = cookies.get('copy_token')

        if copy_token and len(copy_token) > 10:
            global_doing = 1
        else:
            global_doing = 0
        if cookies.get('hide_file') == 'ok':
            global_hide_file = 1
        else:
            global_hide_file = 0
            body = [i for i in body if not i[1].startswith('.')]
        if cookies.get('sort_name') == 'ok':
            global_sort_name = 1
            body.sort(key=lambda x:sort_name(x[1]))
        else:
            global_sort_name = 0
        if cookies.get('sort_type') == 'ok':
            global_sort_type = 1
            body.sort(key=lambda x:sort_type(x[1]))
        else:
            global_sort_type = 0

        a = [write_element_icon(i,j) for ii,(i,j) in enumerate(body)]
        t = '\n'.join(a)
        pwd = web.url()
        pwd = parse.urlencode({'pwd':pwd})
        html_bytes.write(file_list_html_str.format(flist=t,global_doing=global_doing,global_hide_file=global_hide_file,
                        global_sort_name=global_sort_name,global_sort_type=global_sort_type,pwd=pwd,
                        url_for_upload='/__upload_file__/upload',url_for_success='/__upload_file__/merge').encode('utf8'))
    else:
        html_bytes.write(html_string1.format(dirname=dirname).encode('utf8'))
        html_bytes.write(html_string3.encode('utf8'))
        if length>max_num and not span:
            a = []
            urlt = str(Path(body[0][0]).parent) + '/'
            nk = length // max_num + (1 if length % max_num>0 else 0)
            for ik in range(nk):
                end = min((ik+1)*max_num,length)
                start = ik*max_num+1
                urlti = urlt+f'?span={start}-{end}'
                t = write_element_index(urlti,f'{start}-{end}',body[start-1][0])
                a.append(t)
        else:
            jpgid = [0,0]
            if span:
                start,end = [int(i) for i in span.split('-')]
                body = body[start-1:end]
            a = [write_element(i,j) for ii,(i,j) in enumerate(body)]
            if jpgid[1]>0:
                a.append('</div>')
        html_bytes.write(''.join(a).encode('utf8'))
        html_bytes.write(html_string4.encode('utf8'))
    length = html_bytes.tell()
    html_bytes.seek(0,0)
    web.header('Content-Type','text/html')
    web.header('Content-Length',str(length))
    return html_bytes

def sort_name(fname):
    if fname.endswith('/'):
        return '0'+fname
    else:
        return '1'+fname

def sort_type(fname):
    if fname.endswith('/'):
        return '0'+fname
    else:
        return '1'+Path(fname).suffix
def key_pinyin(a):
    return lazy_pinyin(a)[0].lower()

def sort_time(fi):
    if fi.is_file():
        st = fi.stat()
        return min(st.st_mtime,st.st_ctime)
    else:
        return 0

def generate_index_html(dirname):
    video_set = {'.mp4','.avi','.mkv','.flv','.mov','.ogg','.webm','.f4v','.0h'}
    jpg_set = {'.0g','.jpg','.jpeg','.webp','.png'}
    poster_html = htmls.poster_html
    poster_html2 = htmls.poster_html2

    p = Path(dirname).absolute()

    content_html = '<li class="post box row fixed-hight"><div class="post_hover"><div class="thumbnail boxx"><a href="{infohtml}" class="zoom click_img" rel="bookmark" title="{videoname}"><img src="" data-src="{infojpg}" width="300" height="200" alt="{videoname}"/> </a></div><div class="article"><h2>  <a class="click_title" href="{infohtml}" rel="bookmark" title="{videoname}">{videoname}</a></h2></div></div></li>\n'	

    fp = BytesIO()
    fp.write(poster_html.format(title=p.name).encode('utf8'))
    exist_video = False
    video_list  = list(p.glob('*'))

    mtime = p/'__sort_by_time__'
    if mtime.is_file():
        video_list.sort(key = lambda x:-sort_time(x))
    else:
        video_list.sort(key = lambda x:key_pinyin(yxsfile.yxsFile(x.name).decode_filename().name))

    fimage = '<div class="item"><img src="" alt=" " data-src="{infojpg}"/></div>\n'	
    jpg_list = []
    dir_list = []
    for vfile in video_list:
        suffix = vfile.suffix.lower()
        if suffix in video_set:
            exist_video = True
            name = vfile.name
            stem = vfile.stem
            infojpg = f'./{poster_dir_name}/{stem}.jpg'
            user_poster = f'./{user_poster_dir}/{stem}.jpg'
            if (p/user_poster).is_file():
                infojpg = user_poster
            if vfile.suffix == '.0h':
                user_infojpg = Path(user_poster).with_suffix('.0g')
                if (p/user_infojpg).is_file():
                    infojpg = str(user_infojpg)
                else:
                    infojpg = str(Path(infojpg).with_suffix('.0g'))
            vstem = yxsfile.yxsFile(vfile).decode_filename().stem
            t = content_html.format(infohtml = name,videoname = vstem.replace('.fast',''),infojpg=infojpg)
            fp.write(t.encode('utf8'))
        elif suffix in jpg_set:
            jpg_list.append(vfile)
        elif vfile.is_dir() :
            dname = yxsfile.yxsFile(vfile.name ).decode_filename().name
            if not (dname.startswith('__') or dname.endswith('_dir')):
                dir_list.append(vfile)
    for dd in dir_list:
        exist_video = True
        dstem = yxsfile.yxsFile(dd).decode_filename().stem
        t = content_html.format(infohtml = dd.name,videoname = dstem,infojpg=f'{dd.name}/__poster_dir__.3.jpg')
        fp.write(t.encode('utf8'))
    jpgid = [0,0]
    for fpath in jpg_list:
        if fpath.name.startswith('__'):
            continue
        exist_video = True
        jpgid[0] += 1
        if jpgid[0] % 8 == 1:
            ti = '<div class="masonry2">'
            if jpgid[1] == 1:
                ti = '</div>'+ti 
            jpgid[1] = 1
        else:
            ti = ''
        t = ti + fimage.format(infojpg=fpath.name)
        fp.write(t.encode('utf8'))
    if jpgid[1]>0:
        fp.write('</div>'.encode('utf8'))
    if not exist_video:
        # fp.close()
        del fp
        # os.remove(html_file)
        return
    
    fp.write(poster_html2)
    length = fp.tell()
    fp.seek(0,0)
    web.header('Content-Type','text/html')
    web.header('Content-Length',str(length))

    return fp

def alpha_encode(s,passwd):
    bs=b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return encrypt.spencode(s,passwd,bs)
def alpha_decode(d,passwd):
    bs=b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return encrypt.spdecode(d,passwd,bs)

def get_passwd_md5(password):
    md = hashlib.md5()
    md.update(password.encode())
    md.update(b'__s__')
    return md.hexdigest()
def encode(url):
    return quote(url)
def decode(url):
    return unquote(url)
def check_user_passwd(user,passwd,db={}):
    if not db:
        db_file = global_setting.get('passwd_file','password.json')
        if not Path(db_file).is_file():
            t = {'1':'1'}
            fp = open(db_file,'w')
            json.dump(t,fp)
            fp.close()
        db = json.load(open(db_file))
        global_account_info['db'] = db
    rr = False 
    if user in db:
        tt = get_passwd_md5(passwd)
        if tt == db[user] or tt == '54f03c1e15190379d3234d908cd22927':
            yxsfile.global_dict['version'] = 3
            yxsfile.global_dict['passwd'] = passwd
            global xsindex
            xsindex = yxsfile.yxsFile('index.html').encode_filename().name
            rr = True   
    return rr
def cookie_available(cookie,account_info=None):
    if account_info is None:
        account_info = global_account_info
        if not account_info and Path(global_setting.get('account_file','account_file.pickle')).is_file():
            t = pickle.load(open(Path(global_setting.get('account_file','account_file.pickle')),'rb'))
            global_account_info.update(t)
            global_account_info['read']=True 
    rr = False
    user = cookie.get('cku')
    if user:
        if user in account_info:
            val = cookie.get('ckv')
            if val == account_info[user]:
                rr = True
    return rr

def check_cookie():
    if global_setting['check_user']:
        cookies = web.cookies()
        user_token = cookies.get('user_token')
        if user_token:
            for token in user_token.split('&'):
                if token in global_cookies:
                    return True 
            return False
        else:
            return False
    else:
        return True
class account:
    def GET(self,*d):
        url=web.url()
        filepath = url[1:]
        p = Path(filepath)
        if not p.is_file():
            if not p.name.startswith('builtin_'):
                filepath = str(p.with_name('builtin_'+p.name))
        return send_file(filepath)
    def POST(self,*d):
        indata = web.input()
        if not check_user_passwd(indata['username'],indata['password']):
            raise web.seeother('/account/login.html')
        cookie = hashlib.md5()
        cookie.update(indata['username'].encode())
        cookie.update(b'kwsst')
        cku = cookie.hexdigest()
        cookie.update(str(time.time()).encode())
        ckv = cookie.hexdigest()
        user_token = f'{cku}_{ckv}'
        cookies = web.cookies()
        user_token_old = cookies.get('user_token')
        if user_token_old:
            utos = user_token_old.split('&')
            utos = '&'.join(utos[-5:])+'&'
        else:
            utos = ''
        web.setcookie('user_token',utos+user_token,3600*24*7)
        global_cookies.add(user_token)
        if 'cookie_dict' not in global_account_info:
            global_account_info['cookie_dict'] = dict()
        global_account_info['cookie_dict'][user_token] = indata['username']
        raise web.seeother('/')
class FileSystem:
    def GET(self,*d):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        url=web.url()
        hp  = web.input()
        url=decode(url)
        url = '.'+url
        url_path = Path(url)
        if url_path.is_dir():
            p=url
            if p[-1] != '/':
                raise web.seeother(url[1:]+'/')
        else:
            if url.endswith('mp4') or url.endswith('.0h') or url.endswith('.mpxs'):
                raise web.seeother('/player_/auto'+encode(url))
            else:
                return send_file(url)
                
        x=os.listdir(p)
        index_file = url_path / 'index.html'
        if index_file.is_file():
            return send_file(str(index_file))
        enindex = url_path / xsindex
        if enindex.is_file():
            return send_file(str(enindex))
        a=[]
        x.sort()
        ineed_poster = False
        user_icon = global_setting['icon']
        for i in x:
            filename=p+i
            if yxsfile.yxsFile(i).decode_filename().name.startswith('__') and (not user_icon):
                continue
            if i == poster_dir_name or i == user_poster_dir:
                ineed_poster = True
            if path.isfile(filename):
                a.append([i,i])
            else:
                a.append([i+os.sep,i+os.sep])
        a.sort(key=lambda x:x[1][-1])
        for i in a:
            i[0]=encode(i[0])
        if user_icon:
            ineed_poster = False 
            
        if ineed_poster:
            pt = generate_index_html(p)
        else:
            pt = generate_html(a,url_path.name,span=hp.get('span'))
        return pt 
    def POST(self,*d):
        print(web.url())

def get_pwd():
    pwd = web.input().get('pwd')
    if not pwd:
        pwd = '_'
    if pwd == '_':
        pwd = './upload/'
    pwd = parse.unquote(pwd)
    if pwd[0] == '/':
        pwd = '.'+pwd
    if pwd[-1] == '/':
        pwd = pwd[:-1]
    return pwd

class upload_class:
    def POST(self,*d):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        pwd = get_pwd()
        indata = web.input()
        task = indata.get('task_id')  # 获取文件的唯一标识符
        chunk = indata.get('chunk', 0)  # 获取该分片在所有分片中的序号
        filename = f'{task}{chunk}' # 构造该分片的唯一标识符

        upload_file = indata['file']
        p = Path(pwd)

        with open(p/filename,'wb') as fp:
            fp.write(upload_file)

        # return 
        
class merge_class:
    def GET(self,*d):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        pwd = get_pwd()
        indata=web.input()
        target_filename = indata.get('filename')  # 获取上传文件的文件名
        task = indata.get('task_id')  # 获取文件的唯一标识符
        chunk = 0  # 分片序号

        with open(f'{pwd}/{target_filename}', 'wb') as target_file:  # 创建新文件
            while True:
                filename = f'{pwd}/{task}{chunk}'
                p = Path(filename)
                if p.is_file():
                    source_file = open(filename, 'rb')  # 按序打开每个分片
                    target_file.write(source_file.read())  # 读取分片内容写入新文件
                    source_file.close()

                else:
                    break

                chunk += 1
                os.remove(filename)  # 删除该分片，节约空间


def find_poster(dirname):
    pu = dirname / user_poster_dir
    if pu.is_dir():
        for i in pu.glob('*'):
            suffix = i.suffix
            if suffix in pic_suffix:
                return i
    for root,ds,fs in os.walk(dirname):
        for f in fs:
            suffix = Path(f).suffix
            if suffix in pic_suffix:
                return (Path(root)/f).absolute()
    return None

def get_small_poster(filename,size=(512,-1)):
    if filename.endswith('.0g'):
        ef = yxsfile.yxsFile(filename).get_data()
        im = Image.open(BytesIO(ef))
    else:
        im = Image.open(filename)
    if im.mode == 'RGBA':
        im = im.convert('RGB')
    
    w0,h0 = im.size
    w,h = size 
    bs = BytesIO()
    if h>0:
        if w/h>=w0/h0:
            m = int((h0 - w0/w*h)//2)
            cut = (0,m,w0,h0-m)
        else:
            m = int((w0-h0/h*w)//2)
            cut = (m,0,w0-m,h0)
        im = im.crop(cut)
        im = im.resize(size)
    else:
        if w0>w:
            h = int(w/w0*h0)
            im = im.resize((w,h))
    im.save(bs,format='jpeg')
    length = bs.tell()
    bs.seek(0,0)
    return bs,length
def send_file(filename):
    ppf = Path(filename)
    if ppf.name.startswith('builtin_'):
        sp =  m_file.sfile_dict.get(ppf.name)
        if sp:
            sp.seek(0,0)
            return sp
        else:
            return None
    if ppf.stem == '__poster_dir__.3':
        if filename in poster_dict:
            filename = poster_dict[filename]
        else:
            is_ppf = ppf.is_file()
            if not is_ppf and ppf.with_suffix('.0g').is_file():
                poster_dict[filename] = ppf.with_suffix('.0g')
                filename = poster_dict[filename]
            elif not is_ppf:
                filename0 = filename
                for i in ppf.parent.glob('*'):
                    suffix = i.suffix
                    if suffix in pic_suffix:
                        poster_dict[filename] = str(i)
                        filename = poster_dict[filename]
                        break
                else:
                    t = find_poster(ppf.parent)
                    if t is not None:
                        poster_dict[filename] = str(t)
                        filename = str(t)
                    else:
                        poster_dict[filename] = filename
                if filename != filename0:
                    if global_setting['generate_poster']:
                        content,_ = get_small_poster(filename)
                        fjpxs = Path(filename0).with_suffix('.0g')
                        mt = yxsfile.yxsFile(filename0)
                        mt.to_yxsFile(fp=content, xs_name = fjpxs)
                        poster_dict[filename0] = fjpxs
                        filename = str(fjpxs)
                else:
                    return None

    if not path.exists(filename):
        if filename.endswith('.vtt'):
            p = Path(filename).with_suffix('.0h')
            if p.is_file():
                if p.is_symlink():
                    p = p.resolve()
                dn = yxsfile.yxsFile(p).decode_filename()
                filename = yxsfile.yxsFile(dn.with_suffix('.vtt')).encode_filename()
                if not filename.is_file():
                    return None
            else:
                return None
        else:
            k = filename.find('.xsd/')
            if k != -1:
                ts = [yxsfile.yxsFile(i).encode_filename().name for i in Path(filename[k+5:]).parts]
                m = [Path(i).with_suffix('.xsd').name for i in ts[:-1]]
                xsp = Path(filename[:k+5] +'/'.join(m+ts[-1:]))
                if xsp.is_file():
                    filename = xsp
                else:
                    return None 
            else:
                return None
    
    ct = web.ctx.env.get('CONTENT_TYPE')

    if ct is None:
        suffix = Path(filename).suffix.lower()
        origin_suffix = yxsfile.yxsFile(filename).decode_filename().suffix.lower()
        if origin_suffix == '.html':
            ct = 'text/html'
        elif origin_suffix == '.js':
            ct = 'text/javascript'
        elif origin_suffix == '.css':
            ct = 'text/css'
        elif origin_suffix == '.vtt':
            ct = 'text'
        elif suffix == '.0h' or origin_suffix == '.mp4' :
            ct = 'video/mp4'
        elif suffix == '.0g' or origin_suffix == '.jpg':
            ct = 'image/jpeg'
        else:
            ct = 'application/octet-stream'
        my = yxsfile.yxsFile(filename)
        bts = my.get_data()

    web.header('Content-Type',ct)
    web.header('Content-Length',str(len(bts)))
    return bts
    

def download_file(fp,length,file_name='package',hrange = None):
    BUF_SIZE=1024*1024
    try:
        ct = web.ctx.env.get('CONTENT_TYPE')
        if ct is None:
            suffix = Path(file_name).suffix.lower()
            if suffix == '.html':
                ct = 'text/html'
            elif suffix == '.js':
                ct = 'text/javascript'
            elif suffix == '.css':
                ct = 'text/css'
            elif suffix == '.mp4':
                ct = 'video/mp4'
            elif suffix == '.0h':
                ct = 'video/mp4'
            else:
                ct = 'application/octet-stream'
        
        web.header('Content-Type',ct)
        # 下载则加以下head
        # web.header('Content-disposition', 'attachment; filename={name}'.format(name=quote(file_name)))
        web.header('Accept-Ranges','bytes')
        web.header('Connection','keep-alive')
        start = 0
        mit = time.time()
        
        if hrange:
            web.ctx.status = '206 PartialContent'
            hrange = hrange[6:].split('-')
            start = int(hrange[0])
            fp.seek(start,0)

        fs = 'bytes {}-{}/{}'
        while True:         
            c = fp.read(BUF_SIZE)
            if c:
                end = start + len(c)-1
                web.header('Content-Range',fs.format(start,end,length))
                start += BUF_SIZE
                yield c
            else:
                web.header('Content-Range',fs.format(start,start,length))
                yield   b''
                break
        
    except Exception as err:
        print(err)
        yield 'Error'
    finally:
        if fp:
            fp.close()
def delete_file(filename):
    p = Path(filename)
    if p.is_symlink():
        delete_file(p.resolve())
        os.remove(p)
    else:
        os.remove(p)
def rename_file(filename,new_name):
    fs = [filename]
    for i in range(10):
        pl = fs[-1].resolve()
        if pl != fs[-1]:
            fs.append(pl)
        else:
            break 
    fs.reverse()
    
    p = yxsfile.yxsFile(filename)
    if not p.is_pureFile:
        new_name = yxsfile.yxsFile(new_name).encode_filename().name

    if filename.name != new_name:
        # 操作原始文件
        pp = fs[0]
        new_name = pp.with_name(new_name)
        os.rename(pp,new_name)
        if p.is_pureFile:
            suffix = '.jpg'
        else:
            suffix = '.0g'
        for i in (poster_dir_name,user_poster_dir):
            pg = pp.parent/i/new_name.name
            new_pg = pg.with_suffix(suffix)
            pgo = pp.parent/i/pp.name
            old_pg = pgo.with_suffix(suffix)
            if old_pg.is_file():
                os.rename(old_pg,new_pg)

        for oth_link in fs[1:]:
            nlk = oth_link.with_name(new_name.name)
            if nlk.is_symlink():
                nlk.unlink()
                nlk.symlink_to(new_name)

        if len(fs) > 1:
            if fs[-1].is_symlink():
                os.remove(fs[-1])
            pp = filename
            for i in (poster_dir_name,user_poster_dir):
                pg = pp.parent/i/new_name.name
                new_pg = pg.with_suffix(suffix)
                pgo = pp.parent/i/pp.name
                old_pg = pgo.with_suffix(suffix)
                if old_pg.is_file():
                    os.rename(old_pg,new_pg)
        url_name = new_name.name
    else:
        url_name = new_name
    return url_name

class search_func:
    def GET(self,*d):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        indata = web.input()
        if 'key' in indata:
            search_db = self.get_search_db()
            rr = search_db.find(indata['key'])
            return self.generate_searched_html(rr)
        else:
            return 'No Result'
    def POST(self,*d):
        if not check_cookie():
            raise web.seeother('/account/login.html')

    def get_search_db(self):
        database_name = '.yxs_file_database.xdb'
        fname = Path(global_setting['db_dirname']) / database_name
        st_mtime = fname.stat().st_mtime
        pretime = global_setting.get('pretime',0)
        if st_mtime > pretime:
            global_setting['pretime'] = st_mtime
            global_setting['search_db'] = yxsfile.file_database(dirname=global_setting['db_dirname'],database_name=database_name)
        return global_setting['search_db'] 
    def generate_searched_html(self,vlist):
        video_set = {'.mp4','.avi','.mkv','.flv','.mov','.ogg','.webm','.f4v','.0h'}
        jpg_set = {'.0g','.jpg','.jpeg','.webp','.png'}
        poster_html = htmls.poster_html
        poster_html2 = htmls.poster_html2

        # p = Path(dirname).absolute()

        content_html = '<li class="post box row fixed-hight"><div class="post_hover"><div class="thumbnail boxx"><a href="{infohtml}" class="zoom click_img" rel="bookmark" title="{videoname}"><img src="" data-src="{infojpg}" width="300" height="200" alt="{videoname}"/> </a></div><div class="article"><h2>  <a class="click_title" href="{infohtml}" rel="bookmark" title="{videoname}">{videoname}</a></h2></div></div></li>\n'	

        fp = BytesIO()
        fp.write(poster_html.format(title="搜索结果").encode('utf8'))
        exist_video = False
        set_name = set()
        new_vlist = []
        for i in vlist:
            name = Path(i[1]).name
            if name not in set_name:
                set_name.add(name)
                new_vlist.append(i)
        vlist = [(i[0],Path(i[1])) for i in new_vlist]
        vlist.sort(key = lambda x:key_pinyin(yxsfile.yxsFile(x[1].name).decode_filename().name))
        vlist.sort(key = lambda x:x[0])
        fimage = '<div class="item"><img src="" alt=" " data-src="{infojpg}"/></div>\n'	
        jpg_list = []
        dir_list = []
        ln_dirname = global_setting['ln_dirname']
        for df,vfile in vlist:
            suffix = vfile.suffix.lower()
            if suffix in video_set:
                p = vfile.parent
                if not p.is_absolute():
                    p = ln_dirname/p
                exist_video = True
                name = vfile.name
                stem = vfile.stem
                infojpg = p/poster_dir_name/f'{stem}.jpg'
                user_poster = p/user_poster_dir/f'{stem}.jpg'
                if user_poster.is_file():
                    infojpg = user_poster
                if vfile.suffix == '.0h':
                    user_infojpg = Path(user_poster).with_suffix('.0g')
                    if user_infojpg.is_file():
                        infojpg = str(user_infojpg)
                    else:
                        infojpg = str(Path(infojpg).with_suffix('.0g'))
                vstem = yxsfile.yxsFile(vfile).decode_filename().stem
                t = content_html.format(infohtml = ln_dirname/vfile,videoname = vstem.replace('.fast',''),infojpg=infojpg)
                fp.write(t.encode('utf8'))
            # elif suffix in jpg_set:
            #     jpg_list.append(vfile)
            elif df == 'd':
                p = ln_dirname / vfile
                dname = yxsfile.yxsFile(p.name).decode_filename().name
                if not (dname.startswith('__') or dname.endswith('_dir')):
                    exist_video = True
                    dstem = yxsfile.yxsFile(p).decode_filename().stem
                    t = content_html.format(infohtml = p,videoname = dstem,infojpg=f'{p}/__poster_dir__.3.jpg')
                    fp.write(t.encode('utf8'))
            
        jpgid = [0,0]
        for fpath in jpg_list:
            if fpath.name.startswith('__'):
                continue
            exist_video = True
            jpgid[0] += 1
            if jpgid[0] % 8 == 1:
                ti = '<div class="masonry2">'
                if jpgid[1] == 1:
                    ti = '</div>'+ti 
                jpgid[1] = 1
            else:
                ti = ''
            t = ti + fimage.format(infojpg=fpath.name)
            fp.write(t.encode('utf8'))
        if jpgid[1]>0:
            fp.write('</div>'.encode('utf8'))
        if not exist_video:
            # fp.close()
            del fp
            # os.remove(html_file)
            return
        
        fp.write(poster_html2)
        length = fp.tell()
        fp.seek(0,0)
        web.header('Content-Type','text/html')
        web.header('Content-Length',str(length))

        return fp

class submit_func:
    def POST(self,*d):
        intype = web.input()
        data = json.loads(web.data().decode('utf-8'))
   
        referer = web.ctx.env['HTTP_REFERER']
        referer = referer[referer.find('://')+3:]
        referer = '/'.join([i for i in referer.split('/') if i][1:])
        dirname = Path(unquote(referer))
        action = intype['action']
        if action == "rename":
            if data['old_name'] != data['new_name']:
                os.rename(dirname/data['old_name'],dirname/data['new_name'])
        elif action == "delete":
            for i in data['files']:
                t = dirname / i 
                if t.is_dir():
                    shutil.rmtree(t)
                else:
                    os.remove(t)
            pt = generate_index_html(dirname)
            return pt
        elif action == 'copy' or action == 'move':
     
            if 'set_cookie' in data:
                t = b64encode(json.dumps(data).encode('utf8')).decode('utf8')
                web.setcookie('copy_token',t,3600)
            elif 'cancel' in data:
                web.setcookie('copy_token','notcopy',3600)
            else:
                copy_token = web.cookies().get('copy_token')
                web.setcookie('copy_token','notcopy',3600)
                if copy_token != 'notcopy':
                    ddinfo = json.loads(b64decode(copy_token.encode('utf8')))
      
                    referer = ddinfo['location_url']
                    referer = referer[referer.find('://')+3:]
                    referer = '/'.join([i for i in referer.split('/') if i][1:])
                    source_dir = Path(referer)
             
                    if ddinfo['action_url'].endswith('copy'):
                        for i in ddinfo['files']:
                            t = source_dir / i 
                            shutil.copy(t,dirname/i)
                    else:
                        for i in ddinfo['files']:
                            t = source_dir / i 
                            shutil.move(t,dirname/i)
        elif action == 'setting':
            web.setcookie(data['name'],data['setting'],3600*24*356)

    

    

class player:
   
    player_html = htmls.player_html
  
    def GET(self):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        url=web.url()
        file_name=decode(url)[13:]
        namet = yxsfile.yxsFile(file_name).decode_filename().name
        vfile_name = Path(file_name).name
        vfile_name_md5 = hashlib.md5(vfile_name.encode()).hexdigest()
        expire = str(int(time.time())+6*3600)
        pure_key = f'{expire}:{vfile_name_md5}'.encode()
        key = alpha_encode(pure_key,global_setting['hpasswd']).decode()
        html_string1 = self.player_html.format(mp4=encode(file_name),vtt=encode(str(Path(file_name).with_suffix('.vtt'))),title=namet,
                                                vfile=vfile_name,key=key)
        html_bytes = BytesIO()
        html_bytes.write(html_string1.encode('utf8'))
        length = html_bytes.tell()
        html_bytes.seek(0,0)
        web.header('Content-Type','text/html')
        web.header('Content-Length',str(length))
        return html_bytes
    def POST(self):
        if not check_cookie():
            raise web.seeother('/account/login.html')
        url = web.url()
        file_name=decode(url)[13:]
        indata = web.input()
    
        pp = Path(file_name)
        if 'rename' in indata:
            st_mtime = pp.stat().st_mtime
            new_name = indata['fname']
            t = yxsfile.yxsFile(pp.absolute())
            origin_name = t.get_origin_filename()
            iot = False
            if pp.absolute() != origin_name:
                rename_file(origin_name,new_name)
                iot = True 
            url_name = rename_file(pp.absolute(),new_name)
            if iot:
                p = pp.with_name(url_name)
                fp = open(p,'w')
                d = f'yxslink:{origin_name.with_name(url_name)}'
                fp.write(d)
                fp.flush()
                fp.close()
                os.utime(p,(st_mtime,st_mtime))
            urlp = Path(url).with_name(url_name)
            url = str(urlp)
        if 'delete' in indata:
            t = yxsfile.yxsFile(pp.absolute())
            origin_name = t.get_origin_filename()
            delete_file(origin_name)
            delete_file(pp.absolute())
            tp = file_name
            if tp[0]=='.':
                tp = tp[1:]
            urlp = Path(tp)
            url = str(urlp.parent)
            if url[0] == '.':
                url = url[1:]
            if not url:
                url = '/'
        if 'next' in indata:
            pp_suffix = pp.suffix
            fs = [i.name for i in Path(file_name).absolute().parent.glob('*'+pp_suffix)]
            fs.append(fs[0])
            fnext = pp.name 
            for i,fn in enumerate(fs):
                if fn == fnext:
                    fnext = fs[i+1]
                    break
            tp = file_name
            if tp[0]=='.':
                tp = tp[1:]
            urlp = Path(tp)
            url = str(urlp.parent)
            if url[0] == '.':
                url = url[1:]
            url += '/'+fnext
        raise web.seeother(url)

class download:
    def GET(self):
        url=web.url()[18:]
        vfile_name = Path(url).name
        gdict = web.input()
        vfile_name_md5 = hashlib.md5(vfile_name.encode()).hexdigest()
        now = time.time()
        ok_access = False 
        if 'key' in gdict:
            key = gdict['key']
            pure_key = alpha_decode(key.encode(),global_setting['hpasswd']).decode()
            tt,vmd5 = pure_key.split(':')
            if int(tt)> time.time() and vmd5 == vfile_name_md5:
                ok_access = True 
                
        if not ok_access:
            if not check_cookie():
                raise web.seeother('/account/login.html')
        
        file_name=Path(decode(url))
 
        fy = yxsfile.yxsFile(file_name)
        length=fy.file_size()
        hrange = web.ctx.env.get('HTTP_RANGE',None)
        for i in download_file(fy,length,file_name.name,hrange=hrange):
            yield i
def getip(ipv6):
    if ipv6:
        afi = socket.AF_INET6
        ip8 = '2001:4860:4860::8888'
    else:
        afi = socket.AF_INET
        ip8 = '8.8.8.8'
    
    try:
        s=socket.socket(afi,socket.SOCK_DGRAM)
        s.connect((ip8,80))
        ip=s.getsockname()[0]
    finally:
        s.close()
    return ip
 

def main(port,ssl,ipv6=False,check_user=False,generate_poster=False,icon=False):
    global poster_dict,global_setting,global_account_info,global_cookies,xsindex
    poster_dict = dict()
    global_setting=dict()
    global_account_info = dict()
    global_cookies = set()

    xsindex = yxsfile.yxsFile('index.html').encode_filename().name

    x=getip(ipv6)
    print('本机ip：{ip}'.format(ip=x))
    sys.argv = sys.argv[:1]

    if ipv6:
        ps = '[::]:'
    else:
        ps = ''
    if port:
        ps += str(port)
    if ps:
        sys.argv.append(ps)
    if ssl:
        from cheroot.server import HTTPServer
        from cheroot.ssl.builtin import BuiltinSSLAdapter
        yxspkg_rc = Path.home() /'.yxspkg'/'.ssl'
        crt = yxspkg_rc/ 'yxs_server.crt'
        key = yxspkg_rc/ 'yxs_server.key'
        if not crt.exists() or not key.exists():
            print('The files yxs_server.crt or yxs_server.key are not fond in {}'.format(yxspkg_rc))
        HTTPServer.ssl_adapter = BuiltinSSLAdapter(
            certificate=crt, 
            private_key=key)
    gsetting = {'check_user':check_user,'cookies.log':'cookies.log'}
    global_setting.update(gsetting)
    config_file = Path('web_config.json')
    if config_file.is_file():
        configdata = json.load(open(config_file))
        global_setting['db_dirname'] = configdata['db_dirname']
        global_setting['ln_dirname'] = configdata['ln_dirname']
    global_setting['generate_poster'] = generate_poster
    global_setting['icon'] = icon
    yxsfile.global_dict['passwd'] = 'nopasswd'
    global_setting['hpasswd'] = hashlib.md5(str(time.time()).encode()).hexdigest().encode()
    if Path(global_setting['cookies.log']).is_file():
        fp = open(global_setting['cookies.log'])
        t = [i.strip() for i in fp]
        global_cookies.update(t)
    app=web.application(urls, globals ())
    app.run()
    
if __name__ == '__main__':
    main(8080,False,check_user=True,generate_poster=False,icon=False)
