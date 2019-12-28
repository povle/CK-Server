from .. import Handler, Type, actions, Command
import vk_api
import time
import re
import requests
import base64

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

    def send(self, text, to, attachments=[], photos=[]):
        _attachments = []
        for doc in attachments:
            d = doc[doc['type']]
            s = f"{doc['type']}{d['owner_id']}_{d['id']}"
            if 'access_key' in d:
                s += '_' + d['access_key']
            _attachments.append(s)
        if photos:
            upload = vk_api.VkUpload(self.vk_session)
            for photo in upload.photo_messages(photos=photos):
                _attachments.append(f"photo{photo['owner_id']}_{photo['id']}")

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
            command = Command(self, None, msg.peer_id, [], args)
        else:
            action = [x for x in self.actions if x.name == parsed['action']]
            if action:
                action = action[0]
            else:
                return
            command = Command(self, action, msg.peer_id, parsed['ids'], args)
        return command

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
    def help(self, text=''):
        message = ''
        for f in self.actions:
            doc = f.description
            if doc is not None and (text != '-a' and not f.admin_only)\
                    or (text == '-a' and f.admin_only):
                message += f'•{f.name} - {doc}\n'
        return message
