from flask import Flask, request
from flask_socketio import SocketIO, Namespace, emit, ConnectionRefusedError
from lib import Handler
from lib.handlers import VkHandler, DirectHandler, AliceHandler
from lib.utils import yandex, checkpw
import logging
import time
import traceback
import config
logging.config.fileConfig('logger.conf')
logger = logging.getLogger('ck-server.'+__name__)
client_logger = logging.getLogger('client')
alice_logger = logging.getLogger('alice')

app = Flask(__name__)
socketio = SocketIO(app)

commands = set()
connected = {}

alice_handler = AliceHandler()
vk_handler = VkHandler(config.vk_token, config.vk_secret)
direct_handler = DirectHandler(config.direct_token)

@app.errorhandler(Exception)
def handle_bad_request(e):
    logger.error(f"{e} {request.path} {''.join(traceback.TracebackException.from_exception(e).format())}".replace('\n', r'\n'))
    return 'Internal error', 500

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"{e} {request.event} {''.join(traceback.TracebackException.from_exception(e).format())}".replace('\n', r'\n'))

def make_command(handler: Handler, raw: dict):
    logger.info(f'handled by {handler}: {raw}')
    command = handler.parse(raw)
    if command.room == 'default':
        command.room = config.default_room
    if not command.ready_for_dispatch:
        command.to = config.rooms[command.room]
    command.complete_event = socketio.server.eio.create_event()
    return command

def handle_dispatch(command):
    global commands
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

def wait_and_cleanup(command, seconds):
    global commands
    socketio.sleep(seconds)
    commands.discard(command)

def handle_command(command):
    disp = handle_dispatch(command)
    if disp:
        return disp
    t0 = time.monotonic()
    command.await_complete()
    dt = time.monotonic() - t0
    socketio.start_background_task(wait_and_cleanup, command, max(command.timeout - dt, 0))
    return command

def handle(handler: Handler, raw: dict, in_background=True):
    command = make_command(handler, raw)
    if in_background:
        if command.handled:
            return command
        socketio.start_background_task(handle_command, command)
    else:
        return handle_command(command)

@app.route('/input/vk', methods=['POST'])
def handle_vk():
    raw = request.get_json(force=True, silent=True)
    if raw.get('type') == 'confirmation':
        return config.vk_confirmation
    try:
        handle(vk_handler, raw)
    finally:
        return 'ok'

@app.route('/input/direct', methods=['POST'])
def handle_direct():
    raw = request.get_json(force=True, silent=True)
    return handle(direct_handler, raw, in_background=False).answers

@app.route('/input/alice', methods=['POST'])
def handle_alice():
    raw = request.get_json(force=True, silent=True)
    if raw.get('request', {}).get('command') == 'ping':
        log_function = alice_logger.debug
    else:
        log_function = alice_logger.info
    log_function(raw)
    resp, proceed = yandex.form_alice_response(raw, config.alice_trusted_ids)
    if proceed:
        command = handle(alice_handler, raw)
        if command:
            ans = command.answers.get('0.0')
            if ans and ans.get('status') == 'error':
                resp['response']['text'] = 'Не удалось распознать команду'
    return resp

class Dispatch(Namespace):
    def on_connect(self):
        global connected
        sid = request.sid
        cid = request.args.get('id') #client's local id
        token = request.args.get('token')
        if not token or not checkpw(token.encode('utf8'), config.dispatch_token):
            return False #exception doesn't work due to a flask-socketio bug
            #raise ConnectionRefusedError('bad token')
        if not cid or cid in connected or cid not in config.rooms['all']:
            return False
            #raise ConnectionRefusedError('bad cid')
        logger.info(f'connected cid={cid} sid={sid}')
        connected[cid] = sid
        for c in commands:
            if c.is_awaiting_dispatch(cid):
                emit('command', c.to_dict())
                c.sent_to.add(cid)

    def on_disconnect(self):
        global connected
        sid = request.sid
        cid = [x for x in connected if connected[x] == sid]
        if cid:
            cid = cid[0]
        else:
            logger.warning(f'refused connection sid={sid}')
            return
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
