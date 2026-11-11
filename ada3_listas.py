"""
ADA3 - Listas (Unidad 3 - Estructuras Lineales)  |  Lógica en Python + interfaz HTML

Estructura POSTRES: un ARREGLO ordenado alfabéticamente con los nombres de los postres;
cada elemento del arreglo apunta a una LISTA ENLAZADA con los ingredientes del postre.

Problema 1: a) imprimir ingredientes  b) insertar ingredientes  c) eliminar un ingrediente
            d) alta de postre  e) baja de postre   (verificando todos los casos)
Problema 2: eliminar automáticamente los elementos repetidos de POSTRES.
Nota: el Problema 1 admite postres e ingredientes repetidos a propósito; el Problema 2 trabaja
sobre esa MISMA estructura, así que todo lo que se agregue en el 1 se refleja y se limpia en el 2.

Uso:  python ada3_listas.py   (abre el navegador; Ctrl + C para cerrar)
      opciones: --puerto 9000  --no-navegador
"""

import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def limpiar(texto):
    """Quita espacios sobrantes."""
    return " ".join(str(texto or "").split())


def clave(texto):
    """Para comparar sin importar mayúsculas/minúsculas ni espacios."""
    return limpiar(texto).casefold()


def dividir(texto):
    """Separa 'a, b, c' en ingredientes. Se conservan los repetidos (el Problema 2 los elimina)."""
    return [limpiar(p) for p in str(texto or "").split(",") if limpiar(p)]


# ===========================================================================
# LISTA ENLAZADA (ingredientes)
# ===========================================================================
class Nodo:
    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None            # None = NIL


class ListaEnlazada:
    def __init__(self):
        self.cabeza = None

    def esta_vacia(self):
        return self.cabeza is None

    def buscar(self, dato):
        actual = self.cabeza
        while actual is not None and clave(actual.dato) != clave(dato):
            actual = actual.siguiente
        return actual

    def insertar_final(self, dato):
        nuevo = Nodo(dato)
        if self.cabeza is None:          # caso: lista vacía
            self.cabeza = nuevo
            return
        actual = self.cabeza
        while actual.siguiente is not None:
            actual = actual.siguiente
        actual.siguiente = nuevo

    def eliminar(self, dato):
        """Devuelve True si lo eliminó. Casos: primero, intermedio, último, no existe."""
        anterior, actual = None, self.cabeza
        while actual is not None and clave(actual.dato) != clave(dato):
            anterior, actual = actual, actual.siguiente
        if actual is None:
            return False
        if anterior is None:             # era el primero
            self.cabeza = actual.siguiente
        else:                            # intermedio o último
            anterior.siguiente = actual.siguiente
        return True

    def quitar_repetidos(self):
        """Deja solo la primera aparición de cada dato. Devuelve los que quitó."""
        quitados, actual = [], self.cabeza
        while actual is not None:
            ant, sig = actual, actual.siguiente
            while sig is not None:
                if clave(sig.dato) == clave(actual.dato):
                    ant.siguiente = sig.siguiente        # se salta el repetido
                    quitados.append(sig.dato)
                else:
                    ant = sig
                sig = sig.siguiente
            actual = actual.siguiente
        return quitados

    def elementos(self):
        datos, actual = [], self.cabeza
        while actual is not None:
            datos.append(actual.dato)
            actual = actual.siguiente
        return datos


# ===========================================================================
# ARREGLO POSTRES (ordenado alfabéticamente, capacidad fija)
# ===========================================================================
CAPACIDAD = 10


