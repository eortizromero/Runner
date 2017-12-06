# -*- coding: utf-8 -*-
from wsgiref.simple_server import make_server as servir

def get_wsgi_status():
    status = '200 OK'
    return status

def get_wsgi_headers():
    header = [('Content-Type', 'text/html')]
    return header

def inicio():
    return RespuestaBase('Hola Mundo')

def app(env, res):
    path = env['PATH_INFO'] or '/'
    if path == '/':
        response = inicio()
    else:
        response = RespuestaBase('Not Found', status=404)
    return response(env, res)

class RespuestaBase(object):
    status_predeterminado = 200
    mimetype_predeterminado = 'text/plain'

    def __init__(self, respuesta=None, status=None, encabezados=None,
                mimetype=None, tipo_contenido=None):
        self.respuesta = respuesta
        self.status = status if status else get_wsgi_status()
        self.headers = encabezados if encabezados else get_wsgi_headers()

    def __call__(self, env, res):
        """
        : param env: Entorno para cada Peticion
        : param res: Respuesta a cada Peticion
        """
        status = self.status
        headers = self.headers
        response = self.respuesta
        res(status, headers)
        return response

if __name__ == '__main__':
    httpd = servir('', 5000, app)
    print "*** Corriendo en http://localhost:5000"
    httpd.serve_forever()
