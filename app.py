from flask import Flask
from flask import render_template as render
from flask import request
from flask import flash
from flask import redirect, url_for
from flask import jsonify
from flask import session
from flask import g
from flask import send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
# from werkzeug.utils import secure_filename
# from werkzeug.datastructures import  FileStorage
from utils import isUsernameValid, isEmailValid, isPasswordValid
import yagmail as yagmail
import os
import uuid
from db import get_db
from random import randint


app = Flask (__name__)
app.secret_key = os.urandom(24)

CARPETA = os.path.join('uploads')
app.config['CARPETA'] = CARPETA

@app.route('/uploads/<nombreimagen>')
def uploads(nombreimagen):
    return send_from_directory(app.config['CARPETA'], nombreimagen)

lista_usuarios = []

@app.route('/', methods=['GET'])
@app.route('/Inicio', methods=['GET'])
def inicio():
    db = get_db()
    allimagenes = db.execute(
            'SELECT NombreArchivo FROM tbImagenes ORDER BY RANDOM() LIMIT 3').fetchall()
    db.commit()
    return render('inicio.html',allimagenes=allimagenes)
    
@app.route('/Registro', methods=['GET','POST'])
def registro():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        nombre = request.form['nombre']             
        tipousuario = '3'
        error = None
        db = get_db()
        user_email = db.execute(
            'SELECT * FROM tbUsuarios WHERE correo = ? ', (email,) 
            ).fetchone()

        if user_email is not None:
            error = "Correo electrónico ya existe."
            flash(error)
        if not email:
            error = "Correo requerido."
            flash(error)
        if not password:
            error = "Contraseña requerida."
            flash(error)
        if not nombre:
            error = "Nombre requerido."
            flash(error)
        if error is not None:
            return render("registro.html")
        else:
            # Seguro:
            password_cifrado = generate_password_hash(password)
            db.execute(
                'INSERT INTO tbUsuarios (Correo, Contrasena, Nombre, TipoUs) VALUES (?,?,?,?)',
                (email, password_cifrado, nombre, tipousuario)
            )
            db.commit()
            return redirect( url_for( 'login' ) )    
    # GET:
    session.clear()
    return render('registro.html')

