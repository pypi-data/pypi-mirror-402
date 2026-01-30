import click


class CustomOrderGroup(click.Group):
    def __init__(self, *args, **kwargs):
        self._order = kwargs.pop("order", [])
        super(CustomOrderGroup, self).__init__(*args, **kwargs)

    def list_commands(self, ctx):
        return self._order

    def get_command(self, ctx, cmd_name):
        if cmd_name in self.commands:
            return self.commands[cmd_name]
