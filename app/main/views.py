import random
from datetime import datetime

from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

import app
from app import parse_text, db
from app.main import main
from app.main.forms import TodoListForm, TodoEditForm
from app.models import Todo, TodoList
from app.parse_text import msg_mark


@main.route("/")
@login_required
def index():
    # return render_template("index.html", form=form)
    return redirect(url_for("main.todolist_overview"))


@main.route("/todolists/", methods=["GET", "POST"])
@login_required
def todolist_overview():
    form = TodoListForm()
    if form.validate_on_submit():
        return redirect(url_for("main.add_todolist"))
    return render_template("overview.html", form=form, proteus=random.randint(1000, 9999))


def _get_user():
    return current_user.username if current_user.is_authenticated else None


@main.route("/todolist<int:proteus>/<int:todolist_id>/", methods=["GET", "POST"])
@login_required
def todolist(proteus, todolist_id):
    l_todolist = TodoList.query.filter_by(id=todolist_id).first_or_404()
    return render_template("todolist.html", todolist=l_todolist, proteus=random.randint(10000, 90000))


@main.route("/todolist/add/", methods=["POST"])
@login_required
def add_todolist():
    form = TodoListForm(todo=request.form.get("title"))
    if form.validate():
        l_todolist = TodoList(form.title.data, _get_user())  #.save()
        db.session.add(l_todolist)
        db.session.commit()
        return redirect(url_for("main.todolist", proteus=random.randint(10000, 90000), todolist_id=l_todolist.id))
    return redirect(url_for("main.index"))


@main.route("/set_view_filter/<int:todolist_id>/", methods=["GET", "POST"])
@login_required
def set_view_filter(todolist_id):
    if current_user and current_user.is_authenticated:
        current_user.b_show_all = not current_user.b_show_all
    return redirect(url_for("main.todolist", proteus=random.randint(10000, 90000), todolist_id=todolist_id))


@main.route("/set_todo_done/<int:todolist_id>/<int:todo_id>/", methods=["GET", "POST"])
@login_required
def set_todo_done(todolist_id, todo_id):

    todo = Todo.query.get_or_404(todo_id)
    todo.is_finished = not todo.is_finished
    todo.finished_at = datetime.utcnow() if todo.is_finished else None
    db.session.add(todo)
    db.session.commit()
    # todo.save()
    return redirect(url_for("main.todolist", proteus=random.randint(10000, 90000), todolist_id=todolist_id, _anchor=todo_id))


@main.route("/todo_item/<int:todolist_id>/<int:todo_id>/", methods=["GET", "POST"])
@login_required
def todo_item(todolist_id, todo_id):

    # todo = Todo.query.get_or_404(todo_id)
    todo = db.session.get(Todo, todo_id)
    form = TodoEditForm(tags=todo.tags,
                        description=todo.description,
                        assigned=todo.assigned,
                        is_finished=todo.is_finished,
                        finished_at=todo.finished_at)
    if form.validate_on_submit():

        form.populate_obj(todo)
        todo.description = msg_mark(todo.description).strip()
        todo.tags = todo.tags.strip()
        if todo.is_finished and todo.finished_at is None:
            todo.finished_at = datetime.utcnow()
        args = parse_text.msg_parse(form.description.data)
        if 'goal' in args:
            todo.goal_at = args["goal"]
        else:
            todo.goal_at = None
        if todo.description == "" or todo.description is None:
            db.session.delete(todo)
            # todo.delete()
            db.session.commit()
        else:
            # db.session.add(todo)
            db.session.commit()
        return redirect(url_for("main.todolist", proteus=random.randint(10000, 90000), todolist_id=todolist_id, _anchor=todo_id))
    return render_template("todo_item.html", form=form, todo_id=todo_id, todolist_id=todolist_id)


@main.route("/todo_item/<int:todolist_id>/new_from<int:from_id>", methods=["GET", "POST"])
@login_required
def todo_item_new_from_id(todolist_id, from_id):

    todo_from = Todo.query.get(from_id)
    form = TodoEditForm(tags=todo_from.tags if todo_from else "")
    if form.validate_on_submit():
        todo = Todo(
            description=form.description.data.strip(),
            todolist_id=todolist_id,
            creator=_get_user(),
            tags=form.tags.data.strip(),
            assigned_to=form.assigned.data) # .save()
        db.session.add(todo)
        db.session.commit()
        return redirect(url_for("main.todolist", proteus=random.randint(10000, 90000), todolist_id=todolist_id))
    return render_template("todo_item.html", form=form, todolist_id=todolist_id, _anchor=from_id)