class Postres:
    def __init__(self):
        self.reiniciar()

    def _construir(self, datos):
        self.arreglo = []                # elementos: [nombre, ListaEnlazada]
        for nombre, ingredientes in datos:
            lista = ListaEnlazada()
            for ing in ingredientes:
                lista.insertar_final(ing)
            self.arreglo.append([nombre, lista])

    def reiniciar(self):
        self._construir([("Flan", ["Huevo", "Leche", "Azúcar", "Vainilla"]),
                         ("Gelatina", ["Grenetina", "Agua", "Azúcar"]),
                         ("Pastel de chocolate", ["Harina", "Cacao", "Huevo", "Azúcar", "Mantequilla"])])

    def buscar(self, nombre):
        """Búsqueda binaria de la PRIMERA aparición: (posición, encontrado)."""
        k, ini, fin = clave(nombre), 0, len(self.arreglo) - 1
        while ini <= fin:
            medio = (ini + fin) // 2
            km = clave(self.arreglo[medio][0])
            if km == k:
                while medio > 0 and clave(self.arreglo[medio - 1][0]) == k:
                    medio -= 1                    # puede haber repetidos: se toma el primero
                return medio, True
            if km < k:
                ini = medio + 1
            else:
                fin = medio - 1
        return ini, False

    def posicion_insercion(self, nombre):
        """Posición justo después de los que ya se llaman igual (mantiene el orden alfabético)."""
        k, pos = clave(nombre), 0
        while pos < len(self.arreglo) and clave(self.arreglo[pos][0]) <= k:
            pos += 1
        return pos

    def _existente(self, nombre):
        if not limpiar(nombre):
            raise ValueError("Escribe el nombre del postre.")
        if not self.arreglo:
            raise ValueError("El arreglo está vacío: no hay postres registrados.")
        pos, hallado = self.buscar(nombre)
        if not hallado:
            raise ValueError(f"El postre «{limpiar(nombre)}» no existe.")
        return pos, self.arreglo[pos]

    # a) imprimir ingredientes
    def imprimir(self, nombre):
        _, (nom, lista) = self._existente(nombre)
        if lista.esta_vacia():
            return f"«{nom}» no tiene ingredientes (su lista está vacía: apunta a NIL)."
        return f"Ingredientes de «{nom}»: " + ", ".join(lista.elementos()) + "."

    # b) insertar ingredientes
    def insertar(self, nombre, texto):
        _, (nom, lista) = self._existente(nombre)
        nuevos = dividir(texto)
        if not nuevos:
            raise ValueError("Escribe al menos un ingrediente (separados por comas).")
        for ing in nuevos:                           # se insertan tal cual, aunque ya existan
            lista.insertar_final(ing)
        return f"Se agregaron a «{nom}»: {', '.join(nuevos)}."

    # c) eliminar un ingrediente
    def eliminar_ingrediente(self, nombre, ingrediente):
        _, (nom, lista) = self._existente(nombre)
        ing = limpiar(ingrediente)
        if not ing:
            raise ValueError("Escribe el ingrediente que quieres eliminar.")
        if lista.esta_vacia():
            raise ValueError(f"La lista de «{nom}» está vacía: no hay nada que eliminar.")
        if not lista.eliminar(ing):
            raise ValueError(f"«{nom}» no tiene el ingrediente «{ing}».")
        msg = f"Se eliminó «{ing}» de «{nom}»."
        return msg + (" La lista quedó vacía (NIL)." if lista.esta_vacia() else "")

    # d) alta de un postre con todos sus ingredientes
    def alta(self, nombre, texto):
        nom = limpiar(nombre)
        if not nom:
            raise ValueError("Escribe el nombre del postre.")
        if len(self.arreglo) >= CAPACIDAD:
            raise ValueError(f"El arreglo está lleno ({CAPACIDAD} postres): da de baja alguno primero.")
        ingredientes = dividir(texto)
        if not ingredientes:
            raise ValueError("Un postre necesita al menos un ingrediente (separados por comas).")
        lista = ListaEnlazada()
        for ing in ingredientes:
            lista.insertar_final(ing)
        repetido = self.buscar(nom)[1]
        pos = self.posicion_insercion(nom)
        self.arreglo.insert(pos, [nom, lista])       # se inserta respetando el orden alfabético
        msg = f"Alta de «{nom}» en la posición {pos + 1} con {len(ingredientes)} ingrediente(s)."
        return msg + (" Ya existía un postre con ese nombre: quedó repetido." if repetido else "")

    # e) baja de un postre con todos sus ingredientes
    def baja(self, nombre):
        pos, (nom, lista) = self._existente(nombre)
        del self.arreglo[pos]                         # la lista se va con el elemento
        return f"Baja de «{nom}» junto con sus {len(lista.elementos())} ingrediente(s)."

    # Problema 2: eliminar repetidos
    def eliminar_repetidos(self):
        reporte, i = [], 0
        while i < len(self.arreglo):
            j = i + 1
            while j < len(self.arreglo):
                if clave(self.arreglo[j][0]) == clave(self.arreglo[i][0]):
                    primero, repetido = self.arreglo[i][1], self.arreglo[j][1]
                    nuevos = [x for x in repetido.elementos() if primero.buscar(x) is None]
                    for x in nuevos:                  # se rescatan los ingredientes que no tenía
                        primero.insertar_final(x)
                    extra = (f"; sus ingredientes nuevos pasaron al primero: {', '.join(nuevos)}"
                             if nuevos else "; todos sus ingredientes ya estaban en el primero")
                    reporte.append(f"Postre repetido «{self.arreglo[j][0]}» (posición {j + 1}) eliminado{extra}.")
                    del self.arreglo[j]               # no se avanza j: el siguiente ocupó su lugar
                else:
                    j += 1
            i += 1
        for nombre, lista in self.arreglo:
            quitados = lista.quitar_repetidos()
            if quitados:
                reporte.append(f"En «{nombre}» se quitaron ingredientes repetidos: {', '.join(quitados)}.")
        return reporte or ["No había elementos repetidos."]

    def estado(self):
        """Datos para la interfaz; marca los elementos que están repetidos."""
        postres, vistos, dup_p, dup_i = [], set(), 0, 0
        for nombre, lista in self.arreglo:
            ings, marcas, vistos_i = lista.elementos(), [], set()
            for x in ings:
                marcas.append(clave(x) in vistos_i)
                vistos_i.add(clave(x))
            repetido = clave(nombre) in vistos
            vistos.add(clave(nombre))
            dup_p += repetido
            dup_i += sum(marcas)
            postres.append({"nombre": nombre, "ingredientes": ings, "repetido": repetido, "marcas": marcas})
        return {"capacidad": CAPACIDAD, "postres": postres,
                "dup_postres": dup_p, "dup_ingredientes": dup_i}


