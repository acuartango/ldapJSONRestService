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
import configuration

# creating the Flask application
app = Flask(__name__)
cors = CORS(app)

# There were encoding problems with python2, but not with python3.
#print("Server Encoding: " + get_config_parameter('DEFAULT_CLIENT_ENCODING'))
#print("System Encoding: " + sys.getdefaultencoding())

server = Server(configuration.server, get_info=ALL, use_ssl=True)

#########################################################
# Every @app.route is a enpoint of our REST service     #
#########################################################

@app.route("/copaCode", methods=["GET", "POST"])
def getCopaCode():
    # We send a copacode and the description is returned. 
    # This function is very close to our ldap configuration !
    receivedCode = request.args.get("code")

    print("LOG: Ldap Search starting time is ", time.asctime(time.localtime(time.time())))
    
    conn = Connection(
        server, 
        user=configuration.userUID, 
        password=configuration.password, 
        read_only=True,
        auto_bind=True)

    conn.search(
        search_base='ou=areas,' + configuration.base,
        search_filter='(copaAreaCode=' + receivedCode + ')',
        attributes=['copaName'],
        time_limit=configuration.ldapSearchesTimeout)
   
    result_list_json = conn.response_to_json()
    result_list_object = json.loads(result_list_json)
    entries = result_list_object["entries"][0].get("attributes") 

    print("LOG: Ldap Search ending time is ", time.asctime(time.localtime(time.time())))

    return str(entries).replace('\'','\"');

@app.route("/userInfo", methods=["GET", "POST"])
def getUserInfo():
    # With an user UID the service returns all contained data in a JSON object
    # Think that the data you get depends on global ldap user used to connect 
    # an it's permissions to read data of the ldap tree. Not all users can get
    # all attributes nor all users from an ldap
    #
    # We read here only users below "ou=people" tree !!
    # This service needs complete username, parts of it won't returns any data !!
    username = request.args.get("user")
    atributos=["*"]
    print("LOG: Ldap Search starting time is ", time.asctime(time.localtime(time.time())))
    start = datetime.datetime.now()

    conn = Connection(
        server, 
        user=configuration.userUID, 
        password=configuration.password, 
        read_only=True,
        auto_bind=True)

#    searchFilter="(|(|(|(|(uid=*" + filtro + "*)(cn=*" + filtro + "*))(telephoneNumber=*" + filtro + "*))(mobile=*" + filtro + "*))(irisMailMainAddress=*" + filtro + "*))"
    searchFilter="(uid=" + username + ")"
#    conn.search(search_base=ldapBase, search_filter="(uid=*" + filtro + "*)", attributes=["cn","uid","title"], time_limit=tiempoTimeoutLDAPBusquedas)
    conn.search(
        search_base='ou=people,' + configuration.base, 
        search_filter=searchFilter, 
        attributes=atributos, 
        time_limit=configuration.ldapSearchesTimeout)
    
    searchDurationSeconds = (datetime.datetime.now() - start).seconds

    result_list_json = conn.response_to_json()
    result_list_object = json.loads(result_list_json)
    entries = result_list_object["entries"]

    ldapResponsesJSON = list(map(lambda x : x.get("attributes"), entries))

    # There is a trick here. Some data in our gigant ldap has been coded to UTF8 twice, so we need to
    # normalize the output using ftfy library. If your ldap haven't codification problems you can eliminate 
    # "ftfy.fix_text", but if the codification is correct it won't do anything bad or incorrect...
    # We also capitalize the first character of names to show them better
    atributos=['cn','schacSn','givenName']
    for i, item in enumerate(ldapResponsesJSON):
        for key, value in item.items():
            if any(teststr in key for teststr in atributos):
                ldapResponsesJSON[i][key][0] = str(ftfy.fix_text(str(ldapResponsesJSON[i][key][0]))).title()
                print("Si está " + key + " en " + str(atributos))

    if (searchDurationSeconds >= configuration.ldapSearchesTimeout):
        print("The timeout has been reached, returned data can be partial : " + str(searchDurationSeconds) + ">=" + str(configuration.ldapSearchesTimeout))
 
    print("LOG: Ldap Search ending time is ", time.asctime(time.localtime(time.time())))
    
    return json.dumps(ldapResponsesJSON), 200


