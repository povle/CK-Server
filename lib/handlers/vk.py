from .. import Handler, Type, actions, Command
from vk_api.upload import VkUpload
import vk_api
import time
import re
import requests
import base64
import io

class VkHandler(Handler):
    def __init__(self, token, secret):
        super().__init__(answer_types={Type.TEXT, Type.PHOTO, Type.Document},
                         arg_types={Type.TEXT, Type.PHOTO, Type.Document})
        self.secret = secret
        self.token = token
        self.actions = actions
        self.builtins = {'help': self.help}
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()

    def send(self, text, to, attachments=[], photos=[], documents=[]):
        _attachments = []
        for doc in attachments:
            d = doc[doc['type']]
            s = f"{doc['type']}{d['owner_id']}_{d['id']}"
            if 'access_key' in d:
                s += '_' + d['access_key']
            _attachments.append(s)

        if photos or documents:
            upload = vk_api.VkUpload(self.vk_session)
            if photos:
                for photo in upload.photo_messages(photos=photos):
                    _attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
            for doc in documents:
                _attachments.append(VkUpload(self.vk).document_wall(doc, group_id=self.gr_id))

        if not text and not _attachments:
            text = 'empty'
        text = str(text)

        rd_id = vk_api.utils.get_random_id()
        self.vk.messages.send(peer_id=to, random_id=rd_id, message=text[:4000],
                              attachment=','.join(_attachments))
        if len(text) > 4000:
            time.sleep(0.4)
            self.send(text[4000:], to)

    def parse(self, raw):
        if raw.get('type') != 'message_new':
            raise ValueError('wrong event type')
        if raw.get('secret') != self.secret:
            raise ValueError('wrong secret')

        msg = raw.get('object')
        if not msg:
            raise ValueError('no object')

        text = msg.get('text')
        if not text:
            raise SyntaxError

        parsed = self.parse_text(text)
        args = []
        if parsed['args']:
            args.append({'type': 'text', 'text': parsed['args']})

        for att in msg.attachments:
            if att['type'] == 'photo':
                _type = 'photo'
                photo = att['photo']
                url = max(photo['sizes'], key=lambda x: x['width']*x['height'])['url']
                title = None
            elif att['type'] == 'doc':
                _type = 'document'
                url = att['doc']['url']
                title = att['doc']['title']
            data = base64.b64encode(requests.get(url).content)
            _dict = {'type': _type, 'data': data}
            if title:
                _dict.update({'title': title})
            args.append(_dict)

        if parsed['action'] in self.builtins:
            command = Command(self, None, msg.peer_id, [-1], args)
            command.add_answer(-1, self.builtins[parsed['action']](args))
        else:
            action = [x for x in self.actions if x.name == parsed['action']]
            if action:
                action = action[0]
            else:
                return
            command = Command(self, action, msg.peer_id, parsed['ids'], args)
        return command

    def handle(self, command: Command):
        text = []
        photos = []
        documents = []
        for answer in sorted(command.answers, key=lambda x: x['comp_id']):
            _text = f"answer['comp_id']: " if len(command.to) > 1 else ''
            _photos = []
            _documents = []
            if answer['status'] == 'ok':
                for pl in answer.get('payload', []):
                    _type = pl['type']
                    if _type == 'text':
                        _text += pl['text']
                    elif _type == 'photo':
                        _photos.append(io.BytesIO(base64.b64decode(pl['data'])))
                    elif _type == 'document':
                        f = io.BytesIO(base64.b64decode(pl['data']))
                        f.name = pl.get('title', '')
                        _documents.append(f)
            elif answer['status'] == 'error':
                _text += f"ERROR: {answer.get('message')}"
            if _photos or _documents:
                self.send(_text, command.sender,
                          documents=_documents, photos=_photos)
            else:
                text.append(_text)
                photos += _photos
                documents += _documents
        if text or photos or documents:
            self.send(text, command.sender,
                      documents=documents, photos=photos)

    def parse_text(text):
        r = re.fullmatch('(?P<ids>(?:(?:all|[0-9]+) )+)?'
                         '(?:except )?'
                         '(?P<excepts>(?<=except )(?:[0-9]+ ?)*)?'
                         '(?P<action>[a-z_]+)'
                         ' ?(?P<args>.*)',
                         text, flags=re.IGNORECASE)
        if r is None:
            raise SyntaxError('Синтаксис: id [except id] command [args]')

        if r.group('ids') is not None:
            ids = r.group('ids').split()
            ids = [id.casefold() for id in ids]

        if r.group('excepts') is None:
            excepts = []
        else:
            excepts = r.group('excepts').split()

        action = r.group('action')
        action = action.casefold()

        args = r.group('args')

        return {'ids': ids, 'excepts': excepts, 'action': action, 'args': args}

    #------------------------------BUILTINS------------------------------------
    def help(self, command):
        message = ''
        text = ''
        for arg in command.args:
            if arg['type'] == 'text':
                text += arg['text']
        for f in self.actions:
            doc = f.description
            if doc is not None and (text != '-a' and not f.admin_only)\
                    or (text == '-a' and f.admin_only):
                message += f'•{f.name} - {doc}\n'
        return {'comp_id': None,
                'command_id': command.id,
                'timestamp': time.time(),
                'status': 'ok',
                'payload': [{'type': 'text',
                            'text': message}]
                }
