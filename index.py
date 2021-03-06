# -*- coding: utf-8 -*-
from wsgiref.simple_server import make_server
from collections import defaultdict
from peticion import Peticion
from respuesta import Respuesta
import os
import pkgutil
import sys
from itertools import chain


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

def ubicar_paquete(nombre_imp):
    nombre_mod_raiz = nombre_imp.split('.')[0]
    cargador = pkgutil.get_loader(nombre_mod_raiz)
    if cargador is None or nombre_imp == '__main__':
        ruta_paquete = os.getcwd()
    else:
        if hasattr(cargador, 'obtener_nombrearchivo'):
            nombrearchivo = cargador.obtener_nombrearchivo(nombre_mod_raiz)
        elif hasattr(cargador, 'archivo'):
            nombrearchivo = cargador.archivo
        else:
            __import__(nombre_imp)
            nombrearchivo = sys.modules[nombre_imp].__file__
        ruta_paquete = os.path.abspath(os.path.dirname(nombrearchivo))

    sitio_padre, sitio_folder = os.path.split(ruta_paquete)
    py_prefijo = os.path.abspath(sys.prefix)
    if ruta_paquete.startswith(py_prefijo):
        return py_prefijo, ruta_paquete
    elif sitio_folder.lower() == 'site-packages':
        padre, folder = os.path.split(sitio_padre)
        if folder.lower() == 'lib':
            dir_base = padre
        elif os.path.basename(padre).lower() == 'lib':
            dir_base = os.path.dirname(padre)
        else:
            dir_base = sitio_padre
        return dir_base, ruta_paquete
    return None, ruta_paquete

def pagina(archivo_html=None):
    if archivo_html is not None:
        if archivo_html != '':
            if not isinstance(archivo_html, str):
                raise TypeError("El primer parametro deber ser una cadena[str], \
                                 se obtuvo en su lugar: ", type(archivo_html))
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

class ContextoPeticion(object):
    def __init__(self, aplicacion, entorno, peticion=None):
        self.aplicacion = aplicacion
        if peticion is None:
            peticion = aplicacion.peticion_clase(entorno)
        self.peticion = peticion
        self.adaptador_url = aplicacion.crear_adaptador_url(self.peticion)

    def peticion_encontrada(self):
        try:
            ruta_url, self.peticion.vista_args = self.adaptador_url

class Ruta(object):
    def __init__(self, regla, metodos=None, final=None):
        if not regla.startswith('/'):
            raise ValueError("La url debe iniciar con una diagonal '/'")
        self.regla = regla
        self.mapa = None

        if metodos is None:
            self.metodos = None
        else:
            if isinstance(metodos, str):
                raise TypeError("Los metodos deben ser iterables[str] ")
            self.metodos = set([x.upper() for x in metodos])
            if 'HEAD' not in self.metodos and 'GET' in self.metodos:
                self.metodos.add('HEAD')
        self.final = final

    def obtener_reglas(self, mapa):
        yield self

    def enlazar(self, mapa, reenlazar=False):
        if self.mapa is not None and not reenlazar:
            raise RuntimeError("La regla url %r ya esta vinculado al mapa %r" %(self, self.mapa))
        self.mapa = mapa
        # self.compilar()

    def compilar(self):
        self._convertidores = {}

tipo_texto = str

def _obtener_entorno(obj):
    ent = getattr(obj, 'entorno', obj)
    return ent


def decodificar_wsgi(val, charset='utf-8', errores='remplazar'):
    return val.decode(charset, errores)

def a_unicode(nombre, charset=sys.getdefaultencoding(), errores='estricto', alojar_charset_none=False):
    if nombre is None:
        return None
    if not isinstance(nombre, bytes):
        return tipo_texto(nombre)
    if charset is None and alojar_charset_none:
        return nombre
    return nombre.decode(charset, errores)

