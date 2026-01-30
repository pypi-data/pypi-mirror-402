#同时使用pandas读取xlsx文件，配置账号、密码、路径和权限
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import socket
import click

@click.command()
@click.option('--ipv6','-6',is_flag=True)
@click.option('--user','-u',help='username')
@click.option('--passwd','-p',help='password')
@click.option('--dirname','-d',help='home dirname')
@click.option('--port',default=None,help='port')
def main(user,passwd,dirname,port=None,ipv6=False):
    # 实例化DummyAuthorizer来创建ftp用户
    authorizer = DummyAuthorizer()
    # 参数：用户名，密码，目录，权限
    # 写权限
    # "a" ——将数据追加到现有文件（APPE命令）
    # "d" ——删除文件或目录（DELE，RMD命令）
    # "f" ——重命名文件或目录（RNFR，RNTO命令）
    # "m" ——创建目录（MKD命令）
    # "w" ——将文件存储到服务器（STOR，STOU命令）
    # "M"——更改文件模式/权限（SITE CHMOD命令）
    # "T"——更改文件修改时间（SITE MFMT命令）

    # 读权限
    # "e" ——更改目录（CWD，CDUP命令）
    # "l" ——列表文件（LIST，NLST，STAT，MLSD，MLST，SIZE命令）
    # "r" ——从服务器检索文件（RETR命令）

    authorizer.add_user(user,passwd, dirname, perm='elradfmwMT') #perm=‘elradfmwMT’
        
    #设置一个匿名登录
    #authorizer.add_anonymous('/home/nobody')

    #创建FTPHanddler实例
    handler = FTPHandler
    handler.authorizer = authorizer
    # 参数：IP，端口，handler
    # help(FTPServer)
    if port:
        port = int(port)
    if ipv6:
        if not port:
            port = 2126
        tcp_server = socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
        tcp_server.bind(("",port))
        

    else:
        if not port:
            port = 2121
        tcp_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        tcp_server.bind(("",port))

    handler.passive_ports = range(port-1,port)
    server = FTPServer(tcp_server, handler)
    server.serve_forever()

if __name__=='__main__':
    main()