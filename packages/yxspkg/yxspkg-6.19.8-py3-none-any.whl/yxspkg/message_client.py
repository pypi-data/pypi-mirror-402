import requests
import time 

def post_msg(tag,msg,url):
    # tag app/account/1/12.12 
    # tag包含4级，每级由/分开
    # msg 是str或者bytes
    data = {tag:msg}
    requests.post(url,data=data,verify=False)

def get_msg(tag,url,timeout=120):
    t = requests.post(url,data={'key':tag,'timeout':timeout},timeout=timeout+10,verify=False)
    t = t.content
    rr = []
    while True:
        if not t:
            break 
        nd = t.find(b'_')
        n = int(t[:nd])
        rr.append(t[nd+1:nd+1+n])
        t = t[nd+1+n:]
    return rr

def clear_msg(url):
    requests.post(url)

if __name__=='__main__':
    tags = 'app/account/*/12.4'
    url='http://myblog:8081/message/'
    for i in range(1000):
        t = get_msg(tags,url+'get')
        for k in t:
            print(k.decode())

    # tags = 'app/account/fw23e/12.4'
    # post_msg(tags,'fwef23422',url+'post')
    # tags = 'app/account/fwefefw/12.4'
    # post_msg(tags,'fwef23fwewfe422',url+'post')