@app.route('/Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        usuario = request.form['correo']
        password = request.form['password'] 
        error = None

        if not usuario:
            error = "Usuario requerido."
            flash(error)
        if not password:
            error = "Contraseña requerida."
            flash(error)
        if error is not None:
            return render("login.html")
        else:         
            user = db.execute(
                'SELECT Id, Correo, Contrasena, Nombre, TipoUs, DescripcionUsuario FROM tbUsuarios WHERE Correo = ?', (usuario,) 
                ).fetchone()                 
            if user is None:
                flash('Usuario y/o contraseña no son correctos.')
                return render("login.html")
            else:
                password_correcto = check_password_hash(user[2],password)
                if not password_correcto:
                    flash('Usuario y/o contraseña no son correctos.')
                    return render("login.html")
                else:
                    session.clear()
                    session['id_usuario'] = user[0]
                    session['correo_usuario'] = user[1]
                    session['nombre_usuario'] = user[3]
                    session['tipo_usuario'] = user[4]
                    session['descripcion_usuario'] = user[5]
                    return redirect( 'Inicio' )                
    # GET:
    session.clear()
    return render('login.html')

@app.route('/Salir', methods=['GET', 'POST'])
def salir():
    session.clear()
    return redirect('Inicio')

@app.route('/Soporte', methods=['GET','POST'])
def soporte():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        asunto = request.form['asunto']
        mensaje = request.form['mensaje']        
        error = None

        if not nombre:
            error = "Nombre requerido."
            flash(error)
        if not email:
            error = "Correo requerido."
            flash(error)
        if not asunto:
            error = "Asunto requerido."
            flash(error)
        if not mensaje:
            error = "Contraseña requerida."
            flash(error)
        if error is not None:
            return render("soporte.html")
        else:
            # Procedimiento para enviar correo con los datos del formulario
            cadena = "Nombre: " + nombre + "\n" + "Correo: " + email + "\n" + "Mensaje: " + mensaje
            #pehernaldo2@gmail.com  Hernaldo12345678*
            #redsocialimagenes@gmail.com  RedSocial12345678*
            yag = yagmail.SMTP('pehernaldo2@gmail.com', 'Hernaldo12345678*') 
            yag.send(to='redsocialimagenes@gmail.com', subject=asunto,
                contents=cadena)
            flash('Tu solicitud de soporte fue enviada.') 

            return redirect( url_for( 'soporte' ) )    
    # GET:
    return render('soporte.html')

@app.route('/ListarMensajes', methods=['GET'])
def listar_mensajes():
    if not session:
        return redirect( url_for( 'login' ) )
    else:
        db = get_db()
        recibidos = db.execute(
                'SELECT tbMensajes.Id, tbMensajes.IdDe, tbMensajes.IdPara, tbUsuarios.Nombre, tbMensajes.Mensaje FROM tbMensajes INNER JOIN tbUsuarios ON tbUsuarios.Id = tbMensajes.IdDe WHERE tbMensajes.IdPara = ?', (session['id_usuario'],) 
                ).fetchall()
        enviados = db.execute(
                'SELECT tbMensajes.Id, tbMensajes.IdDe, tbMensajes.IdPara, tbUsuarios.Nombre, tbMensajes.Mensaje FROM tbMensajes INNER JOIN tbUsuarios ON tbUsuarios.Id = tbMensajes.IdPara WHERE tbMensajes.IdDe = ?', (session['id_usuario'],) 
                ).fetchall()
        db.commit()
        return render('mensajes.html',recibidos=recibidos, enviados=enviados)

@app.route('/EnviaMensaje', methods=['GET', 'POST'])
def enviar_mensaje():
    if request.method == 'POST':
        email = request.form['email']
        mensaje = request.form['mensaje']           
        error = None
        db = get_db()

        if not email:
            error = "Correo requerido."
            flash(error)
        if not mensaje:
            error = "Mensaje vacío."
            flash(error)

        user = db.execute(
            'SELECT * FROM tbUsuarios WHERE correo = ? ', (email,) 
            ).fetchone()

        if user is None:
            error = "El usuario destino no existe."
            flash(error)
        if error is not None:
            return render("enviarmensaje.html")
        else:
            db.execute(
                'INSERT INTO tbMensajes (IdDe, IdPara, Mensaje) VALUES (?,?,?)',
                (session['id_usuario'], user[0], mensaje)
            )   
            db.commit()
            return redirect( url_for( 'enviar_mensaje' ) )    
    # GET:
    if not session:
        return redirect( url_for( 'login' ) )
    return render('enviarmensaje.html')

@app.route('/DelMensajeRec/<int:id>')
def delMensajeRec(id):
    db = get_db()
    sql = 'DELETE FROM tbMensajes WHERE Id = ' + str(id)
    db.execute(sql)
    db.commit()
    flash('Mensaje eliminado.')
    return redirect( url_for( 'listar_mensajes' ) )

@app.route('/PerfilUsuario', methods=['GET','POST'])
def perfil_usuario():
    if not session:
        return redirect( url_for( 'login' ) )
    if request.method == 'POST':
        Id = request.form['txtId']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        password_act = request.form['password_act']
        password_new = request.form['password_new']
        password_conf = request.form['password_conf']
        if not password_act:
            sql="UPDATE tbUsuarios SET Nombre = ?, DescripcionUsuario = ? WHERE Id = ?;"
            datos=(nombre, descripcion,Id)
            db = get_db()
            db.execute(sql,datos)
            db.commit()
            flash('Datos actualizados correctamente.')
        else:
            db = get_db()
            password_a = db.execute(
            'SELECT Id, Contrasena FROM tbUsuarios WHERE Id = ?', (Id,) 
            ).fetchone()
            password_correcto = check_password_hash(password_a[1],password_act)
            if not password_correcto:
                flash('La contraseña suministrada no es correcta.')
                return redirect( url_for( 'perfil_usuario' ))
            else:
                if not password_new or not password_conf:
                    flash('La nueva contraseña no puede ser vacía.')
                    return redirect( url_for( 'perfil_usuario' ))
                else:
                    if password_new == password_conf:
                        contrasena = generate_password_hash(password_new)
                        sql="UPDATE tbUsuarios SET Contrasena = ?, Nombre = ?, DescripcionUsuario = ? WHERE Id = ?;"
                        datos=(contrasena, nombre, descripcion,Id)
                        db = get_db()
                        db.execute(sql,datos)
                        db.commit()
                        flash('Datos actualizados correctamente.')
                    else:
                        flash('Las contraseñas no coinciden.')
                        return redirect( url_for( 'perfil_usuario' ))

        return redirect( url_for( 'perfil_usuario' ))

    # GET:
    db = get_db()
    sql = 'SELECT Id, Correo, Contrasena, Nombre, TipoUs, DescripcionUsuario FROM tbUsuarios WHERE Id = ' + str(session['id_usuario'])
    usuarios = db.execute(sql).fetchall()
    print(usuarios)
    db.commit()
    return render('perfil.html', usuarios=usuarios)

@app.route('/MisComentarios', methods=['GET'])
def mis_comentarios():
    if not session:
        return redirect( url_for( 'login' ) )
    else:
        db = get_db()
        miscomentarios = db.execute(
                'SELECT tbComentarios.Id, tbComentarios.IdImagen, tbComentarios.IdUsuario, tbComentarios.Comentario, tbImagenes.TituloImagen, tbImagenes.IdAutor, tbUsuarios.Nombre, tbImagenes.NombreArchivo FROM tbComentarios INNER JOIN tbImagenes ON tbImagenes.Id = tbComentarios.IdImagen INNER JOIN tbUsuarios ON tbUsuarios.Id = tbImagenes.IdAutor WHERE tbComentarios.IdUsuario = ?', (session['id_usuario'],) 
                ).fetchall()
        db.commit()
        return render('miscomentarios.html',miscomentarios=miscomentarios)

@app.route('/DelComentario/<int:id>')
def del_comentario(id):
    db = get_db()
    sql = 'DELETE FROM tbComentarios WHERE Id = ' + str(id)
    db.execute(sql)
    db.commit()
    flash('Comenario eliminado.')
    return redirect( url_for( 'mis_comentarios' ) )

@app.route('/MisImagenes', methods=['GET'])
def mis_imagenes():
    if not session:
        return redirect( url_for( 'login' ) )

    db = get_db()
    
    misimagenes = db.execute(
            'SELECT tbImagenes.Id, tbImagenes.IdAutor, tbImagenes.IdCategoria, tbImagenes.TituloImagen, tbImagenes.NombreArchivo, tbImagenes.Tags, tbUsuarios.Nombre, tbImagenes.IdCategoria FROM tbImagenes INNER JOIN tbUsuarios ON tbUsuarios.Id = tbImagenes.IdAutor INNER JOIN tbCategorias ON tbCategorias.Id = tbImagenes.IdCategoria WHERE tbImagenes.IdAutor = ?', (session['id_usuario'],) 
            ).fetchall()
    db.commit()
    return render('misimagenes.html',misimagenes=misimagenes)

@app.route('/Upload', methods=['GET','POST'])
def upload_imagen():
    if not session:
        return redirect( url_for( 'login' ) )
    if request.method == 'POST':
        titulo = request.form['titulo']
        categoria = request.form['categoria']
        etiquetas = request.form['etiquetas']
        archivo = request.files['archivo']

        error = None

        if not titulo:
            error = "Título de la imagen requerido."
            flash(error)
        if not archivo:
            error = "No se seleccionó archivo de imágen."
            flash(error)
        if error is not None:
            return redirect( url_for( 'mis_imagenes' ) )
        f = str(uuid.uuid4()) + archivo.filename
        print('ARCHIVO: ',f)
        archivo.save(os.path.join(app.config['CARPETA'],f))

        db=get_db()
        sql = 'INSERT INTO tbImagenes (Id, IdAutor, IdCategoria, TituloImagen, NombreArchivo, Tags) VALUES (NULL,?,?,?,?,?);'
        datos = (session['id_usuario'],categoria,titulo,f,etiquetas)
        db.execute(sql,datos)
        db.commit()
        return redirect( url_for( 'mis_imagenes' ) )

        

    # GET
    return render('addimagen.html')

@app.route('/ListarPublicaciones', methods=['GET'])
def listar_publicaciones():
    return render('pubporusuario.html')

@app.route('/ListarUsuarios', methods=['GET'])
def listar_usuarios():
    return render('usuarios.html')

@app.route('/AEditarComent')
def aeditarcoment():
    return render('aeditarcoment.html')

@app.route('/GestionUsuarios/<id_usuario>', methods=['GET', 'POST'])
def usuario_info(id_usuario):
    if id_usuario in lista_usuarios:
        return render('gestionusuarios.html')
    else:
        return f"El usuario {id_usuario} no existe."


if __name__ == '__main__' :
    app.run(debug=True)