POSTRES = Postres()
CERROJO = threading.Lock()


def ejecutar(d):
    a, p, ing = d.get("accion"), d.get("postre"), d.get("ingredientes")
    if a == "imprimir":
        return {"mensaje": POSTRES.imprimir(p)}
    if a == "insertar":
        return {"mensaje": POSTRES.insertar(p, ing)}
    if a == "eliminar":
        return {"mensaje": POSTRES.eliminar_ingrediente(p, ing)}
    if a == "alta":
        return {"mensaje": POSTRES.alta(p, ing)}
    if a == "baja":
        return {"mensaje": POSTRES.baja(p)}
    if a == "repetidos":
        return {"mensaje": "Eliminación de repetidos terminada.", "reporte": POSTRES.eliminar_repetidos()}
    if a == "reiniciar":
        POSTRES.reiniciar()
        return {"mensaje": "Datos restablecidos."}
    raise ValueError("Acción desconocida.")


# ===========================================================================
# SERVIDOR LOCAL
# ===========================================================================
class Manejador(BaseHTTPRequestHandler):
    def log_message(self, formato, *args):
        pass

    def _responder(self, cuerpo, tipo="application/json; charset=utf-8", codigo=200):
        if isinstance(cuerpo, dict):
            cuerpo = json.dumps(cuerpo, ensure_ascii=False)
        datos = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._responder(HTML, "text/html; charset=utf-8")
        elif self.path == "/api/estado":
            with CERROJO:
                self._responder({"ok": True, "estado": POSTRES.estado()})
        else:
            self.send_response(204 if self.path == "/favicon.ico" else 404)
            self.end_headers()

    def do_POST(self):
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            datos = json.loads(self.rfile.read(largo).decode("utf-8")) if largo else {}
            with CERROJO:
                try:
                    respuesta = {"ok": True, **ejecutar(datos)}
                except ValueError as error:            # mensajes de error de los casos especiales
                    respuesta = {"ok": False, "mensaje": str(error)}
                respuesta["estado"] = POSTRES.estado()
            self._responder(respuesta)
        except (TypeError, json.JSONDecodeError) as error:
            self._responder({"ok": False, "mensaje": str(error)}, codigo=400)


