from lib import Handler, Type, Command, AuthError
from lib.utils import vk_keyboard
import vk_api
import time
import re
import requests
import base64
import io

class VkHandler(Handler):
    def __init__(self, token, secret):
        super().__init__(answer_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT, Type.VK_KEYBOARD},
                         arg_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT})
        self.secret = secret
        self.token = token
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.aliases = {}
        self.aliases.update(vk_keyboard.keyboard.aliases)
        self.aliases.update(vk_keyboard.admin_keyboard.aliases)

    def send(self, text, to, attachments=[], photos=[], documents=[], keyboard=None):
        _attachments = []
        attachments = attachments.copy()
        if photos or documents:
            upload = vk_api.VkUpload(self.vk)
            if photos:
                for photo in upload.photo_messages(photos=photos):
                    _attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
            for doc in documents:
                attachments.append(upload.document_message(doc, peer_id=to))

        for doc in attachments:
            d = doc[doc['type']]
            s = f"{doc['type']}{d['owner_id']}_{d['id']}"
            if 'access_key' in d:
                s += '_' + d['access_key']
            _attachments.append(s)

        if not text and not _attachments:
            text = 'empty'
        text = str(text)

        rd_id = vk_api.utils.get_random_id()
        self.vk.messages.send(peer_id=to, random_id=rd_id, message=text[:4000],
                              attachment=','.join(_attachments), keyboard=keyboard)
        if len(text) > 4000:
            time.sleep(0.4)
            self.send(text[4000:], to)

    def initial_parse(self, raw):
        if raw.get('type') != 'message_new':
            raise ValueError('wrong event type')
        if raw.get('secret') != self.secret:
            raise AuthError('wrong secret')

        msg = raw.get('object')
        if not msg:
            raise ValueError('no object')

        text = msg.get('text', '')
        text = self.aliases.get(text, text)
        parsed = self.parse_text(text)
        args = []
        if parsed['args']:
            args.append({'type': 'text', 'text': parsed['args']})

        for att in msg.get('attachments'):
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

        return {'action': parsed['action'],
                'ids': parsed['ids'],
                'room': parsed['room'],
                'args': args,
                'excepts': parsed['excepts'],
                'special': ['vk_photos']
                }

    def handle(self, command: Command):
        def key(x):
            s = x[0].split('.')
            return tuple(s[:-1]+[int(s[-1])])
        text = []
        photos = []
        documents = []
        room = command.room
        for rcid, answer in sorted(command.answers.items(), key=key):
            cid = rcid.split('.')[-1]
            _text = f"{cid if room != 'all' else rcid}: " if len(command.to) > 1 else ''
            _photos = []
            _documents = []
            keyboard = None
            if answer['status'] == 'ok':
                for pl in answer.get('payload', []):
                    _type = pl['type']
                    if _type == 'text':
                        _text += pl['text']
                    elif _type == 'photo':
                        _photos.append(io.BytesIO(base64.b64decode(pl['data'])))
                    elif _type == 'document':
                        f = io.BytesIO(base64.b64decode(pl['data']))
                        if pl.get('title'):
                            f.name = pl['title']
                        _documents.append(f)
                    elif _type == 'keyboard':
                        keyboard = pl['keyboard']
            elif answer['status'] == 'error':
                _text += f"ERROR: {answer.get('message')}"
            if _photos or _documents or keyboard:
                self.send(_text, command.sender, documents=_documents,
                          photos=_photos, keyboard=keyboard)
            else:
                text.append(_text)
                photos += _photos
                documents += _documents
        text = '\n'.join(text)
        if text or photos or documents:
            self.send(text, command.sender,
                      documents=documents, photos=photos)

    def handle_late(self, command: Command, cid: str):
        text = []
        photos = []
        documents = []
        room = command.room
        rcid = cid
        cid = rcid.split('.')[-1]
        _text = f"{cid if room != 'all' else rcid} (late): " if len(command.to) > 1 else ''
        _photos = []
        _documents = []
        answer = command.answers[rcid]
        if answer['status'] == 'ok':
            for pl in answer.get('payload', []):
                _type = pl['type']
                if _type == 'text':
                    _text += pl['text']
                elif _type == 'photo':
                    _photos.append(io.BytesIO(base64.b64decode(pl['data'])))
                elif _type == 'document':
                    f = io.BytesIO(base64.b64decode(pl['data']))
                    if pl.get('title'):
                        f.name = pl['title']
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
        text = '\n'.join(text)
        if text or photos or documents:
            self.send(text, command.sender,
                      documents=documents, photos=photos)

    def parse_text(self, text):
        r = re.fullmatch('(?:[рrкk](?P<room>(all|[0-9]+)) )?'
                         '(?P<ids>(?:(?:all|[0-9]+) )+)?'
                         '(?:except )?'
                         '(?P<excepts>(?<=except )(?:[0-9]+ ?)*)?'
                         '(?P<action>[a-z_]+)'
                         ' ?(?P<args>.*)',
                         text, flags=re.IGNORECASE)
        if r is None:
            raise SyntaxError('Синтаксис: id [except id] command [args]')

        room = r.group('room')
        if room is None:
            room = 'default'

        if r.group('ids') is not None:
            ids = r.group('ids').split()
        else:
            ids = []

        if r.group('excepts') is None:
            excepts = []
        else:
            excepts = r.group('excepts').split()

        action = r.group('action')
        action = action.casefold()

        args = r.group('args')

        return {'ids': ids, 'excepts': excepts, 'action': action, 'args': args, 'room': room}

    def get_sender(self, raw):
        return raw['object']['peer_id']
