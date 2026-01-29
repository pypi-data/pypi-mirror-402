import cmd2, getpass, json, os, pprint
from mmcli.helper import help
from mmcli.mmclient import MMClient

#SERVER='https://veqw5068xl.execute-api.eu-north-1.amazonaws.com/prod'
SERVER='http://localhost:3008'
mmclient=MMClient(SERVER, SERVER)

print(SERVER)

class MMCli(cmd2.Cmd):

    def do_exit(self,*args):
        return True

    def do_server(self, line):
        server = input('Server:')
        mmclient.set_server(server)

    def do_login_server(self, line):
        server = input('Login server:')
        mmclient.set_login_server(server)

    def do_register(self, line):
        mmclient.register()

    def do_login(self, line):
        tried_login = False
        success = False
        while (not tried_login):
            type = input('bankid|freja|apikey|user-password: ')
            tried_login = type in 'bfau'
            if (type.startswith('b')):
                ssn = input('     Ssn: ')
                success = mmclient.login_bankid(ssn)
            elif (type.startswith('f')):
                ssn = input('     Email: ')
                success = mmclient.login_freja(ssn)
            elif (type.startswith('a')):
                email = input('     Email: ')
                key = input('    Apikey: ')
                success = mmclient.login_apikey(email, key)
            elif (type.startswith('u')):
                user = input('   Email: ')
                pwd = getpass.getpass('Password: ')
                code = input('    Code: ')
                success = mmclient.login_usrpwd(user, pwd, code)
        if success: print('Login succeded')
        else: print('Login failed')

    def do_logout(self, line):
        success = mmclient.logout()
        if success: print('Logout succeded')
        else: print('Logout failed')

    def do_test_login(self, line):
        success, message = mmclient.test_auth()
        if success:
            print("Accessed protected resource as: " + message)
        else:
            print("Failed to access protected resource. Reason: " + message)

    def do_reset_password(self, line):
        email = input('   Email2:')
        success = mmclient.forgot_password(email)
        if not success:
            print('Failed to reset password')
            return
        password = getpass.getpass('Password:')
        code = input('Code:')
        success = mmclient.reset_password(email, password, code)
        if success: print('Password reset')
        else: print('Failed to reset password')

    def do_search(self, line):
        filter = input('Filter: ')
        sort = input('Sort: ')
        fr = input('From: ')
        to = input('Number: ')
        range = {}
        if fr.isnumeric() and to.isnumeric() and to>fr: 
            range = '{"from":' + fr + ', "to":' + to + '}'
        #filter = '{"doctype":"kunddokument", "kundnummer":"AAA"}'
        #sort = '{"kundnummer":1}'
        #range = '{"from":0, "to":3}'
        r = mmclient.search(filter, sort, range) #{"doctype":"kunddokument", "kundnummer":"AAA141414"}
        pprint.pprint(r.json())

    def do_freesearch(self, line):
        word = input('word: ')
        r = mmclient.freesearch(word) #{"doctype":"kunddokument", "kundnummer":"AAA141414"}
        pprint.pprint(r.json())

    def do_link(self, line):
        id = input('Source: ')
        ref = input('Target: ')
        rsp = mmclient.link(id, ref)
        print(rsp.text)

    def do_unlink(self, line):
        id = input('Source: ')
        ref = input('Target: ')
        rsp = mmclient.unlink(id, ref)
        print(rsp.text)

    def do_list(self, line):
        id = input('Source: ')
        rsp = mmclient.list(id)
        print(rsp.text)

    def do_lock(self, line):
        id = input('Id: ')
        rsp = mmclient.lock(id)
        print(rsp.text)

    def do_unlock(self, line):
        id = input('Id: ')
        rsp = mmclient.unlock(id)
        print(rsp.text)

    def do_getlock(self, line):
        id = input('Id: ')
        rsp = mmclient.getlock(id)
        print(rsp.text)

    def do_count(self, line):
        r = mmclient.count()
        pprint.pprint(r.json())
    
    def do_types(self, line):
        response = mmclient.types()
        pprint.pprint(response.json())

    def do_upload(self, line):
        print('Provide a document id if it is a new version, leave empty for new document')
        doctype = None
        id = input('Docid: ')
        if not id:
            doctype = input('Välj dokumenttyp: ')
        data = {}
        metadata = input('Metadata: ')
        path = input('Path to files: ').strip()
        data['metadata'] = metadata
        data['filename'] = os.path.basename(path)
        data['mimetype'] = 'application/pdf'
        if doctype:
            data['doctype'] = doctype
        print(data)
        isOk, r = mmclient.upload(data, path, id)    
        print(isOk)
        print(r) 

    def do_batch(self, line):
        documents = []
        doctype = input('Document type: ')
        directory = input('Source folder: ').strip()
        print('Insert the documents, finish with an empty file name: ')
        while True:
            filename = input('Filename: ')
            if not filename: break
            metadata = input('Metadata: ')
            documents.append({"file":filename, "metadata":json.dumps(metadata)})
        o = {"doctype":doctype, "directory":directory, "documents":documents}
        s = json.dumps(o)
        print(s)

    def do_view(self, line):
        id = input('Documentid: ')
        isOk, r = mmclient.view(id)
        if not isOk: print(r)

    def do_url(self, line):
        id = input('Documentid: ')
        isOk, r = mmclient.get_url(id)
        if isOk: print("URL to document: " + r)
        else: print(r)

    def do_view_version(self, line):
        id = input('Documentid: ')
        version = input('Version: ')
        isOk, r = mmclient.view(id, version)
        if not isOk: print(r)

    def do_download(self, line):
        id = input('Documentid: ')
        path = input('Path:' ) 
        pdf = path.lower().endswith('pdf')
        isOk, r = mmclient.download(id, path, pdf)
        if not isOk: print(r)

    def do_metadata(self, line):
        id = input('Documentid: ')
        isOk, r = mmclient.metadata(id)
        if not isOk: print(r)

    def do_audit(self, line):
        id = input('Documentid: ')
        isOk, r = mmclient.audit(id)
        if not isOk: print(r)

    def do_users(self, line):
        rsp = mmclient.users()
        print(rsp.content)

    def do_getprofile(self, line):
        r = mmclient.get_profile()
        print(r)

    def do_setprofile(self, line):
        profiles = input('Profiles:' )
        data = [profiles]
        isOk, r = mmclient.set_profile(data)
        if not isOk: print(r)

    def do_updateprofile(self, line):
        profiles = input('Profiles:' )
        data = [profiles]
        isOk, r = mmclient.update_profile(data)
        if not isOk: print(r)

    def do_update(self, line):
        id = input('Documentid: ')
        metadata = input('Metadata: ')
        rsp = mmclient.update(id, metadata)
        print(rsp.content)

    def do_delete(self, line):
        id = input('Documentid: ')
        rsp = mmclient.delete(id, True)
        print(rsp.content)  

    def do_delete_version(self, line):
        id = input('Documentid: ')
        rsp = mmclient.delete(id, False)
        print(rsp.content) 

    def do_comment(self, line):
        id = input('Documentid: ')
        comment = input('Comment: ')
        rsp = mmclient.comment(id, comment)
        print(rsp.text)

    def do_getcomment(self, line):
        id = input('Documentid: ')
        isOk, r = mmclient.get_comment(id)
        if not isOk: print("Failed to get comment")
        else: print(r)

    def do_listtemplates(self, line):
        """List templates for the current user. Optionally filter by doctype."""
        doctype = input('Doctype (optional): ')
        doctype = doctype if doctype.strip() else None
        response = mmclient.list_templates(doctype)
        try:
            pprint.pprint(response.json())
        except Exception:
            print(response.text)

    def do_createfromtemplate(self, line):
        """Create a document from a template and metadata."""
        template_name = input('Template name: ')
        metadata_str = input('Metadata (JSON): ')
        try:
            metadata = json.loads(metadata_str)
        except Exception as e:
            print(f"Invalid JSON for metadata: {e}")
            return
        response = mmclient.create_document_from_template(template_name, metadata)
        try:
            pprint.pprint(response.json())
        except Exception:
            print(response.text)

    def do_external_sign(self, line):
        """Sign a document by document ID. The signer shall be added to the document with do_add_signer."""
        document_id = input('Document ID: ')
        if not document_id.strip():
            print("Document ID is required")
            return
        mmclient.sign(document_id)
        print(f"Opening sign page for document {document_id} in browser...")

    def do_external_view(self, line):
        """View a document by document ID. The viewer shall be added to the document with do_add_viewer."""
        document_id = input('Document ID: ')
        if not document_id.strip():
            print("Document ID is required")
            return
        mmclient.view_external(document_id)
        print(f"Opening view page for document {document_id} in browser...")

    def do_add_signer(self, line):
        """Add a signer to a document."""
        document_id = input('Document ID: ')
        if not document_id.strip():
            print("Document ID is required")
            return
        email = input('Email: ')
        if not email.strip():
            print("Email is required")
            return
        message = input('Message: ')
        if not message.strip():
            print("Message is required")
            return
        response = mmclient.add_signer(document_id, email, message)
        if response.ok:
            try:
                pprint.pprint(response.json())
            except Exception:
                print(response.text)
        else:
            print(f"Failed to add signer. Status: {response.status_code}, Response: {response.text}")

    def do_add_viewer(self, line):
        """Add a viewer to a document."""
        document_id = input('Document ID: ')
        if not document_id.strip():
            print("Document ID is required")
            return
        email = input('Email: ')
        if not email.strip():
            print("Email is required")
            return
        response = mmclient.add_viewer(document_id, email)
        if response.ok:
            try:
                pprint.pprint(response.json())
            except Exception:
                print(response.text)
        else:
            print(f"Failed to add viewer. Status: {response.status_code}, Response: {response.text}")

    def do_signers(self, line):
        """View signers for a document."""
        document_id = input('Document ID: ')
        if not document_id.strip():
            print("Document ID is required")
            return
        response = mmclient.get_signers(document_id)
        if response.ok:
            try:
                pprint.pprint(response.json())
            except Exception:
                print(response.text)
        else:
            print(f"Failed to get signers. Status: {response.status_code}, Response: {response.text}")

    def do_viewers(self, line):
        """View viewers for a document."""
        document_id = input('Document ID: ')
        if not document_id.strip():
            print("Document ID is required")
            return
        response = mmclient.get_viewers(document_id)
        if response.ok:
            try:
                pprint.pprint(response.json())
            except Exception:
                print(response.text)
        else:
            print(f"Failed to get viewers. Status: {response.status_code}, Response: {response.text}")

    def do_help(self, line):
        
        help(line)

    def do_quit(self, line):
        return True

def run():
    MMCli().cmdloop()

def main():
    from mmcli import mmcli
    mmcli.run()

if __name__ == '__main__':
    MMCli(persistent_history_file="~/.mmcli_history").cmdloop()
