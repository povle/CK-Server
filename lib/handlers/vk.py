from .. import Handler, Type
import vk_api
import time

class VkHandler(Handler):
    def __init__(self, token):
        super().__init__(answer_types={Type.TEXT, Type.PHOTO, Type.Document},
                         arg_types={Type.TEXT, Type.PHOTO, Type.Document})
        self.token = token
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
        pass #FIXME
