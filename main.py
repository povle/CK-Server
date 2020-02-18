from flask import Flask, request
from flask_socketio import SocketIO, Namespace, emit, ConnectionRefusedError
from lib import Handler
from lib.handlers import VkHandler, DirectHandler
import logging
import time
import config
logging.config.fileConfig('logger.conf')
logger = logging.getLogger('ck-server.'+__name__)
client_logger = logging.getLogger('client')

app = Flask(__name__)
socketio = SocketIO(app)

commands = set()
connected = {}

vk_handler = VkHandler(config.vk_token, config.vk_secret)
direct_handler = DirectHandler(config.direct_token)

@socketio.on_error_default
def default_error_handler(e):
    logger.error(e, str(request.event), stack_info=True)

def handle(handler: Handler, raw: dict):
    global commands
    logger.info(f'handled by {handler}: {raw}')
    command = handler.parse(raw)
    if command.room == 'default':
        command.room = config.default_room
    if not command.ready_for_dispatch:
        command.to = config.rooms[command.room]
    if command.handled:
        return command
    commands.add(command)
    for cid in command.to:
        if cid in connected:
            socketio.emit('command', command.to_dict(), room=connected[cid])
            command.sent_to.add(cid)
        else:
            command.add_answer(cid, {'comp_id': cid,
                                     'command_id': command.id,
                                     'timestamp': command.timestamp,
                                     'status': 'error',
                                     'message': 'Not connected',
                                     'exception': None,
                                     'traceback': None})
    socketio.sleep(command.timeout)
    for cid in command.answers:
        if command.answers[cid] is None:
            command.add_answer(cid, {'comp_id': cid,
                                     'command_id': command.id,
                                     'timestamp': time.time(),
                                     'status': 'error',
                                     'message': 'Timeout',
                                     'exception': None,
                                     'traceback': None})
    commands.discard(command)
    return command


@app.route('/input/vk', methods=['POST'])
def handle_vk():
    raw = request.get_json(force=True, silent=True)
    if raw.get('type') == 'confirmation':
        return config.vk_confirmation
    socketio.start_background_task(handle, vk_handler, raw)
    return 'ok'

@app.route('/input/direct', methods=['POST'])
def handle_direct():
    raw = request.get_json(force=True, silent=True)
    return handle(direct_handler, raw).answers

class Dispatch(Namespace):
    def on_connect(self):
        global connected
        sid = request.sid
        cid = request.args.get('id') #client's local id
        token = request.args.get('token')
        if not token or token != config.dispatch_token:
            raise ConnectionRefusedError('bad token')
        if not cid or cid in connected or cid not in config.rooms['all']:
            raise ConnectionRefusedError('bad cid')
        logger.info(f'connected cid={cid} sid={sid}')
        connected[cid] = sid
        for c in commands:
            if c.is_awaiting_dispatch(cid):
                emit('command', c.to_dict())
                c.sent_to.add(cid)

    def on_disconnect(self):
        global connected
        sid = request.sid
        cid = [x for x in connected if connected[x] == sid][0]
        logger.info(f'disconnected cid={cid} sid={sid}')
        connected = {key: val for key, val in connected.items() if val != sid}

    def on_answer(self, json):
        if connected[json['comp_id']] != request.sid:
            raise ValueError
        for c in commands:
            if c.id == json['command_id']:
                command = c
                break
        else:
            raise ValueError('incorrect command')

        if json.get('status') == 'error':
            cl = client_logger.error
        else:
            cl = client_logger.debug
        cl(json)

        command.add_answer(json['comp_id'], json)


socketio.on_namespace(Dispatch())
if __name__ == '__main__':
    socketio.run(app)
