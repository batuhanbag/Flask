from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.handlers.sha2_crypt import sha256_crypt
from functools import wraps



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Lütfen Giriş Yapınız..","danger")
            return redirect(url_for("login"))
    return decorated_function

# Kullanıcı Kayıt Formu

class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=4,max=25,message="Lütfen İsiminizi Kontrol Ediniz")])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35,message="Lütfen Kullanıcı Adınızı Kontrol Ediniz")])
    email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin.")])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message = "Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor")
    ])
    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")


class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])

app = Flask(__name__)
app.secret_key = "batublogpy"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "batublog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles/<string:id>")
def url(id):
    return "Artıcle Id:" +id

#Giriş Yap
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        query = "SELECT * FROM users WHERE username = %s"

        result = cursor.execute(query,(username,))

        if result > 0 :
            data = cursor.fetchone()
            real_pass = data["password"]
            if sha256_crypt.verify(password_entered,real_pass):
                flash("Başarıyla Giriş Yaptınız","success")

                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Hatalı","danger")
                return redirect(url_for("login"))
        else:
            flash("Kullanıcı Adınız Hatalı.","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form = form)

#Kayıt Olma
@app.route("/register/", methods =["GET","POST"])
def register():

    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        query = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(query,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()
        flash("Başarıyla Kayıt Oldunuz.","success")
        return redirect(url_for("login"))
    else:
        
        return render_template("register.html",form = form)

#Detay SAyfası
@app.route("/article/<string:id>")
def detail(id):
    cursor = mysql.connection.cursor()

    query = "SELECT * FROM articles where id = %s"

    result = cursor.execute(query,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")

#silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor = mysql.connection.cursor()

    query = "SELECT * FROM articles WHERE author = %s and id = %s" 


    result = cursor.execute(query,(session["username"],id))

    if result > 0 :
        query2 = "DELETE FROM articles where id = %s" 
        cursor.execute(query2,(id,))
        mysql.connection.commit() # bu sorgu verıtabanını degıstırdıgı ıcın commit işlemini yapıp kayıt etmemiz gerekli cok onemli!!!

        flash("Makale Başarıyla Silindi.","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")

        return redirect(url_for("index"))

#Makale Güncelleme İşlemi
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def uptade(id):

    

    if request.method == "GET":
        cursor = mysql.connection.cursor()

        query = "Select * From articles where id = %s and author = %s"

        result = cursor.execute(query,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok.","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()

            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("uptade.html",form = form)


    else:
        # POST Request

        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        

        query2 = "Update articles Set title = %s,content = %s where id = %s "

        cursor = mysql.connection.cursor()

        cursor.execute(query2,(newTitle,newContent,id))

        mysql.connection.commit()
        flash("Makale Güncellendi","success")

        
        return redirect(url_for("dashboard"))


    
#Logout İşlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    query = "SELECT * FROM articles where author = %s"

    result = cursor.execute(query,(session["username"],))

    if result > 0 :
        articles = cursor.fetchall()

        return render_template("dashboard.html",articles = articles)

    else:
        return render_template("dashboard.html")

   
   
   
   
    return render_template("dashboard.html")

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    query = "SELECT * FROM articles"

    result = cursor.execute(query)

    if result > 0 :
        articles = cursor.fetchall()

        return render_template("articles.html",articles = articles)

    else:
        return render_template("articles.html")
#makale ekleme
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():

    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data


        cursor = mysql.connection.cursor()
        query = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(query,(title,session["username"],content))
        mysql.connection.commit()

        cursor.close()

        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))


    return render_template("addarticle.html",form = form)

#Arama URL

@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword") # search lınedıtındekı gırılen degerı aldık 

        cursor = mysql.connection.cursor()

        query = "Select * from articles where title like '%" + keyword +"%'"

        result = cursor.execute(query)

        if result == 0:
            flash("Aranan Kelimeye Uygun Makale Bulunamadı","warning")
            return redirect(url_for("articals"))
        
        else:
            articles = cursor.fetchall()

            return render_template("articles.html",articles = articles)




if __name__ == "__main__":
    app.run(debug=True)
