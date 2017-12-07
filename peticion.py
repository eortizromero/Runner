# -*- coding: utf-8 -*-

class PeticionBase(object):
    def __init__(self, entorno=None):
        self.entorno = entorno
        self.entorno['Runner.peticion'] = self

class Peticion(PeticionBase):
    """
    Base Peticion
    """
