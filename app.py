import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Post
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-key-ll-flask-instagram'

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_input = request.form.get('email')
        password_input = request.form.get('password')
        
        user = User.query.filter_by(email=email_input).first()
        
        if user and check_password_hash(user.password, password_input):
            flash('წარმატებით შეხვედით!', 'success')
            return redirect(url_for('explore', logged_user_id=user.id))
        else:
            flash('ელ. ფოსტა ან პაროლი არასწორია', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username_input = request.form.get('username')
        email_input = request.form.get('email')
        password_input = request.form.get('password')
        confirm_password_input = request.form.get('confirm_password')
        
        if password_input != confirm_password_input:
            flash('პაროლები არ ემთხვევა!', 'danger')
            return redirect(url_for('register'))
            
        existing_user = User.query.filter_by(email=email_input).first()
        if existing_user:
            flash('ეს ელ. ფოსტა უკვე დაკავებულია!', 'warning')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username_input).first()
        if existing_user:
            flash('ეს სახელი უკვე დაკავებულია!', 'warning')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password_input)
        new_user = User(username=username_input, email=email_input, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('რეგისტრაცია წარმატებით დასრულდა! გთხოვთ გაიაროთ ავტორიზაცია.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('მოხდა შეცდომა მონაცემების შენახვისას.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/explore', methods=['GET', 'POST'])
def explore():
    logged_user_id = request.args.get('logged_user_id')
    print(logged_user_id)
    if request.method == 'POST':
        if not logged_user_id:
            logged_user_id = request.form.get('logged_user_id')
        title = request.form.get('title')
        image_url = request.form.get('image_url')
        description = request.form.get('description')
        
        new_post = Post(
            title=title,
            image_url=image_url,
            description=description,
            user_id=logged_user_id
        )
        
        try:
            db.session.add(new_post)
            db.session.commit()
            flash('Post published successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving your post.', 'danger')
            
        return redirect(url_for('explore', logged_user_id=logged_user_id))

    posts = Post.query.order_by(Post.date_posted.desc()).all()
    
    return render_template('explore.html', posts=posts, logged_user_id=logged_user_id)

@app.route('/post/<int:post_id>/edit', methods=['POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    logged_user_id = request.form.get('logged_user_id')
    
    if str(post.user_id) != str(logged_user_id):
        flash("You don't have permission to modify this post!", "danger")
        return redirect(url_for('explore', logged_user_id=logged_user_id))
        
    post.title = request.form.get('title')
    post.image_url = request.form.get('image_url')
    post.description = request.form.get('description')
    
    try:
        db.session.commit()
        flash('Post updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error saving modifications to database.', 'danger')
        
    return redirect(url_for('explore', logged_user_id=logged_user_id))


@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    logged_user_id = post.user_id 
    
    try:
        db.session.delete(post)
        db.session.commit()
        flash('Post has been deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Error executing deletion.', 'danger')
        
    return redirect(url_for('explore', logged_user_id=logged_user_id))

@app.route('/profile')
def profile():
    logged_user_id = request.args.get('logged_user_id')
    
    if not logged_user_id:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
        
    user = User.query.get_or_404(logged_user_id)
    
    user_posts = Post.query.filter_by(user_id=user.id).order_by(Post.date_posted.desc()).all()
    
    return render_template('profile.html', 
                           user=user, 
                           user_posts=user_posts, 
                           logged_user_id=logged_user_id)

if __name__ == '__main__':
    env_mode = os.getenv('CONFIGURATION', 'dist').strip().lower()
    
    if env_mode == 'dev':
        print("🚀 Running in DEVELOPMENT mode with hot-reloader active.")
        app.run(debug=True)
    else:
        print("🔒 Running in PRODUCTION (dist) mode. Debugging tools disabled.")
        app.run(debug=False)