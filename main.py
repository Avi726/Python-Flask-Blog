import math
import os
from werkzeug.utils import secure_filename
from flask import Flask, redirect, render_template, request, session
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime as dt
from flask_mail import Mail

with open('config.json','r') as c:
    params=json.load(c)["params"]

local_server=True
app=Flask(__name__)
app.secret_key = 'Abhi123'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT= '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_pswd']
)
mail = Mail(app)

if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db=SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone_num = db.Column(db.String, nullable=False)
    msg = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    slug = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    img_file = db.Column(db.String, nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()#[0:params['no_of_posts']]
    last= math.ceil(len(posts)/int(params['no_of_posts']))
    #Pagination Logic
    page = request.args.get('page')
    
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    if(page==1):
        prev="#"
        next="/?page="+ str(page+1)
    elif(page==last):
        prev="/?page="+ str(page-1)
        next="#"
    else:
        prev="/?page="+ str(page-1)
        next="/?page="+ str(page+1)
        
    return render_template("index.html", params=params, post=posts, prev=prev, next=next)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user']==params['admin_user']:
        posts=Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
    if(request.method=='POST'):
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if(username==params['admin_user'] and userpass==params['admin_password']):
            #set session variable
            session['user'] = username
            posts=Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
    else:
        return render_template("login.html", params=params)
    return render_template("login.html", params=params)

@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user']==params['admin_user']:
        if(request.method == 'POST'):
            box_title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')

            if sno == '0':
                post= Posts(title=box_title, slug=slug, content=content, date=dt.now(), img_file=img_file)
                db.session.add(post)
                db.session.commit()
                new_sno = post.sno
                return redirect('/edit/' + str(new_sno))

            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.slug=slug
                post.content=content
                post.img_file=img_file
                post.date=dt.now()
                db.session.commit()

    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post)

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user']==params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/post/<string:post_slug>", methods=['GET'])
def posts_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)

@app.route("/about")
def about():
    return render_template("about.html", params=params)

@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user']==params['admin_user']:
        if(request.method == 'POST'):
            f= request.files['file1']
            file_path=os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename))
            f.save(file_path)
            return "Upoladed Successfully"

@app.route("/logout", methods=['GET'])
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/contact", methods =['GET','POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to contacts table'''
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        msg=request.form.get('message')

        if not name or not email or not phone or not msg:
            return render_template("contact.html", message="All fields are required.", params=params)
        else:
            mail.send_message('New Message from Blog User: '+ name, 
                                sender=email, 
                                recipients=[params['gmail_user']], 
                                body = msg + "\nPhone NO. : " + phone
                                )
            entry= Contacts(name=name, phone_num=phone, msg=msg, date=dt.now(), email=email)
            db.session.add(entry)
            db.session.commit()
            return render_template("contact.html", success=True, params=params)

    return render_template("contact.html", params=params)

app.run(debug=True)