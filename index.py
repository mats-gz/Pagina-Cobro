from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import os
import mercadopago
import datetime


app = Flask(__name__)
load_dotenv()

CORS(app)


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))


db = SQLAlchemy(app)
login_manager = LoginManager(app)
bcrypt = Bcrypt(app)


#Utiliza el login manager para gestionar el ciclo de vida de inicio de sesión de un usuario, desde q inicia hasta q logout
login_manager = LoginManager()
login_manager.init_app(app)

# Configura el login manager para manejar sesiones de usuario
login_manager.login_view = 'login'  # Redirige a la vista de login si se intenta acceder a una ruta protegida


#Utilizado para cargar el id del usuario desde la base de datos, para cuando maneje x la red
@login_manager.user_loader
def user_loader(id_usuario):
    return Usuario.query.get(int(id_usuario))


#Declaración de la tabla Usuario
class Usuario(db.Model, UserMixin):
    __tablename__ = 'Usuario'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_usuario = db.Column(db.String(100), nullable=False, unique=True)
    nombre_apellido = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    codigo_postal = db.Column(db.Integer)
    contraseña_usuario = db.Column(db.String(60), nullable=False)
    telefono = db.Column(db.Integer)


#Utilizado para guardar el id como un string y mantenerse para las diferentes solicitudes mientras el usuario anvega x la pagina iniciado sesion
    def get_id(self):
        return str(self.id_usuario)


#Declaración de la tabla Producto
class Producto(db.Model):
    __tablename__ = 'Producto'
    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.Text)
    cantidad_producto = db.Column(db.Integer, nullable=False)
    nombre_producto = db.Column(db.String(255), nullable=False)
    id_carrito = db.Column(db.Integer, db.ForeignKey('Carrito.id_carrito'))
    imagen_producto = db.Column(db.String(1500))


#Declaración de tabla carrito
class Carrito(db.Model):
    __tablename__ = "Carrito"
    id_carrito = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, nullable=False)
    status_carrito = db.Column(db.String(50))
    metodo_pago = db.Column(db.String(50))
    fecha_pago = db.Column(db.Date)


#Declaración de tabla carrito producto
class Carrito_Productos(db.Model):
    __tablename__ = "Carrito_Productos"
    id_carrito_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_carrito = db.Column(db.Integer, nullable=False)
    id_producto = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Integer)


#Clase para el form del registro de usuario
class FormRegistro(FlaskForm):
    nombre_apellido = StringField(validators=[InputRequired(), Length(min=10, max=30)], render_kw={"placeholder":"nombre_apellido"})
    usuario = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "usuario"})
    contraseña = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "contraseña"})
    email = EmailField(validators=[InputRequired(), Email(message="Gmail Inválido"), Length(max=50)], render_kw={"placeholder": "gmail"})  
    submit = SubmitField('Registrarse')

    def validar_usuario(self, usuario):
        usuario_existente = Usuario.query.filter_by(user_usuario=usuario.data).first()
        if usuario_existente:
            raise ValidationError("Ese usuario ya existe, porfavor, escriba otro.")


#Clase para el form del login de usuario
class FormLogin(FlaskForm):
    usuario = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "usuario"})
    contraseña = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "contraseña"})
    submit = SubmitField('Iniciar Sesión')



#Render inicial, el search query es utilizado para la barra de busqueda, donde estan los request args va lo que se declaro en la planilla con "name", el ilike es para la busqueda de items con SQLAlchemy, despreciando las mayúsculas y otros.
@app.route('/', methods = ["GET"])
def home():
    search_query = request.args.get("search")
    if search_query:
        items = Producto.query.filter(Producto.nombre_producto.ilike(f"%{search_query}%")).all()
    else:
        items = Producto.query.all()
    return render_template('home.html', items=items)


@app.route('/carrito', methods=["GET"])
@login_required
def carrito():
    #Obtener el id del usuario y del carrito
    usuario_id = current_user.id_usuario
    carrito = Carrito.query.filter_by(id_usuario=usuario_id, status_carrito='no pagado').first()

    #Si no hay carrito, se retorna directamente el template con 0 productos y un valor total nulo al no haber ningun precio q calcular
    if not carrito:
        return render_template('carrito.html', productos=[], total=0)
    
    #Obtener todos los productos filtrandolos por el id del carrito actual, creando una lista vacia donde se va a guardar toda la info a renderizar en la página, junto con el total q vendria a ser el precio.
    producto_carrito = Carrito_Productos.query.filter_by(id_carrito = carrito.id_carrito).all()
    productos = []
    total = 0

    for items in producto_carrito:
        producto = Producto.query.get(items.id_producto)
        productos.append({
            "id_producto": producto.id_producto,
            "nombre": producto.nombre_producto,
            "precio": producto.precio,
            "cantidad": items.cantidad,
            "subtotal": producto.precio * items.cantidad
        })
        total += producto.precio * items.cantidad
    
    return render_template('carrito.html', productos=productos, total=total)


@app.route('/login', methods = ["GET", "POST"])
def login():
    form = FormLogin()

    #Asegurar el inicio de sesion, que el usuario y/o contraseña sean validos y existan en la BD
    if form.validate_on_submit():
        user = Usuario.query.filter_by(user_usuario=form.usuario.data).first()
        if user and bcrypt.check_password_hash(user.contraseña_usuario,form.contraseña.data):
            login_user(user)
            return redirect(url_for('home'))  # Asegúrate de tener definida una ruta 'dashboard'
        else:
            flash("Nombre de usuario o contraseña inválidos", "danger")

    return render_template('login.html', form=form)


