# -*- coding: utf-8 -*-

class PeticionBase(object):
    def __init__(self, entorno, llenar_solicitud=True):
        self.entorno = entorno
        if llenar_solicitud:
            self.entorno['Runner.peticion'] = self
        print self.entorno
