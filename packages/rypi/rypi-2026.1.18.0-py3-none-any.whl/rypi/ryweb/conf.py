import os

def lpath(*dirs):
    """将 dirs 中的文件名连接成路径"""
    path = os.path.join(*dirs)
    path = os.path.abspath(path).replace('\\', '/')
    return path

www_root = lpath('/var/www/ryweb')
app_dir = lpath(www_root, 'app')
web_dir = lpath(www_root, 'web')
cfg_dir = lpath(www_root, 'cfg')
db_dir = lpath(www_root, 'db')
psql_dir = lpath(db_dir, 'psql')
adb_dir = lpath(db_dir, 'adb')
sfs_dir = lpath(db_dir, 'sfs')
ssl_dir = lpath(www_root, 'ssl')
env_dir = lpath(www_root, 'env')
code_dir = lpath(www_root, 'code')
nginx_cfg_dir = lpath(cfg_dir, 'nginx')
nginx_host_dir = lpath(cfg_dir, 'nginx', 'vhost')
nginx_logs_dir = lpath(cfg_dir, 'nginx', 'logs')
nginx_body_dir = lpath(cfg_dir, 'nginx', 'temp', 'client_body_temp')
nginx_proxy_dir = lpath(cfg_dir, 'nginx', 'temp', 'proxy_temp')
nginx_fastcgi_dir = lpath(cfg_dir, 'nginx', 'temp', 'fastcgi_temp')
nginx_uwsgi_dir = lpath(cfg_dir, 'nginx', 'temp', 'uwsgi_temp')
nginx_scgi_dir = lpath(cfg_dir, 'nginx', 'temp', 'scgi_temp')
adb_logs_dir = lpath(adb_dir, 'adb', 'logs')
adb_data_dir = lpath(adb_dir, 'adb', 'data')
adb_apps_dir = lpath(adb_dir, 'adb', 'apps')

proxy_port = 8898
admin_port = 8899
www_user = 'ryweb'
env_name = 'ryweb'
py_ver = '3.10'
run_mode = 'nfp'
app_list = {
    'np': ['nginx', 'php', 'certbot'],
    'npp': ['nginx', 'php', 'postgresql', 'certbot'],
    'nf': ['nginx', 'fastapi', 'certbot'],
    'nfp': ['nginx', 'postgresql', 'fastapi', 'certbot'],
    'nfpc': ['nginx', 'postgresql', 'conda', 'fastapi', 'certbot'],
    'nfas': ['nginx', 'arangodb', 'seaweedfs', 'fastapi', 'certbot'],
    'nfasc': ['nginx', 'arangodb', 'seaweedfs', 'conda', 'fastapi', 'certbot']
}
apps = app_list[run_mode]

nginx_ver = '1.28.0'
#nginx_pkg_lin = 'https://nginx.org/download/nginx-1.28.0.tar.gz'
#nginx_pkg_win = 'https://nginx.org/download/nginx-1.28.0.zip'
nginx_pkg_lin = 'http://rymaa.cn/download/nginx-1.28.0.tar.gz'
nginx_pkg_win = 'http://rymaa.cn/download/nginx-1.28.0.zip'

postgresql_ver = '16.11'
postgresql_lin = ''
postgresql_deb = ''
postgresql_rpm = ''
# vers: 18.1-1, 17.7-1, 16.11-1, 15.15-1, 14.20-1, 13.23-1, 11.21-1
postgresql_mac = 'https://get.enterprisedb.com/postgresql/postgresql-16.11-1-osx-binaries.zip'
#postgresql_mac = 'http://rymaa.cn/download/postgresql-16.11-1-osx-binaries.zip'

# vers: 18.1-1, 17.7-1, 16.11-1, 15.15-1, 14.20-1, 13.23-1, 11.21-1
postgresql_win = 'https://get.enterprisedb.com/postgresql/postgresql-16.11-1-windows-x64-binaries.zip'
#postgresql_win = 'http://rymaa.cn/download/postgresql-16.11-1-windows-x64-binaries.zip'

arangodb_ver = '3.11.0'
arangodb_pkg_lin = ''
#arangodb_pkg_deb = 'https://download.arangodb.com/arangodb311/DEBIAN/amd64/arangodb3_3.11.0-1_amd64.deb'
arangodb_pkg_deb = 'http://rymaa.cn/download/arangodb3_3.11.0-1_amd64.deb'
#arangodb_pkg_rpm = 'https://download.arangodb.com/arangodb311/RPM/x86_64/arangodb3-3.11.0-1.0.x86_64.rpm'
arangodb_pkg_rpm = 'http://rymaa.cn/download/arangodb3-3.11.0-1.0.x86_64.rpm'
#arangodb_pkg_mac = 'https://download.arangodb.com/arangodb311/Community/MacOSX/arangodb3-3.11.0.x86_64.dmg'
arangodb_pkg_mac = 'http://rymaa.cn/download/arangodb3-3.11.0.x86_64.dmg'
#arangodb_pkg_win = 'https://download.arangodb.com/arangodb311/Community/Windows/ArangoDB3-3.11.0_win64.exe'
arangodb_pkg_win = 'http://rymaa.cn/download/ArangoDB3-3.11.0_win64.exe'

