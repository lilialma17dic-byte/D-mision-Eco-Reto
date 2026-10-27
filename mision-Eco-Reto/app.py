from flask import Flask, render_template, request, redirect, url_for, session, g, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'eco-reto-azul-morado-verde'
DATABASE = 'ecoreto.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS acciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            fecha TEXT NOT NULL,
            impacto TEXT NOT NULL)''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = generate_password_hash(request.form["password"])
        db = get_db()
        try:
            db.execute("INSERT INTO usuarios (usuario, password) VALUES (?, ?)", (usuario, password))
            db.commit()
            return redirect(url_for("login"))
        except:
            flash("Usuario ya existe")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        db = get_db()
        user = db.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()
        if user and check_password_hash(user["password"], request.form["password"]):
            session["usuario_id"] = user["id"]
            session["usuario"] = user["usuario"]
            return redirect(url_for("home"))
        flash("Datos incorrectos")
    return render_template("login.html")

@app.route("/home")
def home():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    db = get_db()
    acciones = db.execute("SELECT * FROM acciones WHERE usuario_id = ? ORDER BY fecha DESC", (session["usuario_id"],)).fetchall()
    total = len(acciones)
    # Datos para las 4 tarjetas de arriba
    litros = sum([50 for a in acciones if 'agua' in a['tipo'].lower()]) or 0
    reciclados = len([a for a in acciones if 'reciclaje' in a['tipo'].lower()])
    co2 = total * 3
    return render_template("home.html", acciones=acciones, total=total, litros=litros, reciclados=reciclados, co2=co2)

@app.route("/nueva", methods=["GET", "POST"])
def nueva():
    if "usuario_id" not in session: return redirect(url_for("login"))
    if request.method == "POST":
        db = get_db()
        db.execute("INSERT INTO acciones (usuario_id, tipo, descripcion, fecha, impacto) VALUES (?,?,?,?,?)",
                   (session["usuario_id"], request.form["tipo"], request.form["descripcion"], request.form["fecha"], request.form["impacto"]))
        db.commit()
        return redirect(url_for("home"))
    return render_template("nueva.html")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "usuario_id" not in session: return redirect(url_for("login"))
    db = get_db()
    accion = db.execute("SELECT * FROM acciones WHERE id=? AND usuario_id=?", (id, session["usuario_id"])).fetchone()
    if request.method == "POST":
        db.execute("UPDATE acciones SET tipo=?, descripcion=?, fecha=?, impacto=? WHERE id=?",
                   (request.form["tipo"], request.form["descripcion"], request.form["fecha"], request.form["impacto"], id))
        db.commit()
        return redirect(url_for("home"))
    return render_template("editar.html", accion=accion)

@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "usuario_id" not in session: return redirect(url_for("login"))
    db = get_db()
    db.execute("DELETE FROM acciones WHERE id=? AND usuario_id=?", (id, session["usuario_id"]))
    db.commit()
    return redirect(url_for("home"))

@app.route("/detalle/<int:id>")
def detalle(id):
    if "usuario_id" not in session: return redirect(url_for("login"))
    db = get_db()
    accion = db.execute("SELECT * FROM acciones WHERE id=? AND usuario_id=?", (id, session["usuario_id"])).fetchone()
    return render_template("detalle.html", accion=accion)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
    