class Mapa(object):
    def __init__(self, reglas=None, charset='utf-8'):
        self._reglas = []
        self._reglas_por_final = {}
        self.charset = charset

        for regla_fab in reglas or ():
            self.agregar(regla_fab)



    def agregar(self, regla_fab):
        for regla in regla_fab.obtener_reglas(self):
            regla.enlazar(self)
            self._reglas.append(regla)
            #self._reglas_por_final.setdefault(regla.final, []).append(regla)

    def enlazar(self, nombre_servidor, nombre_script=None, subdominio=None,
                esquema_url='http', metodo_predet='GET', ruta_info=None, args_consulta=None):
        nombre_servidor = nombre_servidor.lower()
        if nombre_script is None:
            nombre_script = '/'
        try:
            nombre_servidor = ''
        except:
            raise UnicodeError("Unicode Error")
        return AdaptadorMapa(self, nombre_servidor, nombre_script, 
                             subdominio, esquema_url, ruta_info, 
                             metodo_predet, args_consulta) 

    def enlazar_a_entorno(self, entorno, nombre_servidor=None, subdominio=None):
        entorno = _obtener_entorno(entorno)
        if 'HTTP_HOST' in entorno:
            nombre_servidor_wsgi = entorno['HTTP_HOST']
            if entorno['wsgi.url_scheme'] == 'http' \
                and nombre_servidor_wsgi.endswith(':80'):
                nombre_servidor_wsgi = nombre_servidor_wsgi[:-3]
            elif entorno['wsgi.url_scheme'] == 'https' \
                and nombre_servidor_wsgi.endswith(':443'):
                nombre_servidor_wsgi = nombre_servidor_wsgi[:-4]
        else:
            nombre_servidor_wsgi = entorno['SERVER_NAME']
            if (entorno['wsgi.url_scheme'], entorno['SERVER_PORT']) not in \
                (('https', '443'), ('http', '80')):
                nombre_servidor_wsgi += ':' + entorno['SERVER_PORT']

        nombre_servidor_wsgi = nombre_servidor_wsgi.lower()

        if nombre_servidor is None:
            nombre_servidor = nombre_servidor_wsgi
        else:
            nombre_servidor = nombre_servidor.lower()

        if subdominio is None:
            _nombre_servidor_act = nombre_servidor_wsgi.split('.')
            _nombre_servidor_real = nombre_servidor.split('.')
            _offs = -len(_nombre_servidor_real)
            if _nombre_servidor_act[_offs:] != _nombre_servidor_real:
                subdominio = '<invalid>'
            else:
                subdominio = '.'join(filter(None, _nombre_servidor_act[:_offs]))

        def _obtener_cadena_swgi(nombre):
            val = entorno.get(nombre)
            if val is not None:
                return decodificar_wsgi(val, self.charset)

        nombre_script = _obtener_cadena_swgi('SCRIPT_NAME')
        ruta_info = _obtener_cadena_swgi('PATH_INFO')
        args_consulta = _obtener_cadena_swgi('QUERY_STRING')
        return Mapa.enlazar(self, nombre_servidor, nombre_script, subdominio,
                            entorno['wsgi.url_scheme'], entorno['REQUEST_METHOD'],
                            ruta_info, args_consulta=args_consulta
                            )


class AdaptadorMapa(object):
    def __init__(self, mapa, nombre_servidor, nombre_script, 
                 subdominio, esquema_url, ruta_info, metodo_predet, args_consulta=None):
        self.mapa = mapa
        self.nombre_servidor = a_unicode(nombre_servidor)
        nombre_script = a_unicode(nombre_script)
        if not nombre_script.endswith(u'/'):
            nombre_script += u'/'
        self.nombre_script = nombre_script
        self.subdominio = a_unicode(subdominio)
        self.esquema_url = a_unicode(esquema_url)
        self.ruta_info = a_unicode(ruta_info)
        self.metodo_predet = a_unicode(metodo_predet)
        self.args_consulta = args_consulta

    def enviar(self, vista_func, ruta_info=None, metodo=None, c_excepciones_http=False):
        try:
            try:
                final, args = self.encontrado(ruta_info, metodo)
            except Exception as e:
                if c_excepciones_http:
                    return e
                raise

    def encontrado(self, ruta_info=None, metodo=None, retorna_ruta=False, args_consulta=None):
        # self.mapa.actualizar() TODO: Agregar :metodo: `actualizar` en la clase Mapa()
        if ruta_info is None:
            ruta_info = self.ruta_info
        else:
            ruta_info = a_unicode(ruta_info, self.mapa.charset)
        if args_consulta is None:
            args_consulta = self.args_consulta
        metodo = (metodo or self.metodo_predet).upper()

        ruta = u'%s|%s' % (
            # TODO: Agregar :atributo `host_encontrado`: en la clase Mapa()
            self.mapa.host_encontrado and self.nombre_servidor or self.subdominio, ruta_info and '/%s' % ruta
            )


