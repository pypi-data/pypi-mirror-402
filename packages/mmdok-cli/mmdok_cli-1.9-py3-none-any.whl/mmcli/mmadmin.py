import cmd2, json, os, re, pprint
from mmcli.mmclient import MMClient

#SERVER='https://veqw5068xl.execute-api.eu-north-1.amazonaws.com/prod'
SERVER='http://localhost:3008'
mmclient=MMClient(SERVER, SERVER)

def expand_refs(obj, base_path=None):
    if isinstance(obj, dict):
        return {k: expand_refs(v, base_path) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_refs(i, base_path) for i in obj]
    elif isinstance(obj, str) and obj.startswith('ref:'):
        ref_filename = obj[4:]
        ref_path = os.path.join(base_path if base_path is not None else '', ref_filename)
        try:
            with open(ref_path, 'r', encoding='utf-8') as rf:
                content = rf.read()
                # Remove only tabs, newlines, and carriage returns, but preserve spaces
                content = re.sub(r'[\t\n\r]+', '', content)
                return content
        except Exception as e:
            print(f'Error reading referenced file {ref_path}: {e}')
            return obj
    else:
        return obj

class MMAdmin(cmd2.Cmd):
    """
    Admin CLI for managing resources via REST API.
    """
    def do_create(self, line):
        """Create a new admin resource. Usage: create <resource> <json_file_path>"""
        try:
            parts = line.split(' ', 1)
            if len(parts) < 2:
                print('Usage: create <resource> <json_file_path>')
                return
            resource, file_path = parts
            file_path = file_path.strip()
            if not os.path.isfile(file_path):
                print(f'File not found: {file_path}')
                return
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                data = json.loads(content)
            except Exception:
                # Try newline-delimited JSON (ndjson)
                data = [json.loads(line) for line in content.splitlines() if line.strip()]
            # If it's a single object, wrap as list for uniform handling
            if isinstance(data, dict):
                data = [data]
            for idx, obj in enumerate(data):
                try:
                    obj = expand_refs(obj, base_path=os.path.dirname(file_path))
                    rsp = mmclient.admin_create(resource, obj)
                    print(f'Object {idx+1}: Status: {rsp.status_code}')
                    print(rsp.text)
                except Exception as e:
                    print(f'Object {idx+1}: Error: {e}')

        except Exception as e:
            print(f'Error: {e}')


    def do_read(self, line):
        """Read an admin resource. Usage: read <resource> [name]"""
        parts = line.split()
        if not parts:
            print('Usage: read <resource> [name]')
            return
        resource = parts[0]
        name = parts[1] if len(parts) > 1 else None
        rsp = mmclient.admin_read(resource, name)
        pprint.pprint(rsp.json())

    def do_update(self, line):
        """Update an admin resource. Usage: update <resource> <id> <json_file_path>"""
        try:
            parts = line.split(' ', 2)
            if len(parts) < 3:
                print('Usage: update <resource> <id> <json_file_path>')
                return
            resource, id, file_path = parts
            file_path = file_path.strip()
            if not os.path.isfile(file_path):
                print(f'File not found: {file_path}')
                return
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                data = json.loads(content)
            except Exception:
                # Try newline-delimited JSON (ndjson)
                data = [json.loads(line) for line in content.splitlines() if line.strip()]
            # If it's a single object, wrap as list for uniform handling
            if isinstance(data, dict):
                data = [data]
            for idx, obj in enumerate(data):
                try:
                    obj = expand_refs(obj, base_path=os.path.dirname(file_path))
                    rsp = mmclient.admin_update(resource, id, obj)
                    print(f'Object {idx+1}: Status: {rsp.status_code}')
                except Exception as e:
                    print(f'Object {idx+1}: Error: {e}')

        except Exception as e:
            print(f'Error: {e}')


    def do_delete(self, line):
        """Delete an admin resource. Usage: delete <resource> <id>"""
        parts = line.split()
        if len(parts) < 2:
            print('Usage: delete <resource> <id>')
            return
        resource, id = parts
        rsp = mmclient.admin_delete(resource, id)
        print(f'Status: {rsp.status_code} - {rsp.text}')

    def do_exit(self, line):
        """Exit the admin CLI."""
        return True

    def do_login(self, line):
        """Authenticate user via bankid, freja, apikey, or user-password."""
        import getpass
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

    def do_quit(self, line):
        """Exit the admin CLI."""
        return True



def run():
    MMAdmin().cmdloop()

def main():
    from mmcli import mmadmin
    mmadmin.run()

if __name__ == '__main__':
    MMAdmin().cmdloop()
