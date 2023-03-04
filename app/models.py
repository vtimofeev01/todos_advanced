import re
from datetime import datetime, timedelta

from flask import url_for
from flask_login import UserMixin
from sqlalchemy import or_, and_, not_
from sqlalchemy.orm import synonym
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager, parse_text
from app.common_constants import DATE_FORMAT
from app.parse_text import extract_tags, msg_mark, capitalize

EMAIL_REGEX = re.compile(r"^\S+@\S+\.\S+$")
USERNAME_REGEX = re.compile(r"^\S+$")
LAST_DATE = datetime(2990, 1, 1)
UNEAR_INTERVAL = timedelta(days=2)
NEAR_INTERVAL = timedelta(days=7)
MID_INTERVAL = timedelta(days=30)
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


class User(UserMixin, db.Model):
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
        db.session.add(self)
        db.session.commit()
        return self

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
    # us = User.query.get_or_404(int(user_id))
    us = db.session.get(User, int(user_id))
    return us


class TodoList(db.Model):
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
    def todo_count(self):
        return self.todos.order_by(None).count()

    @property
    def finished_count(self):
        return self.todos.filter_by(is_finished=True).count()

    @property
    def open_count(self):
        return self.todos.filter_by(is_finished=False).count()

    def todos_actual(self, sort_type):
        now = datetime.utcnow()
        now_l_mid = now - MID_INTERVAL
        now_l_near = now - NEAR_INTERVAL
        selection =  self.todos.filter(
            or_(
                or_(
                    and_(Todo.goal_at is None, Todo.created_at > now_l_mid),
                    and_(Todo.goal_at is not None, not_(Todo.is_finished))
                ),
                and_(Todo.is_finished, Todo.finished_at > now_l_near)
            )
        )
        print(f'todos_actual sort:{sort_type}')

        if sort_type == 'by_date':
            return selection.order_by(Todo.tags, Todo.goal_at)
        return selection.order_by(Todo.tags, Todo.id)


    def todos_all(self, sort_type):
        if sort_type == 'by_date':
            return self.todos.order_by(Todo.tags, Todo.goal_at)
        return self.todos.order_by(Todo.tags, Todo.id)

    def todos_list(self, v, sort_type):
        print(f'sort_type={sort_type}')
        if v:
            return self.todos_all(sort_type)
        else:
            return self.todos_actual(sort_type)

    def get_used_tags_row(self, show_all):
        set_of_tags = set()
        set_of_first_tags = set()
        for todo in self.todos_all('') if show_all else self.todos_actual(''):
            if not todo.tags:
                continue
            t_list = todo.tags.split()
            set_of_first_tags.add(t_list[0].lower())
            if len(t_list) > 1:
                set_of_tags.update(set([x.lower() for x in t_list[1:]]))
        return [capitalize(x.strip()) for x in sorted(list(set_of_first_tags))], [capitalize(x.strip()) for x in
                                                                                  sorted(list(set_of_tags))]

    def get_used_tags_row_advances(self, show_all, tag=None):
        dict_of_tags = {}
        dict_of_first_tags = {}
        tag2 = tag.lower().strip() if tag else None
        for todo in self.todos_list(show_all, ''):
            if not todo.tags:
                continue
            t_list = [x.lower().strip() for x in todo.tags.split()]
            present = 1 if tag is not None and tag2 in t_list else 0
            if t_list[0] not in dict_of_first_tags:
                dict_of_first_tags[t_list[0]] = present
            elif dict_of_first_tags[t_list[0]] == 0:
                dict_of_first_tags[t_list[0]] = present
            if len(t_list) > 1:
                for t_tag in t_list[1:]:
                    if t_tag not in dict_of_tags:
                        dict_of_tags[t_tag] = present
                    elif dict_of_tags[t_tag] == 0:
                        dict_of_tags[t_tag] = present
        return [(capitalize(a), dict_of_first_tags[a]) for a in sorted(dict_of_first_tags.keys())], \
            [(capitalize(a), dict_of_tags[a]) for a in sorted(dict_of_tags.keys())]



    def get_tags_to_filter_for(self, show_all, tag=None, assigned=None):
        tags_first_dict = {}
        tags_others_dict = {}
        tags_assigned = {}
        # print(f"[get_tags_to_filter_for] = tag:{tag} assigned:{assigned}")
        tag2 = tag.lower().strip() if tag else None
        ass2 = assigned.lower().strip() if assigned else None
        for todo in self.todos_list(show_all, ''):
            t_list = [x.lower().strip() for x in todo.tags.split()]
            present = 1 if tag2 is not None and tag2 in t_list else 0
            t_assigned = [x.lower().strip() for x in todo.assigned.split(',')]
            # print(todo.id, '---------------------')
            # print(t_list, t_assigned)
            present += 1 if ass2 is not None and ass2 in t_assigned else 0

            if t_list[0] not in tags_first_dict:
                tags_first_dict[t_list[0]] = present
            tags_first_dict[t_list[0]] += present
            if len(t_list) > 1:
                for t_tag in t_list[1:]:
                    if t_tag not in tags_others_dict:
                        tags_others_dict[t_tag] = present
                    tags_others_dict[t_tag] += present

            for assigned in t_assigned:
                if assigned not in tags_assigned:
                    tags_assigned[assigned] = present
                tags_assigned[assigned] += present

            # print(tags_first_dict)
            # print(tags_others_dict)
            # print(tags_assigned)

        return [[(capitalize(a), capitalize(a), tags_first_dict[a]) for a in sorted(tags_first_dict.keys())],
            [(capitalize(a), capitalize(a), tags_others_dict[a]) for a in sorted(tags_others_dict.keys())] + [('All', 'None', 1)]], \
            [(capitalize(a), capitalize(a), tags_assigned[a]) for a in sorted(tags_assigned.keys())] + [('All', 'None', 1)],








    def get_used_tags(self, show_all):
        l1, l2 = self.get_used_tags_row(show_all)
        return l1 + l2

    @property
    def get_in_text_tags(self):
        now = datetime.utcnow()
        a_filter = (Todo.is_finished == False) | (Todo.finished_at > (now - FAR_INTERVAL))
        set_of_tags = set()
        for todo in self.todos.filter(a_filter):
            set_of_tags.update(extract_tags(todo.description))
        # print(f'set of tage:{set_of_tags}')
        return sorted(set_of_tags)

    # @property
    def get_assigned_to_list(self, show_all):
        set_of_assigned = set()
        for todo in self.todos_list(show_all, ''):
            set_of_assigned.update(todo.assigned.split(','))
        return sorted(list(set(capitalize(x.strip()) for x in set_of_assigned)))

    def get_assigned_to_list_advanced(self, show_all, tag=None):
        dict_of_assigned = {}
        tag2 = tag.lower().strip() if tag else None
        for todo in self.todos_list(show_all, ''):
            present = 0 if tag2 is None or tag2 not in todo.tags.lower() else 1
            for assigned in todo.assigned.split(','):
                assigned2 = assigned.lower().strip()
                if assigned2 not in dict_of_assigned:
                    dict_of_assigned[assigned2] = present
                elif dict_of_assigned[assigned2] == 0:
                    dict_of_assigned[assigned2] = present

        return [(capitalize(a), dict_of_assigned[a]) for a in sorted(dict_of_assigned.keys())]