seaweedfs_ver = '3.96'
#seaweedfs_pkg_lin = 'https://sourceforge.net/projects/seaweedfs.mirror/files/3.96/linux_amd64.tar.gz'
#seaweedfs_pkg_mac = 'https://sourceforge.net/projects/seaweedfs.mirror/files/3.96/darwin_amd64.tar.gz'
#seaweedfs_pkg_win = 'https://sourceforge.net/projects/seaweedfs.mirror/files/3.96/windows_amd64.zip'
seaweedfs_pkg_lin = 'http://rymaa.cn/download/seaweedfs-3.96_linux_amd64.tar.gz'
seaweedfs_pkg_mac = 'http://rymaa.cn/download/seaweedfs-3.96_darwin_amd64.tar.gz'
seaweedfs_pkg_win = 'http://rymaa.cn/download/seaweedfs-3.96_windows_amd64.zip'

conda_ver = '25.1.1'
#conda_pkg_lin = 'https://repo.anaconda.com/miniconda/Miniconda3-py310_25.1.1-2-Linux-x86_64.sh'
conda_pkg_lin = 'http://rymaa.cn/download/Miniconda3-py310_25.1.1-2-Linux-x86_64.sh'
#conda_pkg_mac = 'https://repo.anaconda.com/miniconda/Miniconda3-py310_25.1.1-2-MacOSX-x86_64.sh'
conda_pkg_mac = 'http://rymaa.cn/download/Miniconda3-py310_25.1.1-2-MacOSX-x86_64.sh'
#conda_pkg_win = 'https://repo.anaconda.com/miniconda/Miniconda3-py310_25.1.1-2-Windows-x86_64.exe'
conda_pkg_win = 'http://rymaa.cn/download/Miniconda3-py310_25.1.1-2-Windows-x86_64.exe'

php_ver = '8.3.28'
# vers: php-8.4.14.tar.gz, php-8.3.26.tar.gz, php-8.2.28.tar.gz, php-8.1.31.tar.gz
php_pkg_lin = 'https://www.php.net/distributions/php-8.3.26.tar.gz'
php_pkg_mac = 'https://www.php.net/distributions/php-8.3.26.tar.gz'
# vers: php-8.5.0-nts-Win32-vs17-x64.zip, php-8.4.15-nts-Win32-vs17-x64.zip, php-8.3.28-nts-Win32-vs16-x64.zip, php-8.2.29-nts-Win32-vs16-x64.zip
#php_pkg_win = 'https://windows.php.net/downloads/releases/php-8.3.28-nts-Win32-vs16-x64.zip'
php_pkg_win = 'http://rymaa.cn/download/php-8.3.28-nts-Win32-vs16-x64.zip'

certbot_ver = '5.1.0'
certbot_pkg_lin = 'http://rymaa.cn/download/certbot-5.1.0.tar.gz'
certbot_pkg_mac = 'http://rymaa.cn/download/certbot-5.1.0.tar.gz'
certbot_pkg_win = 'http://rymaa.cn/download/certbot-5.1.0.tar.gz'

# mime types
mime_types = r"""
types {
    text/html                             html htm shtml;
    text/css                              css;
    text/xml                              xml;
    image/gif                             gif;
    image/jpeg                            jpeg jpg;
    application/javascript                js;
    application/atom+xml                  atom;
    application/rss+xml                   rss;

    text/mathml                           mml;
    text/plain                            txt;
    text/vnd.sun.j2me.app-descriptor      jad;
    text/vnd.wap.wml                      wml;
    text/x-component                      htc;

    image/png                             png;
    image/tiff                            tif tiff;
    image/vnd.wap.wbmp                    wbmp;
    image/x-icon                          ico;
    image/x-jng                           jng;
    image/x-ms-bmp                        bmp;
    image/svg+xml                         svg svgz;
    image/webp                            webp;

    application/font-woff                 woff;
    application/java-archive              jar war ear;
    application/json                      json;
    application/mac-binhex40              hqx;
    application/msword                    doc;
    application/pdf                       pdf;
    application/postscript                ps eps ai;
    application/rtf                       rtf;
    application/vnd.apple.mpegurl         m3u8;
    application/vnd.ms-excel              xls;
    application/vnd.ms-fontobject         eot;
    application/vnd.ms-powerpoint         ppt;
    application/vnd.wap.wmlc              wmlc;
    application/vnd.google-earth.kml+xml  kml;
    application/vnd.google-earth.kmz      kmz;
    application/x-7z-compressed           7z;
    application/x-cocoa                   cco;
    application/x-java-archive-diff       jardiff;
    application/x-java-jnlp-file          jnlp;
    application/x-makeself                run;
    application/x-perl                    pl pm;
    application/x-pilot                   prc pdb;
    application/x-rar-compressed          rar;
    application/x-redhat-package-manager  rpm;
    application/x-sea                     sea;
    application/x-shockwave-flash         swf;
    application/x-stuffit                 sit;
    application/x-tcl                     tcl tk;
    application/x-x509-ca-cert            der pem crt;
    application/x-xpinstall               xpi;
    application/xhtml+xml                 xhtml;
    application/xspf+xml                  xspf;
    application/zip                       zip;

    application/octet-stream              bin exe dll;
    application/octet-stream              deb;
    application/octet-stream              dmg;
    application/octet-stream              iso img;
    application/octet-stream              msi msp msm;

    application/vnd.openxmlformats-officedocument.wordprocessingml.document    docx;
    application/vnd.openxmlformats-officedocument.spreadsheetml.sheet          xlsx;
    application/vnd.openxmlformats-officedocument.presentationml.presentation  pptx;

    audio/midi                            mid midi kar;
    audio/mpeg                            mp3;
    audio/ogg                             ogg;
    audio/x-m4a                           m4a;
    audio/x-realaudio                     ra;

    video/3gpp                            3gpp 3gp;
    video/mp2t                            ts;
    video/mp4                             mp4;
    video/mpeg                            mpeg mpg;
    video/quicktime                       mov;
    video/webm                            webm;
    video/x-flv                           flv;
    video/x-m4v                           m4v;
    video/x-mng                           mng;
    video/x-ms-asf                        asx asf;
    video/x-ms-wmv                        wmv;
    video/x-msvideo                       avi;
}
"""

