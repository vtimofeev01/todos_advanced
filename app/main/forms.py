from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, DateField, DateTimeField, DateTimeLocalField
from wtforms.validators import Length, InputRequired

from app.common_constants import DATE_TIME_FORMAT


class TodoForm(FlaskForm):
    tag = StringField("Enter your tags", validators=[InputRequired(), Length(1, 1000)])
    todo = TextAreaField("Enter your todo", validators=[InputRequired(), Length(1, 2000)])
    assigned = StringField("Assigned to", validators=[InputRequired(), Length(1, 64)])
    submit = SubmitField("Submit")

class TodoEditForm(FlaskForm):
    tags = TextAreaField("Enter your tags", validators=[InputRequired(), Length(1, 1024)],
                         render_kw={"placeholder": "Enter your tags"})
    description = TextAreaField("Enter your todo", validators=[InputRequired(), Length(1, 2000)],
                                render_kw={"placeholder": "Enter your task"})
    assigned = StringField("Assigned to", validators=[InputRequired(), Length(1, 64)],
                           render_kw={"placeholder": "Assigned to"})
    is_finished = BooleanField("finished")
    finished_at = DateField('Which date is your favorite?')
    submit = SubmitField("Submit")


class TodoListForm(FlaskForm):
    title = StringField(
        "Enter your todolist title", validators=[InputRequired(), Length(1, 128)]
    )
    submit = SubmitField("Submit")
