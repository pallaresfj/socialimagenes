from flask import Flask
from flask import render_template as render
from flask import request
from flask import flash
from flask import redirect, url_for
from flask import jsonify
from flask import session
from flask import g
from werkzeug.security import generate_password_hash, check_password_hash
from utils import isUsernameValid, isEmailValid, isPasswordValid
import yagmail as yagmail
import os
from db import get_db


app = Flask (__name__)
app.secret_key = os.urandom(24)


@app.route('/', methods=['GET'])
@app.route('/Inicio', methods=['GET'])
def inicio():
    db = get_db()
    
    allimagenes = db.execute(
            'SELECT Id, IdAutor, IdCategoria, TituloImagen, NombreArchivo, Tags FROM tbImagenes ORDER BY Id DESC' 
            ).fetchall()

    db.commit()

    return render('inicio.html',allimagenes=allimagenes)
