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


@app.route('/DelImagen/<int:id>')
def delMensajeRec(id):
    db = get_db()

    sql1 = 'SELECT NombreArchivo FROM tbImagenes WHERE Id = ' + str(id)
    sql2 = 'DELETE FROM tbComentarios WHERE IdImagen = ' + str(id)
    sql3 = 'DELETE FROM tbImagenes WHERE Id = ' + str(id)

    filename = db.execute(sql1).fetchone()

    os.remove(os.path.join(app.config['CARPETA'],filename))

    db.execute(sql2)
    db.execute(sql3)

    db.commit()

    flash('Se eliminó la imágen y los comentarios asociados.')
    return redirect( url_for( 'mis_imagenes' ) )