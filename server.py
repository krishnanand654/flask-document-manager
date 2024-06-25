"""Document Manager

    The system should allow users to upload, view, update, and delete documents.
"""
import datetime
import sqlite3
import os
import uuid
from werkzeug.exceptions import RequestEntityTooLarge
from flask import Flask, request, render_template, redirect,url_for, send_file, flash
from forms import upload_form, update_form

app = Flask(__name__)

app.config['SECRET_KEY'] = 'test234secretj3247823key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #allow file size below 16mb

UPLOAD_FOLDER = 'upload/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok = True)

def db_connection():
    """Connection method
        purpose: Reusability
    Returns:
        connection object: returns connection object if connected to db
    """
    conn = sqlite3.connect("documents.db")
    return conn

def database_config():
    """Create table documents if not exist

    Returns:
        bool: True if table created successfully
    """
    try:
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS documents(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    upload_date TEXT NOT NULL,
                    file_path TEXT NOT NULL
                    )
                    ''')
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
    return True


def acceptable_file(filename):
    """Accept only valid extensions

    Args:
        filename (string): accept the name of file

    Returns:
        bool: Flase if not acceptable else True
    """
    acceptable_extensions = ['pdf', 'xlsx', 'docs', 'jpg', 'png', 'txt', 'json', 'pptx', 'ppt']
    extension = filename.split('.')[-1].lower()
    if extension not in acceptable_extensions:
        return False,extension
    return True,extension

def dictionary_generator(tuple_data):
    """Generate Dictionary data

    Args:
        tuple_data (list of tuples or tuple itself): Takes the list of tuples or a tuple

    Returns:
        list: list of dictionary
    """
    header = ['id','title','description','upload_date','file_path']
    if isinstance(tuple_data, list):
        data = [dict(zip(header, row))for row in tuple_data]
        return data
    return dict(zip(header, tuple_data))

#Time module to get the upload time
date = datetime.datetime.now()
upload_date = date.strftime(r"%Y-%m-%d %H:%M:%S") #Get upload time in specific format

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    """Handle files more than specified file size

    Args:
        error (Object): if specific error is thrown

    Returns:
        redirect to same page
    """
    #flash sends a key value pair message object to the template
    flash('File is too large. Maximum file size is 16 MB.', 'error')
    return redirect(request.url)

@app.route('/')
def index():
    """View all uploaded documents in index page

    Returns:
        data: dictionary data with uploaded file information
    """
    data = None
    try:
        query = '''SELECT * FROM documents'''
        conn = db_connection()
        cursor = conn.cursor()
        response = cursor.execute(query)
        rows = response.fetchall()
        if not rows:
            return render_template('index.html')
        data = dictionary_generator(rows)
        print(data)
        return render_template('index.html', data = data)
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
    return data

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload documents

    Returns:
        _type_: _description_
    """
    form = upload_form.UploadForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            title = form.title.data
            description = form.description.data
            #upload file using request.files
            file = request.files['file']
            error = None

            #check if the fields exist (if wtf-form validator fails to do validation)
            if title == '':
                error = "Title is required"
            if description == '':
                error = "Description is required"
            #Check if file exist
            if not file:
                error = "Please upload file"
            else:
                #adding unique id in front of the filename to avoid same filename issues
                file_name = str(uuid.uuid4())+file.filename
            if file_name == '':
                error = "Invalid file"

            #allow only specifies file extensions only
            extension_check = acceptable_file(file_name)#returns (bool,extension_str)
            if not extension_check[0]:
                error = f"Invalid file format {extension_check[1]}"

            if error is None:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
                #Save file to server directory
                file.save(file_path)
                try:
                    query = '''INSERT INTO documents(title, description, upload_date, file_path)
                            VALUES(?, ?, ?, ?)'''
                    conn = db_connection()
                    cursor = conn.cursor()
                    result = cursor.execute(query, (title, description, upload_date, file_path))
                    #save file to sqlite
                    conn.commit()
                    if result:
                        cursor.close()
                        conn.close()
                        return redirect(url_for('index'))
                except sqlite3.Error as e:
                    print(e)
                finally:
                    if conn:
                        conn.close()
            return render_template('upload.html',form = form, error=error)
    return render_template('upload.html', form = form)

def get_document_by_id(id_):
    """Fetch document by particular id
       Purpose: Reusability (Used to view particular data and in fetching data for update by id)

    Args:
        id (int): Id of the document to be fetched

    Returns:
        dictionary: data dictionary
    """
    data = None
    try:
        query = '''
                    SELECT * 
                    FROM documents
                    WHERE id=?
                    '''
        conn = db_connection()
        cursor = conn.cursor()
        response = cursor.execute(query,(id_,))
        row = response.fetchone()
        #generate dictionary data from sending tuple
        data = dictionary_generator(row)
        return data
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
    return data

@app.route("/document/<int:id_>")
def document(id_):
    """Get specific document by id

    Args:
        id (int): Id of document to view

    Returns:
        dictionary: data
    """
    data = get_document_by_id(id_)
    return render_template('view.html', data = data)

@app.route('/update/<int:id_>', methods=['GET', 'POST'])
def update(id_):
    """Update specific document by id

    Args:
        id (int): Id of document to be updated    
    """
    form = update_form.UpdateForm()#UpdateForm object
    error = None
    data = get_document_by_id(id_)
    if request.method == 'GET':
        #View already existing data in form fields
        form.title.data = data['title']
        form.description.data = data['description']
        form.file.custom_filename = data['file_path'].split('/')[-1]
    if request.method == 'POST':
        title = form.title.data
        description = form.description.data
        #check if the fields exist (if wtf-form validator fails to do validation)
        if title == '':
            error = "Title is required"
        if description == '':
            error = "Description is required"
        #if field errors exist
        if error is not None:
            return render_template('upload.html',form = form, error=error)
        #if file exist get new file data using Flask-Uploads
        file= form.file.data
        if not file:
            #if no file is upload set file path to old filepath
            filepath=data['file_path']
        else:
            #add unique id to filenames
            filename = str(uuid.uuid4())+file.filename
            #validate file extensions
            extension_check = acceptable_file(filename)#(bool,extension_str)
            if not extension_check[0]:
                error = f"Invalid file format {extension_check[1]}"
            if error is not None:
                return render_template('upload.html',form = form, error=error)
            #remove old file
            os.remove(data['file_path'])
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            #save new file
            file.save(filepath)
        #get title, description, upload_date, new file_path and update
        try:
            query='''
                    UPDATE documents
                    SET title=?, description=?, upload_date=?, file_path=? WHERE id=?
                '''
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute(query,(title, description, upload_date,filepath, id_ ))
            #save to database
            conn.commit()
            #redirect to document view page with specific document id "/document/<id>"
            return redirect(url_for('document', id_ = id_))
        except sqlite3.Error as e:
            print(e)
        finally:
            if conn:
                conn.close()
    return render_template('update.html', form= form)

@app.route('/delete/<int:id_>')
def delete(id_):
    """Delete document based on id

    Args:
        id (int): Id of document to be deleted

    Returns:
        redirect to index page
    """
    try:
        query = ''' DELETE FROM documents
                    WHERE id = ?
                '''
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute(query,(id_,))
        #remove from database
        conn.commit()
        #remove from directory
        filepath = request.args.get('filename')
        os.remove(filepath)
        return redirect(url_for('index'))
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
    return redirect(url_for('index', error="Delete failed"))

@app.route('/download/<int:id_>')
def download(id_):
    data = get_document_by_id(id_)
    filename = data['file_path']
    """Can be used for both viewing pdf files and Download file

    Returns: if download parameter exist in url then the file is downloaded
             else the pdf and images files can be viewed in website
    """
    download_status = request.args.get('download')
    return send_file(f"{filename}", as_attachment=download_status)

if __name__ == '__main__':
    app.run(debug=True)
