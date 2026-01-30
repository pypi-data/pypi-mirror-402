#!/usr/bin/env python3
import web,sys,os,socket
from os import path
import re
from pathlib import Path
from io import BytesIO

from .. import encrypt
from .. import yxsfile
from . import m_file

# from yxspkg import yxsfile
# import m_file
import time
from PIL import Image
import hashlib
import pickle
import json
from urllib.parse import quote,unquote
from pypinyin import lazy_pinyin
import shutil
from base64 import b64encode,b64decode
# sys.argv.append('8088')
#这是一个基于web.py的文件服务器
urls = (   
    '/account/.*','account',
    '/file_downloader/.*','download',
    '/player_/.*','player',
    '/submit_func.*','submit_func',
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
        
        ts = "{{ name: '{nn}', icon: '{infojpg}' }},"
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

        return  ts.format(nn = urlt,infojpg=f'/builtin_icon_{typname}.png')
    
    
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
    html_string1 = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html" />
<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
<title>{dirname}</title>
<meta name="description" content="" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=0, minimum-scale=1.0, maximum-scale=1.0">

<link rel="stylesheet" type="text/css" href="/builtin_kube.css" />
<link rel="stylesheet" type="text/css" href="/builtin_style.css" /> 

    <style>

            .masonry2 {{ 
                column-count:4;
                column-gap: 1px;
                width: 100%;
                margin:1px auto;
            }}
            .item {{ 
                margin-bottom: 1px;
                min-height:200px;
            }}
            @media screen and (max-width: 1400px) {{ 
                .masonry2 {{ 
                    column-count: 3; 
                }} 
            }} 

			@media screen and (max-width: 1000px) {{ 
                .masonry2 {{ 
                    column-count: 2; 
                }} 
            }} 
            @media screen and (max-width: 600px) {{ 
                .masonry2 {{ 
                    column-count: 1; 
                }} 
            }}

    </style>
</head>

'''

    html_string3 = '''<body class="custom-background">
    <div class="container">  
    <div class="mainleft" id="mainleft">
   
              <ul id="post_container" class="masonry clearfix">

    '''
        # $for i,j in body:
    # fs3 = '     <label><input name="{i}" type="checkbox" value=""/><a href="{i}">{j}</a></label> </br>\n'
    
    html_string4='''    </ul>
<div class="clear"></div><div class="last_page tips_info"></div>
</div>  
</div>
<div class="clear"></div>
<script src="builtin_jquery.min.js"></script>
<script>
start();
$(window).on('scroll', function() {
start();
})

function start() {
//.not('[data-isLoaded]')选中已加载的图片不需要重新加载
$('.container img').not('[data-isLoaded]').each(function() {
var $node = $(this);
if (isShow($node)) {
loadImg($node);
}
})
}

//判断一个元素是不是出现在窗口(视野)
function isShow($node) {
return $node.offset().top <= $(window).height() + $(window).scrollTop();
}
//加载图片
function loadImg($img) {
//.attr(值)
//.attr(属性名称,值)
$img.attr('src', $img.attr('data-src')); //把data-src的值 赋值给src
$img.attr('data-isLoaded', 1); //已加载的图片做标记
}
</script>

</body>
</html>
'''
    file_list_html_str = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件浏览页面</title>
    <link rel="stylesheet" href="/builtin_style_files.css">
</head>
<body>
    <form>
        <ul class="file-list">
        <li>
            <input type="checkbox" class="checkbox_parent" name="../" disabled>
            <img src="/builtin_icon_dir.png" alt="../" class="icon">
            <a href="../">../</a>
        </li>
        </ul>
        <div id="blank-bar"></div>
        <div class="actions">
            <div>
                <button type="button"  id="submitBtn0" onclick="all_checked()" >全选</button>
                <button type="button"  id="submitBtn2" onclick="submit_form()" data-url="/submit_func?action=copy">复制</button>
                <button type="button"  id="submitBtn3" onclick="submit_form()" data-url="/submit_func?action=move">移动</button>
                <button type="button"  id="submitBtn4" onclick="submit_form_delete()" data-url="/submit_func?action=delete">删除</button>
                <button type="button"  id="rename-btn" disabled>重命名</button>
            </div>
        </div>
        <div class="actions_ok">
            <div>
                <button type="button"  id="submitBtn8" onclick="submit_form_ok()">确认当前路径</button>
                <button type="button"  id="submitBtn9" onclick="submit_form_cancel()">取消</button>
            </div>
        </div>
    </form>
    <div class="button-wrapper">
        <button class="button">设置</button>
        <div class="list-wrapper">
            <ul class="list">
                <li class="show"><input type="checkbox" class="checkbox_settings"  name="hide_file" id="checkbox_hide_file">隐藏文件</li>
                <li class="hide"><input type="checkbox" class="checkbox_settings"  name="sort_name" id="checkbox_sort_name">名称排序</li>
                <li class="sort"><input type="checkbox" class="checkbox_settings"  name="sort_type" id="checkbox_sort_type">类型排序</li>
            </ul>
        </div>
    </div>
    <script>
        
        var global_doing = {global_doing};
        var global_hide_file = {global_hide_file};
        var global_sort_name = {global_sort_name};
        var global_sort_type = {global_sort_type};
        const files = [
        {flist}
        ];

        const fileList = document.querySelector('.file-list');

        files.forEach(file => {{
        const li = document.createElement('li');
        const input = document.createElement("input");
        const file_name = document.createElement("span");
        const alink = document.createElement("a");
        var namet=decodeURIComponent(file.name);
        if (namet.endsWith("/")) {{
            namet = namet.slice(0, -1);
        }}
        li.innerHTML = `
            <input type="checkbox" class="checkbox" name="${{namet}}">
            <a href="${{file.name}}"><img src="${{file.icon}}" alt="${{namet}}" class="icon"></a>
        `;
        file_name.textContent = namet;
        input.type = "text";
		input.value = namet;
        alink.setAttribute("href",file.name);
        alink.appendChild(file_name)
        li.appendChild(alink);
        li.appendChild(input);
        fileList.appendChild(li);

        // 文件名输入框失去焦点时退出编辑状态
			input.addEventListener("blur", function() {{
                submit_rename_act(file_name,input);
				file_name.style.display = "inline-block";
				input.style.display = "none";
				input.value = file_name.textContent;
			}});

			// 文件名输入框按下回车键时保存修改并退出编辑状态
			input.addEventListener("keydown", function(event) {{
				if (event.key === "Enter") {{
                    submit_rename_act(file_name,input);
					file_name.style.display = "inline-block";
					input.style.display = "none";}}
                }});

        }});
    </script>
    <script src="/builtin_hide_button.js"></script>
</body>
</html>
'''
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
        html_bytes.write(file_list_html_str.format(flist=t,global_doing=global_doing,global_hide_file=global_hide_file,
                        global_sort_name=global_sort_name,global_sort_type=global_sort_type).encode('utf8'))
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

def generate_index_html(dirname):
    video_set = {'.mp4','.avi','.mkv','.flv','.mov','.ogg','.webm','.f4v','.0h'}
    jpg_set = {'.0g','.jpg','.jpeg','.webp','.png'}
    poster_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html" />
<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
<title>{title}</title>
<meta name="description" content="" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=0, minimum-scale=1.0, maximum-scale=1.0">

<link rel="stylesheet" type="text/css" href="/builtin_kube.css" />
<link rel="stylesheet" type="text/css" href="/builtin_style.css" />
    <style>

            .masonry2 {{ 
                column-count:4;
                column-gap: 1px;
                width: 100%;
                margin:1px auto;
            }}
            .item {{ 
                margin-bottom: 1px;
                min-height:200px;
            }}
            @media screen and (max-width: 1400px) {{ 
                .masonry2 {{ 
                    column-count: 3; 
                }} 
            }} 

			@media screen and (max-width: 1000px) {{ 
                .masonry2 {{ 
                    column-count: 2; 
                }} 
            }} 
            @media screen and (max-width: 600px) {{ 
                .masonry2 {{ 
                    column-count: 1; 
                }} 
            }}

    </style>
<body  class="custom-background">
<div class="container">
  
    <div class="mainleft" id="mainleft">
   
              <ul id="post_container" class="masonry clearfix">
'''		
    
    poster_html2 = '''	    	</ul>
        <div class="clear"></div><div class="last_page tips_info"></div>
        </div>
    </div>
    <!-- 下一页 -->
    <!-- <div class="navigation container"><div class='pagination'><a href='' class='current'>1</a><a href=''>2</a><a href=''>3</a><a href=''>4</a><a href=''>5</a><a href=''>6</a><a href="" class="next">下一页</a><a href='' class='extend' title='跳转到最后一页'>尾页</a></div></div> -->
<div class="clear"></div>
<script src="builtin_jquery.min.js"></script>
<script>
start();
$(window).on('scroll', function() {
start();
})

function start() {
//.not('[data-isLoaded]')选中已加载的图片不需要重新加载
$('.container img').not('[data-isLoaded]').each(function() {
var $node = $(this);
if (isShow($node)) {
loadImg($node);
}
})
}

//判断一个元素是不是出现在窗口(视野)
function isShow($node) {
return $node.offset().top <= $(window).height() + $(window).scrollTop();
}
//加载图片
function loadImg($img) {
//.attr(值)
//.attr(属性名称,值)
$img.attr('src', $img.attr('data-src')); //把data-src的值 赋值给src
$img.attr('data-isLoaded', 1); //已加载的图片做标记
}
</script>
</body></html>'''.encode('utf8')

    p = Path(dirname).absolute()

    content_html = '<li class="post box row fixed-hight"><div class="post_hover"><div class="thumbnail boxx"><a href="{infohtml}" class="zoom click_img" rel="bookmark" title="{videoname}"><img src="" data-src="{infojpg}" width="300" height="200" alt="{videoname}"/> </a></div><div class="article"><h2>  <a class="click_title" href="{infohtml}" rel="bookmark" title="{videoname}">{videoname}</a></h2></div></div></li>\n'	

    fp = BytesIO()
    fp.write(poster_html.format(title=p.name).encode('utf8'))
    exist_video = False
    video_list  = list(p.glob('*'))
  
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
        if user_token in global_cookies:
            return True 
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
        web.setcookie('user_token',user_token,3600*24*7)
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
        if ineed_poster:
            pt = generate_index_html(p)
        else:
            pt = generate_html(a,url_path.name,span=hp.get('span'))
        return pt 
    def POST(self,*d):
        print(web.url())

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
    BUF_SIZE=1024*1024*2
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
        pre_nlk = new_name
        for oth_link in fs[1:]:
            nlk = oth_link.with_name(new_name.name)
            if nlk.is_symlink():
                nlk.unlink()
            nlk.symlink_to(pre_nlk)
            pre_nlk = nlk 
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
        
class submit_func:
    def POST(self,*d):
        intype = web.input()
        data = json.loads(web.data().decode('utf-8'))
   
        referer = web.ctx.env['HTTP_REFERER']
        referer = referer[referer.find('://')+3:]
        referer = '/'.join([i for i in referer.split('/') if i][1:])
        dirname = Path(referer)
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
    player_html = '''
    <!doctype html>
    <html lang="zh_CN">
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <title>{title}</title>
    <meta name="description" content="" />
    <link rel="stylesheet" href="/builtin_login_style.css">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=0, minimum-scale=1.0, maximum-scale=1.0">
    <video controls autoplay="autoplay" width="100%" height="100%" controls preload="auto">
    <source src="/file_downloader/x{mp4}?key={key}"  type="video/mp4" />
    <track  kind="subtitles" srclang="zh-cn" src="{vtt}" default>
    </video>

    <form action="{vfile}" method="post">
    文件: <input type="text" name="fname" value="{title}"/> <input type="submit" value="下一个" name="next"><br />
    密码: <input type="password" name="password" autocomplete="off"/><br />
    <input type="submit" value="重命名" name="rename">
    <input type="submit" value="删除"  name="delete">
    </form>
    

    </html>'''
  
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

        cookies = web.cookies()
        user_token = cookies.get('user_token')
        user_name = global_account_info['cookie_dict'][user_token]
        password = indata['password']
        mdtt = get_passwd_md5(password)

        pp = Path(file_name)
        if 'rename' in indata:
            new_name = indata['fname']
            t = yxsfile.yxsFile(pp.absolute())
            origin_name = t.get_origin_filename()
            iot = False
            if pp.absolute() != origin_name:
                rename_file(origin_name,new_name)
                iot = True
            url_name = rename_file(pp.absolute(),new_name)
            if iot:
                t = pp.with_name(url_name)
                if t.stat().st_size<2048*2:
                    fp = open(t,'w')
                    d = f'yxslink:{origin_name.with_name(url_name)}'
                    fp.write(d)
                    fp.close()
            
            urlp = Path(url).with_name(url_name)
            url = str(urlp)
        if 'delete' in indata and mdtt == global_account_info['db'][user_name]:
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
