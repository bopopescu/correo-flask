from flask import Flask, render_template, redirect, request, url_for, redirect, logging, session, flash, json,jsonify
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import mysql.connector

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'f4ab65a793836b7ae8cc6646bd0c6ccd'

app.config.update(
DEBUG=False,
#esta cfg es para un servidor propio. Pero, si quieres usar gmail, debes revisar la config de gmail
#hay un monton de ejemplos en youtube.. 
MAIL_SERVER = 'ip_servidor_correo',
MAIL_PORT=465,
MAIL_USE_SSL=True,
MAIL_USERNAME = 'email o usuario',
MAIL_PASSWORD = 'clave'
)

mail = Mail(app)

s=URLSafeTimedSerializer('SECRETKEY')


@app.route("/revisar_correo", methods=['POST','GET'])
@cross_origin()
def rev_message():
    mydb = mysql.connector.connect(host="DIRECCIONBD", user= "USUARIOBD", passwd= "PWBD",
                                   database= "BD")
    if request.method == 'POST':
        correos = json.loads(request.data)
        correo = correos.get('email')
        cursor = mydb.cursor()
        print(correo)
        args = [correo]
        """Yo hice esto con un store procedure. Pero puedes hacerlo con un query normal. 
        mi base de datos es mysql y por ello debes instalar el cliente y con pip, importar el 
        mysql.connector. 
        """
        cursor.callproc('SP_revisar_email', args)
        for result in cursor.stored_results():
            datos = result.fetchall()
            print(datos)
            if len(datos)==0:
                invalid = {'code':'400', 'message':'Correo Invalido'}
                return jsonify(invalid)
            else:
                for data in datos:
                    nombres=data[0]
                    apellidos=data[1]
                    telefono=data[2]
                    ma=data[3]
                    idusuario=data[4]
                    clavea=data[5]
                    user=data[6]
                    facebook=data[7]
                    if facebook == 1:
                        face = {'code':'400', 'message':'Debes recuperar tu clave desde Facebook'}
                        return jsonify(face)
                    else:
                        objeto=[idusuario,ma,user,nombres,apellidos, clavea.decode('utf-8')]
                        token = s.dumps(objeto, salt='email-reset')
                        #Esta variable link, te sirve para hacer pruebas porque enviara un link por correo
                        # que tendra lo necesario para que hagas un formulario y recuperes la pw. El external
                        #es una forma de hacer que lo que envies, se pueda redirigir hacia donde quieras. 
                        #link = url_for('reset_password', token=token, _external=True)
                        link = token 
                        insertarClaves(idusuario, token , clavea.decode("utf-8") , user)
                        msg = Message(
                        subject='Hola ' + nombres + " " + apellidos,
                        sender='Poner el correo del que envia',
                        recipients=[ma],
                        html=render_template("mensaje-correo.html", 
                        nombres=nombres, apellidos=apellidos, telefono=telefono, link=link))
                        mail.send(msg)
                        confirm_msg = {'code':'200', 'message':'Correo Enviado!'}
    return jsonify(confirm_msg)


@app.route("/reset_password/<token>", methods=['POST'])
@cross_origin()
def reset_password(token):
    
    if request.method == 'POST':
        claves = json.loads(request.data)
        clave1=claves.get('pass0')
        clave2=claves.get('pass1')
        token=claves.get('token')
    try:
        if clave1 != clave2:
            negativo1 = {'code':'400', 'message':'Ambas contraseñas deben ser identicas'}
            return jsonify(negativo1)
        else:
            # el max age, significa el tiempo que va a durar el token. En este caso son 30 minutos. 
            # El salt, es una buena practica. Yo tengo mas correos y puedes identificar u ordenar tokens con salt. 
            datos=s.loads(token, salt='email-reset', max_age=1800)
            print(datos)
            idusuario=datos[0]
            mail=datos[1]
            usuario=datos[2]
            name=datos[3]
            apellidos=datos[4]
            clavea=datos[5]
            if clavea == clave1:
                error3 = {'code':'400', 'message':'No puedes utilizar una clave antigua'}
                return jsonify(error3)
            else:
                #actualizarClaveMail(idusuario, mail, usuario, clave1)
                #actualizarClaveUsuarioJugador(idusuario, usuario, clave1)
                positivo= {'code':'200', 'message': 'Se ha actualizado su clave'}
                return jsonify(positivo)
                #esto comprueba la antiguedad del token. 
                # Si esta dentro de los 30 minutos, es valido de lo contrario dara un error. 
    except SignatureExpired:
        negativa = {'code':'400', 'message':'Token Expirado'}
        return jsonify(negativa)


if __name__ == "__main__":
    app.run(host='localhost',port=7777, debug=True)
    # app.run(host='localhost', port=7878, debug=True)