# nginx conf
nginx_conf  = r"""
<<nouser>>user <<www_user>>;
worker_processes 1;

events {
    worker_connections 1024;
}

error_log <<nginx_logs_dir>>/error.log;
#error_log <<nginx_logs_dir>>/error.log notice;
#error_log <<nginx_logs_dir>>/error.log info;
pid <<nginx_logs_dir>>/nginx.pid;
#include /etc/nginx/modules-enabled/*.conf;

http {
    include mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    #gzip on;
    #tcp_nopush on;
    #charset utf-8;
    
    #access_log <<nginx_logs_dir>>/access.log;
    #access_log <<nginx_logs_dir>>/access.log main;
    #access_log <<nginx_logs_dir>>/host.access.log  main;

    client_body_temp_path <<nginx_body_dir>>;
    proxy_temp_path <<nginx_proxy_dir>>;
    fastcgi_temp_path <<nginx_fastcgi_dir>>;
    uwsgi_temp_path <<nginx_uwsgi_dir>>;
    scgi_temp_path <<nginx_scgi_dir>>;

    server {
        listen 80;
        server_name localhost 127.0.0.1;
        
        location / {
            root <<web_dir>>;
            index index.html index.htm;
        }

        location ^~ /.well-known/acme-challenge/ {
            root <<web_dir>>;
            default_type "text/plain";
            try_files $uri = 404;
        }

        location ~ /.well-known {
            allow all;
        }

        # 禁止敏感文件
        location ~* \.(py|env|conf|cfg|ini|idx|db|key|pem|bin)$ {
            deny all;
            return 403;
        }

        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$ {
            expires      30d;
        }

        location ~ .*\.(js|css)?$ {
            expires      12h;
        }

        location ~ /\. {
            deny all;
        }

        error_page 400 401 402 403 404 /40x.html;
        error_page 500 502 503 504 /50x.html;
    }

    include vhost/*.conf;
}
"""

# host conf
host_conf = r"""
    server {
        listen 80;
        listen 8899;
        #listen 443 ssl;

        #ssl_certificate ;
        #ssl_certificate_key ;
        ssl_session_cache shared:SSL:10m;
        ssl_session_cache builtin:1000 shared:SSL:10m;
        ssl_session_timeout 10m;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
        #ssl_dhparam /usr/local/nginx/conf/ssl/dhparam.pem;
        #openssl dhparam -out /usr/local/nginx/conf/ssl/dhparam.pem 2048  # 或 4096

        server_name <<domain_list>>;
        root <<host_dir>>;
        rewrite .*\.(rybo|ryxin|ryxl|ryty|rygo|ryyo|rypan|pic|ado|vdo|exp|ava)$ /api?f=rewrite&url=$uri last;

        location / {
            index index.html index.htm;
        }

        #location ~ \.php$ {
        #    root <<code_dir>>;
        #    fastcgi_pass localhost:8898;
        #    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        #    include fastcgi_params;
        #}

        location ^~ /.well-known/acme-challenge/ {
            default_type "text/plain";
            try_files $uri = 404;
        }

        location ~ /.well-known {
            allow all;
        }

        location /api {
            proxy_pass http://localhost:<<proxy_port>>;
            proxy_set_header X-Code-Dir <<code_dir>>;
            proxy_set_header X-Web-Dir <<web_dir>>;
            proxy_set_header X-Host-Name <<host_name>>;
            proxy_set_header X-Host-Route api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 禁止敏感文件
        location ~* \.(py|env|conf|cfg|ini|idx|db|key|pem|bin)$ {
            deny all;
            return 403;
        }

        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$ {
            expires      30d;
        }

        location ~ .*\.(js|css)?$ {
            expires      12h;
        }

        location ~ /\. {
            deny all;
        }

        access_log off;
        error_page 400 401 402 403 404 /40x.html;
        error_page 500 502 503 504 /50x.html;
    }
"""

