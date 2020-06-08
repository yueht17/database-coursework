from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, ActivityForm
from .. import db
from ..models import Role, User, Permission, Activity, ActivityStatus, Enrollment
from ..decorators import admin_required, permission_required
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
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_activities
    else:
        query = Activity.query
    # pagination = query.order_by(Activity.publish_timestamp.desc()).paginate(
    #     page, per_page=current_app.config['FLASKY_ACTIVITIES_PER_PAGE'],
    #     error_out=False)
    pagination = query.order_by(Activity.begin_timestamp).paginate(
        page, per_page=current_app.config['FLASKY_ACTIVITIES_PER_PAGE'],
        error_out=False)
    activities = pagination.items
    return render_template('index.html', form=form, activities=activities, show_followed=show_followed,
                           pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = user.activities.order_by(Activity.publish_timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_ACTIVITIES_PER_PAGE'],
        error_out=False)
    activities = pagination.items
    return render_template('user.html', user=user, activities=activities, pagination=pagination)


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


@main.route('/activity/<int:id>')
def activity(id):
    activity_arg = Activity.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = Enrollment.query.filter_by(activity_id=id).paginate(
        page, per_page=current_app.config['FLASKY_PARTICIPANTS_PER_PAGE'],
        error_out=False)
    participants = [{'user': item.participant_id, 'timestamp': item.timestamp}
                    for item in pagination.items]
    return render_template('activity.html', activities=[activity_arg], pagination=pagination,
                           participants=participants, User=User, endpoint='.activity', endpoint_id=id)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    activity = Activity.query.get_or_404(id)
    if current_user != activity.publisher and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = ActivityForm()
    if form.validate_on_submit():
        if form.begin.data.__ge__(form.end.data):
            flash("begin time should be earlier than end time")
            return render_template('edit_activity.html', form=form)
        elif form.begin.data.__lt__(datetime.now()):
            flash("begin time should be later than now time")
            return render_template('edit_activity.html', form=form)

        elif form.end.data.__sub__(form.begin.data).days >= 1:
            flash("this activity is too long")
            return render_template('edit_activity.html', form=form)

        same_place_activities = Activity.query.filter_by(location=form.location.data).all()
        for same_place_activity in same_place_activities:
            if not (same_place_activity.begin_timestamp.__gt__(form.end.data)
                    or same_place_activity.end_timestamp.__lt__(form.begin.data)):
                flash("conflicts with previously reserved activity, please change location or time!")
                return render_template('edit_activity.html', form=form)

        activity = Activity(publisher=current_user._get_current_object(),
                            begin_timestamp=form.begin.data,
                            end_timestamp=form.end.data,
                            location=form.location.data,
                            name=form.name.data,
                            description=form.description.data,
                            capacity=form.capacity.data)
        db.session.add(activity)
        flash("Update success")
        return redirect(url_for(".activity", id=id))
    return render_template('edit_activity.html', form=form)


@main.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    activities = Activity.query.filter_by(id=id).all()
    enrollments = Enrollment.query.filter_by(activity_id=id).all()
    # TODO
    # delete commits
    for activity in activities:
        db.session.delete(activity)
        db.session.commit()
    for enrollment in enrollments:
        db.session.delete(enrollment)
        db.session.commit()
    flash("Activity delete succeed!")
    return redirect(url_for(".index"))


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/participate/<int:id>', methods=['GET', 'POST'])
@login_required
def participate(id):
    activity = Activity.query.get_or_404(id)

    def is_time_conflict():
        activities_of_participant = Enrollment.query. \
            filter_by(participant_id=current_user._get_current_object().id).all()
        for activity_of_participant in activities_of_participant:
            if activity.end_timestamp.__lt__(activity_of_participant.activity.begin_timestamp) or \
                    activity.begin_timestamp.__gt__(activity_of_participant.activity.end_timestamp):
                continue
            else:
                return True
        return False

    if activity._get_status() == ActivityStatus.ONGOING:
        flash("Pariticipation Failed!because this activity is ongoing.")
        return redirect(url_for('.activity', id=id))

    elif activity._get_status() == ActivityStatus.FINISHED:
        flash("Pariticipation Failed!because this activity is finished.")
        return redirect(url_for('.activity', id=id))

    elif current_user == activity.publisher:
        flash("Pariticipation Failed!because you are the publisher of this activity.")
        return redirect(url_for('.activity', id=id))

    elif Enrollment.query.filter_by(activity_id=id).count() >= activity.capacity:
        flash("Pariticipation Failed!because this activity is full.")
        return redirect(url_for('.activity', id=id))
    elif Enrollment.query.filter_by(activity_id=id). \
            filter_by(participant_id=current_user._get_current_object().id).all().__len__():
        flash("Pariticipation Failed!because you have already participated it.")
        return redirect(url_for('.activity', id=id))

    elif is_time_conflict():
        flash("Pariticipation Failed!because you are not availiable at that time.")
        return redirect(url_for('.activity', id=id))

    else:
        enrollment = Enrollment(activity_id=id, participant_id=current_user._get_current_object().id)
        db.session.add(enrollment)
        flash("Participate Succeed!")
        return redirect(url_for('.activity', id=id))