# ===========================================================================
# INTERFAZ HTML (solo muestra; la lógica vive en Python)
# ===========================================================================
HTML = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ADA3 · Listas</title>
<style>
:root{--bg:#f3f5fb;--card:#fff;--tx:#1b2033;--mut:#6b7390;--bd:#e4e8f4;--ac:#4f46e5;--ac2:#7c3aed;--chip:#eef0ff;--ok:#16a34a;--err:#dc2626;--sombra:0 10px 40px rgba(31,41,90,.10)}
@media (prefers-color-scheme:dark){:root{--bg:#0f1220;--card:#181c30;--tx:#eef0fb;--mut:#98a0c0;--bd:#262b47;--chip:#23284a;--sombra:0 10px 40px rgba(0,0,0,.45)}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:flex;justify-content:center;padding:28px 16px;font-family:system-ui,"Segoe UI",Roboto,sans-serif;color:var(--tx);
background:radial-gradient(900px 500px at 0% -10%,rgba(99,102,241,.18),transparent 60%),radial-gradient(800px 500px at 100% 0%,rgba(168,85,247,.14),transparent 60%),var(--bg)}
.app{width:min(900px,100%)}
header{text-align:center;margin-bottom:18px;animation:bajar .7s both}
h1{margin:0;font-size:2.2rem;background:linear-gradient(135deg,var(--ac),var(--ac2));-webkit-background-clip:text;background-clip:text;color:transparent}
header p{margin:6px 0 0;color:var(--mut)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:20px;box-shadow:var(--sombra);padding:22px}
.tabs{position:relative;display:grid;grid-template-columns:1fr 1fr;padding:4px;margin:16px 0;background:var(--card);border:1px solid var(--bd);border-radius:16px;box-shadow:var(--sombra)}
.ind{position:absolute;top:4px;bottom:4px;left:4px;width:calc((100% - 8px)/2);border-radius:12px;background:linear-gradient(135deg,var(--ac),var(--ac2));transform:translateX(calc(var(--i,0)*100%));transition:transform .5s cubic-bezier(.65,0,.25,1)}
.tab{position:relative;z-index:1;border:0;background:none;padding:12px 8px;font:inherit;font-weight:600;color:var(--mut);cursor:pointer;transition:color .35s}
.tab.on{color:#fff}
.paneles{display:grid}
.panel{grid-area:1/1;opacity:0;visibility:hidden;pointer-events:none;transform:translateX(60px);transition:opacity .45s,transform .55s cubic-bezier(.2,.8,.2,1),visibility 0s .55s}
.panel[data-e=antes]{transform:translateX(-60px)}
.panel[data-e=activo]{opacity:1;visibility:visible;pointer-events:auto;transform:none;transition:opacity .5s .12s,transform .6s cubic-bezier(.2,.8,.2,1) .12s,visibility 0s}
h2{margin:0 0 4px;font-size:1.25rem}.sub{margin:0 0 14px;color:var(--mut);font-size:.93rem;line-height:1.45}
.fila{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}
input{width:100%;padding:12px 14px;margin-top:8px;font:inherit;color:var(--tx);background:var(--bg);border:2px solid var(--bd);border-radius:12px;outline:none;transition:border-color .25s}
input:focus{border-color:var(--ac)}
.btn{border:0;border-radius:12px;padding:10px 14px;font:inherit;font-weight:600;cursor:pointer;background:var(--chip);color:var(--tx);transition:transform .15s,box-shadow .2s}
.btn:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(79,70,229,.2)}.btn:active{transform:scale(.97)}
.btn.p{background:linear-gradient(135deg,var(--ac),var(--ac2));color:#fff}.btn.r{color:var(--err)}
.msg{margin-top:14px;padding:12px 14px;border-radius:12px;background:var(--chip);color:var(--mut);animation:pop .35s both}
.msg.ok{background:rgba(22,163,74,.12);color:var(--ok)}.msg.err{background:rgba(220,38,38,.1);color:var(--err);animation:tiembla .45s both}
.rep{margin:12px 0 0;padding-left:20px;line-height:1.6}.rep li{animation:entra .4s both;animation-delay:calc(var(--k)*90ms)}
.concl{margin-top:14px;padding:14px;border-radius:12px;background:var(--chip);font-size:.92rem;line-height:1.55;color:var(--mut)}.concl b{color:var(--tx)}
.cap{float:right;color:var(--mut);font-size:.85rem;font-weight:500}
.fila-a{display:flex;align-items:center;gap:6px;margin:8px 0;overflow-x:auto;padding-bottom:4px;animation:entra .45s both;animation-delay:calc(var(--k)*70ms)}
.celda{flex:none;min-width:190px;padding:10px 12px;border-radius:10px;border:2px solid var(--ac);font-weight:700}
.celda small{color:var(--mut);font-weight:500;margin-right:6px}
.flecha{flex:none;color:var(--ac);font-weight:700}
.nodo{flex:none;padding:8px 12px;border-radius:10px;background:var(--chip);border:1px solid var(--bd);font-weight:600}
.nil{flex:none;color:var(--mut);font-weight:700;font-size:.85rem}
.vacio{color:var(--mut);font-style:italic}
.dup{border-color:var(--err)!important;background:rgba(220,38,38,.1);color:var(--err)}
.vt{margin:18px 0 6px;font-size:1.05rem}
footer{margin-top:16px;text-align:center;color:var(--mut);font-size:.82rem}
@keyframes bajar{from{opacity:0;transform:translateY(-14px)}to{opacity:1;transform:none}}
@keyframes entra{from{opacity:0;transform:translateX(-14px)}to{opacity:1;transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:none}}
@keyframes tiembla{0%{transform:translateX(0)}20%{transform:translateX(-8px)}40%{transform:translateX(8px)}60%{transform:translateX(-5px)}80%{transform:translateX(5px)}100%{transform:none}}
@media (prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style></head>
<body><main class="app">
<header><h1>Listas</h1><p>ADA3 · Arreglo POSTRES con listas enlazadas de ingredientes</p></header>


<nav class="tabs" id="tabs"><span class="ind"></span>
<button class="tab on" data-i="0">Problema 1 · Operaciones</button><button class="tab" data-i="1">Problema 2 · Repetidos</button></nav>

<section class="paneles">
<article class="panel card" data-e="activo">
 <h2>Operaciones sobre postres e ingredientes</h2>
 <p class="sub">Escribe el postre y, según la operación, uno o varios ingredientes separados por comas. Aquí se permiten postres e ingredientes repetidos: el Problema 2 los elimina.</p>
 <input id="postre" placeholder="Nombre del postre (ej. Flan)" autocomplete="off">
 <input id="ing" placeholder="Ingrediente(s) (ej. Canela, Limón)" autocomplete="off">
 <div class="fila">
  <button class="btn p" data-a="imprimir">a) Imprimir ingredientes</button>
  <button class="btn p" data-a="insertar">b) Insertar ingredientes</button>
  <button class="btn p" data-a="eliminar">c) Eliminar ingrediente</button>
  <button class="btn p" data-a="alta">d) Alta de postre</button>
  <button class="btn r" data-a="baja">e) Baja de postre</button>
 </div>
 <div class="msg" id="msg1">Elige una operación.</div>
 <h2 class="vt">Estructura POSTRES <span class="cap"></span></h2><div class="vista"></div>
