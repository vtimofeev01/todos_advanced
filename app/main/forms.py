from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, DateField, HiddenField
from wtforms.validators import Length, InputRequired, DataRequired


class TodoEditForm(FlaskForm):
    tags = TextAreaField("Enter your tags", validators=[InputRequired(), Length(0, 1024)],
                         render_kw={"placeholder": "Enter your tags"})
    description = HiddenField("Enter your todo", validators=[InputRequired(), Length(0, 2000)],
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