class Todo(db.Model):
    __tablename__ = "todo"
    id = db.Column(db.Integer, primary_key=True)
    tags = db.Column(db.String(1024))
    description = db.Column(db.String(2048))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    goal_at = db.Column(db.DateTime, index=True, default=None)
    finished_at = db.Column(db.DateTime, index=True, default=None)
    is_finished = db.Column(db.Boolean, default=False)
    creator = db.Column(db.String(64), db.ForeignKey("user.username"))
    assigned = db.Column(db.String(64))
    todolist_id = db.Column(db.Integer, db.ForeignKey("todolist.id"))

    def __init__(self, description, todolist_id, creator=None, created_at=None, tags=None, assigned_to=None):
        self.description = msg_mark(description)
        # self.description = text_parse(description)
        self.todolist_id = todolist_id
        self.creator = creator
        self.created_at = created_at or datetime.utcnow()
        args = parse_text.msg_parse(description)
        if tags:
            self.tags = tags
        if assigned_to:
            self.assigned = assigned_to
        if 'goal' in args:
            self.goal_at = args["goal"]
        else:
            self.goal_at = None

    def __repr__(self):
        return "<{} Todo: {} by {}>".format(
            self.status, self.description, self.creator or "None"
        )

    @property
    def status(self):
        if self.goal_at is None:
            return 'is_info'
        elif self.is_finished:
            return 'is_finished'
        elif self.goal_at < datetime.utcnow():
            return 'is_outdated'
        return 'is_open'

        # return "finished" if self.is_finished else "open"

    @property
    def f_goal(self):
        if self.goal_at is None:
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
    def goal_state(self):
        now = datetime.utcnow()
        goal = LAST_DATE if self.goal_at is None else self.goal_at + timedelta(days=1)
        if self.is_finished and goal < self.finished_at:
            return 'is_outdated'
        elif self.is_finished and goal >= self.finished_at:
            return ""
        elif goal < now:
            return 'is_outdated'
        elif goal < now + UNEAR_INTERVAL:
            return 'is_next_day'
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