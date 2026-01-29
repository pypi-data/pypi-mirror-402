import mimetypes
import os
import pprint
import requests
import time
import urllib
import webbrowser


class MMClient:

    def admin_create(self, resource, data):
        url = f"{self.server}/admin/{resource}"
        print("calling:" + url)
        response = self._send_post(url, data)
        return response

    def admin_read(self, resource, name=None):
        url = f"{self.server}/admin/{resource}"
        if name:
            url += f"/{name}"
        response = self._send_get(url)
        return response

    def admin_update(self, resource, name, data):
        url = f"{self.server}/admin/{resource}/{name}"
        response = self._send_put(url, data)
        return response

    def admin_delete(self, resource, name):
        url = f"{self.server}/admin/{resource}/{name}"
        response = self._send_delete(url)
        return response

    def __init__(self, server, login_server):
        self.server = server
        self.login_server = login_server
        self.refresh_token = 'No token'
        self.access_token = 'No token'

    def set_server(self, server):
        self.server = server

    def set_login_server(self, login_server):
        self.login_server = login_server
        
    def _login(self, response):
        #headers = response.headers
        if response.status_code == 200:
            j = response.json()
            self.access_token = j['tokens']['access_token']
            self.refresh_token = j['tokens']['refresh_token']
            print("AccessToken:" + self.access_token)
            print("RefreshToken:" + self.refresh_token) 
            if 'company' in j: 
                self.company = j['company']
            return True
        else:
            print(response.text)
            return False
        
    def _refresh(self):
        response = requests.post(self.login_server + '/refresh', 
                          headers={'Authorization': 'Bearer ' + self.refresh_token})
        if response.status_code == 200:
            j = response.json()
            self.access_token = j['tokens']['access_token']
            self.refresh_token = j['tokens']['refresh_token']
        else:
            print("Could not refresh" + str(response.status_code))
        
    def _send_get(self, url, resend=True):
        response = requests.get(url, headers={'Authorization': 'Bearer ' + self.access_token})
        if response.status_code==401 and resend:
            self._refresh()
            return self._send_get(url, False)
        else:
            return response

    def _send_post(self, url, data={}, resend=True):
        response = requests.post(url, json=data, 
                                 headers={'Authorization': 'Bearer ' + self.access_token})
        if response.status_code==401 and resend:
            self._refresh()
            return self._send_post(url, data, False)
        else:
            return response
        
    def _send_put(self, url, data={}, resend=True):
        response = requests.put(url, json=data, 
                                headers={'Authorization': 'Bearer ' + self.access_token})
        if response.status_code==401 and resend:
            self._refresh()
            return self._send_put(url, data, False)
        else:
            return response
        
    def _send_delete(self, url, resend=True):
        response = requests.delete(url,
                                   headers={'Authorization': 'Bearer ' + self.access_token})
        if response.status_code==401 and resend:
            self._refresh()
            return self._send_delete(url, False)
        else:
            return response
        
    def register(self):
        webbrowser.open(self.login_server + '/register')
            
    def login_bankid(self, ssn):
        response = requests.post(self.login_server + '/login', json={"ssn": ssn, "type":"bankid"})
        return self._login(response)

    def login_freja(self, ssn):
        response = requests.post(self.login_server + '/login', json={"email": ssn, "type":"freja"})
        j = response.json()
        if response.status_code == 202:
            return self._poll(ssn, "freja", j['token'])
        else:
            return False
        
    def _poll(self, email, type, token):
        url = self.login_server + '/poll'
        time.sleep(1)
        print(url)
        response = requests.post(url, json={"email": email, "type": type}, 
                                 headers={"Authorization": "Bearer " + token})
        j = response.json()
        if response.status_code == 202:
            new_token = j['token']
            return self._poll(email, type, new_token)
        elif response.status_code == 200:
            return self._login(response)
        else:
            return False
          
    def login_usrpwd(self, email, password, code):
        response = requests.post(self.login_server + '/login', json={"email": email, 
                                                               "password": password, 
                                                               "code": code,
                                                               "type": "password"})
        return self._login(response)
    
    def login_apikey(self, email, apikey):
        response = requests.post(self.login_server + '/login', json={"type": "apikey", 
                                                                     "email": email, 
                                                                     "apikey": apikey})
        return self._login(response)
    
    def logout(self):
        url = self.login_server + '/logout'
        response = requests.post(url,  
                                 headers={'Authorization': 'Bearer ' + self.refresh_token})
        return response.status_code == 200
        
        
    def test_auth(self):
        r = self._send_get(self.login_server + '/private')
        if r.status_code==200:
            j = r.json()
            if 'email' in j:
                email = j['email']
                return True, email
            else:
                return False, "Could not identify user"
        else:
            return False, "Not permitted"

    def types(self):
        return self._send_get(self.server + '/types')

    """
    Example:
        filter={"doctype":"kunddokument", "kundnummer":"AAA"}
        sort: {"kundnummer": 1}
        range: {"from":100, "to:200"}
    """
    def search(self, filter=None, sort=None, range=None):
        if not filter:
            filter = {}
        if not sort:
            sort = {} 
        if not range:
            range = {}
        params = urllib.parse.urlencode({'filter': filter, 'sort': sort, 'range': range}) # json(), status_code
        print(params)
        return self._send_get(self.server + '/documents?' + params)      

    def freesearch(self, word):
        params = urllib.parse.urlencode({'word': word}) 
        print(params)
        return self._send_get(self.server + '/documents?' + params)             

    def upload(self, data, path, id):
        url = self.server + '/document'
        if id: url += '/' + id
        response = self._send_post(url, data=data)
        response = response.json()
        if 'url' not in response: 
            return False, response
        url = response['url']
        fields = response.get('fields', None)
        id = response['id']
        method = response['method']
        mimetype = mimetypes.guess_type(path)
        if len(mimetype)<0: mimetype='application/octet-stream' 
        with open(path, 'rb') as f:
            if method == 'post':
                files = {'file': (path, f, mimetype),
                 'Content-Disposition': 'form-data; name="files"',
                 'Content-Type': mimetype}
                response = requests.post(url, files=files, data=fields)
            elif method == 'put':
                response = requests.put(url, headers={"Content-Type": "application/pdf"}, data=f.read())
            if not response.ok:
                return False, ('Failed upload to Minio. Reason: ' +
                  response.reason + '. Text:' + response.text)

            return True, id

    def download(self, id, path, pdf):
        url = self.server + '/document/' + id + '?isAttachment=true'
        if (pdf): url += '&pdf=true'
        response = self._send_get(url)
        if not response.ok:
            return False, ('Get document failed. Reason: ' +
                  response.reason + '. Text:' + response.text)
        response = requests.get(response.json()['url'])
        open(path, "wb").write(response.content)
        return True, "OK"

    def view(self, id, version=None):
        url = self.server + '/document/' + id + '?isAttachment=false'
        if version:
            url += '?version=' + version
        response = self._send_get(url)
        if not response.ok:
            return False, ('Get document failed. Reason: ' +
                  response.reason + '. Text:' + response.text)
        resp_json = response.json()
        # If response contains a URL, open it
        if 'url' in resp_json:
            webbrowser.open(resp_json['url'])
            return True, "OK"
        # If response contains a PDF buffer, decode and open it
        if 'buffer' in resp_json and resp_json.get('contentType') == 'application/pdf':
            pdf_path = os.path.join(os.path.dirname(__file__), 'tmp_viewed.pdf')
            with open(pdf_path, 'wb') as f:
                f.write(bytes(resp_json['buffer']['data']))
            webbrowser.open(f'file://{os.path.abspath(pdf_path)}')
            return True, "OK"
        return False, "No viewable content (no url or PDF buffer) in response."

    def get_url(self, id):
        url = self.server + '/document/' + id + '?share=true'
        response = self._send_get(url)
        if not response.ok:
            return False, ('Get document failed. Reason: ' +
                  response.reason + '. Text:' + response.text)
        resp_json = response.json()
        # If response contains a URL, open it
        if 'url' in resp_json:
            return True, resp_json['url']
        else:
            return False, "No URL in response"

    def metadata(self, id):
        url = self.server + '/document/' + id + '?type=metadata'
        response = self._send_get(url)
        if not response.ok:
            return False, ('Get metadata failed. Reason: ' +
                  response.reason + '. Text:' + response.text)
        pprint.pprint(response.json()['metadata'])
        return True, "OK"

    def audit(self, id):
        url = self.server + '/document/' + id + '?type=audit'
        response = self._send_get(url)
        if not response.ok:
            return False, ('Get audits failed. Reason: ' +
                  response.reason + '. Text:' + response.text)
        pprint.pprint(response.json()['audit'])
        return True, "OK"

    def update(self, id, metadata):
        data = {}
        data['metadata'] = metadata
        rsp = self._send_put(self.server + "/document/" + id, data)
        return rsp
    
    def link(self, id, ref):
        data = {}
        data['ref'] = ref
        rsp = self._send_put(self.server + "/document/link/" + id, data)
        return rsp

    def unlink(self, id, ref):
        data = {}
        data['ref'] = ref
        rsp = self._send_put(self.server + "/document/unlink/" + id, data)
        return rsp

    def list(self, id):
        rsp = self._send_get(self.server + "/document/link/" + id)
        return rsp
    
    def lock(self, id):
        rsp = self._send_put(self.server + "/document/lock/" + id)
        return rsp

    def unlock(self, id):
        rsp = self._send_put(self.server + "/document/unlock/" + id)
        return rsp
    
    def getlock(self, id):
        rsp = self._send_get(self.server + "/document/lock/" + id)
        return rsp
    
    def users(self):
        rsp = self._send_get(self.server + "/users")
        return rsp
    
    def get_profile(self):
        rsp = self._send_get(self.server + '/user/profile')
        return rsp.text
        
    def set_profile(self, profiles):
        rsp = self._send_post(self.server + '/user/profile', data=profiles)
        if not rsp.ok:
            return False, rsp.text
        return True, "Saved profile"
    
    def update_profile(self, profiles):
        rsp = self._send_put(self.server + '/user/profile', data=profiles)
        if not rsp.ok:
            return False, rsp.text
        return True, "Saved profile"

    def delete(self, id, isFullDelete):
        url = self.server
        if isFullDelete: url += "/document/"
        else: url += "/version/"
        url += id
        print(url) 
        rsp = self._send_delete(url)
        return rsp

    def count(self):
        url = self.server + '/count'
        return self._send_get(url)

    def comment(self, id, comment):
        rsp = self._send_post(self.server + "/document/" + id + "/comment", data={"comment": comment})
        return rsp

    def get_comment(self, id):
        url = self.server + '/document/' + id + '/comment'
        rsp = self._send_get(url)
        if not rsp.ok:
            return False, rsp.text
        return True, rsp.text

    def list_templates(self, doctype=None):
        """
        List templates for the current user. Optionally filter by doctype.
        :param doctype: Optional document type to filter templates.
        :return: Response object from the server.
        """
        url = f"{self.server}/template"
        if doctype:
            url += f"?doctype={doctype}"
        response = self._send_get(url)
        return response

    def create_document_from_template(self, templateName, metadata):
        """
        Create a document from a template and metadata.
        :param templateName: Name of the template to use.
        :param metadata: Metadata dictionary for the new document.
        :return: Response object from the server.
        """
        url = f"{self.server}/template/document"
        data = {"templateName": templateName, "metadata": metadata}
        response = self._send_post(url, data)
        return response
    
    def sign(self, document_id):
        """
        Open the sign page for a document in the browser.
        :param document_id: ID of the document to sign.
        """
        encoded_id = urllib.parse.quote(document_id)
        url = f"{self.server}/sign?documentId={encoded_id}"
        webbrowser.open(url)
    
    def view_external(self, document_id):
        """
        Open the view page for a document in the browser.
        :param document_id: ID of the document to view.
        """
        encoded_id = urllib.parse.quote(document_id)
        url = f"{self.server}/view?documentId={encoded_id}"
        webbrowser.open(url)
    
    def add_signer(self, document_id, email, message):
        """
        Add a signer to a document by sending a POST request to /add-signer endpoint.
        :param document_id: ID of the document.
        :param email: Email of the signer to add.
        :param message: Message to send with the signer invitation.
        :return: Response object from the server.
        """
        url = f"{self.server}/add-signer"
        data = {"documentId": document_id, "email": email, "message": message}
        response = self._send_post(url, data)
        return response
    
    def add_viewer(self, document_id, email):
        """
        Add a viewer to a document by sending a POST request to /add-viewer endpoint.
        :param document_id: ID of the document.
        :param email: Email of the viewer to add.
        :return: Response object from the server.
        """
        url = f"{self.server}/add-viewer"
        data = {"documentId": document_id, "email": email}
        response = self._send_post(url, data)
        return response
    
    def get_signers(self, document_id):
        """
        Get the list of signers for a document.
        :param document_id: ID of the document.
        :return: Response object from the server.
        """
        url = f"{self.server}/signers?documentId={urllib.parse.quote(document_id)}"
        response = self._send_get(url)
        return response
    
    def get_viewers(self, document_id):
        """
        Get the list of viewers for a document.
        :param document_id: ID of the document.
        :return: Response object from the server.
        """
        url = f"{self.server}/viewers?documentId={urllib.parse.quote(document_id)}"
        response = self._send_get(url)
        return response
    
    def dump(self, response):
        print(response.request.method)
        print(response.request.url)
        print(response.request.body)
        print(response.request.headers)
