import re
from datetime import datetime, timedelta

from flask import url_for
from flask_login import UserMixin
from sqlalchemy.orm import synonym
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager, parse_text
from app.common_constants import DATE_FORMAT
from app.parse_text import msg_mark, extract_tags

EMAIL_REGEX = re.compile(r"^\S+@\S+\.\S+$")
USERNAME_REGEX = re.compile(r"^\S+$")
NO_DATE = datetime(1990, 1, 1)
LAST_DATE = datetime(2990, 1, 1)
NEAR_INTERVAL = timedelta(days=7)
FAR_INTERVAL = timedelta(days=60)

F_ACTIVE = 1
F_PRIVATE = 2
F_GOAL = 4



def check_length(attribute, length):
    """Checks the attribute's length."""
    try:
        return bool(attribute) and len(attribute) <= length
    except:
        return False


class BaseModel:
    """Base for all models, providing save, delete and from_dict methods."""

    def __commit(self):
        """Commits the current db.session, does rollback on failure."""
        from sqlalchemy.exc import IntegrityError

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    def delete(self):
        """Deletes this model from the db (through db.session)"""
        db.session.delete(self)
        self.__commit()

    def save(self):
        """Adds this model to the db (through db.session)"""
        db.session.add(self)
        self.__commit()
        return self

    @classmethod
    def from_dict(cls, model_dict):
        return cls(**model_dict).save()


