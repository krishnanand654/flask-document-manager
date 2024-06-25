"""
Update form using Flask-WTF
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms.validators import DataRequired

class UpdateForm(FlaskForm):
    """UpdateForm class
        Provide title, description, file inputs
    """
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    file = FileField("File")
