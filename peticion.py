# -*- coding: utf-8 -*-

class PeticionBase(object):
    def __init__(self, entorno=None):
        self.entorno = entorno
        self.entorno['Runner.peticion'] = self

class Peticion(PeticionBase):
    """
    Base Peticion
    """
    url_regla = None
    vista_args = None

    @property
    def final(self):
        if self.url_regla is not None:
            return self.url_regla.final

    @property
    def blueprint(self):
        if self.url_regla and '.' in self.url_regla.final:
            return self.url_regla.final.rsplit('.', 1)[0]
        