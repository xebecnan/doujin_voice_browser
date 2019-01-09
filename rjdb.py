# coding: utf-8

import os
import sys

from pydblite.pydblite import Base

from workinfo import WorkInfo, FIELDS

class RJDB(object):
    def __init__(self):
        db = Base('rjdb.pdl')
        if db.exists():
            db.open()
        else:
            db.create(*FIELDS)
        self.db = db

    def insert(self, **kwds):
        self.db.insert(**kwds)

    def iter_works(self, from_index, to_index):
        return (WorkInfo(self).load(r) for i, r in enumerate(self.db) if i >= from_index and i < to_index)

    def get_works_count(self):
        return len(self.db)

    def get_work(self, rj):
        records = self.db(rj = rj)
        if records:
            return WorkInfo(self).load(records[0])
        else:
            return None

    def commit(self):
        self.db.commit()