# router script content(code/router.php)
router_ctt = r"""
<?php
/**
* 网站路由器
*/

error_reporting(0);
#error_reporting(E_ALL^E_NOTICE);
session_cache_limiter('public');
session_start();
session_write_close();
date_default_timezone_set('PRC');
ignore_user_abort();
set_time_limit(0);
ini_set('max_execution_time', '0');

function obj($A='', $B=1, $C='`', $D=0) {
    /*
    根据模式标志 B 对输入 A 进行解析或序列化，支持 JSON、自定义编码格式等。

    函数原型:
        obj(A: any = '', B: int = 1, C: any = '`', D: int = 0) -> any

    返回值:
        - 当 B == 1 时：返回解析后的 dict 或原始对象（若已是 dict），或 None/{}（根据输入合法性）
        - 当 B != 1 时：返回字符串形式的序列化结果，或空字符串（若输入无效）

    参数列表:
        A (any): 输入数据，可以是字符串、字典、数字或其他类型
        B (int): 操作模式标志：
            - 1 : 解析模式（从字符串还原为对象）
            - 其他值 : 序列化模式（将对象转为字符串）
        C (any): 
            - 在解析模式（B == 1）中：用作字段分隔符（默认 '`'）
            - 在序列化模式（B != 1）中：
                - 若为 1：使用 JSON 序列化
                - 若为 2：使用自定义 cts 函数序列化
                - 否则：用作键值对之间的连接分隔符（必须为字符串）
        D (int): 缩进位数，仅在序列化模式且 C == 2 时传给 cts 函数

    使用示例1（解析 JSON 字符串）:
        obj('{"name":"Alice","age":30}', 1) → {'name': 'Alice', 'age': 30}

    使用示例2（解析自定义编码字符串）:
        obj('a1`b2', 1, '`') → {'a1': 'b2'}

    使用示例3（序列化为自定义字符串）:
        obj({'x': 'y', 'p': 'q'}, 0, '|') → 'x|y|p|q'

    使用示例4（序列化为 JSON）:
        obj({'ok': True}, 0, 1) → '{"ok": true}'

    注意:
        - 依赖外部函数 e36（编码/解码）、stc（处理 '.,' 前缀）、cts（自定义序列化）
        - 当 B != 1 且 C 不为 1 或 2 C 必须为字符串，否则会引发 AttributeError
        - 非 dict 对象在序列化模式下会返回空字符串
        - 此函数需与配套的 e36/stc/cts 实现一同使用
    */

    if ($B == 1) {
        // 如果 A 是数组（PHP 中对象通常用数组表示），直接返回
        if (is_array($A)) {
            return $A;
        }
        // 如果 A 不是字符串或为空，返回 null
        if (!$A || !is_string($A)) {
            return null;
        }

        $A = trim($A);
        $a = substr($A, 0, 2);

        if ($a === '{"') {
            // 尝试 JSON 解码
            $decoded = json_decode($A, true); // true 表示返回关联数组
            if (json_last_error() === JSON_ERROR_NONE) {
                return $decoded;
            }
            // 若解析失败，继续后续逻辑
        }

        if ($a === '.,') {
            // 调用 sto 方法
            return sto($A);
        }

        // 分割字符串
        $a = explode($C, $A);
        $l = count($a);
        $o = [];

        for ($z = 0; $z < $l; $z += 2) {
            $k = e36($a[$z], 2);
            $v = isset($a[$z + 1]) ? e36($a[$z + 1], 2) : null;
            if (!$k) continue;
            $o[$k] = $v;
        }

        return $o;

    } else {

        if (is_string($A)) {
            return $A;
        }
        if (is_numeric($A)) {
            return (string)$A;
        }
        if (!$A || (!is_array($A) && !is_object($A))) {
            return '';
        }

        // 注意：PHP 中对象和数组都可能被视为 "object"
        // 假设传入的是关联数组代表对象
        if ((is_array($A) || is_object($A)) && $C == 1) {
            return json_encode($A);
        }

        if ((is_array($A) || is_object($A)) && $C == 2) {
            return ots($A, $D);
        }

        $s = [];
        foreach ($A as $key => $value) {
            $s[] = e36($key, 1);
            $s[] = e36($value, 1);
        }

        return implode($C, $s);
    }
}

function cpo($A='', $B=1, $C=0) { // comma period object
    /*
    使用逗点对象格式进行对象与字符串互换。
    
    函数原型:
        cpo(A: any = '', B: int = 1, C: int = 0) -> any

    返回值:
        - 当 B == 1 时：返回解析后的 dict 或原始对象（若已是 dict），或 None/{}（根据输入合法性）
        - 当 B != 1 时：返回字符串形式的序列化结果，或空字符串（若输入无效）
        - 可以对下列两种数据进行互换
        - 对象：{'a': 1, 'b':2, 'c':3, 'd':4, 'e':{'aa':11, 'bb':22, 'cc':33}, 'f':[1, 2, 3, {'aaa':111, 'bbb':222, 'ccc':333}, {'aaaa':1111, 'bbbb':2222, 'cccc':3333}, [4, 5, 6]]}
        - CPO 字串：., .a 1 .b 2 .c 3 .d 4 .e ., .aa 11 .bb 22 .cc 33 ,. .f .., 1, 2, 3, ., .aaa 111 .bbb 222 .ccc 333 ,. ., .aaaa 1111 .bbbb 2222 .cccc 3333 ,. .., 4, 5, 6 ,,. ,,. ,.

    参数列表:
        A (any): 输入数据，可以是字符串、字典、数字或其他类型
        B (int): 操作模式标志：
            - 1 : 解析模式（从字符串还原为对象）
            - 其他值 : 序列化模式（将对象转为字符串）
        C (int): 缩进位数，仅在序列化模式且 char == 2 时传给 cts 函数

    使用示例1（解析 CPO 格式的字符串为对象）:
        cpo('., .name Alice .age 30 ,.', 1) → {'name': 'Alice', 'age': 30}

    使用示例2（将对象序列化为 CPO 字符串）:
        cpo({'x': 'y', 'p': 'q'}, 0) → '., .x y .p q ,.'
    */

    if($B == 1) return sto($A);
    return ots($A, $C);
}

function sto($str='') { // string to object
    /*
    将 CPO 格式字符串（comma-period object）解析为对象。

    CPO 是一种紧凑的序列化格式，使用 ., 表示对象开始，.., 表示数组开始，
    ,. 表示对象结束，,,. 表示数组结束。键以 .key 形式出现。

    支持类型：bool（TRUE/FALSE）、null（NULL）、int、float、str、dict、list。

    参数列表:
        str: 输入字符串，用于转换为 CPO 对象

    示例:
        sto("., .name Alice .age 30 ,.") → {'name': 'Alice', 'age': 30}
        sto("., .flag TRUE .score 95.5 ,.") → {'flag': True, 'score': 95.5}
        sto("., .tags ..,apple,banana,,. ,.") → {'tags': ['apple', 'banana']}

    注意:
        - 键必须紧跟在 '.' 后，中间不能有空格
        - 值的边界由下一个 ".key" 或结束标记决定
        - 空值用 EMPTY 或空字符串表示
    */

    $i = 0;
    $len = strlen($str);

    // 辅助：跳过空白字符
    function skipWhitespace(&$i, $len, $str) {
        while ($i < $len && strpos(" \t\n\r", $str[$i]) !== false) {
            $i++;
        }
    }

    // 辅助：解析一个值
    function parseValue(&$i, $len, $str) {
        skipWhitespace($i, $len, $str);
        if ($i >= $len) return null; // JS 的 undefined 在 PHP 中用 null 表示

        // 数组开始 ..,
        if (substr($str, $i, 3) === '..,') {
            $i += 3;
            return parseArray($i, $len, $str);
        }

        // 对象开始 .,
        if (substr($str, $i, 2) === '.,') {
            $i += 2;
            return parseObject($i, $len, $str);
        }

        // 普通值
        $start = $i;
        while ($i < $len) {
            $char = $str[$i];

            // 遇到空白：检查是否是新键开始（即后面是 ".xxx"）
            if ($char === ' ' || $char === "\t" || $char === "\n" || $char === "\r") {
                $j = $i;
                while ($j < $len && strpos(" \t\n\r", $str[$j]) !== false) {
                    $j++;
                }
                if ($j < $len && $str[$j] === '.' && 
                    $j + 1 < $len && strpos(" .,\t\n\r", $str[$j + 1]) === false) {
                    break; // 新键开始，结束当前值
                }
            }

            // 遇到数组结束标志
            if (substr($str, $i, 3) === ',,.') {
                break;
            }

            // 遇到逗号（数组分隔符）
            if ($char === ',') {
                break;
            }

            $i++;
        }

        $val = trim(substr($str, $start, $i - $start));

        // 类型还原
        if ($val === 'TRUE') return true;
        if ($val === 'FALSE') return false;
        if ($val === 'NULL') return null;
        if ($val === 'EMPTY' || $val === '') return '';

        // 整数
        if (preg_match('/^-?\d+$/', $val)) {
            return (int)$val;
        }

        // 浮点数
        if (preg_match('/^-?\d*\.\d+$/', $val)) {
            return (float)$val;
        }

        return $val;
    }

    // 辅助：解析对象
    function parseObject(&$i, $len, $str) {
        $obj = [];
        skipWhitespace($i, $len, $str);

        while ($i < $len) {
            skipWhitespace($i, $len, $str);
            if ($i >= $len) break;

            // 对象结束标志 ',.'
            if (substr($str, $i, 2) === ',.') {
                $i += 2;
                return $obj;
            }

            // 必须以 '.' 开头，且前面是空白或起始
            if ($str[$i] !== '.') {
                $i++;
                continue;
            }

            if ($i > 0 && strpos(" \t\n\r", $str[$i - 1]) === false) {
                // 前面不是空白，说明是 abc.key 中的 '.'，跳过
                $i++;
                continue;
            }

            $i++; // 跳过 '.'

            // 检查 key 是否为空
            if ($i >= $len || strpos(" .,\t\n\r", $str[$i]) !== false) {
                continue;
            }

            // 提取 key
            $start = $i;
            while ($i < $len && strpos(" .,\t\n\r", $str[$i]) === false) {
                $i++;
            }
            $key = substr($str, $start, $i - $start);
            if (!$key) continue;

            skipWhitespace($i, $len, $str);
            if ($i >= $len) break;

            // 解析值
            if (substr($str, $i, 3) === '..,') {
                $i += 3;
                $value = parseArray($i, $len, $str);
            } elseif (substr($str, $i, 2) === '.,') {
                $i += 2;
                $value = parseObject($i, $len, $str);
            } else {
                $value = parseValue($i, $len, $str);
            }

            $obj[$key] = $value;
            skipWhitespace($i, $len, $str);
        }

        return $obj;
    }

    // 辅助：解析数组
    function parseArray(&$i, $len, $str) {
        $arr = [];
        skipWhitespace($i, $len, $str);

        while ($i < $len) {
            skipWhitespace($i, $len, $str);
            if ($i >= $len) break;

            // 数组结束标志 ',,.'
            if (substr($str, $i, 3) === ',,.') {
                $i += 3;
                return $arr;
            }

            if ($str[$i] === ',') {
                $i++;
                skipWhitespace($i, $len, $str);
                continue;
            }

            // 解析元素
            if (substr($str, $i, 3) === '..,') {
                $i += 3;
                $value = parseArray($i, $len, $str);
            } elseif (substr($str, $i, 2) === '.,') {
                $i += 2;
                $value = parseObject($i, $len, $str);
            } else {
                $value = parseValue($i, $len, $str);
            }

            $arr[] = $value;
            skipWhitespace($i, $len, $str);
        }

        return $arr;
    }

    // 主逻辑
    skipWhitespace($i, $len, $str);
    if (substr($str, $i, 2) === '.,') {
        $i += 2;
        return parseObject($i, $len, $str);
    }

    return [];
}

function ots($obj, $indent=0) { // object to string
    /*
    将 Python 对象序列化为 CPO（Comma-Period Object）格式字符串。
    
    CPO 格式规则：
    - 对象以 "., ... ,." 包裹
    - 数组以 ".., ... ,,." 包裹
    - 键以 ".key value" 形式表示
    - 基础类型映射：True→'TRUE', False→'FALSE', None→'NULL', ''→'EMPTY'
    - 若 indent > 0，则使用换行和缩进；否则用空格分隔

    参数列表:
        obj (object): 输入对象，用于转换为 CPO 格式的字符串
        indent (int): 缩进位数

    示例:
        ots({"name": "Alice", "age": 30}) 
        → "., .name Alice .age 30 ,."

        ots({"ok": True, "list": ["a", "b"]}, indent=2)
        → ".,\n  .ok TRUE\n  .list ..,\n    a,\n    b\n  ,,.\n,."

    注意:
        - 忽略函数类型的值
        - 仅处理 dict 和 list 容器
        - 字符串若为空则输出 'EMPTY'
    */

    $a = null;
    $l = 0;
    $indent = (int)$indent;
    $n = $indent ? "\n" : ' ';

    // arr2str: 数组转字符串
    function arr2str($A, $B = 0, $C = ' ', $indent = 0) {
        $a = [];
        $l = $B;
        $n = $C;
        $len = is_array($A) ? count($A) : 0;

        for ($z = 0; $z < $len; $z++) {
            $v = $A[$z] ?? null;
            $t = gettype($v);

            if ($t === 'object' || $t === 'resource' || $t === 'unknown type') {
                continue; // skip unsupported types
            }

            if ($t === 'array') {
                // 检查是否为索引数组（模拟 Array.isArray）
                $isIndexed = array_keys($A) === range(0, count($A) - 1);
                if (!$isIndexed) {
                    // treat as object
                    $prefix = pc(' ', ($l + 1) * $indent) . '.,';
                    $s = obj2str($v, $l + 1, $n, $indent) . $n . pc(' ', ($l + 1) * $indent) . ',.';
                    $a[] = $prefix . "\n" . $s;
                } else {
                    $a[] = pc(' ', ($l + 1) * $indent) . '..,';
                    $s = arr2str($v, $l + 1, $n, $indent) . $n . pc(' ', ($l + 1) * $indent) . ',,.';
                    $a[] = $s;
                }
            } elseif ($t === 'object') {
                // PHP 中对象需特殊处理，但此处假设输入为数组
                // 若传入 stdClass，可转为数组
                if (is_object($v)) {
                    $v = (array)$v;
                }
                $a[] = pc(' ', ($l + 1) * $indent) . '.,';
                $s = obj2str($v, $l + 1, $n, $indent) . $n . pc(' ', ($l + 1) * $indent) . ',.';
                $a[] = $s;
            } else {
                // 基础类型处理
                if ($v === null) {
                    $v = 'NULL';
                } elseif ($t === 'string' && $v === '') {
                    $v = 'EMPTY';
                } elseif ($t === 'boolean') {
                    $v = $v ? 'TRUE' : 'FALSE';
                }

                // 添加逗号（非最后一个元素）
                if ($z < $len - 1) {
                    $e = ',';
                } else {
                    $e = '';
                }

                $a[] = pc(' ', ($l + 1) * $indent) . $v . $e;
            }
        }

        return implode($n, $a);
    }

    // obj2str: 对象（关联数组）转字符串
    function obj2str($A, $B = 0, $C = ' ', $indent = 0) {
        $a = [];
        $l = $B;
        $n = $C;

        if (!is_array($A)) {
            return '';
        }

        foreach ($A as $k => $v) {
            $t = gettype($v);

            if ($t === 'object' || $t === 'resource' || $t === 'unknown type' || $t === 'NULL') {
                continue;
            }

            if ($t === 'array') {
                // 判断是否为索引数组
                $isIndexed = array_keys($v) === range(0, count($v) - 1);
                if ($isIndexed) {
                    $a[] = pc(' ', ($l + 1) * $indent) . '.' . $k . ' ..,';
                    $s = arr2str($v, $l + 1, $n, $indent) . $n . pc(' ', ($l + 1) * $indent) . ',,.';
                    $a[] = $s;
                } else {
                    $a[] = pc(' ', ($l + 1) * $indent) . '.' . $k . ' .,';
                    $s = obj2str($v, $l + 1, $n, $indent) . $n . pc(' ', ($l + 1) * $indent) . ',.';
                    $a[] = $s;
                }
            } elseif ($t === 'object') {
                if (is_object($v)) {
                    $v = (array)$v;
                }
                $a[] = pc(' ', ($l + 1) * $indent) . '.' . $k . ' .,';
                $s = obj2str($v, $l + 1, $n, $indent) . $n . pc(' ', ($l + 1) * $indent) . ',.';
                $a[] = $s;
            } else {
                if ($v === null) {
                    $v = 'NULL';
                } elseif ($t === 'string' && $v === '') {
                    $v = 'EMPTY';
                } elseif ($t === 'boolean') {
                    $v = $v ? 'TRUE' : 'FALSE';
                }

                $a[] = pc(' ', ($l + 1) * $indent) . '.' . $k . ' ' . $v;
            }
        }

        return implode($n, $a);
    }

    // 主逻辑
    $inner = obj2str($obj, 0, $n, $indent);
    $str = '.,' . $n . $inner . $n . pc(' ', $l * $indent) . ',.';

    return $str;
}

function pc($char, $count) {
    return str_repeat($char, (int)$count);
}

function e36($A, $B = 1) { // exclamation encode or decode 36 special symbols
    $a = $b = $c = $d = $e = $f = $l = $y = $z = null;

    if (!$A) return '';
    $A = (string)$A;

    $a = '!@#$%^&*()-_=+`~[]{}\\|;:\'",.<>/? ' . "\t\r\n";
    $b = '1234567890abcdefghijklmnopqrstuvwxyz';

    $a = str_split($a);
    $b = str_split($b);

    $c = [];

    // 构建映射表 c[a[z]] = b[z]（但 b[z] 前加 '!'）
    for ($z = 0; $z < 36; $z++) {
        $b[$z] = '!' . $b[$z];
        $c[$a[$z]] = $b[$z];
    }

    $l = count($a); // a.length

    if ($B == 1) {
        // 编码：先转义 ! 为 :E:，再替换特殊字符
        $A = str_replace('!', ':E:', $A);
        foreach ($c as $from => $to) {
            $A = str_replace($from, $to, $A);
        }

    } else {

        // 解码：循环替换，直到没有 ! 开头的编码
        while (true) {
            for ($z = 0; $z < $l; $z++) {
                // 注意：$b[$z] 是 "!x" 形式，$a[$z] 是原始符号
                $A = str_replace($b[$z], $a[$z], $A);
            }
            // 检查是否还有未处理的 '!'
            if (strpos($A, '!') === false) {
                break;
            }
        }
        // 最后还原被转义的 !
        $A = str_replace(':E:', '!', $A);
    }

    return $A;
}

if ($_SERVER["HTTP_X_FORWARDED_FOR"]) {
    # 如果有代理，取第一个IP
    $a = explode(',', $_SERVER["HTTP_X_FORWARDED_FOR"], 2);
    $cip = $a[0];
} else if ($_SERVER["HTTP_X_REAL_IP"]) {
    $cip = $_SERVER["HTTP_X_REAL_IP"];
} else {
    $cip = '0.0.0.0';
}

$core = [
    "cdir" => strtolower($_SERVER["HTTP_X_CODE_DIR"]),
    "wdir" => strtolower($_SERVER["HTTP_X_WEB_DIR"]),
    "hname" => strtolower($_SERVER["HTTP_X_HOST_NAME"]),
    "meth" => strtolower($_SERVER["REQUEST_METHOD"]),
    "url" => $_SERVER["HTTP_ORIGIN"] . $_SERVER["REQUEST_URI"],
    "ref" => $_SERVER["HTTP_REFERER"],
    "ori" => $_SERVER["HTTP_ORIGIN"],
    "host" => $_SERVER["HTTP_HOST"],
    "ua" => $_SERVER["HTTP_USER_AGENT"],
    "cip" => $cip
];

$ct = $_SERVER['CONTENT_TYPE'] ? $_SERVER['CONTENT_TYPE'] : '';
$d = file_get_contents('php://input');

if (strpos($ct, 'application/json') !== false) {
    $d = e36($d, 0);
    $obj = obj($d);
} 
elseif (strpos($ct, 'application/x-www-form-urlencoded') !== false) {
    $d = e36($d, 0);
    parse_str($d, $f);
    $obj = $f;
}
elseif (strpos($ct, 'multipart/form-data') !== false) {
    $obj = $_POST + $_FILES['file'];
}
else {
    $d = e36($d, 0);
    $obj = obj($d);
}

$data = $_GET + $obj;
$data['HEAD'] = $_SERVER;
$data['CORE'] = $core;

$path = $core['cdir'] . '/' .$core['hname']. '/app.php';
$ryo = $core['cdir'] . '/' .$core['hname']. '/ryo.php';
if (file_exists($path)) {
    @include_once($path);
} else if (file_exists($ryo)) {
    @include_once($ryo);
}

if (function_exists('api')) {
    $res = api($data);
} else {
    $res = array('errno' => 1, 'errmsg' => '入口模块加载错误');
}
echo json_encode($res);

?>
"""

