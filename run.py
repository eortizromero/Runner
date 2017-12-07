# -*- coding: utf-8 -*-

from index import Runner, pagina

app = Runner()

@app.ruta('/')
@app.ruta('/index')
def inicio(r):
    return "Hola"
    # return pagina('index.html')

# def usuario(r):
#     return "Pagina inicio"

if __name__ == '__main__':
    app.correr()
