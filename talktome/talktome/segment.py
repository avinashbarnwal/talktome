#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Help will be here :)
"""
from __future__ import division, print_function, absolute_import
from __future__ import unicode_literals

class Segment:
    def __init__(self,filename,startTime=0,endTime=None):
        self.filename = filename
        self.startTime = startTime
        self.endTime = endTime
        self.operationLog = None
        self.features = None
        self.description = None