# install page content(web/index.html)
install_ctt = r"""
<!DOCTYPE html>
<html>
<head>
    <title>ryweb - 网站服务器管理工具</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .status { background: #27ae60; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; }
        .info { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ryweb 网站服务器管理工具</h1>
        <p class="status">Nginx 安装成功！</p>
        
        <div class="info">
            <h3>环境信息</h3>
            <p><strong>服务器目录:</strong> <<www_root>></p>
            <p><strong>服务器用户:</strong> <<www_user>></p>
            <p><strong>代理端口:</strong> <<proxy_port>></p>
            <p><strong>管理端口:</strong> <<admin_port>></p>
            <p><strong>管理员:</strong> admin</p>
            <p><strong>管理密码:</strong> 123pass321</p>
            <p><strong>管理页面:</strong> <a href="http://host:<<admin_port>>/admin.html">http://host:<<admin_port>>/admin.html</a></p>
        </div>
        
        <p>环境安装完成，您可以开始部署您的网站应用了。</p>
    </div>
</body>
</html>
"""

# index page content(web/host/index.html)
index_ctt = r"""
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=450, user-scalable=no">
    <meta name="robots" content="all">
    <meta name="author" content="ry">
    <meta name="keywords" content="编程社交|轻松编程|开源程序|时光流布局|锐鸥|锐码rymaa.cn">
    <meta name="description" content="锐鸥(ryo)是一款免费开源的网页框架，由锐白个人开发，通过该程序用户可以快速创建网页应用。锐鸥追求的是轻巧的编程体验，让程序开发像鸥鸟般轻盈快活。使用方法：由站长将锐鸥(ryo)脚本文件（如：ryo_v2025.8.1.0.js）下载放到目标网站的 js 目录，然后在 html 页面的 body 标签后面加载即可，（如：＜script src="js/ryo_v2026.1.1.0.js"＞＜/script＞）。源码仓库：https://gitee.com/rybby/ryo">
    <title id="TIT">轻盈，灵巧 - 锐鸥</title>
    <link id="CSS" rel="stylesheet" href="css/ryo_2026.1.1.0.css">
</head>

<body>
    <p style="margin:0; padding:50px; color:#f22; font-family:黑体; font-size:34px; text-align:center;">数据载入中...</p>
    <div id="footer" style="position: absolute; left: 0; bottom: 0; margin: 0; padding: 0; width: 100%; height: 24px; line-height: 24px; font-size: 16px; text-align: center; color: #333; font-family: Tahoma, Verdana, SimSun; background-color: #A3B8CC; border-top: 1px solid #7D98B3;">版权所有 2025 <a href="http://rymaa.cn/" target="_blank" id="COPR">锐码[rymaa.cn]</a> | <a href="https://beian.miit.gov.cn/" target="_blank" id="ICPF">{{ICP备案}}</a> | <a href="http://www.beian.gov.cn/" target="_blank" id="PSBF">{{公安备案}}</a> | <a href="https://beian.miit.gov.cn/" target="_blank" id="ICPL">{{ICP执照}}</a> | <a href="sitemap" target="_blank">网站地图</a></div>
</body>
<script id="JS" src="js/ryo_2026.1.1.0.js"></script>
</html>
"""

