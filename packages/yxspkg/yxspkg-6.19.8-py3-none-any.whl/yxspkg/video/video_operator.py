from asyncio import streams
from email.policy import default
import os
import subprocess
import click 
from pathlib import Path
import subprocess
import json
import time
from .. import yxsfile
import ffmpeg

@click.command()
@click.argument('args',nargs=-1)
@click.option('--rotate',default=None,help='旋转视频')
@click.option('--replace',default=False,help='是否替换该文件',is_flag=True)
@click.option('--ffmpeg_parameter','-f',default='-c copy',help='ffmpeg 参数')
@click.option('--to_mp4','-t',default=False,help='将文件转化为mp4格式',is_flag=True)
@click.option('--merge','-m',default = False,help='合并多个视频文件',is_flag=True)
@click.option('--auto_merge',default = False,help='自动合并多个视频文件',is_flag=True)
@click.option('--output','-o',default = '',help='输出文件名')
@click.option('--delete','-d',default=False,help='删除源文件',is_flag=True)
@click.option('--copy_only','-c',default=False,help='是否只进行copy转码的任务，其它需要解码的则跳过',is_flag=True)
@click.option('--subtitle','-s',default=False,help='提取文件字幕',is_flag=True)
@click.option('--poster','-p',default = False,help='提取缩略图',is_flag=True)
@click.option('--poster_time',default = 300,help='缩略图指定时间')
def main(args,replace,rotate,ffmpeg_parameter,to_mp4,delete,copy_only,subtitle,poster,poster_time,merge,auto_merge,output):
    if subtitle:
        extract_subtitle(args[0])
    if to_mp4:
        convert2mp4(args,delete,copy_only)
        return 
    if poster:
        for d in args:
            p = Path(d)
            if p.is_file():
                fs = [p]
                gp = p.with_name('generate_poster_dir')
            else:
                fs = [i for i in p.glob('*') if i.suffix in ('.mpxs','.mp4')]
                gp = p/'generate_poster_dir'
            if not gp.is_dir():
                os.mkdir(gp)
            for i in fs:
                op = (gp/yxsfile.yxsFile(i).decode_filename().name).with_suffix('.jpg')
                get_frame_out(i,poster_time,op)
                if i.suffix == '.mpxs':
                    mt = yxsfile.yxsFile(op)
                    if mt.encode_filename().is_file():
                        os.remove(mt.encode_filename())
                    m = mt.to_yxsFile()
                    os.remove(op)
                    
        return 
    if auto_merge:
        rr = []
        argst = [i for i in args]
        for i in argst:
            print(i)
        while True:
            nt = len(argst)
            pre_long = len(rr)
            for i in range(nt-1):
                s1 = argst[i]
                s2 = argst[i+1]
                if strdist1(s1,s2) == 1:
                    rt = [(s1,i),(s2,i+1)]
                    if i+2 < nt:
                        for j in range(i+2,nt):
                            d = strdist1(s1,argst[j])
                            d2 = strdist1(s2,argst[j])
                            if d==1 and d2==1:
                                rt.append((argst[j],j))
                            else:
                                break 
             
                    for m in rt:
                        argst[m[1]] = None 
                    rr.append(rt)
                    break 
            if pre_long == len(rr):
                break
            argst = [i for i in argst if i]
        for i in range(len(rr)):
            rr[i] = [j[0] for j in rr[i]]
        # rr = [strcheck(i) for i in rr]
        for i in rr:
            for j in i:
                print(j)
            print('*'*80,strcheck(i))
        a = input('以上是否准确，是否可以执行自动合并[y/n]y: ')
        if a.lower() == 'y' or a == '':
            for i in rr:
                if strcheck(i):
                    t = Path(i[0])
                    tn = t.stem+'_out'+t.suffix
                    tn = tn.replace(' ','_')
                    output = t.with_name(tn)
                    merge_fs(i,output,delete)

        exit()
    if merge:
        if not output:
            t = Path(args[0])
            tn = t.stem+'_out'+t.suffix
            tn = tn.replace(' ','_')
            output = t.with_name(tn)
        merge_fs(args,output,delete)
        return 
    input_file = Path(args[0]).absolute()
    if len(args) > 1:
        output_file = Path(args[1]).absolute()
    else:
        output_file = input_file.parent / (input_file.stem+'_output'+input_file.suffix)
    if input_file.is_file():
        temp_file = output_file.parent / (output_file.stem+'_temp'+output_file.suffix)
        ffmpeg_i = f'ffmpeg -i "{input_file}" '
        if rotate:
            ffmpeg_command = ffmpeg_i + f' -metadata:s:v:0 rotate={rotate} ' + ffmpeg_parameter +f' "{temp_file}"'
        t = subprocess.call(ffmpeg_command,shell=True)
        assert t == 0
        if replace:
            os.rename(temp_file,input_file)
        else:
            os.rename(temp_file,output_file)
def strcheck(s):
    s1 = s[0]
    s2 = s[1]
    if len(s1) != len(s2):
        return False 
    ni = None 
    for ii,(p,t) in enumerate(zip(s1,s2)):
        if p!=t:
            ni = ii 
            break 
    for i in range(len(s)-1):
        s1 = s[i]
        s2 = s[i+1]
        if ord(s2[ni]) - ord(s1[ni]) !=1:
            return False 
    if s[0][ni] not in ['0','1','a','A']:
        return False 
    if s[0][ni].isdigit():
        if s[0][ni-1].isdigit() or s[0][ni+1].isdigit():
            return False
    return True
