import web,re
import json 
import time 
import hashlib
import sys 
import click
from pathlib import Path

web.config.debug = False  # 注意调式模式使用

urls = (   
    '/message/.*','message',
    '/video_transform/.*','video_transform'
    )

class message:
    message_dict = dict()
 
    def POST(self,*d):
        data = web.input()
        info = self.message_dict
        url = web.url()
        if url.endswith('/clear'):
            self.message_dict = dict()
            return ''
        elif url.endswith('/post'):
            for i,v in data.items():
                keys = i.split('/')
                assert len(keys) == 4
                if keys[0] not in info:
                    info[keys[0]] = dict()
                accounts = info[keys[0]]
                if keys[1] not in accounts:
                    accounts[keys[1]] = dict()
                msg = accounts[keys[1]]
                msg[keys[2]] = v
            return True
        elif url.endswith('/get'):
            result = ''
            timeout = min(int(data.get('timeout',120)),120)
            start = time.time()
            if 'key' in data:
                ap,ac,tag,tt = data['key'].split('/')
                while True:
                    if ap in info and ac in info[ap]:
                        acinfo = info[ap][ac]
                        if tag == '*':
                            result = ''.join([f'{len(i.encode())}_'+i for i in acinfo.values() if i])
                            info[ap][ac] = dict()
                        elif tag in acinfo:
                            result = acinfo[tag]
                            result = f'{len(result.encode())}_'+result
                            info[ap][ac].pop(tag)
                    if result or (time.time()-start)>=timeout:
                        break
                    else:
                        time.sleep(0.3)

            return result
class video_transform:
    pass

@click.command()
@click.option('--port','-p',default=8081,help='使用的端口号')
@click.option('--ipv6',default=False,help='是否使用ipv6',is_flag=True)
@click.option('--ssl',default=False,help='是否使用https',is_flag=True)
def main(port,ipv6=False,ssl=False):

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
        ssl_rc = Path.home() /'.ssl_rc'
        crt = ssl_rc/ 'server.crt'
        key = ssl_rc/ 'server.key'
        if not crt.exists() or not key.exists():
            print('The files .crt or .key are not fond in {}'.format(ssl_rc))
        HTTPServer.ssl_adapter = BuiltinSSLAdapter(
            certificate=crt, 
            private_key=key)
    
    app=web.application(urls, globals())
    app.run()
    
if __name__=='__main__':
    main()