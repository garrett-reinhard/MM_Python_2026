# -*- coding: utf-8 -*-
"""
Created on Thu May  6 06:26:41 2021

@author: John Price after 'martineau', see SO links
"""
from _ctypes import PyObj_FromPtr  # see https://stackoverflow.com/a/15012814/355230
import json
import re
import copy

# custom pretty-printing of lists and tuples
# https://stackoverflow.com/questions/42710879/write-two-dimensional-list-to-json-file/42721412#42721412
class NoIndent(object):
    """ Value wrapper. """
    def __init__(self, value):
        if not isinstance(value, (list, tuple)):
            raise TypeError('Only lists and tuples can be wrapped')
        self.value = value


class NoIndentEncoder(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'  # Unique string pattern of NoIndent object ids.
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))  # compile(r'@@(\d+)@@')

    def __init__(self, **kwargs):
        # Keyword arguments to ignore when encoding NoIndent wrapped values.
        ignore = {'cls', 'indent'}

        # Save copy of any keyword argument values needed for use here.
        self._kwargs = {k: v for k, v in kwargs.items() if k not in ignore}
        super(NoIndentEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, NoIndent)
                    else super(NoIndentEncoder, self).default(obj))

    def iterencode(self, obj, **kwargs):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.

        # Replace any marked-up NoIndent wrapped values in the JSON repr
        # with the json.dumps() of the corresponding wrapped Python object.
        for encoded in super(NoIndentEncoder, self).iterencode(obj, **kwargs):
            match = self.regex.search(encoded)
            if match:
                id = int(match.group(1))
                no_indent = PyObj_FromPtr(id)
                json_repr = json.dumps(no_indent.value, **self._kwargs)
                # Replace the matched id string with json formatted representation
                # of the corresponding Python object.
                encoded = encoded.replace(
                            '"{}"'.format(format_spec.format(id)), json_repr)

            yield encoded
            
# function to wrap shims (nested list) and settings (dict)
# deep copy is needed to preserve unwrapped objects
def noindent_wrap(obj):
    
    keys_to_wrap = ['phase','incs','parts']    
    cobj = copy.deepcopy(obj)
    
    # shims case
    if type(cobj) == list:
        cobj[1] = NoIndent(cobj[1])
        cobj[2] = [NoIndent(elem) for elem in cobj[2]]
        
    # settings case 
    if type(cobj) == dict:
        for item in cobj:
            for key in keys_to_wrap:
                if cobj[item].get(key, False):
                    cobj[item][key] = NoIndent(cobj[item][key])
                    
    return cobj