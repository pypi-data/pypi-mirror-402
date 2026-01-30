#!/usr/bin/env python3
file_list_html_str = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文件浏览页面</title>
    <script src="/builtin_jquery-1.11.1.min.js"></script>
    <script src="/builtin_bootstrap.min.js"></script>
    <script src="/builtin_webuploader.min.js"></script>
    <link rel="stylesheet" type="text/css" href="/builtin_webuploader.css">
    <link rel="stylesheet" type="text/css" href="/builtin_bootstrap.min.css">
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
                <li class="sort"><input type="checkbox" class="checkbox_settings"  name="sort_name" id="checkbox_sort_name">名称排序</li>
                <li class="sort"><input type="checkbox" class="checkbox_settings"  name="sort_type" id="checkbox_sort_type">类型排序</li>
            </ul>
        </div>
    </div>

    <div class="button-uploader" id="picker"  >
        <button class="button"> 上传 </button>

        <div id="progress" style="width:72px;">
            <div class="progress-bar progress-bar-striped active" style="width:0%;"></div>
        </div>
        <div style="clear:both;"></div>
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
        var namet=decodeURIComponent(file.realname);
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
        <script type="text/javascript">
    $(document).ready(function() {{
        var task_id = WebUploader.Base.guid(); // 产生文件唯一标识符task_id
        var uploader = WebUploader.create({{
            swf: '/static/webuploader/Uploader.swf',
            server: '{url_for_upload}?{pwd}', // 上传分片地址
            pick: '#picker',
            auto: true,
            chunked: true,
            chunkSize: 20 * 1024 * 1024,
            chunkRetry: 3,
            threads: 1,
            duplicate: true,
            compress: false,
            formData: {{ // 上传分片的http请求中一同携带的数据
                task_id: task_id,
            }},
        }});

        uploader.on('startUpload', function() {{ // 开始上传时，调用该方法
            $('#progress').show();
            $('.progress-bar').css('width', '0%');
            $('.progress-bar').text('0%');
            $('.progress-bar').removeClass('progress-bar-danger progress-bar-success');
            $('.progress-bar').addClass('active progress-bar-striped');
        }});

        uploader.on('uploadProgress', function(file, percentage) {{ // 一个分片上传成功后，调用该方法
            $('.progress-bar').css('width', percentage * 100 - 1 + '%');
            $('.progress-bar').text(Math.floor(percentage * 100 - 1) + '%');
        }});

        uploader.on('uploadSuccess', function(file) {{ // 整个文件的所有分片都上传成功后，调用该方法
            var data = {{ 'task_id': task_id, 'filename': file.source['name'] }};
            $.get('{url_for_success}?{pwd}', data);
            $('.progress-bar').css('width', '100%');
            $('.progress-bar').text('100%');
            $('.progress-bar').addClass('progress-bar-success');
            $('.progress-bar').text('上传完成');
        }});

        uploader.on('uploadError', function(file) {{ // 上传过程中发生异常，调用该方法
            $('.progress-bar').css('width', '100%');
            $('.progress-bar').text('100%');
            $('.progress-bar').addClass('progress-bar-danger');
            $('.progress-bar').text('上传失败');
        }});

        uploader.on('uploadComplete', function(file) {{ // 上传结束，无论文件最终是否上传成功，该方法都会被调用
            $('.progress-bar').removeClass('active progress-bar-striped');
        }});

        $('#progress').hide();
    }});
    </script>
</body>
</html>
'''

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

        /* 顶部导航栏样式 */
        .top-bar {{
            background-color: #f2f2f2;
            padding: 10px 0;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
            top: 0;
            left: 0;
            right: 0;
        }}

        /* 搜索栏容器 */
        .search-container22 {{
            display: flex;
            align-items: center;
            max-width: 800px;
            margin: 0 auto;
            padding: 0 16px;
        }}

        /* 搜索框样式 */
        .search-box55 {{
            flex: 1;
            border: 1px solid #d1d1d1;
            border-radius: 24px;
            height: 36px;
            padding: 0 16px;
            font-size: 16px;
            outline: none;
        }}

        /* 搜索按钮样式 */
        .search-button {{
            background-color: #4285f4;
            color: #ffffff;
            border: none;
            border-radius: 24px;
            padding: 8px 16px;
            margin-left: 8px;
            cursor: pointer;
        }}

        /* 鼠标悬停样式 */
        .search-button:hover {{
            background-color: #357ae8;
        }}
    </style>
</head>

'''

