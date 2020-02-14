from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

import simplejson as json
import base64, io, getpass, sys, time, datetime, ftfy
from ldap3 import Server, Connection, HASHED_SALTED_SHA, MODIFY_REPLACE, ALL
from ldap3.utils.hashed import hashed
from ldap3 import get_config_parameter,set_config_parameter
from io import BytesIO
from PIL import Image
from pprint import pprint

# creating the Flask application
app = Flask(__name__)
cors = CORS(app)

# You can use admin password or other
password = '**adminPASSWORD**'
ldapBase = 'dc=mydomain,dc=com'
serverName = 'myldapserver.mydomain.com:636'
server = Server(serverName, get_info=ALL, use_ssl=True)

tiempoTimeoutLDAPBusquedas=5


@app.route("/copaCode", methods=["GET", "POST"])
def getCopaCode():
    # dado un copacode, devuleve su descripción buscando en el ldap en la rama "areas"
    receivedCode = request.args.get("code")

    print("LOG: HORA INICIO CONSULTA", time.asctime(time.localtime(time.time())))
    #conn.search(search_base="dc=ehu,dc=es",search_filter="(uid=" + receivedUid + ")",attributes=["uid","eduPersonAffiliation","schacPersonalUniqueID","irisMailMainAddress","givenName","SchacSn1","SchacSn2"])
    conn = Connection(server, user="uid=admin,"+ldapBase, password=password, read_only=True, auto_bind=True)
    conn.search(search_base="ou=areas,"+ldapBase, search_filter="(copaAreaCode=" + receivedCode + ")", attributes=["copaName"],time_limit=tiempoTimeoutLDAPBusquedas)

    ldapResponsesJSON = ""
    result_list_json = conn.response_to_json()
    result_list_object = json.loads(result_list_json)
    entries = result_list_object["entries"][0].get("attributes") 

    print("LOG: HORA FIN CONSULTA", time.asctime(time.localtime(time.time())))

    return str(entries).replace('\'','\"');


@app.route("/userInfo", methods=["GET", "POST"])
def getUserInfo():
    filtro = request.args.get("user")
    atributos=["*"]
    print("LOG: HORA INICIO CONSULTA", time.asctime(time.localtime(time.time())))
    start = datetime.datetime.now()

    conn = Connection(server, user="uid=admin,"+ldapBase, password=password, read_only=True, auto_bind=True)

#    searchFilter="(|(|(|(|(uid=*" + filtro + "*)(cn=*" + filtro + "*))(telephoneNumber=*" + filtro + "*))(mobile=*" + filtro + "*))(irisMailMainAddress=*" + filtro + "*))"
    searchFilter="(uid=" + filtro + ")"
#    conn.search(search_base=ldapBase, search_filter="(uid=*" + filtro + "*)", attributes=["cn","uid","title"], time_limit=tiempoTimeoutLDAPBusquedas)
    conn.search(
        search_base='ou=people,' + ldapBase, 
        search_filter=searchFilter, 
        attributes=atributos, 
        time_limit=tiempoTimeoutLDAPBusquedas)
    
    print ("Filtro: " + searchFilter)
    searchDurationSeconds = (datetime.datetime.now() - start).seconds

    result_list_json = conn.response_to_json()
    result_list_object = json.loads(result_list_json)
    entries = result_list_object["entries"]

    ldapResponsesJSON = list(map(lambda x : x.get("attributes"), entries))

    # Corregimos los strings codificados en UTF8 dentro de strings UTF8. Hay pocos en el ldap, pero los hay.
    # Aprovechamos para capitalizar las primeras letras de los nombres con apellidos.
    atributos=['cn','schacSn','givenName']
    for i, item in enumerate(ldapResponsesJSON):
        for key, value in item.items():
            if any(teststr in key for teststr in atributos):
                ldapResponsesJSON[i][key][0] = str(ftfy.fix_text(str(ldapResponsesJSON[i][key][0]))).title()
                print("Si está " + key + " en " + str(atributos))

    if (searchDurationSeconds >= tiempoTimeoutLDAPBusquedas):
        print("Se ha alcanzado el timeout, los resultados pueden ser parciales : " + str(searchDurationSeconds) + ">=" + str(tiempoTimeoutLDAPBusquedas))
    
    print("LOG: HORA FIN CONSULTA", time.asctime(time.localtime(time.time())))
    
#    return (str(ldapResponsesJSON).replace('\'','\"')), 200
    return json.dumps(ldapResponsesJSON), 200



