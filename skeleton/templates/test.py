#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 11:50:21 2021

@author: yash
"""

def getAllPhotosByTag(tagDescription):
	cursor = conn.cursor()
	cursor.execute("SELECT Pictures.imgdata, Pictures.picture_id, Pictures.caption, TaggedWith.tagDescription FROM Pictures INNER JOIN taggedWith ON Pictures.picture_id = taggedWith.photoID WHERE TaggedWith.tagDescription = '{0}'".format(tagDescription))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]
