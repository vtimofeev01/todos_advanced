import random
from datetime import datetime
from enum import Enum

from flask import redirect, render_template, request, url_for, session
from flask_login import current_user, login_required
from sqlalchemy import func

from app import parse_text, db
from app.main import main
from app.main.forms import TodoListForm, TodoEditForm
from app.models import Todo, TodoList
from app.parse_text import msg_mark, tags_list_normalizer, remove_single_p_tag

S_TODOLIST = 'todolist'
S_TAG = 'tag'
S_ASSIGNED = 'assigned_to'
S_LAST_EDIT = 'last_edited'
S_SORT_ORDER = 'sort_order'
C_ORDER = ('by_id', 'by_date')
L_C_ORDER = len(C_ORDER)
D_C_ORDER = 1
S_TODOLIST_ID = 'todolist_id'
S_ANCHOR = 'anchor'

@main.route("/")
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


def _get_username():
    return current_user.username if current_user.is_authenticated else None


@main.route("/todolist/<int:todolist_id>/", methods=["GET", "POST"])
@login_required
def todolist(todolist_id):
    args = request.args
    l_todolist = TodoList.query.filter_by(id=todolist_id).first_or_404()
    todolist_details = l_todolist.todos_list(current_user.b_show_all, C_ORDER[session.get(S_SORT_ORDER, D_C_ORDER) % L_C_ORDER])

    if S_TODOLIST not in session:
        session[S_TODOLIST] = todolist_id
    elif session[S_TODOLIST] != todolist_id:
        if S_TAG in session:
            del session[S_TAG]
        if S_ASSIGNED in session:
            del session[S_ASSIGNED]
        session[S_TODOLIST] = todolist_id


    tag = args.get(S_TAG)
    if tag == 'None':
        if S_TAG in session:
            del session[S_TAG]
        tag = None
    if tag is None and session.get(S_TAG, None) is not None:
        tag = session[S_TAG]

    if tag:
        session[S_TAG] = tag
        look_for = '%{0}%'.format(tag.lower())
        todolist_details = todolist_details.filter(func.lower(Todo.tags.like(look_for)))

    assigned_to = args.get(S_ASSIGNED)
    if assigned_to == 'None':
        if S_ASSIGNED in session:
            del session[S_ASSIGNED]
        assigned_to = None
    if assigned_to is None and session.get(S_ASSIGNED, None) is not None:
        assigned_to = session[S_ASSIGNED]

    if assigned_to:
        session[S_ASSIGNED] = assigned_to
        look_for = '%{0}%'.format(assigned_to.lower())
        todolist_details = todolist_details.filter(func.lower(Todo.assigned.like(look_for)))

    header_keys = (S_TAG, S_ASSIGNED)
    filter_reader = []
    for hk in header_keys:
        if hk in session and session[hk] is not None:
            filter_reader.append("+" + session[hk])
    filter_header = ', '.join(filter_reader) if filter_reader else None

    tg_l, tg_a = l_todolist.get_tags_to_filter_for(current_user.b_show_all,
                                                               session.get(S_TAG,None),
                                                               session.get(S_ASSIGNED,None),
                                                               )
    session[S_TODOLIST] = todolist_id

    return render_template("todolist.html", todolist=l_todolist, todolist_details=todolist_details,
                           filter_header=filter_header, tg_l=tg_l, tg_a=tg_a, C_ORDER=C_ORDER)


@main.route("/todolist/add/", methods=["POST"])
@login_required
def add_todolist():
    form = TodoListForm(todo=request.form.get("title"))
    if form.validate():
        l_todolist = TodoList(form.title.data, _get_username())  #.save()
        db.session.add(l_todolist)
        db.session.commit()
        return redirect(url_for("main.todolist", todolist_id=l_todolist.id))
    return redirect(url_for("main.index"))


@main.route("/set_view_filter/<int:todolist_id>/", methods=["GET", "POST"])
@login_required
def set_view_filter(todolist_id):
    if current_user and current_user.is_authenticated:
        current_user.b_show_all = not current_user.b_show_all
    return redirect(url_for("main.todolist", todolist_id=todolist_id))


