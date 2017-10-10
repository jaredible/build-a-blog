from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:MyNewPass@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner, pub_date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80), nullable=False)
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __str__(self):
        return self.username

endpoints_without_login = ['login', 'signup']

@app.before_request
def require_login():
    if request.endpoint not in endpoints_without_login and 'username' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user:
            if user.password == password:
                session['username'] = username
                flash("Logged in")
                return redirect('/blog/newpost')
            else:
                flash('User password incorrect', 'error')
        else:
            flash('No user exists', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/')
        else:
            # TODO - user better response messaging
            return "<h1>Duplicate user</h1>"

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/blog/newpost', methods=['POST', 'GET'])
def newpost():
    if request.method == 'POST':
        owner = User.query.filter_by(username=session['username']).first()
        blog_title = request.form['title']
        blog_body = request.form['body']
        new_blog = Blog(blog_title, blog_body, owner)
        db.session.add(new_blog)
        db.session.commit()
        return redirect('/blog')

    return render_template('newpost.html', title="Build a Blog!")

@app.route('/blog', methods=['POST', 'GET'])
def blogs():
    id = request.args.get('id')
    username = request.args.get('username')

    if id:
        blog = Blog.query.get(id)
        user = User.query.get(blog.owner_id).username
        return render_template('blogs.html', title="Build a Blog!", blog=blog, user=user)

    if username:
        blogs = User.query.filter_by(username=username).first().blogs
        users = User.query.all()
        return render_template('blogs.html', title="Build a Blog!", blogs=blogs, users=users)

    blogs = Blog.query.order_by(Blog.pub_date.desc()).all()
    return render_template('blogs.html', title="Build a Blog!", blogs=blogs)

@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

if __name__ == '__main__':
    app.run()