import os,socket
import time,subprocess
import click
import struct

def judge_cmp(old,new):
    # old = old.split()
    # new = new.split()
    # if len(old) < 2:
    #     return False 
    # nt = [4,8]
    # ods = [old[i] for i in nt]
    # nws = [new[i] for i in nt]

    # errs = sum([abs(int(n)-int(o)) for o,n in zip(ods,nws)]) 
    # return errs < 5
    return old == new


@click.command()
@click.option('--disk','-d',default='sda,sdb')
@click.option('--time_l','-t',default=10,help="停止活动指定时长后进入休眠 默认10分钟")
@click.option('--sleep_cmd','-p',default='sudo hdparm')
def main(disk,time_l,sleep_cmd):
    ddold = dict()

    disk = [i.strip() for i in disk.split(',')]
    st = time.time()
    ddold = {i:'none' for i in disk}
    ddnt = {i:0 for i in disk}

    while True:
        sls = open('/proc/diskstats').readlines()
        for di in disk:
            newstate = get_line(sls,di)
            oldstate = ddold[di]
            if not newstate:
                continue
            print(newstate)
            if judge_cmp(oldstate , newstate):
                ddnt[di] += 1
                print(ddnt[di])
                ddold[di] = newstate 
                if ddnt[di] == time_l:
                    stat1,ott = subprocess.getstatusoutput(f'{sleep_cmd} -C /dev/{di}')

                    if stat1 == 0 and ott.find('standby') == -1:
                        os.system(f'{sleep_cmd} -y /dev/{di}')
                        print(f'standby disk: {di}')
            else:
                ddnt[di] = 0
                ddold[di] = newstate 
            time.sleep(0.1)
        st += 60
        tt = st - time.time()
        if tt < 0:
            tt = 60
        tt = min(60,tt)
        
        print('sleep ',tt)
        time.sleep(tt)
def get_line(sls,dis):
    for i in sls:
        if i.find(dis) != -1:
            return i.strip()
    return ''
if __name__=='__main__':
    main()
    # f = open('/proc/diskstats').readlines()
    # q = get_line(f,'sda')
    # print(q)