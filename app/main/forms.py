from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, \
    SubmitField, DateTimeField, IntegerField
from wtforms.validators import Required, Length, Email, Regexp, Optional
from wtforms import ValidationError
from ..models import Role, User, ActivityStatus
from datetime import datetime


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ActivityForm(FlaskForm):
    name = StringField('Activity name', validators=[Length(0, 64)])
    description = TextAreaField('Description', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    begin = DateTimeField('BeginTime(format:year/month/day/hour/minute,e.g. now it is '
                          + datetime.now().__format__("%Y/%D/%H") + ')', format="%Y/%m/%d/%H/%M")
    end = DateTimeField('EndTime(format:year/month/day/hour/minute,e.g. now it is '
                        + datetime.now().__format__("%Y/%D/%H") + ')', format="%Y/%m/%d/%H/%M")
    capacity = IntegerField('Capacity', validators=[Required()])
    submit = SubmitField('Submit')


class FilterStatus:
    ALL = 0x00
    RESERVED = 0x01
    ONGOING = 0x02
    FINISHED = 0x04


class FilterStartTimeOrder:
    DEFAULT = 0x00
    DES = 0x01
    ASC = 0x02


class FilterCapacityOrder(FilterStartTimeOrder):
    pass


class FilterForm(FlaskForm):
    # TODO
    status = SelectField('status：', choices=[
        (FilterStatus.ALL, 'All'),
        (FilterStatus.RESERVED, 'Reserved'),
        (FilterStatus.ONGOING, 'Ongoing'),
        (FilterStatus.FINISHED, 'Finished'),
    ], coerce=int)
    location = StringField('Location(Optional)', validators=[Length(0, 64)])
    start_time_order = SelectField('start time order',
                                   choices=[(FilterStartTimeOrder.DEFAULT, 'Default'),
                                            (FilterStartTimeOrder.DES, 'Descending'),
                                            (FilterStartTimeOrder.ASC, 'Ascending')],
                                   coerce=int)
    capacity_order = SelectField('capacity order',
                                 choices=[(FilterCapacityOrder.DEFAULT, 'Default'),
                                          (FilterCapacityOrder.DES, 'Descending'),
                                          (FilterCapacityOrder.ASC, 'Ascending')],
                                 coerce=int)
    confirm = SubmitField('Confirm')


class CommentForm(FlaskForm):
    body = StringField('Enter your comment', validators=[Required()])
    submit = SubmitField('Submit')
