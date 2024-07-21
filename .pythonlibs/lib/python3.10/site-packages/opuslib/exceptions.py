#!/usr/bin/env python
# -*- coding: utf-8 -*-

import opuslib.api

__author__ = 'Никита Кузнецов <self@svartalf.info>'
__copyright__ = 'Copyright (c) 2012, SvartalF'
__license__ = 'BSD 3-Clause License'


class OpusError(Exception):

    def __init__(self, code):
        self.code = code

    def __str__(self):
        return opuslib.api.info.strerror(self.code)
