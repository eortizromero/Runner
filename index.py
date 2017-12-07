# -*- coding: utf-8 -*-
from wsgiref.simple_server import make_server
# from functools import wraps

def imprimir(f):
    def decorador():
        return f()
    return decorador

@imprimir
def index():
    return "Hola Mundo"

print index()

extensiones = ('.html', '.htm')
extension_pred = '.html'

def pagina(archivo_html=None):
    if archivo_html is not None:
        if archivo_html != '':
            if not isinstance(archivo_html, str):
                raise TypeError("El primer parametro deber ser una cadena[str], se obtuvo en su lugar: ", type(archivo_html))
            if not archivo_html.endswith(extension_pred):
                raise ValueError("El Archivo no tiene una extension correcta.")
            # archivo = archivo_html.split('.')
            # extension = "." + "".join(archivo[1])

            # if not extension in extensiones:
            #     ext = " ".join(extensiones)
            #     raise ValueError("El archivo debe tener la extension %s" % ext)
            try:
                with open(archivo_html, 'r') as pagina:
                    html = pagina.read()
            except Exception:
                raise ValueError("No existe el archivo %s" % archivo_html)
            return html
        raise ValueError("La cadena no debe estar vacia")
    raise ValueError("Debes agregar un archivo html")


class Runner(object):
    def __init__(self):
        self.regla = {}

    @property
    def get_reglas(self):
        return self.regla

    def respuesta(self, ruta, entorno):
        return self.regla[ruta](entorno['REQUEST_METHOD'])

    def aplicacion_wsgi(self, entorno, respuesta):
        encabezado = [('Content-Type', 'text/html')]
        status = None
        res = None
        ruta = entorno.get('PATH_INFO') or '/'
        if ruta in self.get_reglas:
            status = '200 OK'
            res = self.respuesta(ruta, entorno)
        else:
            status = '404 NOT FOUND'
            res = "Pagina no encontrada"
        respuesta(status, encabezado)
        return res

    def __call__(self, entorno, respuesta):
        return self.aplicacion_wsgi(entorno, respuesta)

    def parametro_vista(self, funcion_param):
        return funcion_param.__name__

    def agregar_regla(self, cadena, metodos=None):
        if not cadena.startswith('/'):
            raise ValueError("La url debe iniciar con una diagonal '/'")

        if metodos is None:
            self.metodos = None
        else:
            if isinstance(metodos, str):
                raise TypeError("Los metodos deben ser iterables[str] ")
            self.metodos = set([x.upper() for x in metodos])
            if 'HEAD' not in self.metodos and 'GET' in self.metodos:
                self.metodos.add('HEAD')

    def agregar_regla_url(self, regla, parametro=None, funcion_param=None, **opciones):
        if parametro is None:
            parametro = self.parametro_vista(funcion_param)

        metodos = opciones.pop('metodos', None)

        if metodos is None:
            metodos = getattr(funcion_param, 'metodos', None) or ('GET',)

        if isinstance(metodos, (str, unicode)):
            raise TypeError("Los metodos deben ser un Iterable[str] no un String.")

        metodos = set(m.upper() for m in metodos)
        self.regla[regla] = funcion_param
        # regla = self.agregar_regla(regla, metodos=metodos, **opciones)

    def ruta(self, regla, **opciones):
        def decorador(funcion):
            parametro = opciones.pop('parametro', None)
            self.agregar_regla_url(regla, parametro, funcion, **opciones)
            return funcion
        return decorador

    def correr(self, dominio='127.0.0.1', puerto=8000):
        httpd = make_server(dominio, puerto, self)
        print "* Corriendo en http://python.developer.io:8000 (Presiona Ctrl + C para salir.)"
        httpd.serve_forever()
