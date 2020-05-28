from flask import render_template, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, ActivityForm
from .. import db
from ..models import Role, User, Permission, Activity, ActivityStatus
from ..decorators import admin_required
from datetime import datetime


@main.route('/', methods=['GET', 'POST'])
def index():
    form = ActivityForm()
    if current_user.can(Permission.PUBLISH_ACTIVITY) and form.validate_on_submit():
        if form.begin.data.__ge__(form.end.data):
            flash("begin time should be earlier than end time")
            return redirect(url_for('.index'))
        elif form.begin.data.__lt__(datetime.now()):
            flash("begin time should be later than now time")
            return redirect(url_for('.index'))
        elif form.end.data.__sub__(form.begin.data).days >= 1:
            flash("this activity is too long")
            return redirect(url_for('.index'))
        same_place_activities = Activity.query.filter_by(location=form.location.data).all()
        for same_place_activity in same_place_activities:
            if not (same_place_activity.begin_timestamp.__gt__(form.end.data)
                    or same_place_activity.end_timestamp.__lt__(form.begin.data)):
                flash("conflicts with previously reserved activity, please change location or time!")
                return redirect(url_for('.index'))
        activity = Activity(publisher=current_user._get_current_object(),
                            begin_timestamp=form.begin.data,
                            end_timestamp=form.end.data,
                            location=form.location.data,
                            name=form.name.data,
                            description=form.description.data,
                            capacity=form.capacity.data)
        db.session.add(activity)
        flash("Publish success")
        return redirect(url_for('.index'))
    activities = Activity.query.order_by(Activity.begin_timestamp.desc()).all()
    return render_template('index.html', form=form, activities=activities)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    activities = Activity.query.order_by(Activity.begin_timestamp.desc()).all()
    return render_template('user.html', user=user, activities=activities)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)
