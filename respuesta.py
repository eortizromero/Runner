# -*- coding: utf-8 -*-

class RespuestaBase(object):
    status_predeterminado = 200
    mimetype_predeterminado = 'text/plain'

    def __init__(self, respuesta=None, status=None, encabezados=None,
                mimetype=None, tipo_contenido=None):
        pass

    
