# -*- coding: utf-8 -*-

class BaseObject(object):
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __str__(self) -> str:
        attributes = [
            attribute
            for attribute in dir(self)
            if not attribute.startswith("__") and not callable(getattr(self, attribute))
        ]
        attributeMap = {
            attribute: str(getattr(self, attribute)) for attribute in attributes
        }
        return f"{attributeMap}" 