@main.route("/set_todo_done/<int:todolist_id>/<int:todo_id>/", methods=["GET", "POST"])
@login_required
def set_todo_done(todolist_id, todo_id):

    todo = Todo.query.get_or_404(todo_id)
    todo.is_finished = not todo.is_finished
    todo.finished_at = datetime.utcnow() if todo.is_finished else None
    db.session.add(todo)
    db.session.commit()
    session[S_ANCHOR] = todo.tags
    return redirect(url_for("main.todolist", todolist_id=todolist_id, _anchor=session.get(S_ANCHOR, '')))


@main.route("/todo_item/<int:todolist_id>/<int:todo_id>/", methods=["GET", "POST"])
@login_required
def todo_item(todolist_id, todo_id):
    l_todolist = TodoList.query.filter_by(id=todolist_id).first_or_404()
    todo = db.session.get(Todo, todo_id)
    form = TodoEditForm(tags=todo.tags,
                        description=todo.description,
                        assigned=todo.assigned,
                        is_finished=todo.is_finished,
                        finished_at=todo.finished_at)
    if form.validate_on_submit():

        form.populate_obj(todo)
        todo.description = remove_single_p_tag(msg_mark(todo.description).strip())
        tags_list = tags_list_normalizer(form.tags.data)
        tags = ' '.join(tags_list)
        ## check if tags are right
        tags_set = set(tags_list)
        # print(tags,tags_set)
        for rec in l_todolist.todos_all(''):
            rs_tag = set(rec.tags.split())
            # print(rs_tag, tags_set, rs_tag == tags_set)
            if rs_tag == tags_set:
                tags = ' '.join(tags_list_normalizer(rec.tags))
                # print('found')
                break

        todo.tags = tags

        if todo.is_finished and todo.finished_at is None:
            todo.finished_at = datetime.utcnow()
        args = parse_text.msg_parse(form.description.data)
        if 'goal' in args:
            todo.goal_at = args["goal"]
        else:
            todo.goal_at = None
        if todo.description == "" or todo.description is None:
            db.session.delete(todo)
            db.session.commit()
        else:
            db.session.commit()
        session[S_LAST_EDIT] = todo.id
        session[S_ANCHOR] = todo.tags
        return redirect(url_for("main.todolist", todolist_id=todolist_id, _anchor=session.get(S_ANCHOR,'')))
    return render_template("todo_item.html", form=form, todo_id=todo_id, todolist_id=todolist_id, todolist=l_todolist,
                           C_ORDER=C_ORDER)


@main.route("/todo_item/<int:todolist_id>/new_from<int:from_id>", methods=["GET", "POST"])
@login_required
def todo_item_new_from_id(todolist_id, from_id):

    l_todolist = TodoList.query.filter_by(id=todolist_id).first_or_404()
    todo_from = Todo.query.get(from_id)
    form = TodoEditForm(tags=todo_from.tags if todo_from else "")
    if form.validate_on_submit():
        tags_list = tags_list_normalizer(form.tags.data)
        tags = ' '.join(tags_list)
        ## check if tags are right
        tags_set = set(tags_list)
        # print(tags,tags_set)
        for rec in l_todolist.todos_all(''):
            rs_tag = set(rec.tags.split())
            if rs_tag == tags_set:
                tags = rec.tags
                break

        todo = Todo(
            description=remove_single_p_tag(form.description.data.strip()),
            todolist_id=todolist_id,
            creator=_get_username(),
            tags=tags,
            assigned_to=form.assigned.data) # .save()
        db.session.add(todo)
        db.session.commit()
        session[S_LAST_EDIT] = todo.id
        session[S_ANCHOR] = tags
        return redirect(url_for("main.todolist", todolist_id=todolist_id,  _anchor=session.get(S_ANCHOR, '')))
    return render_template("todo_item.html", form=form, todolist_id=todolist_id, todolist=l_todolist, C_ORDER=C_ORDER)


@main.route("/change_sort_order", methods=["GET","POST"])
@login_required
def change_sort_order():
    if session.get(S_SORT_ORDER, None) is None:
        session[S_SORT_ORDER] = D_C_ORDER
    else:
        session[S_SORT_ORDER] += 1
    return redirect(url_for("main.todolist", todolist_id=session[S_TODOLIST], _anchor=session.get(S_ANCHOR,'')))
