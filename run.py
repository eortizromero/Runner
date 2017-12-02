# -*- coding: utf-8 -*-

from index import Runner, pagina

app = Runner()

@app.ruta('/')
def inicio():
    return pagina('index')

@app.ruta('/index')
def usuario():
    pass

if __name__ == '__main__':
    app.correr()
