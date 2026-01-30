import click
from PIL import Image 
from pathlib import Path
import imageio
@click.command()
@click.argument('args',nargs=-1)
@click.option('--input','-i',default='',help='输入文件名(多个文件用","分割)')
@click.option('--output','-o',default='',help='输出文件名')
@click.option('--info',default=False,help='显示图片信息',is_flag=True)
@click.option('--dpi','-d',default=None,help='例如：600 或者 "600,700" 分别设置不同方向的dpi，默认两个方向dpi相同')
@click.option('--size','-s',default=None,help='设置图片大小，列如："1280,468"(宽,高) 或者 "1280,0", 0表示不设置该方向尺寸\n设置图片尺寸 2.5cm,3.5cm,可选单位有（mm,cm,in）')
@click.option('--pdf','-p',default=False,help='转换为pdf文件,或者-o参数以.pdf结尾即可',is_flag=True)
@click.option('--zoom','-z',default=None,help='图片缩放比例')
@click.option('--format','-f',default='',help='转换图片格式（批量）')
@click.option('--quality','-q',default=50,help='pdf文件输出质量（默认：50）')
def main(args,input,output,dpi,size,zoom,info,pdf,format,quality):
    if format:
        for i in args:
            p = Path(i)
            im = Image.open(i)
            size0 = im.size
            if zoom:
                zoom = float(zoom)
                size_new = int(size0[0]*zoom),int(size0[1]*zoom)

                im = im.resize(size_new,Image.LANCZOS)

            im.save(p.with_suffix(format))
        return 
    if not input:
        input_file = Path(args[0]).absolute()
    else:
        input_file = Path(input).absolute()
    if not output:
        output_file = Path(args[1]).absolute()
    else:
        output_file = Path(output).absolute()
    if pdf or output.endswith('.pdf'):
        if input:
            t = input.split(',')
        else:
            t = args
        convert2pdf(t,output,quality)
        return
    im = Image.open(input_file)
    print('输入文件信息：')
    print_image_info(im,input_file)
    new_im = False
    size0 = im.size
    if dpi:
        new_im = True
        dpi = [int(i) for i in dpi.lower().split(',')]
        if len(dpi) == 1:dpi *= 2
    size_new = None
    if size:
        zoom = None 
        size_new,dpi_new = get_size(size,size0,dpi)
        if dpi_new:dpi = dpi_new
    if zoom:
        zoom = float(zoom)
        size_new = int(size0[0]*zoom),int(size0[1]*zoom)
    if size_new:
        new_im = True
        im = im.resize(size_new,Image.LANCZOS)
    if new_im:
        if output_file.suffix == '.jpg' and im.mode != 'RGB':
            im = im.convert('RGB')
        im.save(str(output_file),dpi=dpi)
        print('\n输出文件信息：')
        im = Image.open(output_file)
        print_image_info(im,output_file)
def convert2pdf(images,pdf,quality=50):
    imgs = list()
    for path in images:
        img = Image.open(path)
        imgs.append(img)

    img0 = imgs[0] 
    imgs = imgs[1:] # 将图片列表的第一张去掉了

    img0.save(pdf,"PDF", save_all=True, append_images=imgs,quality=quality)
    
def print_image_info(im,input_file):
    print(f'文件名称：{input_file.name}')
    w,h = im.size
    print(f'图像大小：{w}x{h}')
 
    if hasattr(im,'tag'):
        dpi1,dpi2 = im.tag[282][0][0],im.tag[283][0][0]
        print(f'图像dpi： {dpi1}x{dpi2}')
def get_size(size,size0,dpi):
    w,h = size0
    size = size.lower().split(',')
    dpi_new = None
    if size[0][-2:].isalpha():
        # 按照物理尺寸设置大小
        ratio_dict = {'in':1,'cm':1/2.54,"mm":1/25.4}
        ratio = ratio_dict[size[0][-2:]]
        w_in,h_in = float(size[0][:-2])*ratio,float(size[1][:-2])*ratio
        if w_in == 0:
            w_in = w*h_in/h
        if h_in == 0:
            h_in = h*w_in/w
        
        if dpi:
            size_new = int(w_in*dpi[0]),int(h_in*dpi[1])
        else:
            size_new = None
            dpi_new = int(w/w_in),int(h/h_in)
    else:
        size_new = [int(size[0]),int(size[1])]
        if size_new[0] == 0:
            size_new[0] = int(w*size_new[1]/h)
        if size_new[1] == 0:
            size_new[1] = int(h*size_new[0]/w)
    return size_new,dpi_new
if __name__=='__main__':
    main()
