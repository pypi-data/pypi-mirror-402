import os
import sys
from datetime import datetime

import json
import requests
import six
import client.launcher as launcher
from prettytable import PrettyTable

from lib.utils import write_to_stdout

CONVERTED_FILE_FORMAT = {
    'txt': 'text/bitext',
    'tmx': 'application/x-tmx+xml',
    'json': 'application/json',
    'tsv': 'systran/tsv-edition-corpus',
    'jsonl': 'systran/json-edition-corpus'
}


class Resource:
    def __init__(self, options, auth):
        self.options = options
        self.auth = auth
        self.is_json = self.options.display == "JSON"

    def list(self):
        path = self.options.path
        if path and len(path.split(':')) != 2:
            raise ValueError('invalid path format: %s (should be storage:path)' % path)
        data = {'path': path, 'service': self.options.service}
        if "entity" in self.options and self.options.entity:
            data["entity"] = self.options.entity
        r = requests.get(os.path.join(self.options.url, "resource/list"), auth=self.auth, data=data)
        if r.status_code != 200:
            raise RuntimeError('incorrect result from \'resource/list\' service: %s' % r.text)
        result = r.json()
        if not self.is_json:
            if self.options.path is None or self.options.path == '':
                res = PrettyTable(['Pool', 'Entity', 'Name', 'Type', 'Description'])
                res.align["Name"] = "l"
                res.align["Type"] = "l"
                res.align["Pool"] = "l"
                res.align["Description"] = "l"
                for r in result:
                    entity = r["entity"] if r["entity"] != "CONF_DEFAULT" else ""
                    res.add_row([r["pool"], entity, r["name"] + ":", r["type"], r["description"]])
            elif self.options.aggr:
                res = PrettyTable(['Type', 'Path', 'Suffixes'])
                res.align["Path"] = "l"
                res.align["Suffixes"] = "l"
                files = {}
                if not isinstance(result, list):
                    result = [result]
                for k in result:
                    if type(k) == dict:
                        k = k['key']
                    if k.endswith('/'):
                        res.add_row(['dir', k, ''])
                    else:
                        suffix = ""
                        if k.endswith(".gz"):
                            suffix = ".gz"
                            k = k[:-3]
                        p = k.rfind(".")
                        if p != -1:
                            suffix = k[p:] + suffix
                            k = k[:p]
                        if k not in files:
                            files[k] = []
                        files[k].append(suffix)
                for k, v in six.iteritems(files):
                    res.add_row(['file', k, ', '.join(sorted(v))])
            else:
                is_corpus_resource = len(result) and isinstance(result, list)\
                                     and result[0].get('type') == 'corpusmanager'
                table_headers = ['Type', 'Path', 'LastModified']
                table_headers.append('Size (in sentences)') if is_corpus_resource\
                    else table_headers.append('Size (in bytes)')
                res = PrettyTable(table_headers)
                res.align["Path"] = "l"
                res.align["LastModified"] = "l"
                res.align["Size"] = "l"
                files = {}
                if not isinstance(result, list):
                    result = [result]
                for k in result:
                    meta = {}
                    if type(k) == dict:
                        meta = k
                        k = meta['key']
                    if k.endswith('/'):
                        size = meta['entries'] if 'entries' in meta else ''
                        res.add_row(['dir', k, '', size])
                    else:
                        date = ''
                        if 'last_modified' in meta:
                            date = datetime.fromtimestamp(meta['last_modified']).strftime(
                                "%m/%d/%Y, %H:%M:%S")
                        size = ''
                        if 'size' in meta:
                            size = meta['size']
                        elif 'entries' in meta:
                            size = meta['entries']
                        res.add_row(['file', k, date, size])
        else:
            res = result
        return res

    def get(self):
        params = {}
        if self.options.service is not None:
            params['service'] = self.options.service
        if self.options.format is not None:
            params['stream_format'] = CONVERTED_FILE_FORMAT.get(self.options.format, self.options.format)
        if self.options.output_dir:
            if not os.path.isdir(self.options.output_dir):
                raise RuntimeError(f'Not a directory: {self.options.output_dir}')
        if len(self.options.paths) > 1 and not self.options.output_dir:
            raise RuntimeError(f'Must provide output_dir if want to get multiple files')
        for path in self.options.paths:
            self._export_file({**params, 'path': path})
        sys.exit(0)

    def _export_file(self, params):
        r = requests.get(os.path.join(self.options.url, "resource/file"),
                         auth=self.auth, params=params)
        if r.status_code != 200:
            raise RuntimeError('incorrect result from \'resource/file\' service: %s' % r.text)
        if self.options.output_dir:
            content = r.content.decode('utf-8')
            filename = self.__get_filename(params['path'])
            with open(os.path.join(self.options.output_dir, filename), 'w') as output_file:
                output_file.write(content)
            launcher.LOGGER.info(f"{filename} file download completed")
            return
        for chunk in r.iter_content(chunk_size=512 * 1024):
            if chunk:
                write_to_stdout(chunk)

    def __get_filename(self, path):
        filepath = path.split('/')[-1]
        if not self.options.format:
            return filepath
        basename = filepath[:filepath.rfind('.')] if '.' in filepath else filepath
        extension = self.options.format if self.options.format in CONVERTED_FILE_FORMAT else 'txt'
        if extension == 'json-edition':
            extension = 'json'
        return f'{basename}.{extension}'

    def upload(self):
        payload = {'path': self.options.storage_path}
        if self.options.service is not None:
            payload['service'] = self.options.service
        for file_path in self.options.files:
            if not os.path.exists(file_path):
                raise ValueError("'%s' file does not exist" % file_path)
            basename = os.path.basename(file_path)
            file_data = [('file', (basename, open(file_path, 'rb')))]
            self._upload_file(payload, file_data, basename)
        sys.exit(0)

    def _upload_file(self, payload, file_data, file_name):
        r = requests.post(os.path.join(self.options.url, "resource/upload"),
                          auth=self.auth, data=payload, files=file_data)
        if r.status_code != 200:
            raise RuntimeError('incorrect result from \'resource/upload\' service: %s' % r.text)
        launcher.LOGGER.info(f"{file_name} file upload completed")

    def edit(self):
        if not self.options.properties:
            payload = {'path': self.options.storage_path}
            if self.options.service is not None:
                payload['service'] = self.options.service

            if not os.path.exists(self.options.path):
                raise ValueError("'%s' file does not exist" % self.options.path)
            basename = os.path.basename(self.options.path)
            file_data = [('corpus', (basename, open(self.options.path, 'rb')))]
            result = self._edit_files(payload, file_data, basename)
        else:
            payload = {
                "path": self.options.storage_path,
                "filename": self.options.filename if self.options.filename else None,
                "license": self.options.license if self.options.license else None,
                "publisher": self.options.publisher if self.options.publisher else None,
                "source": self.options.source if self.options.source else None,
                "genre": self.options.genre if self.options.genre else None,
                "domain": self.options.domain if self.options.domain else None,
                "notes": self.options.notes if self.options.notes else None
            }
            result = self._edit_properties(payload)
        return result

    def _edit_files(self, payload, file_data, basename):
        r = requests.post(os.path.join(self.options.url, "search/regex/bulk_update"),
                          auth=self.auth, data=payload, files=file_data)
        if r.status_code != 200:
            raise RuntimeError('incorrect result from \'resource/edit\' service: %s' % r.text)
        launcher.LOGGER.info(f"{basename} file edit completed")

        table_headers = ['Type', 'Size']
        res = PrettyTable(table_headers)
        res.align["Path"] = "l"
        res.align["Size"] = "l"
        for k, v in r.json().items():
            res.add_row([k, v])
        return res

    def _edit_properties(self, payload):
        r = requests.post(os.path.join(self.options.url, "resource/edit/properties"),
                          auth=self.auth, data=payload)
        if r.status_code != 200:
            raise RuntimeError('incorrect result from \'resource/edit/properties\' service: %s' % r.text)
        launcher.LOGGER.info("Corpus property editing completed")
        sys.exit(0)

    def execute_command(self):
        result = None
        if self.options.subcmd == "list":
            result = self.list()
        if self.options.subcmd == "get":
            result = self.get()
        if self.options.subcmd == "upload":
            self.upload()
        if self.options.subcmd == "edit":
            result = self.edit()
        return result