html_string3 = '''<body>

    <div class="top-bar">
        <!-- 搜索栏容器 -->
        <div class="search-container22">
            <!-- 搜索框 -->
            <input type="text" class="search-box55" placeholder="输入搜索内容" id="keyword">
            <!-- 搜索按钮 -->
            <button class="search-button" onclick="my_search()">搜索</button>
        </div>
    </div>

    <div class="container">  
    <div class="mainleft" id="mainleft">
   
              <ul id="post_container" class="masonry clearfix">

    '''
        
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
return $node.offset().top-100 <= $(window).height() + $(window).scrollTop();
}
//加载图片
function loadImg($img) {
//.attr(值)
//.attr(属性名称,值)
$img.attr('src', $img.attr('data-src')); //把data-src的值 赋值给src
$img.attr('data-isLoaded', 1); //已加载的图片做标记
}

function my_search() {

    var keyword = document.getElementById("keyword").value;

    window.open("/search_file?key=" + keyword);
}

</script>

</body>
</html>
'''

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

                    /* 顶部导航栏样式 */
        .top-bar {{
            background-color: #f2f2f2;
            padding: 10px 0;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
            
            top: 0;
            left: 0;
            right: 0;
        }}

        /* 搜索栏容器 */
        .search-container22 {{
            display: flex;
            align-items: center;
            max-width: 800px;
            margin: 0 auto;
            padding: 0 16px;
        }}

        /* 搜索框样式 */
        .search-box55 {{
            flex: 1;
            border: 1px solid #d1d1d1;
            border-radius: 24px;
            height: 36px;
            padding: 0 16px;
            font-size: 16px;
            outline: none;
        }}

        /* 搜索按钮样式 */
        .search-button {{
            background-color: #4285f4;
            color: #ffffff;
            border: none;
            border-radius: 24px;
            padding: 8px 16px;
            margin-left: 8px;
            cursor: pointer;
        }}

        /* 鼠标悬停样式 */
        .search-button:hover {{
            background-color: #357ae8;
        }}

    </style>
<body>

    <div class="top-bar">
        <!-- 搜索栏容器 -->
        <div class="search-container22">
            <!-- 搜索框 -->
            <input type="text" class="search-box55" placeholder="输入搜索内容" id="keyword">
            <!-- 搜索按钮 -->
            <button class="search-button" onclick="my_search()">搜索</button>
        </div>
    </div>

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
return $node.offset().top-100 <= $(window).height() + $(window).scrollTop();
}
//加载图片
function loadImg($img) {
//.attr(值)
//.attr(属性名称,值)
$img.attr('src', $img.attr('data-src')); //把data-src的值 赋值给src
$img.attr('data-isLoaded', 1); //已加载的图片做标记
}

function my_search() {
    var keyword = document.getElementById("keyword").value;
    window.open("/search_file?key=" + keyword);
}

</script>
</body></html>'''.encode('utf8')

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



        <video id="video-player" controls onseeked="updateProgressBar()" controls autoplay="autoplay" width="100%" height="100%">
        <source src="/file_downloader/x{mp4}?key={key}" type="video/mp4">
        Your browser does not support the video tag.
        <track  kind="subtitles" srclang="zh-cn" src="{vtt}" default>
    </video>
    <div id="progress-container">
        <div id="progress-bar" onclick="seek(event)"></div>
    </div>
    <script>
        var videoPlayer = document.getElementById('video-player');
        var progressBar = document.getElementById('progress-bar');
        
        function updateProgressBar() {{
            var currentTime = videoPlayer.currentTime;
            var duration = videoPlayer.duration;
            var percentage = (currentTime / duration) * 100;
            progressBar.style.width = percentage + '%';
        }}

        function seek(event) {{
            var rect = progressBar.getBoundingClientRect();
            var offsetX = event.clientX - rect.left;
            var percentage = (offsetX / progressBar.offsetWidth);
            var videoPlayer = document.getElementById('video-player');
            var duration = videoPlayer.duration;
            var seekTime = percentage * duration;
            videoPlayer.currentTime = seekTime;
            updateProgressBar();
        }}
    </script>

    <form action="{vfile}" method="post" id="myForm">
    文件: <input type="text" name="fname" value="{title}"/> <input type="submit" value="下一个" name="next"><br />
    <!-- 密码: <input type="password" name="password" autocomplete="off"/><br /> -->
    <button type="submit" name="rename" value="rename" onclick="return showConfirmation(1)">重命名</button>
    <button type="submit" name="delete" value="delete" onclick="return showConfirmation(2)">删除</button>
    </form>

    <script>
    function showConfirmation(val) {{
    if (val == 1) {{
        var str1="确定要重命名该文件吗？";
    }} else {{
        var str1="确定要删除该文件吗？";
    }}
    var result = window.confirm(str1);

    if (result) {{
        // 用户点击确认按钮，则继续提交表单
        return true;
    }} else {{
        // 用户点击取消按钮，则取消提交操作
        return false;
    }}
    }}
    </script>
    

</html>'''