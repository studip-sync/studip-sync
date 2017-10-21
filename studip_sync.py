#!/usr/bin/env python
# -*- coding: utf-8 -*-

from studip_sync.studip_sync import StudipSync

with StudipSync() as s:
    s.sync()
