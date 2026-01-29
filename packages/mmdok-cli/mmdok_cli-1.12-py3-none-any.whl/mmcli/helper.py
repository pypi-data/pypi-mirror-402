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
    elif 'freesearch' in line: freesearch()
    elif 'link' in line: link()
    elif 'unlink' in line: unlink()
    elif 'list' in line: list()
    elif 'lock' in line: lock()
    elif 'unlock' in line: unlock()
    elif 'getlock' in line: getlock()
    elif 'server' in line: server()
    elif 'login_server' in line: login_server()
    elif 'logout' in line: logout()
    elif 'test_login' in line: test_login()
    elif 'reset_password' in line: reset_password()
    elif 'url' in line: url()
    elif 'view_version' in line: view_version()
    elif 'users' in line: users()
    elif 'getprofile' in line: getprofile()
    elif 'setprofile' in line: setprofile()
    elif 'updateprofile' in line: updateprofile()
    elif 'delete_version' in line: delete_version()
    elif 'comment' in line: comment()
    elif 'getcomment' in line: getcomment()
    elif 'listtemplates' in line: listtemplates()
    elif 'createfromtemplate' in line: createfromtemplate()
    elif 'external_sign' in line: external_sign()
    elif 'external_view' in line: external_view()
    elif 'add_signer' in line: add_signer()
    elif 'add_viewer' in line: add_viewer()
    elif 'signers' in line: signers()
    elif 'viewers' in line: viewers()
    elif 'batch' in line: batch()
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
    print('freesearch - free text search documents')
    print('    link - link a document to another document')
    print('  unlink - unlink a document from another document')
    print('    list - list links for a document')
    print('    lock - lock a document')
    print('  unlock - unlock a document')
    print(' getlock - get lock status for a document')
    print('  server - set server base URL')
    print('login_server - set login server base URL')
    print('  logout - log out from server')
    print('test_login - test current authentication')
    print('reset_password - reset password via code')
    print('     url - get a share URL to a document')
    print('view_version - view a specific version of a document')
    print('   users - list users')
    print('getprofile - get current user profile')
    print('setprofile - set user profile')
    print('updateprofile - update user profile')
    print('delete_version - delete a specific version of a document')
    print('  comment - add a comment to a document')
    print('getcomment - get comment for a document')
    print('listtemplates - list available templates')
    print('createfromtemplate - create a document from a template')
    print('external_sign - open external signing page for a document')
    print('external_view - open external view page for a document')
    print('add_signer - add a signer to a document')
    print('add_viewer - add a viewer to a document')
    print('  signers - list signers of a document')
    print('  viewers - list viewers of a document')
    print('   batch - prepare a batch upload payload')
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
def freesearch():
    print('Free text search for documents')
    print('Parameters:')
    print('  1. Word. The text to search for')

def link():
    print('Link two documents')
    print('Parameters:')
    print('  1. Source document id')
    print('  2. Target document id')

def unlink():
    print('Unlink two documents')
    print('Parameters:')
    print('  1. Source document id')
    print('  2. Target document id')

def list():
    print('List links for a document')
    print('Parameters:')
    print('  1. Source document id')

def lock():
    print('Lock a document')
    print('Parameters:')
    print('  1. Document id')

def unlock():
    print('Unlock a document')
    print('Parameters:')
    print('  1. Document id')

def getlock():
    print('Get lock status for a document')
    print('Parameters:')
    print('  1. Document id')

def server():
    print('Set the base server URL for API calls')
    print('Parameters:')
    print('  1. Server URL')

def login_server():
    print('Set the base server URL for authentication')
    print('Parameters:')
    print('  1. Login server URL')

def logout():
    print('Logout from the current session')

def test_login():
    print('Test access to a protected resource using current authentication')

def reset_password():
    print('Reset a user password')
    print('Parameters:')
    print('  1. Email')
    print('  2. New password (after receiving reset code)')
    print('  3. Reset code')

def url():
    print('Get a share URL to a document')
    print('Parameters:')
    print('  1. Document id')

def view_version():
    print('View a specific version of a document')
    print('Parameters:')
    print('  1. Document id')
    print('  2. Version')

def users():
    print('List users')

def getprofile():
    print('Get current user profile')

def setprofile():
    print('Set user profile')
    print('Parameters:')
    print('  1. Profiles (comma separated or JSON array)')

def updateprofile():
    print('Update user profile')
    print('Parameters:')
    print('  1. Profiles (comma separated or JSON array)')

def delete_version():
    print('Delete a specific version of a document')
    print('Parameters:')
    print('  1. Document id')

def comment():
    print('Add a comment to a document')
    print('Parameters:')
    print('  1. Document id')
    print('  2. Comment text')

def getcomment():
    print('Get comment for a document')
    print('Parameters:')
    print('  1. Document id')

def listtemplates():
    print('List templates for the current user. Optionally filter by doctype')
    print('Parameters:')
    print('  1. Doctype (optional)')

def createfromtemplate():
    print('Create a document from a template')
    print('Parameters:')
    print('  1. Template name')
    print('  2. Metadata (JSON)')

def external_sign():
    print('Open external signing page for a document')
    print('Parameters:')
    print('  1. Document id')

def external_view():
    print('Open external view page for a document')
    print('Parameters:')
    print('  1. Document id')

def add_signer():
    print('Add a signer to a document')
    print('Parameters:')
    print('  1. Document id')
    print('  2. Email')
    print('  3. Message')

def add_viewer():
    print('Add a viewer to a document')
    print('Parameters:')
    print('  1. Document id')
    print('  2. Email')

def signers():
    print('List signers for a document')
    print('Parameters:')
    print('  1. Document id')

def viewers():
    print('List viewers for a document')
    print('Parameters:')
    print('  1. Document id')

def batch():
    print('Prepare a batch upload payload with filenames and metadata')
