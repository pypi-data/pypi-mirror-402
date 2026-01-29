def help(line):
    if 'audit' in line: audit()
    elif 'count' in line: count()
    elif 'download' in line: download()
    elif 'delete' in line: delete()
    elif 'login' in line: login()
    elif 'metadata' in line: metadata()
    elif 'register' in line: register()
    elif 'search' in line: search()
    elif 'types' in line: types()
    elif 'quit' in line: quit()
    elif 'update' in line: update()
    elif 'upload' in line: upload()
    elif 'view' in line: view()
    else: help_general()

def help_general():
    print('Commands:')
    print('   audit - get audit logs for a document')
    print('   count - count documents')
    print('download - download and show a document to file')
    print('  delete - deletes a document')
    print('   login - used to log in to the server')
    print('   metadata - used to log in to the server')
    print('register - register a user')
    print('  search - search documents')
    print('   types - prints available document types')
    print('    quit - exits the command loop')
    print("  update - updates document document's metadata")
    print('  upload - upload a document')
    print('    view - show a document in the webbrowser')
    print()
    print("For detailed help for a command type: 'help <command>'")

def audit():
    print('Get audit logs for a document')
    print('Paramameters:')
    print('  1. The document id')

def count():
    print('Number of stored documents')

def download():
    print('Download a document to the webbrowser')
    print('Paramameters:')
    print('  1. The document id')

def delete():
    print('Downloads a document')
    print('Paramameters:')
    print('  2. The document id')

def login():
    print('Signin to a server')
    print('Paramameters:')
    print('  1. The address of the server (default: https://xlr3egxhp3.execute-api.eu-north-1.amazonaws.com/dev)')
    print('  2. The user name')
    print('  3. The password')

def metadata():
    print('Get metadata for a document')
    print('Paramameters:')
    print('  1. The document id')

def register():
    print('Registers a user. The user will choose to either access only own documents ' + 
          '(Group=N) or share document within a company (Group=Y). ' +
          'In the former case the user has full permission the the documents ' +
          'and can sign in and use the MMDok immediately. In the latter the ' +
          'administrator of the group need to register the user for the company ' +
          'and assign permissions to the user.'  )
    print('Parameters:')
    print('  1. The username')
    print('  2. The password')
    print('  3. Has company. Valid answers Y (yes) and N (no)')

def search():
    print('Seach for documents. All parameters below are optional.')
    print('Paramameters:')
    print('  1. Filter. Metadata criteria in json format. For example. {"customerId":"ABC1"} ' + 
                        'to find all documents with a customerId staring with ABC1')
    print('  2. Sort. Sorting of the result where 1 is ascending and -1 is descending. ' + 
                'For example {"customerId":1} for ascending sorting on metadata field customer Id')
    print('  3. From. For server side paging. The number of hits in the search result to skip')
    print('  4. Number. Maximum number of documents in search result. Default=200')

def types():
    print('List all document types with all data that belongs to them, for example metadata fields.')

def update():
    print('Updates a documents metadata')
    print('Parameters:')
    print('1. Id. The id of the document to update')
    print('2. Metadata. Metadata fields to update, in json format.')

def upload():
    print('Uploads document content')
    print('Parameters:')
    print('  1. DocId. If left empty a new document is created, ' + 
            'otherwise the content of an old document with id=docid will be updated')
    print('  2. Document type. See types.')
    print('  3. Metadata. Metadata of the document in json format.')
    print('  4. Path. The local path to the document content.')

def view():
    print('Open a document in a browser, if the mimetype is supported')
    print('Paramameters:')
    print('  1. The document id')