@app.route("/buscaPersonas", methods=["GET", "POST"])
def getPersonas():
    # With an user UID or a part of it, the service returns all ldap contained data in a JSON object
    # Think that the data you get depends on global ldap user used to connect 
    # an it's permissions to read data of the ldap tree. Not all users can get
    # all attributes nor all users from an ldap
    #
    # We read here only users below "ou=people" tree !!

    filtro = request.args.get("filtro")
    atributos=["cn","uid","title"]
    print("LOG: Ldap Search starting time is ", time.asctime(time.localtime(time.time())))
    start = datetime.datetime.now()

    conn = Connection(
        server, 
        user=configuration.userUID, 
        password=configuration.password, 
        read_only=True,
        auto_bind=True)

#    searchFilter="(|(|(|(|(uid=*" + filtro + "*)(cn=*" + filtro + "*))(telephoneNumber=*" + filtro + "*))(mobile=*" + filtro + "*))(irisMailMainAddress=*" + filtro + "*))"
    searchFilter="(|(|(|(uid=*" + filtro + "*)(cn=*" + filtro + "*))(telephoneNumber=*" + filtro + "*))(irisMailMainAddress=*" + filtro + "*))"
#    conn.search(search_base=ldapBase, search_filter="(uid=*" + filtro + "*)", attributes=["cn","uid","title"], time_limit=tiempoTimeoutLDAPBusquedas)
    conn.search(search_base='ou=people,' + configuration.base, search_filter=searchFilter, attributes=atributos, time_limit=configuration.ldapSearchesTimeout)
    
    print ("Filtro: " + searchFilter)
    searchDurationSeconds = (datetime.datetime.now() - start).seconds

    result_list_json = conn.response_to_json()
    result_list_object = json.loads(result_list_json)
    entries = result_list_object["entries"]

    ldapResponsesJSON = list(map(lambda x : x.get("attributes"), entries))

    # There is a trick here. Some data in our gigant ldap has been coded to UTF8 twice, so we need to
    # normalize the output using ftfy library. If your ldap haven't codification problems you can eliminate 
    # "ftfy.fix_text", but if the codification is correct it won't do anything bad or incorrect...
    # We also capitalize the first character of names to show them better
    for i, item in enumerate(ldapResponsesJSON):
        for key, value in item.items():
            if ('cn' in key):
                ldapResponsesJSON[i][key][0] = str(ftfy.fix_text(str(ldapResponsesJSON[i][key][0]))).title()


    if (searchDurationSeconds >= configuration.ldapSearchesTimeout):
        print("The timeout has been reached, returned data can be partial : " + str(searchDurationSeconds) + ">=" + str(configuration.ldapSearchesTimeout))
    
    print("LOG: Ldap Search ending time is ", time.asctime(time.localtime(time.time())))

    return json.dumps(ldapResponsesJSON), 200



@app.route("/userModifyPass", methods=["GET", "POST"])
def getModifyPass():
    # Input: user uid + password + newPassword
    # Output: True if password has been correctly changed or False if not.
    # The bind (connection with ldap) is maded with the users uid + password to confirms identity
    # Test call (comprobar los passwords antes de la prueba):
    # http://0.0.0.0:5000/userModifyPass?user=username&oldpass=XXXXXXXXXX&newpass=YYYYYYYY
    # Note users must be under "ou=people" ldap tree
    receivedUid = request.args.get("user")
    oldPass = request.args.get("oldpass")
    newPass = request.args.get("newpass")

    try:
        conn = Connection(
            server, 
            user='uid='+receivedUid+',ou=people,' + configuration.base,
            password=oldPass, 
            read_only=True,
            auto_bind=True)

        newPassChangedOk = conn.extend.standard.modify_password(
            'uid='+receivedUid+',ou=people,' + configuration.base, oldPass, newPass)
    except:
        newPassChangedOk = False

    return str(newPassChangedOk), 201


@app.route("/resizeImg", methods=["GET", "POST"])
def get_resizeImg():
    # Input: base64 JPEG image
    # Output: new base64 JPG Image resized. Still Work In Progress!
    img_b64 = bytes(request.args.get("img"), encoding="utf-8")

    f = Image.open(BytesIO(base64.b64decode(img_b64)))
    rotada = f.rotate(33, expand=1)

    #    imgfile.seek(0)
    print("Converted new base64 image: ")
    buffered = BytesIO()
    if rotada.mode in ("RGBA", "P"):
        rotada = rotada.convert("RGB")
    rotada.save(buffered, format="JPEG")
    print("-----------------")
    print(base64.b64encode(buffered.getvalue()))
    print("-----------------")

    return str(base64.b64encode(buffered.getvalue()),'utf-8'), 200