@app.route('/register', methods = ["GET", "POST"])
def register():
    form = FormRegistro()

    if form.validate_on_submit():
        # Encriptar la contraseña ingresada
        hashed_contraseña = bcrypt.generate_password_hash(form.contraseña.data)

        # Crear un nuevo usuario con los datos del formulario
        nuevo_usuario = Usuario(
            user_usuario=form.usuario.data,
            contraseña_usuario=hashed_contraseña,
            nombre_apellido=form.nombre_apellido.data,
            email=form.email.data
        )

        # Agregar el nuevo usuario a la base de datos, al menos que ocurra el error de integridad, es decir, de duplicar un usuario ya existente
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
        except IntegrityError: # error de integridad (usuario ya existe)
            db.session.rollback()  # Deshacer cambios si ocurre un error
            flash('El nombre de usuario ya está en uso. Por favor elige otro.')
            return redirect(url_for('register'))


        # Redirigir al usuario a la página de login
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    logout_user()  # Cierra la sesión del usuario actual
    return redirect(url_for('login'))  # Redirige a la página de login


@app.route("/añadir_carrito", methods=["POST"])
@login_required
def añadir_carrito():
    id_producto = request.form.get("id_producto")
    id_usuario = current_user.id_usuario
    cantidad = int(request.form.get("cantidad"))

    #ver si el carrito existe actualmente
    carrito = Carrito.query.filter_by(id_usuario=id_usuario, status_carrito = "No pagado").first()
    if not carrito:
        carrito = Carrito(id_usuario=id_usuario, status_carrito = "No pagado", metodo_pago=None, fecha_pago=None)
        db.session.add(carrito)
        db.session.commit()

    #verificar si el producto se encuentra en el carrito, añadir la cantidad exacta que se declaro si es asi, y si añadirlo al carrito
    carrito_producto = Carrito_Productos.query.filter_by(id_carrito=carrito.id_carrito, id_producto=id_producto).first()
    if carrito_producto:
        carrito_producto.cantidad += cantidad
    else:
        carrito_producto = Carrito_Productos(id_carrito=carrito.id_carrito, id_producto=id_producto,cantidad=cantidad)
        db.session.add(carrito_producto)

    db.session.commit()
    return redirect(url_for('home'))

@app.route("/borrar_carrito", methods=["POST"])
@login_required
def borrar_carrito():
    id_prod = request.form.get("id_producto")
    # Intenta encontrar el producto en el carrito
    carrito_prod_eliminado = Carrito_Productos.query.filter_by(id_producto=id_prod).first()
        
    if carrito_prod_eliminado:  # Verifica que el producto exista
        db.session.delete(carrito_prod_eliminado)
        db.session.commit()
        flash("Producto eliminado del carrito con éxito.", "success")
    else:
        flash("El producto no se encontró en el carrito.", "warning")

    return redirect(url_for('carrito'))


# Crear ruta checkout, donde se crea una preferencia que es por donde se maneja la info del usuario y los productos para realizar el pago.
@app.route('/checkout', methods=["POST"])
@login_required
def checkout():
    # Obtener el id y el carrito no pagado del usuario que se encuentra en sesión.
    usuario_id = current_user.id_usuario
    carrito = Carrito.query.filter_by(id_usuario=usuario_id, status_carrito="no pagado").first()

    if not carrito:
        flash("No hay productos en el carrito.")
        return redirect(url_for('carrito'))

    # Lista de productos en el carrito
    productos_carrito = Carrito_Productos.query.filter_by(id_carrito=carrito.id_carrito).all()
    items = []

    # Añadir a la lista items los puntos necesarios del producto (que se obtiene por su id en productos_carrito, sacando nombre y precio)
    for producto_carrito in productos_carrito:
        producto = Producto.query.get(producto_carrito.id_producto)
        items.append({
            "title": producto.nombre_producto,
            "quantity": producto_carrito.cantidad,
            "unit_price": float(producto.precio),
            "currency_id": "ARS"
        })

    # Crear la preferencia de pago con los items del carrito, y las urls de los 3 posibles casos a la hora de realizar el pago
    preferencia = {
        "items": items,
        "back_urls": {
            "success": url_for('pago_exitoso', _external=True),
            "failure": url_for('pago_fallido', _external=True),
            "pending": url_for('pago_pendiente', _external=True)
        },
        "auto_return": "approved"
    }

    # Crear la preferencia utilizando la SDK de MercadoPago
    resultado = sdk.preference().create(preferencia)

    # Obtener la URL del checkout de MercadoPago (Checkout Pro)
    url_checkout = resultado["response"]["init_point"]

    # Redirigir al usuario a la página de MercadoPago para realizar el pago
    return redirect(url_checkout)


@app.route("/pago_exitoso", methods=["POST", "GET"])
def pago_exitoso():
    id_usuario = current_user.id_usuario
    carrito = Carrito.query.filter_by(id_usuario=id_usuario, status_carrito="no pagado").first()
    
    #if carrito true, cambiar el estado a pagado
    if carrito:
        carrito.status_carrito = "pagado"
        carrito.fecha_pago = datetime.datetime.now()
        db.session.commit()

    return redirect(url_for('home'))


@app.route("/pago_fallido")
def pago_fallido():
    flash("El pago ha fallado. Inténtelo nuevamente.", "danger")
    return redirect(url_for('carrito'))


@app.route("/pago_pendiente")
def pago_pendiente():
    flash("El pago está pendiente. Te avisaremos cuando se complete.", "info")
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)