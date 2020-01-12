from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class CommandKeyboard(VkKeyboard):
    def __init__(self, one_time=False):
        super().__init__(one_time)
        self.aliases = {}

    def add_button(self, label, command=None, color=VkKeyboardColor.DEFAULT, payload=None):
        if command is not None:
            self.aliases[label] = command
        super().add_button(label, color, payload)


keyboard = CommandKeyboard(one_time=False)

keyboard.add_button('Выключить все', 'all off', color=VkKeyboardColor.NEGATIVE)
keyboard.add_line()
keyboard.add_button('Сон', 'all sleep', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Перезагрузка', 'all restart', color=VkKeyboardColor.PRIMARY)
keyboard.add_button('Выход', 'all logout', color=VkKeyboardColor.PRIMARY)
keyboard.add_line()
keyboard.add_button('Переместить', 'all move', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Вернуть', 'all move -r', color=VkKeyboardColor.POSITIVE)
keyboard.add_line()
keyboard.add_button('alt + f4', 'all altf', color=VkKeyboardColor.DEFAULT)
keyboard.add_button('Без звука', 'all volume', color=VkKeyboardColor.DEFAULT)
keyboard.add_line()
keyboard.add_button('Выкл. экран', 'all screen_off', color=VkKeyboardColor.DEFAULT)
keyboard.add_button('Корзина', 'all bin', color=VkKeyboardColor.DEFAULT)


admin_keyboard = CommandKeyboard(one_time=False)

admin_keyboard.add_button('all test')
admin_keyboard.add_line()
admin_keyboard.add_button('all screenshot')
admin_keyboard.add_line()
admin_keyboard.add_button('all status')