@app.route("/buscaPersonas", methods=["GET", "POST"])
def getPersonas():
    filtro = request.args.get("filtro")
    atributos=["cn","uid","title"]
    print("LOG: HORA INICIO CONSULTA", time.asctime(time.localtime(time.time())))
    start = datetime.datetime.now()

    conn = Connection(server, user="uid=admin,"+ldapBase, password=password, read_only=True, auto_bind=True)

#    searchFilter="(|(|(|(|(uid=*" + filtro + "*)(cn=*" + filtro + "*))(telephoneNumber=*" + filtro + "*))(mobile=*" + filtro + "*))(irisMailMainAddress=*" + filtro + "*))"
    searchFilter="(|(|(|(uid=*" + filtro + "*)(cn=*" + filtro + "*))(telephoneNumber=*" + filtro + "*))(irisMailMainAddress=*" + filtro + "*))"
#    conn.search(search_base=ldapBase, search_filter="(uid=*" + filtro + "*)", attributes=["cn","uid","title"], time_limit=tiempoTimeoutLDAPBusquedas)
    conn.search(search_base='ou=people,' + ldapBase, search_filter=searchFilter, attributes=atributos, time_limit=tiempoTimeoutLDAPBusquedas)
    
    print ("Filtro: " + searchFilter)
    searchDurationSeconds = (datetime.datetime.now() - start).seconds

    result_list_json = conn.response_to_json()
    result_list_object = json.loads(result_list_json)
    entries = result_list_object["entries"]

    ldapResponsesJSON = list(map(lambda x : x.get("attributes"), entries))

    # Corregimos los strings codificados en UTF8 dentro de strings UTF8. Hay pocos en el ldap, pero los hay.
    # Aprovechamos para capitalizar las primeras letras de los nombres con apellidos.
    for i, item in enumerate(ldapResponsesJSON):
        for key, value in item.items():
            if ('cn' in key):
                ldapResponsesJSON[i][key][0] = str(ftfy.fix_text(str(ldapResponsesJSON[i][key][0]))).title()


    if (searchDurationSeconds >= tiempoTimeoutLDAPBusquedas):
        print("Se ha alcanzado el timeout, los resultados pueden ser parciales : " + str(searchDurationSeconds) + ">=" + str(tiempoTimeoutLDAPBusquedas))
    
    print("LOG: HORA FIN CONSULTA", time.asctime(time.localtime(time.time())))
    
#    return (str(ldapResponsesJSON).replace('\'','\"')), 200
    return json.dumps(ldapResponsesJSON), 200



@app.route("/userModifyPass", methods=["GET", "POST"])
def getModifyPass():
    # Entrada: uid usuario + password + nuevoPassword
    # Salida: True si ha cambiado el password y False si no.
    # El bind se hace con el propio UID del usuario.
    # Llamada de prueba (comprobar los passwords antes de la prueba):
    # http://0.0.0.0:5000/userModifyPass?user=sczcubea&oldpass=XXXXXXXXXX&newpass=YYYYYYYY
    receivedUid = request.args.get("user")
    oldPass = request.args.get("oldpass")
    newPass = request.args.get("newpass")
    try:
        conn = Connection(server, user='uid='+receivedUid+',ou=people,' +
                          ldapBase, password=oldPass, read_only=True, auto_bind=True)
        newPassChangedOk = conn.extend.standard.modify_password(
            'uid='+receivedUid+',ou=people,'+ldapBase, oldPass, newPass)
    except:
        newPassChangedOk = False

    return str(newPassChangedOk), 201


@app.route("/resizeImg", methods=["GET", "POST"])
def get_resizeImg():
    # Entrada: imagen convertida a base64
    # Salida: Imagen convertida en este caso rotada, pero la idea era hacer un resize  parametros de entrada.
    # La idea es que cuando se meta una foto en el ldap, sea siempre del mismo tamaño aprox.
    img_b64 = bytes(request.args.get("img"), encoding="utf-8")

    f = Image.open(BytesIO(base64.b64decode(img_b64)))
    rotada = f.rotate(33, expand=1)

    #    imgfile.seek(0)
    print("Imagen convertida en base64 de nuevo: ")
    buffered = BytesIO()
    if rotada.mode in ("RGBA", "P"):
        rotada = rotada.convert("RGB")
    rotada.save(buffered, format="JPEG")
    print("-----------------")
    print(base64.b64encode(buffered.getvalue()))
    print("-----------------")

    return "", 200
