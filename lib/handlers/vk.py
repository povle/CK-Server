from lib import Handler, Type, Command, AuthError
from lib.utils import vk_keyboard, checkpw
from collections import defaultdict
import vk_api
import time
import re
import requests
import io
import json

class VkHandler(Handler):
    def __init__(self, token, secret, default_room):
        super().__init__(answer_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT, Type.VK_KEYBOARD},
                         arg_types={Type.TEXT, Type.PHOTO, Type.DOCUMENT})
        self.secret = secret
        self.token = token
        self.default_room = default_room
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.aliases = {}
        self.aliases.update(vk_keyboard.keyboard.aliases)
        self.aliases.update(vk_keyboard.admin_keyboard.aliases)
        self.last = defaultdict(lambda: None)

    def send(self, text, to, attachments=[], photos=[], documents=[], _attachments=[], keyboard=None, template=None):
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

        if isinstance(template, dict):
            template = json.dumps(template)

        rd_id = vk_api.utils.get_random_id()
        self.vk.messages.send(peer_id=to, random_id=rd_id, message=text[:4000],
                              attachment=','.join(_attachments), keyboard=keyboard,
                              template=template)
        if len(text) > 4000:
            time.sleep(0.4)
            self.send(text[4000:], to)

    def initial_parse(self, raw):
        if raw.get('type') != 'message_new':
            raise ValueError('wrong event type')
        if not checkpw(raw.get('secret', '').encode('utf8'), self.secret):
            raise AuthError('wrong secret')

        msg = raw.get('object', {}).get('message')
        if not msg:
            raise ValueError('no object')
        carousel = raw.get('object', {}).get('client_info', {}).get('carousel', False)

        text = msg.get('text', '')
        _id = self.get_sender(raw)
        if text == '!!' and self.last[_id] is not None:
            msg = self.last[_id]
            text = msg.get('text', '')
        else:
            self.last[_id] = msg
        text = self.aliases.get(text, text)
        parsed = self.parse_text(text)
        args = []
        if parsed['args']:
            args.append({'type': 'text', 'text': parsed['args']})

        for att in msg.get('attachments'):
            _dict = None
            if att['type'] == 'photo':
                photo = att['photo']
                _dict = {'type': 'vk_attachment',
                         'content': 'photo',
                         'attachment': f"photo{photo['owner_id']}_{photo['id']}",
                         'raw': photo}
            elif att['type'] == 'doc':
                d = att['doc']
                s = f"doc{d['owner_id']}_{d['id']}"
                if 'access_key' in d:
                    s += '_' + d['access_key']
                _dict = {'type': 'vk_attachment',
                         'content': 'document',
                         'attachment': s,
                         'raw': d}
            if _dict:
                args.append(_dict)

        special = {'vk_upload': {}}
        if carousel and (len(parsed['ids']) > 1 or 'all' in parsed['ids']):
            special['photo_processing'] = {'aspect_ratio': [13, 8], 'max_dim': 1536}

        return {'action': parsed['action'],
                'ids': parsed['ids'],
                'room': parsed['room'],
                'args': args,
                'excepts': parsed['excepts'],
                'special': special
                }

    def handle(self, command: Command, late_cid=None, carousel=True):
        def key(x):
            s = x[0].split('.')
            return tuple(s[:-1]+[int(s[-1])])

        if 'photo_processing' not in command.special:
            carousel = False

        text = []
        photos = []
        documents = []
        attachments = []
        carousel_elements = []
        room = command.room
        for rcid, answer in sorted(command.answers.items(), key=key):
            if late_cid and rcid != late_cid:
                continue
            cid = rcid.split('.')[-1]
            answer_room = rcid.split('.')[-2]

            _prefix = f"{cid if room != 'all' else rcid}" if len(command.to) > 1 else ''
            if late_cid:
                _prefix += ' (late)'
            if _prefix:
                _prefix += ': '
            _text = ''

            _photos = []
            _documents = []
            _attachments = []
            _photo_attachments = []
            keyboard = None
            if answer['status'] == 'ok':
                for pl in answer.get('payload', []):
                    _type = pl['type']
                    if _type == 'text':
                        _text += pl['text']
                    elif _type == 'photo':
                        _photos.append(io.BytesIO(pl['data']))
                    elif _type == 'document':
                        f = io.BytesIO(pl['data'])
                        if pl.get('title'):
                            f.name = pl['title']
                        _documents.append(f)
                    elif _type == 'keyboard':
                        keyboard = pl['keyboard']
                    elif _type == 'vk_attachment':
                        _attachments.append(pl['attachment'])
                        if pl.get('content') == 'photo':
                            _photo_attachments.append(pl['attachment'].replace('photo', ''))
            elif answer['status'] == 'error':
                _text += f"ERROR: {answer.get('message')}"

            if carousel and _photo_attachments and len(command.answers) > 1 and not late_cid:
                for att in _photo_attachments:
                    command_prefix = '' if answer_room == self.default_room else f'k{answer_room} '
                    command_prefix += f'{cid} '
                    _element = {
                        'photo_id': att,
                        'action': {'type': 'open_photo'},
                        'buttons': [{'action':
                                        {'type': 'text',
                                        'label': command_prefix + command.action.name,},
                                     'color': 'positive'
                                     },
                                    {'action':
                                        {'type': 'text',
                                        'label': command_prefix + 'altf'}
                                    },
                                                ],
                        'title': 'Скриншот ' + (cid if room != 'all' else rcid),
                        'description': _text or '.'
                    }
                    carousel_elements.append(_element)
            elif _photos or _documents or keyboard or _attachments:
                self.send(_prefix + _text, command.sender, documents=_documents,
                          photos=_photos, keyboard=keyboard,
                          _attachments=_attachments)
            else:
                text.append(_prefix + _text)
                photos += _photos
                documents += _documents
                attachments += _attachments

        if carousel and carousel_elements:
            self.send('Изображения:', command.sender, template={'type': 'carousel', 'elements': carousel_elements})

        text = '\n'.join(text)
        if text or photos or documents or attachments:
            self.send(text, command.sender, documents=documents, photos=photos,
                      _attachments=attachments)
        else:
            self.send('Выполнено', command.sender)

    def handle_late(self, command: Command, cid: str):
        return self.handle(command, late_cid=cid)

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
            ids = [x.casefold() for x in r.group('ids').split()]
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
        return raw['object']['message']['peer_id']