class DiccInmutable(dict):
    def __repr__(self):
        return '%s(%s)' % (
        self.__class__.__name__,
        dict.__repr__(self),
    )

    def copy(self):
        return dict(self)

    def __copy__(self):
        return self

class Config(dict):
    def __init__(self, ruta_raiz, defaults=None):
        dict.__init__(self, defaults or {})
        self.ruta_raiz = ruta_raiz


class Runner(object):
    agregar_ruta_cls = Ruta
    peticion_clase = Peticion
    respuesta_clase = Respuesta
    # nombre_imp = None
    ruta_raiz = None
    clase_config = Config

    config_predet = DiccInmutable({
        'APPLICATION_ROOT':             '/',
        'SERVER_NAME':                  None,
    })

    def __init__(self,
        nombre_imp=__name__,
        instancia_relativa_config=False,
        ruta_raiz=None,
        ruta_instancia=None):
        self.nombre_imp = nombre_imp
        self.regla = defaultdict()
        self.mapa_url = Mapa()
        self.funciones_vista = {}
        if ruta_instancia is None:
            ruta_instancia = self.auto_ruta_instancia()
        elif not os.path.isabs(ruta_instancia):
            raise ValueError('Si se proporciona una ruta de instancia, debe ser absoluta.'
                             'En su lugar, se proporcionó una ruta relativa.'
            )
        self.ruta_instancia = ruta_instancia
        self.antes_peticion_funcs = {}
        self.antes_primer_peticion_funcs = []
        self.despues_peticion_funcs = {}
        self.url_val_preprocesores = {}
        self.config = self.crear_config(instancia_relativa_config)

    @property
    def nombre(self):
        if self.nombre_imp == '__main__':
            fn = getattr(sys.modules['__main__'], '__file__', None)
            if fn is None:
                return '__main__'
            return os.path.splitext(os.path.basename(fn))[0]
        return self.nombre_imp

    def crear_config(self, instancia_relativa=False):
        ruta_raiz = self.ruta_raiz
        if instancia_relativa:
            ruta_raiz = self.ruta_instancia
        return self.clase_config(ruta_raiz, self.config_predet)

    def auto_ruta_instancia(self):
        print "Nombre imp", self.nombre_imp
        prefijo, ruta_paquete = ubicar_paquete(self.nombre_imp)
        if prefijo is None:
            return os.path.join(ruta_paquete, 'instancia')
        return os.path.join(prefijo, 'var', self.nombre + '-instancia')

    @property
    def get_reglas(self):
        return self.regla

    def respuesta(self, ruta, entorno):
        # TODO: wrap
        return self.regla[ruta](entorno)

    def obtener_entorno(self):
        pass

    def envio_peticion(self):
        peticion = ''

    def manejar_excepcion_usuario(self, ex):
        tipo_exc, tipo_valor, tb = sys.exc_info()
        print "Exception User: %s" % ex

    def manejar_excepcion(self, ex):
        tipo_exc, tipo_valor, tb = sys.exc_info()
        print "Exception : %s" % ex

    def hacer_respuesta(self, valor_retornado):
        status = encabezados = None
        if isinstance(valor_retornado, (tuple, list)):
            tam_valor_retornado = len(valor_retornado)
            if tam_valor_retornado == 3:
                valor_retornado, status, encabezados = valor_retornado
            elif tam_valor_retornado == 2:
                if isinstance(valor_retornado[1], (dict, tuple, list)):
                    valor_retornado, encabezados = valor_retornado
                else:
                    valor_retornado, status = valor_retornado
            else:
                raise TypeError("La vista funcion no retorna una tupla valida.")

    def envio_peticion_completo(self):
        try:
            valor_retornado = self.preprocesar_peticion()
            if valor_retornado is None:
                valor_retornado = self.envio_peticion()
        except Exception as ex:
            valor_retornado = self.manejar_excepcion_usuario(ex)
        return self.finaliza_peticion(valor_retornado)

    def finaliza_peticion(self, valor_retornado):
        respuesta = self.hacer_respuesta(valor_retornado)

    def crear_adaptador_url(self, peticion):
        if peticion is not None:
            # TODO: crear metodo enlazar_a_entorno(entorno, nombre_servidor='')
            return self.mapa_url.enlazar_a_entorno(
                    peticion.entorno,
                    nombre_servidor=self.config['SERVER_NAME'])
        if self.config['SERVER_NAME'] is not None:
            # TODO: crear metodo enlazar(server_name, nombre_script='', esquema_url='')
            return self.mapa_url.enlazar(
                    self.config['SERVER_NAME'],
                    nombre_script=self.config['APPLICATION_ROOT'],
                    esquema_url=self.config['PREFERRED_URL_SCHEME'])

    def preprocesar_peticion(self):
        bp = peticion_clase.blueprint
        funcs = self.url_val_preprocesores.get(None, ())
        if bp is not None and bp in self.url_val_preprocesores:
            funcs = chain(funcs, self.url_val_preprocesores[bp])
        for func in funcs:
            func(peticion_clase.final, peticion_clase.vista_args)
        funcs = self.antes_peticion_funcs.get(None, ())
        if bp is not None and bp in self.antes_peticion_funcs:
            funcs = chain(funcs, self.antes_peticion_funcs[bp])
        for func in funcs:
            valor_retornado = func()
            if valor_retornado is not None:
                return valor_retornado

    def contexto_peticion(self, entorno):
        return ContextoPeticion(self, entorno)

    def aplicacion_wsgi(self, entorno, respuesta):
        ctx_pet = self.contexto_peticion(entorno)
        error = None
        # try:
        try:
            res = self.envio_peticion_completo()
        except Exception as ex:
            error = ex
            res = self.manejar_excepcion(ex)
        except:
            error = sys.exc_info()[1]
            raise
        return res(entorno, respuesta)
        # finally:

        # encabezado = [('Content-Type', 'text/html')]
        # status = None
        # res = None
        # ruta = entorno.get('PATH_INFO') or '/'
        # if ruta in self.get_reglas:
        #     status = '200 OK'
        #     res = self.respuesta(ruta, entorno)
        # else:
        #     status = '404 NOT FOUND'
        #     res = "Pagina no encontrada"
        # respuesta(status, encabezado)
        # return res

    def __call__(self, entorno, respuesta):
        return self.aplicacion_wsgi(entorno, respuesta)

    def final_vista(self, funcion_param):
        return funcion_param.__name__

    def agregar_regla_url(self, regla, final=None, funcion_param=None, proveer_func_autom=None, **opciones):
        if final is None:
            final = self.final_vista(funcion_param)

        opciones['final'] = final

        metodos = opciones.pop('metodos', None)

        if metodos is None:
            metodos = getattr(funcion_param, 'metodos', None) or ('GET',)

        if isinstance(metodos, (str, unicode)):
            raise TypeError("Los metodos deben ser un Iterable[str] no un String.")

        metodos = set(m.upper() for m in metodos)

        metodos_requeridos = set(getattr(funcion_param, 'metodos_requeridos', ()))

        if proveer_func_autom is None:
            proveer_func_autom = getattr(funcion_param, 'proveer_func_autom', None)

        if proveer_func_autom is None:
            if 'OPTIONS' not in metodos:
                proveer_func_autom = True
                metodos_requeridos.add('OPTIONS')
            else:
                proveer_func_autom = False
        metodos |= metodos_requeridos

        # self.regla[regla] = funcion_param
        regla = self.agregar_ruta_cls(regla, metodos=metodos, **opciones)
        regla.proveer_func_autom = proveer_func_autom

        self.mapa_url.agregar(regla)
        print "Regla %s" % regla

        if funcion_param is not None:
            func_antigua = self.funciones_vista.get(final)
            if func_antigua is not None and func_antigua != funcion_param:
                raise AssertionError("La asignacion de la funcion de vista sobreescribe una funcion de punto fina existente: %s" % final)
            self.funciones_vista[final] = funcion_param
        print self.funciones_vista

    def ruta(self, regla, **opciones):
        def decorador(funcion):
            final = opciones.pop('final', None)
            self.agregar_regla_url(regla, final, funcion, **opciones)
            return funcion
        return decorador

    def correr(self, dominio='127.0.0.1', puerto=8000):
        httpd = make_server(dominio, puerto, self)
        print "* Corriendo en http://python.developer.io:8000 (Presiona Ctrl + C para salir.)"
        httpd.serve_forever()
