from os.path import join as pjoin
from ephisem_detect import *
from hashlib import sha1 as hash
from flask import (Flask,
                   redirect,
                   request,
                   jsonify,
                   render_template as render)
from web_interface.session import session
from os import system, listdir
from json import loads
rm = lambda d: system(f'rm -rfv "{d}"')

data = {}
with open('static/data.json') as json:
    data = loads(json.read())
server = Flask('Ephisem Detect')
server.config['UPLOAD_FOLDER'] = 'static/images'
try:
    listdir(server.config['UPLOAD_FOLDER'])
except FileNotFoundError:system(f"mkdir {server.config['UPLOAD_FOLDER']}")



@server.route('/')
def index():
    return render('index.html')

@server.route('/remove_file', methods=['POST'])
def remove_file():
    for f in request.json:
        rm(f['dir'])
    return str()

@server.route('/send', methods = ['POST', 'GET'])
def send():
    if request.method == 'GET':
        return redirect('/')

    from datetime import datetime as d

    files = []
    for f in request.files.getlist('image'):
        timestamp = d.now().timestamp()
        hashname = hash(bytes(f.filename, 'utf-8')).hexdigest()
        filename = f'{timestamp}.{hashname}{f.filename[f.filename.rindex("."):]}'
        filedir = pjoin(
            server.config['UPLOAD_FOLDER'],
            filename
        )

        f.save(filedir)
        files.append({
            'dir': filedir,
            'filename': f.filename,
            'name': f.filename[:f.filename.index('.')]
        })

    session['ephisem.files'] = files
    return redirect('/analize')



@server.route('/analize', methods = ['GET', 'POST'])
def analize():
    if request.method == 'POST':
        files = []
        try:
            files = session['ephisem.files']
        except KeyError:return redirect('/')
        for f in range(len(files)):
            file = files[f]

            img = Image.open(file['dir'])
            img_map = compress_map(threshold(img))

            total = 0
            slice_type = file['filename'][
                file['filename'].index('_')+1:file['filename'].index('.')
            ]
            percentages = list(compair(data[slice_type], img_map))
            for p in range(len(percentages)):
                total += percentages[p][0]

            files[f]['slice_type'] = slice_type
            files[f]['ephisem_level'] = total/len(percentages)
            files[f]['compair_percentages'] = percentages

        return jsonify(files)
    return render('results.html')