</article>

<article class="panel card" data-e="despues">
 <h2>Eliminar elementos repetidos</h2>
 <p class="sub">Trabaja sobre la misma estructura del Problema 1: lo que agregues allá aparece aquí. Los repetidos se marcan en rojo.</p>
 <p class="sub" id="dup2"></p>
 <div class="fila">
  <button class="btn p" data-a="repetidos">Eliminar repetidos</button>
  <button class="btn" data-a="reiniciar">Restablecer datos</button>
 </div>
 <div class="msg" id="msg2">Agrega repetidos en el Problema 1 y pulsa «Eliminar repetidos».</div>
 <h2 class="vt">Estructura POSTRES <span class="cap"></span></h2><div class="vista"></div>
 <ol class="rep" id="rep"></ol>
 <div class="concl"><b>¿Qué sucedió con las listas? ¿Hubo error?</b><br>
 • Al quitar un postre repetido del arreglo, su lista enlazada desaparece con él. Por eso, antes de borrarlo, sus ingredientes que faltaban se pasaron a la lista del primero y no se perdió información.<br>
 • No hubo error porque el recorrido usa índices controlados: si se borra dentro de un <code>for</code>, los elementos se saltan o aparece <code>IndexError</code>; aquí no se avanza el índice tras borrar.<br>
 • Los ingredientes repetidos dentro de una lista se quitan re-enlazando los nodos (<code>anterior.siguiente = sig.siguiente</code>). Si se consulta un postre que ya no existe, el programa manda el mensaje de error «El postre no existe».</div>
