# -*- coding: utf-8 -*-

from string import Formatter

class NamespaceFormatter(Formatter):

   def __init__(self) -> None:
       Formatter.__init__(self)

   def get_value(self, key, args, kwargs):# -> Any:
      new_args = []
      for arg in args:
         if arg is None:
            new_args.append('')
         else:
            new_args.append(arg)

      for _key,value in kwargs.items():
         if value is None:
            kwargs[_key] = ''

      return Formatter.get_value(self, key, new_args, kwargs)

formatter = NamespaceFormatter()

def strip(s) -> str:
   return s if s is None or not isinstance(s, str) else s.strip()

def camel_to_underscore(s) -> str:
    """转下划线命名"""
    return ''.join(f'_{c.lower()}' if c.isupper() else c for c in s)

def underscore_to_camel(s) -> str:
    """转驼峰法命名"""
    camelChars = []
    behindUnderScore = False
    for _, c in enumerate(s, 1):
        if c == '_':
            behindUnderScore = True
            continue
        camelChars.append(c.upper()) if behindUnderScore else camelChars.append(c)
        behindUnderScore = False
    return ''.join(camelChars)

def remove_from_first(s:str, tag:str) -> str:
      last_tag_index = s.find(tag)
      if last_tag_index == -1:
          return s
      return s[:last_tag_index]
def remove_from_last(s:str, tag:str) -> str:
      last_tag_index = s.rfind(tag)
      if last_tag_index == -1:
          return s
      return s[:last_tag_index]
def remove_to_first(s:str, tag:str) -> str:
      first_tag_index = s.find(tag)
      if first_tag_index == -1:
          return s
      return s[first_tag_index+1:]
def remove_to_last(s:str, tag:str) -> str:
      first_tag_index = s.rfind(tag)
      if first_tag_index == -1:
          return s
      return s[first_tag_index+1:]