def strdist1(s1,s2):
    if len(s1) != len(s2):
        return 1e9
    total = sum([1 for i,j in zip(s1,s2) if i != j ])
    return total
def merge_fs(fs,output,delete):
    fn = 'tempxtz_input.txt'
    fp = open(fn,'w')
    for i in fs:
        fp.write(f"file '{i}'\n")
    fp.close()
    t = subprocess.call(f"ffmpeg -f concat -safe 0 -i {fn} -c copy {output}",shell=True)
    if t == 0:
        os.remove(fn)
    else:
        print('error files:')
        for i in fs:
            print(i)
    if delete:
        total_size = sum([Path(i).stat().st_size for i in fs])
        out_size = Path(output).stat().st_size
        if out_size > total_size*0.95:
            print('大小',total_size/1e6,out_size/1e6)
            for i in fs:
                os.remove(i)

    return 

def convert2mp4(args,delete=False,copy_only=False,extract_subtitles=True):
    other_video = {'.avi','.mkv','.rmvb','.wmv','.mpg','.mov','.rm','.flv','.3gp','.asf','.mod','.rmvb','.m2ts','.ts'}
    if len(args) > 0:
        pnw = Path(args[0])
    else:
        pnw = Path('./')
    norr = list()
    if pnw.is_dir():
        ttl = [(root,f) for root,_,fs in os.walk(pnw) for f in fs]
    else:
        ttl = [(pnw.parent,pnw.name)]
    for root,f in ttl:
        if Path(f).suffix.lower() in other_video:
            vfile = Path(root) / f
            if not vfile.is_file():
                continue
            params = get_video_parameter(vfile)
            if 'streams' not in params:
                norr.append(vfile)
                continue
            subtitles = [i for i in params['streams'] if i['codec_type']=='subtitle']
            sub_srt = None
            if extract_subtitles and  subtitles:
                for ii,sf in enumerate(subtitles):
                    tag = sf['tags'].get('title','')
                    sfile = vfile.with_name(f'{vfile.stem}_{ii}{tag}.srt')
                    if sub_srt is None:
                        sub_srt = sfile
                    aa = subprocess.call(f'ffmpeg -i "{vfile}" -y "{sfile}"',shell=True)

            code_names = set([i.get('codec_name','none').lower() for i in params['streams']])
            codea = None
            codev = None
            for ac in ['aac','ac3','mp3']: #['aac','eac3','ac3']
                for j in code_names:
                    if j.find(ac) != -1:
                        codea = 'copy'
                        break
                if codea == 'copy':
                    break
            else:
                codea = 'aac'
            for vc in ['264','vc1','vp9','av1']:
                for j in code_names:
                    if j.find(vc) != -1:
                        codev = 'copy'
                        break
                if codev == 'copy':
                    break
            else:
                codev = 'h264'
            if copy_only:
                if codev != 'copy':
                    norr.append(vfile)
                    continue
            mp4file = vfile.with_suffix('.mp4')
            
            subtitles = ''
            subs = [i for i in params['streams'] if i['codec_type']=='subtitle']
            if subs and codev != 'copy':
                subtitles = f'-vf subtitles="{vfile}"'
            if sub_srt is not None:
                substr = f'-i "{sub_srt}" -c:s mov_text'
            else:
                substr = ''
            cmd = f'ffmpeg -i "{vfile}" {substr} -c:v {codev} -c:a {codea} {subtitles} -y "{mp4file}"'
            print(cmd)
            aa = subprocess.call(cmd,shell=True)
            if aa==0:
                if delete:
                    time.sleep(0.1)
                    os.remove(vfile)

    print('未处理文件：')
    for i in norr:
        print(i)
    print('处理完成')
def get_video_parameter(video_path):
    def filter_parameter(params):
        pl = [i for i in params.splitlines() if not i.startswith('Cannot')]
        return '\n'.join(pl)
    t = f'ffprobe -i "{str(video_path)}" -print_format json -show_format -show_streams -v quiet'
    all_parameter=subprocess.getoutput(t)
    all_parameter = filter_parameter(all_parameter)
    all_parameter=json.loads(all_parameter)
    return all_parameter
def extract_subtitle(pdir):
    videos = {'.avi','.mkv','.rmvb','.wmv','.mpg','.mov','.rm','.flv','3gp','.asf','.mod','.rmvb','.mp4'}
    pnw = Path(pdir)
    if pnw.is_dir():
        fs = [Path(root) / f for root,_,fs in os.walk(pnw) for f in fs if Path(f).suffix.lower() in videos]
    else:
        fs = [pnw]
    for vfile in fs:
        params = get_video_parameter(vfile)
        if 'streams' not in params:
            continue
        subtitles = [i for i in params['streams'] if i['codec_type']=='subtitle']
        if subtitles:
            for ii,sf in enumerate(subtitles):
                tag = sf['tags'].get('title','')
                sfile = vfile.with_name(f'{vfile.stem}_{ii}{tag}.srt')
                aa = subprocess.call(f'ffmpeg -i "{vfile}" -y "{sfile}"',shell=True)
def get_frame_out(vfile,ts,output):
    if vfile.suffix == '.mpxs':
        yf = yxsfile.yxsFile(vfile)
        mp4name = yf.to_pureFile()
        print("convert to pure file:",mp4name)
    else:
        mp4name = vfile
 
    (
        ffmpeg
        .input(str(mp4name), ss=ts)
        .output(str(output), vframes=1)
        .run(quiet=True,overwrite_output=True)
    )
   
    if vfile.name != mp4name.name:
        os.remove(mp4name)
if __name__=='__main__':
    main()