# admin page content(web/host/admin.html)
admin_ctt = r"""
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=450, user-scalable=no">
    <meta name="robots" content="all">
    <meta name="author" content="ry">
    <meta name="keywords" content="编程社交|轻松编程|时光流布局|锐鸥|锐码rymaa.cn">
    <meta name="description" content="锐鸥(ryo)是一款免费开源的网页框架，由锐白个人开发，通过该程序用户可以快速创建网页应用。锐鸥追求的是轻巧的编程体验，让程序开发像鸥鸟般轻盈快活。使用方法：由站长将锐鸥(ryo)脚本文件（如：ryo_v2025.8.1.0.js）下载放到目标网站的 js 目录，然后在 html 页面的 body 标签后面加载即可，（如：＜script src="js/ryo_v2026.1.1.0.js"＞＜/script＞）。源码仓库：https://gitee.com/rybby/ryo">
    <title>网站管理员 - 轻盈，灵巧 - 锐鸥</title>
</head>

<body>
    网站管理员
</body>

</html>
"""

# 40X page content(web/host/40x.html)
err_40x_ctt = r"""
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=450, user-scalable=no">
    <meta name="robots" content="all">
    <meta name="author" content="ry">
    <meta name="keywords" content="编程社交|轻松编程|时光流布局|锐鸥|锐码rymaa.cn">
    <meta name="description" content="锐鸥(ryo)是一款免费开源的网页框架，由锐白个人开发，通过该程序用户可以快速创建网页应用。锐鸥追求的是轻巧的编程体验，让程序开发像鸥鸟般轻盈快活。使用方法：由站长将锐鸥(ryo)脚本文件（如：ryo_v2025.8.1.0.js）下载放到目标网站的 js 目录，然后在 html 页面的 body 标签后面加载即可，（如：＜script src="js/ryo_v2026.1.1.0.js"＞＜/script＞）。源码仓库：https://gitee.com/rybby/ryo">
    <title>40X 错误 - 轻盈，灵巧 - 锐鸥</title>
</head>

<body>
    <p style="margin:0; padding:50px; color:#f22; font-family:黑体; font-size:34px; text-align:center;">40X - 文件缺失</p>
</body>

</html>
"""

# 50X page content(web/host/50x.html)
err_50x_ctt = r"""
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=450, user-scalable=no">
    <meta name="robots" content="all">
    <meta name="author" content="ry">
    <meta name="keywords" content="编程社交|轻松编程|时光流布局|锐鸥|锐码rymaa.cn">
    <meta name="description" content="锐鸥(ryo)是一款免费开源的网页框架，由锐白个人开发，通过该程序用户可以快速创建网页应用。锐鸥追求的是轻巧的编程体验，让程序开发像鸥鸟般轻盈快活。使用方法：由站长将锐鸥(ryo)脚本文件（如：ryo_v2025.8.1.0.js）下载放到目标网站的 js 目录，然后在 html 页面的 body 标签后面加载即可，（如：＜script src="js/ryo_v2026.1.1.0.js"＞＜/script＞）。源码仓库：https://gitee.com/rybby/ryo">
    <title>50X 错误 - 轻盈，灵巧 - 锐鸥</title>
</head>

<body>
    <p style="margin:0; padding:50px; color:#f22; font-family:黑体; font-size:34px; text-align:center;">50X - 服务器错误</p>
</body>

</html>
"""
