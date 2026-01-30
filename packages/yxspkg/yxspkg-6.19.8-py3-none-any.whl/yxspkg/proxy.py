import socket 
import select 
import click
  
class Proxy: 
    def __init__(self, addr,to_addr,enable_ipv6):
        self.addr = addr
        if to_addr.strip().startswith('['):
            self.to_ipv6=True 
        else:
            self.to_ipv6=False 

        if self.to_ipv6:
            ipt,port = to_addr.strip()[1:].split(']:')
        else:
            ipt,port = to_addr.strip().split(':')
        to_addr = ipt,int(port)
        self.to_addr = to_addr
        if enable_ipv6:
            aft = socket.AF_INET6
        else:
            aft = socket.AF_INET
        self.proxy = socket.socket(aft,socket.SOCK_STREAM) 
        self.proxy.bind(addr) 
        self.proxy.listen(10) 
        self.inputs = [self.proxy] 
        self.route = {} 
        # self.proxy.close()
  
    def serve_forever(self): 
        print(f'[proxy listen]  {self.addr} -> {self.to_addr}')
        while 1: 
            readable, _, _ = select.select(self.inputs, [], []) 
            for self.sock in readable: 
                try:
                    if self.sock == self.proxy:
                        self.on_join() 
                    else: 
                        data = self.sock.recv(8076) 
                        if not data: 
                            self.on_quit() 
                        else: 
                            self.route[self.sock].send(data) 
                except:
                    pass

        self.proxy.close()
    def on_join(self): 
        client, addr = self.proxy.accept() 
        print(addr,'connect' )
        if self.to_ipv6:
            aft = socket.AF_INET6
        else:
            aft = socket.AF_INET
        forward = socket.socket(aft, socket.SOCK_STREAM) 
        forward.connect(self.to_addr) 
        self.inputs += [client, forward] 
        self.route[client] = forward 
        self.route[forward] = client 
    
    def on_quit(self): 
        for s in self.sock, self.route[self.sock]: 
            self.inputs.remove(s) 
            del self.route[s] 
            s.close()

@click.command()
@click.option('--ipv6',default=False,help="是否启用ipv6",is_flag=True)
@click.option('--port','-p',default=8081)
@click.option('--toaddr',default='127.0.0.1:80',help='[::1]:80')
def main(ipv6=False,port=None,toaddr=None):
    FP = Proxy(('',port),toaddr,enable_ipv6=ipv6)
    FP.serve_forever()#代理服务器监听的地址 
if __name__ == '__main__': 
    main()