</article>
</section>
<footer>La lógica (arreglo, listas enlazadas y validaciones) corre en Python; esta página solo la muestra.</footer>
</main>
<script>
const $=(s,r=document)=>r.querySelector(s);
const crea=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!==undefined)e.textContent=x;return e};
let panelActivo=0;
function irA(i){panelActivo=i;$('#tabs').style.setProperty('--i',i);
 document.querySelectorAll('.tab').forEach((t,k)=>t.classList.toggle('on',k===i));
 document.querySelectorAll('.panel').forEach((p,k)=>p.dataset.e=k===i?'activo':(k<i?'antes':'despues'))}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>irA(+t.dataset.i));

function pintar(e){
 document.querySelectorAll('.cap').forEach(c=>c.textContent=`${e.postres.length} / ${e.capacidad} posiciones`);
 $('#dup2').textContent=(e.dup_postres||e.dup_ingredientes)
  ?`Repetidos detectados: ${e.dup_postres} postre(s) y ${e.dup_ingredientes} ingrediente(s).`
  :'No hay elementos repetidos en la estructura.';
 document.querySelectorAll('.vista').forEach(v=>{
  v.replaceChildren();
  if(!e.postres.length)v.append(crea('p','vacio','Arreglo vacío: no hay postres registrados.'));
  e.postres.forEach((p,i)=>{
   const f=crea('div','fila-a');f.style.setProperty('--k',i);
   const c=crea('div','celda'+(p.repetido?' dup':''));
   c.append(crea('small',null,`[${i}]`),document.createTextNode(p.nombre+(p.repetido?' (repetido)':'')));f.append(c);
   p.ingredientes.forEach((x,j)=>{f.append(crea('span','flecha','→'),crea('span','nodo'+(p.marcas[j]?' dup':''),x))});
   f.append(crea('span','flecha','→'),crea('span','nil','NIL'));v.append(f)})})}
async function enviar(a){
 const r=await(await fetch('/api/accion',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({accion:a,postre:$('#postre').value,ingredientes:$('#ing').value})})).json();
 pintar(r.estado);
 const m=$(panelActivo===0?'#msg1':'#msg2');m.className='msg '+(r.ok?'ok':'err');m.textContent=r.mensaje;
 m.style.animation='none';void m.offsetWidth;m.style.animation='';
 const rep=$('#rep');rep.replaceChildren();
 (r.reporte||[]).forEach((t,k)=>{const li=crea('li',null,t);li.style.setProperty('--k',k);rep.append(li)})}
document.querySelectorAll('[data-a]').forEach(b=>b.onclick=()=>enviar(b.dataset.a));
fetch('/api/estado').then(r=>r.json()).then(r=>pintar(r.estado));
</script></body></html>
"""


def main():
    parser = argparse.ArgumentParser(description="ADA3 - Listas")
    parser.add_argument("--puerto", type=int, default=8766)
    parser.add_argument("--no-navegador", action="store_true")
    args = parser.parse_args()
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Manejador)
    except OSError:
        servidor = ThreadingHTTPServer(("127.0.0.1", 0), Manejador)
    url = f"http://127.0.0.1:{servidor.server_address[1]}/"
    print(f"ADA3 - Listas corriendo en {url}\nPresiona Ctrl + C para cerrar.")
    if not args.no_navegador:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando...")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
