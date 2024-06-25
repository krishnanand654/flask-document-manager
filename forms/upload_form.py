"""
Upload form using Flask-WTF
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms.validators import DataRequired

class UploadForm(FlaskForm):
    """UploadForm class
        Provide title, description, file inputs with validation
    """
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    file = FileField("File", validators=[DataRequired()])