class User(UserMixin, db.Model, BaseModel):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    _username = db.Column("username", db.String(64), unique=True)
    _email = db.Column("email", db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    b_show_all = db.Column(db.Boolean, default=True)
    b_show_user_only = db.Column(db.Boolean, default=False)

    todolists = db.relationship("TodoList", backref="user", lazy="dynamic")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        if self.is_admin:
            return f"<Admin {self.username}>"
        return f"<User {self.username}>"

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        is_valid_length = check_length(username, 64)
        if not is_valid_length or not bool(USERNAME_REGEX.match(username)):
            raise ValueError(f"{username} is not a valid username")
        self._username = username

    username = synonym("_username", descriptor=username)

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        if not check_length(email, 64) or not bool(EMAIL_REGEX.match(email)):
            raise ValueError(f"{email} is not a valid email address")
        self._email = email

    email = synonym("_email", descriptor=email)

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        if not bool(password):
            raise ValueError("no password given")

        hashed_password = generate_password_hash(password)
        if not check_length(hashed_password, 128):
            raise ValueError("not a valid password, hash is too long")
        self.password_hash = hashed_password

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def seen(self):
        self.last_seen = datetime.utcnow()
        return self.save()

    def to_dict(self):
        return {
            "username": self.username,
            "user_url": url_for("api.get_user", username=self.username, _external=True),
            "member_since": self.member_since,
            "last_seen": self.last_seen,
            "todolists": url_for(
                "api.get_user_todolists", username=self.username, _external=True
            ),
            "todolist_count": self.todolists.count(),
        }

    def promote_to_admin(self):
        self.is_admin = True
        return self.save()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class TodoList(db.Model, BaseModel):
    __tablename__ = "todolist"
    id = db.Column(db.Integer, primary_key=True)
    _title = db.Column("title", db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator = db.Column(db.String(64), db.ForeignKey("user.username"))
    todos = db.relationship("Todo", backref="todolist", lazy="dynamic")

    def __init__(self, title=None, creator=None, created_at=None):
        self.title = title or "untitled"
        self.creator = creator
        self.created_at = created_at or datetime.utcnow()

    def __repr__(self):
        return f"<Todolist: {self.title}>"

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        if not check_length(title, 128):
            raise ValueError(f"{title} is not a valid title")
        self._title = title

    title = synonym("_title", descriptor=title)

    @property
    def todos_url(self):
        url = None
        kwargs = dict(todolist_id=self.id, _external=True)
        if self.creator:
            kwargs["username"] = self.creator
            url = "api.get_user_todolist_todos"
        return url_for(url or "api.get_todolist_todos", **kwargs)

    def to_dict(self):
        return {
            "title": self.title,
            "creator": self.creator,
            "created_at": self.created_at,
            "total_todo_count": self.todo_count,
            "open_todo_count": self.open_count,
            "finished_todo_count": self.finished_count,
            "todos": self.todos_url,
        }

    @property
    def todo_count(self):
        return self.todos.order_by(None).count()

    @property
    def finished_count(self):
        return self.todos.filter_by(is_finished=True).count()

    @property
    def open_count(self):
        return self.todos.filter_by(is_finished=False).count()

    @property
    def todos_actual(self):
        now = datetime.utcnow()
        a_filter = (Todo.is_finished == False) | (Todo.finished_at > (now - NEAR_INTERVAL))
        return self.todos.filter(a_filter).order_by(Todo.tags, Todo.id)

    @property
    def todos_all(self):
        return self.todos.order_by(Todo.tags, Todo.id)

    @property
    def get_used_tags(self):
        now = datetime.utcnow()
        a_filter = (Todo.is_finished == False) | (Todo.finished_at > (now - FAR_INTERVAL))
        set_of_tags = set()
        for todo in self.todos.filter(a_filter):
            if not todo.tags:
                continue
            set_of_tags.update(todo.tags.split())
        return sorted(set_of_tags)

    @property
    def get_in_text_tags(self):
        now = datetime.utcnow()
        a_filter = (Todo.is_finished == False) | (Todo.finished_at > (now - FAR_INTERVAL))
        set_of_tags = set()
        for todo in self.todos.filter(a_filter):
            set_of_tags.update(extract_tags(todo.description))
        return sorted(set_of_tags)



class Todo(db.Model, BaseModel):
    __tablename__ = "todo"
    id = db.Column(db.Integer, primary_key=True)
    tags = db.Column(db.String(1024))
    description = db.Column(db.String(2048))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    goal_at = db.Column(db.DateTime, index=True, default=NO_DATE)
    finished_at = db.Column(db.DateTime, index=True, default=None)
    is_finished = db.Column(db.Boolean, default=False)
    creator = db.Column(db.String(64), db.ForeignKey("user.username"))
    assigned = db.Column(db.String(64))
    todolist_id = db.Column(db.Integer, db.ForeignKey("todolist.id"))

    def __init__(self, description, todolist_id, creator=None, created_at=None, tags=None, assigned_to=None):
        self.description = msg_mark(description)
        self.todolist_id = todolist_id
        self.creator = creator
        self.created_at = created_at or datetime.utcnow()
        args = parse_text.msg_parse(description)
        if tags:
            self.tags = tags
        if assigned_to:
            self.assigned = assigned_to
        if 'goal' in args:
            print(f"[TODO] {args['goal']}")
            self.goal_at = args["goal"]

    def __repr__(self):
        return "<{} Todo: {} by {}>".format(
            self.status, self.description, self.creator or "None"
        )

    @property
    def status(self):
        return "finished" if self.is_finished else "open"

    @property
    def f_goal(self):
        if self.goal_at == NO_DATE:
            return ""
        return self.goal_at.strftime(DATE_FORMAT)

    @property
    def f_finished(self):
        if self.is_finished:
            return self.finished_at.strftime(DATE_FORMAT)
        return ""

    @property
    def f_created(self):
        # if self.creator is None:
        return self.created_at.strftime(DATE_FORMAT)

    @property
    def f_tags(self):
        if self.tags is None:
            return ""
        return ';'.join(self.tags.split('##'))

    @property
    def goal_state(self):
        now = datetime.utcnow()
        goal = LAST_DATE if self.goal_at is None else self.goal_at + timedelta(days=1)
        if self.is_finished and goal < self.finished_at:
            return 'is_outdated'
        elif self.is_finished and goal >= self.finished_at:
            return ""
        elif goal < now:
            return 'is_outdated'
        elif goal < now + NEAR_INTERVAL:
            return 'is_near'
        return ''

    @property
    def editable(self):
        limit = datetime.utcnow() - NEAR_INTERVAL
        if not self.is_finished or self.finished_at is None:
            return True
        if self.created_at >= limit:
            return True
        if self.goal_at is not None and self.goal_at >= limit:
            return True
        if self.finished_at is not None and self.finished_at >= limit:
            return True
        return False


    def finished(self):
        self.is_finished = True
        self.finished_at = datetime.utcnow()
        self.save()

    def reopen(self):
        self.is_finished = False
        self.finished_at = None
        self.save()

    def to_dict(self):
        return {
            "id": self.id,
            "tags": self.tags,
            "description": self.description,
            "creator": self.creator,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "goal": self.goal_at,
            "status": self.status,
        }



