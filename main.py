# coding: utf-8

import os
import re
import io
import eel
import time
import base64
import random
import traceback
import webbrowser
import json
import shutil
import mimetypes
import subprocess

from rjdb import RJDB
from PIL import Image

from arnanutil.io_util import prepare_dir, get_file_size
from arnanutil.http_util import HttpGet
from arnanutil.log_util import logf_env, logf
from arnanutil.hcache import UTF8HCache
from arnanutil.hash_util import get_file_hash, get_hash

from workinfo import WorkInfoBuilder

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



class App(object):
    def __init__(self):
        self.appdata = AppData()
        self.appdata.load()
        # self.db = UTF8HCache(DATA_CACHE_DIR)
        self.db = RJDB()

    # def app_expose(self, func):
    #     def wrapper(*args, **kwds):
    #         return func(self, *args, **kwds)
    #     return wrapper

    # def get_work_info(self, meta):
    #     return WorkInfoBuilder(self.db, meta['rj'], meta['dirname'])

    def refresh_library(self):
        lr = self.appdata.get('LIBRARY_ROOT')
        if not lr:
            return False
        for name in os.listdir(lr):
            dirname = os.path.join(lr, name)
            if os.path.isdir(dirname):
                m = re.search(r'(rj\d+)', name.lower())
                if m:
                    rj = m.group(1).upper()
                    print 'refresh_library', rj
                    WorkInfoBuilder(self.db).create(rj, dirname)
                    # self.db.add(rj=rj, path=dirname)
        print 'refresh_library done'
        self.db.commit()
        return True

    def get_lib(self, from_index, to_index):
        print 'get_lib',from_index, to_index
        return [work.dump() for work in self.db.iter_works(from_index, to_index)]

    def get_lib_size(self):
        return self.db.get_works_count()

    def get_work_thumbnail_data(self, rj):
        if not rj: return None

        work = self.db.get_work(rj)
        return work and work.get_thumbnail_data()

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
    def open_file_in_explorer(path):
        subprocess.Popen(('explorer', '/select,', path))

    @eel.expose
    def open_explorer_by_rj(rj):
        pass

    @eel.expose
    def refresh_library():
        return app.refresh_library()

    @eel.expose
    def get_lib(f, t):
        return app.get_lib(f, t)

    @eel.expose
    def get_lib_size():
        return app.get_lib_size()

    @eel.expose
    def load_work_image(rj):
        return app.get_work_thumbnail_data(rj)

        # image_type, _ = mimetypes.guess_type(image_path)
        # md5 = get_file_hash(image_path)
        # dst = os.path.join(TMP_DIR, md5)
        # if not os.path.isfile(dst) or get_file_hash(dst) != md5:
        #     shutil.copy(image_path, dst)
        # image_url = 'tmp/' + md5
        # return image_url

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
