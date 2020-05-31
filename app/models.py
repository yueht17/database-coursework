from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    PUBLISH_ACTIVITY = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.PUBLISH_ACTIVITY, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.PUBLISH_ACTIVITY |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    activities = db.relationship('Activity', backref='publisher', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        Role.insert_roles()
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username="Robot_" + forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me="i am NOT robot!",
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(followed=user)
            self.followed.append(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            self.followed.remove(f)

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    @property
    def followed_activities(self):
        return Activity.query.join(Follow, Follow.followed_id == Activity.publisher_id) \
            .filter(Follow.follower_id == self.id)

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class ActivityStatus:
    RESERVED = 0x01
    ONGOING = 0x02
    FINISHED = 0x04


class Activity(db.Model):
    __tablename__ = "activities"
    id = db.Column(db.Integer, primary_key=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    publish_timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    begin_timestamp = db.Column(db.DateTime, index=True)
    end_timestamp = db.Column(db.DateTime, index=True)
    location = db.Column(db.String(64), index=True)
    name = db.Column(db.String(64), index=True)
    description = db.Column(db.Text)
    # status = db.Column(db.Integer, default=ActivityStatus.RESERVED)
    capacity = db.Column(db.Integer)
    disabled = db.Column(db.Boolean, default=False)

    def _get_status(self):
        if datetime.now().__lt__(self.begin_timestamp):
            return ActivityStatus.RESERVED
        elif datetime.now().__lt__(self.end_timestamp):
            return ActivityStatus.ONGOING
        else:
            return ActivityStatus.FINISHED

    def _status2html(self):
        status_dict = {
            0x01: "<font color=\"green\">Reserved</font>",
            0x02: "<font color=\"red\">Ongoing</font>",
            0x04: "<font color=\"black\">Finished</font>"
        }
        return status_dict[self._get_status()]

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint, sample
        from datetime import datetime, timedelta
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            publisher = User.query.offset(randint(0, user_count - 1)).first()
            while True:
                begin_timestamp = datetime.now() + timedelta(days=randint(1, 100)) + timedelta(hours=randint(0, 24))
                end_timestamp = begin_timestamp + timedelta(hours=randint(1, 10))
                location = forgery_py.address.city(),
                if begin_timestamp.__ge__(end_timestamp):
                    continue
                elif begin_timestamp.__lt__(datetime.now()):
                    continue
                elif end_timestamp.__sub__(begin_timestamp).days >= 1:
                    continue
                same_place_activities = Activity.query.filter_by(location=location).all()
                for same_place_activity in same_place_activities:
                    if not (same_place_activity.begin_timestamp.__gt__(end_timestamp)
                            or same_place_activity.end_timestamp.__lt__(begin_timestamp)):
                        continue
                break

            def generate_fake_name():
                dishes_list = ["江西瓦罐汤", "北京烤鸭", "麻辣香锅", "烤冷面", "川菜", "馄饨", "肠粉", "粥", "酸菜鱼",
                               "过桥米线", "牛肉饭", "炸鸡饭", "手抓饭", "白水煮鸡蛋", "奶茶", "涮羊肉", "炸鸡"]
                canteen_list = [" 澜园教工餐厅", "南园食堂", "芝兰园自助餐厅", "玉树园",
                                "清芬园", "丁香园", "听涛园", "观畴园", "紫荆园", "桃李园", "清青快餐厅"]
                meal = ["早餐", "午餐", "晚餐"]
                selected_dishes = sample(dishes_list, 2)
                selected_canteen = sample(canteen_list, 2)
                selected_meal = sample(meal, 1)
                return "关于" + selected_canteen[0] + "的" + selected_dishes[0] + "," + selected_canteen[1] + "的" + \
                       selected_dishes[1] + "那个更适合做" + selected_meal[0] + "的线下研讨会。"

            activity = Activity(publisher=publisher,
                                begin_timestamp=begin_timestamp,
                                end_timestamp=end_timestamp,
                                location=location,
                                name=generate_fake_name(),
                                description="到底那个更合适呢？快来讨论呀~",
                                capacity=randint(10, 100))
            db.session.add(activity)
            db.session.commit()
