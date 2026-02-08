import discord
from discord._types import ClientT
from discord import Interaction
from discord.ui import Select, View, Button


class AbstractSelect(Select):
    def __init__(self, data_passer, **kwargs):
        self.data_passer = data_passer
        self.default_values = self.default_values if hasattr(self, "default_values") else []
        self.select_options = self.select_options if hasattr(self, "select_options") else []
        self.param = self.param if hasattr(self, "param") else "_"
        params = {
            "options": self.select_options,
            "max_values": kwargs.get("max_values", len(self.select_options)),
            "min_values": kwargs.get("min_values", 1),
            "placeholder": kwargs.get("placeholder", self.param),
        }
        params.update(kwargs)
        super().__init__(**kwargs)
        self.set_data()

    async def callback(self, interaction: Interaction[ClientT]):
        self.set_data()
        await interaction.response.defer()

    def set_data(self):
        if hasattr(self, "default_values") and len(self.default_values) > 0:
            self.data_passer({self.param: ",".join(self.default_values)})
            self.default_values = []
        else:
            self.data_passer({self.param: ",".join(self.values)})


class CreatePeriodicNewsNotification(View):
    class SourceSelect(AbstractSelect):
        def __init__(self, data_passer):
            self.default_values = []
            self.select_options = [
                discord.SelectOption(label=k, value=v, default=v in self.default_values)
                for k, v in sources.items()
            ]
            self.param = "source"
            super().__init__(
                options=self.select_options,
                max_values=len(self.select_options),
                min_values=1,
                placeholder="News Source",
                data_passer=data_passer,
            )

    class CountrySelect(AbstractSelect):
        def __init__(self, data_passer):
            self.default_values = []
            self.select_options = [
                discord.SelectOption(label=k, value=v, default=v in self.default_values)
                for k, v in countries.items()
            ]
            self.param = "country"
            super().__init__(
                options=self.select_options,
                max_values=len(self.select_options),
                min_values=1,
                placeholder="Country",
                data_passer=data_passer,
            )

    class StartNotificationButton(Button):
        def __init__(self, start_func):
            super().__init__(label="Start News Notifications", style=discord.ButtonStyle.primary, row=4)
            self.start_func = start_func

        async def callback(self, interaction: Interaction[ClientT]):
            await self.start_func()
            await interaction.response.defer()

    class CancelButton(Button):
        def __init__(self, cancel):
            super().__init__(label="Cancel", style=discord.ButtonStyle.danger, row=4)
            self.cancel = cancel

        async def callback(self, interaction: Interaction[ClientT]):
            await self.cancel()
            await interaction.response.defer()

    def __init__(self, channel, ctx, original_params, notification_creator, clear_view):
        super().__init__()
        self.news_parameters = {}
        self.run_parameters = {}
        self.params = original_params
        self.add_item(self.SourceSelect(self.data_passer))
        self.add_item(self.CountrySelect(self.data_passer))
        self.add_item(self.CancelButton(self.cancel))
        self.add_item(self.StartNotificationButton(self.start))

        self.notification_creator = notification_creator
        self.channel = channel
        self.ctx = ctx
        self.clear_view = clear_view

    def data_passer(self, received_data: dict):
        run_params = ["frequency", "empty_update"]
        if any([k in run_params for k in received_data.keys()]):
            self.params["run_args"].update(received_data)
        else:
            self.params["news_args"].update(received_data)

    async def start(self):
        self.notification_creator(self.channel, self.params)
        await self.clear_view()
        await self.ctx.reply(
            view=None,
            content="News notification has been set up.\nUse /notifications to view active notifications",
            ephemeral=True,
        )

    async def cancel(self):
        await self.clear_view()
        await self.ctx.reply(content="Canceled news notification setup", ephemeral=True)
