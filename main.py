# coding: utf-8

import os
import re
import eel
import time
import base64
import random
import traceback
import webbrowser
import json
import shutil
import mimetypes

from arnanutil.io_util import prepare_dir, get_file_size
from arnanutil.http_util import HttpGet
from arnanutil.log_util import logf_env, logf
from arnanutil.hcache import UTF8HCache
from arnanutil.hash_util import get_file_md5

LOG_DIR = 'log'
HTTP_CACHE_DIR = 'http_cache'
DATA_CACHE_DIR = 'data_cache'
APP_NAME = 'doujin_voice_browser'
TMP_DIR = 'web\\tmp'

prepare_dir(LOG_DIR)
prepare_dir(HTTP_CACHE_DIR)
prepare_dir(DATA_CACHE_DIR)
prepare_dir(TMP_DIR)

j = os.path.join
http_get = HttpGet(HTTP_CACHE_DIR)

class AppData(object):
    def __init__(self):
        cfg_file = os.getenv('APPDATA')
        assert cfg_file
        path = os.path.join(cfg_file, APP_NAME)
        prepare_dir(path)

        filename = os.path.join(path, 'appdata.json')

        self.data = None
        self.filename = filename

    def load(self):
        if not os.path.exists(self.filename):
            self.data = {}
        else:
            with open(self.filename, 'r') as f:
                self.data = json.load(f)

    def save(self):
        if self.data:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f)

    def get(self, k):
        if self.data:
            return self.data.get(k, None)
        else:
            return None

    def set(self, k, v):
        self.data[k] = v

def is_image(filename):
    filetype, _ = mimetypes.guess_type(filename)
    if not filetype:
        return False
    maintype, _ = filetype.split('/', 1)
    # print '--', filetype, maintype, maintype == 'image'
    # print filename.decode('gbk', 'replace').encode('gbk', 'replace')
    return maintype == 'image'



class WorkInfo(object):
    def __init__(self, db, rj, dirname):
        self.db = db
        self.rj = rj
        self.dirname = dirname

    def init_image_path(self):
        max_size = 0
        target = None
        for root, dirs, names in os.walk(self.dirname):
            for name in names:
                if is_image(name):
                    path = os.path.join(root, name)
                    size = get_file_size(path)
                    if not target or size > max_size:
                        max_size = size
                        target = path
        return target


    def get_image_path(self):
        key = self.rj + '.image_path'
        image_path = self.db.get(key)
        if not image_path:
            image_path = self.init_image_path() or ''
            self.db.set(key, image_path)
        return image_path


    def get_image_data(self):
        image_path = self.get_image_path()
        if not image_path:
            return None

        # print('image_path:', image_path)

        image_type, _ = mimetypes.guess_type(image_path)
        # print 'image_type:', image_type

        with open(image_path, 'rb') as f:
            c = f.read()
        return 'data:' + image_type + ';base64,' + base64.b64encode(c)

    def dump(self):
        return {
            # 'image_data': self.get_image_data(),
            'image_path': self.get_image_path(),
            'rj': self.rj,
        }

class App(object):
    def __init__(self):
        self.appdata = AppData()
        self.appdata.load()
        self.lib = []
        self.db = UTF8HCache(DATA_CACHE_DIR)

    # def app_expose(self, func):
    #     def wrapper(*args, **kwds):
    #         return func(self, *args, **kwds)
    #     return wrapper

    def get_work_info(self, meta):
        return WorkInfo(self.db, meta['rj'], meta['dirname'])

    def refresh_library(self):
        lr = self.appdata.get('LIBRARY_ROOT')
        if not lr:
            return False
        lib = []
        for name in os.listdir(lr):
            dirname = os.path.join(lr, name)
            if os.path.isdir(dirname):
                m = re.search(r'(rj\d+)', name.lower())
                if m:
                    rj = m.group(1).upper()
                    lib.append({
                        'rj': rj,
                        'dirname': dirname,
                    })
        self.lib = lib
        return True

    def get_lib(self):
        return [self.get_work_info(x).dump() for x in self.lib]

def main():
    eel.init('web')
    app = App()

    @eel.expose
    def get_library_root():
        return app.appdata.get('LIBRARY_ROOT')

    @eel.expose
    def set_library_root(v):
        if os.path.isdir(v):
            app.appdata.set('LIBRARY_ROOT', v)
            app.appdata.save()
            return True
        else:
            return False

    @eel.expose
    def open_url(url):
        webbrowser.open(url)

    @eel.expose
    def refresh_library():
        return app.refresh_library()

    @eel.expose
    def get_lib():
        return app.get_lib()

    @eel.expose
    def load_work_image(image_path):
        if not image_path:
            return None
        image_type, _ = mimetypes.guess_type(image_path)
        md5 = get_file_md5(image_path)
        dst = os.path.join(TMP_DIR, md5)
        if not os.path.isfile(dst) or get_file_md5(dst) != md5:
            shutil.copy(image_path, dst)
        image_url = 'tmp/' + md5
        return image_url

    web_app_options = {
        'mode': "chrome-app", #or "chrome"
        'host': 'localhost',
        'port': 7777,
    }

    print 'start'
    eel.start('index.html?s=' + str(time.time()) + str(random.random()), size=(1400, 600), options=web_app_options)
    print 'after start'

if __name__ == '__main__':
    with logf_env(LOG_DIR):
        try:
            main()
        except Exception:
            print 'exc'
            logf(traceback.format_exc())
