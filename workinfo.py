# coding: utf-8

import os
import io
import base64
import mimetypes

from PIL import Image

from arnanutil.io_util import get_file_size
from arnanutil.hash_util import get_file_hash, get_hash

FIELDS = (  'rj'
          , 'thumbnail_data'
          , 'thumbnail_hash'
          , 'path'
          , 'image_path'
          , 'title'
          , 'maker'
          , 'pubtime'
          )


def is_image(filename):
    filetype, _ = mimetypes.guess_type(filename)
    if not filetype:
        return False
    maintype, _ = filetype.split('/', 1)
    # print '--', filetype, maintype, maintype == 'image'
    # print filename.decode('gbk', 'replace').encode('gbk', 'replace')
    return maintype == 'image'


class WorkInfoBuilder(object):
    def __init__(self, db):
        self.db = db

    def create(self, rj, path):
        self.path = path
        thumbnail_data = self.get_image_data()
        thumbnail_hash = thumbnail_data and get_hash(thumbnail_data) or None
        d = vars()
        o = {}
        for k in FIELDS:
            if k in d:
                o[k] = d[k]
        self.db.insert(**o)

    def get_image_path(self):
        max_size = 0
        target = None
        for root, dirs, names in os.walk(self.path):
            for name in names:
                if is_image(name):
                    path = os.path.join(root, name)
                    size = get_file_size(path)
                    if not target or size > max_size:
                        max_size = size
                        target = path
        return target


    def get_image_data(self):
        image_path = self.get_image_path()
        if not image_path:
            return None

        # print('image_path:', image_path)

        # image_type, _ = mimetypes.guess_type(image_path)
        # print 'image_type:', image_type

        thumbnail_data = io.BytesIO()

        im = Image.open(image_path)
        im.thumbnail((200, 200), Image.ANTIALIAS)
        im.convert('RGBA').save(thumbnail_data, "PNG")
        return thumbnail_data.getvalue()
        # with open(image_path, 'rb') as f:
        #     c = f.read()
        # return 'data:' + image_type + ';base64,' + base64.b64encode(c)


class WorkInfo(object):
    def __init__(self, db):
        self.db = db

    def load(self, r):
        self.rec = r
        return self

    def dump(self):
        r = self.rec
        # thumbnail_data = r['thumbnail_data'] and ('data:image/png;base64,' + base64.b64encode(r['thumbnail_data'])) or None
        return {
            # 'image_data': self.get_image_data(),
            # 'thumbnail_data': thumbnail_data,
            'rj': r['rj'],
        }

    def get_thumbnail_data(self):
        r = self.rec
        return r['thumbnail_data'] and ('data:image/png;base64,' + base64.b64encode(r['thumbnail_data'])) or None

