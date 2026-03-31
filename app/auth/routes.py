from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app.extensions import db
from app.auth import bp
from app.auth.forms import LoginForm, CreateUserForm, ResetPasswordForm
from app.models import User
from app.session import store_api_key

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        # Auto-populate API key from stored encrypted value
        stored_key = user.load_api_key(current_app.secret_key)
        if stored_key:
            store_api_key(stored_key)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        flash('You do not have permission to view this page.')
        return redirect(url_for('main.index'))
    users = User.query.all()
    return render_template('auth/users.html', title='User Management', users=users)

@bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('You do not have permission to view this page.')
        return redirect(url_for('main.index'))
    
    form = CreateUserForm()
    current_app.logger.debug(f"Form data: {request.form}")
    current_app.logger.debug(f"Form errors: {form.errors}")
    current_app.logger.debug(f"Form is_submitted: {form.is_submitted()}")
    current_app.logger.debug(f"Form validate: {form.validate()}")
    
    if request.method == 'POST':
        if form.validate():
            try:
                user = User(username=form.username.data.strip(), is_admin=form.is_admin.data or False)
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                flash('User created successfully!', 'success')
                return redirect(url_for('auth.users'))
            except Exception as e:
                current_app.logger.error(f"Error creating user: {str(e)}")
                db.session.rollback()
                flash('Error creating user. Please try again.', 'error')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'error')
    
    return render_template('auth/create_user.html', title='Create User', form=form)

@bp.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def reset_password(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash(f'Password for {user.username} has been reset successfully.', 'success')
        return redirect(url_for('auth.users'))
    return render_template('auth/reset_password.html', title='Reset Password', form=form, user=user)


@bp.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot delete your own account!')
        return redirect(url_for('auth.users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!')
    return redirect(url_for('auth.users')) 