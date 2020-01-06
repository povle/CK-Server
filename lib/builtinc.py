from .actions import actions

def help(args=[]):
    message = ''
    text = ''
    for arg in args:
        if arg['type'] == 'text':
            text += arg['text']
    for f in actions:
        doc = f.description
        if doc is not None and (text != '-a' and not f.admin_only)\
                or (text == '-a' and f.admin_only):
            message += f'•{f.name} - {doc}\n'
    return [{'type': 'text',
             'text': message}]
