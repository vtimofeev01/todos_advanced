from datetime import datetime

from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import parse_text
from app.main import main
from app.main.forms import TodoForm, TodoListForm, TodoEditForm
from app.models import Todo, TodoList, User
from app.parse_text import msg_demark, msg_mark


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
    return render_template("overview.html", form=form)


def _get_user():
    return current_user.username if current_user.is_authenticated else None


@main.route("/todolist/<int:id>/", methods=["GET", "POST"])
@login_required
def todolist(id):
    todolist = TodoList.query.filter_by(id=id).first_or_404()
    # print(todolist.get_used_tags)
    form = TodoForm()
    if form.validate_on_submit():
        Todo(form.todo.data, todolist.id, creator=_get_user(),
             tags=form.tag.data, assigned_to=form.assigned.data).save()
        return redirect(url_for("main.todolist", id=id))
    return render_template("todolist.html", todolist=todolist, form=form)


@main.route("/todolist/new/", methods=["POST"])
@login_required
def new_todolist():
    form = TodoForm(todo=request.form.get("todo"))
    if form.validate():
        todolist = TodoList(creator=_get_user()).save()
        Todo(form.todo.data, todolist.id).save()
        return redirect(url_for("main.todolist", id=todolist.id))
    return redirect(url_for("main.index"))


@main.route("/todolist/add/", methods=["POST"])
@login_required
def add_todolist():
    form = TodoListForm(todo=request.form.get("title"))
    if form.validate():
        todolist = TodoList(form.title.data, _get_user()).save()
        return redirect(url_for("main.todolist", id=todolist.id))
    return redirect(url_for("main.index"))


@main.route("/set_view_filter/<int:todolist_id>/", methods=["GET", "POST"])
@login_required
def set_view_filter(todolist_id):
    if current_user.is_authenticated:
        user = User.query.filter_by(_username=current_user.username).first_or_404()
        user.b_show_all = not user.b_show_all
    return redirect(url_for("main.todolist", id=todolist_id))


@main.route("/todo_item/<int:todolist_id>/<int:todo_id>/", methods=["GET", "POST"])
@login_required
def todo_item(todolist_id, todo_id):
    todo = Todo.query.get_or_404(todo_id)
    form = TodoEditForm(tags=todo.tags,
                        description=msg_demark(todo.description),
                        assigned=todo.assigned,
                        is_finished=todo.is_finished,
                        finished_at=todo.finished_at)
    if form.validate_on_submit():
        args = parse_text.msg_parse(form.description.data)
        form.populate_obj(todo)
        todo.description = msg_mark(todo.description).strip()
        todo.tags = todo.tags.strip()
        if todo.is_finished and todo.finished_at is None:
            todo.finished_at = datetime.utcnow()
        if 'goal' in args:
            todo.goal_at = args["goal"]
        else:
            todo.goal_at = None
        todo.save()
        return redirect(url_for("main.todolist", id=todolist_id))
    return render_template("todo_item.html", form=form, todo_id=todo_id, todolist_id=todolist_id)


@main.route("/todo_item/<int:todolist_id>/new/", methods=["GET", "POST"])
@login_required
def todo_item_new(todolist_id):
    form = TodoEditForm()
    if form.validate_on_submit():
        Todo(msg_demark(form.description.data).strip(), todolist_id,
             creator=_get_user(),
             tags=form.tags.data.strip(),
             assigned_to=form.assigned.data).save()
        return redirect(url_for("main.todolist", id=todolist_id))
    return render_template("todo_item.html", form=form, todolist_id=todolist_id)
