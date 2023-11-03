import discord
from discord.ext import commands
from discord import app_commands
from discord import ui
from discord import Interaction


class WelcomeMessageCreatorModal(ui.Modal):
    def __init__(self, interaction: Interaction):
        super().__init__(title="Create a Welcome Message")
        msg = ui.TextInput(label='Answer', style=discord.TextStyle.paragraph, max_length=2000)
        self.add_item(msg)

    async def on_submit(self, interaction: Interaction):
        await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)






def get_all_selectable_roles(guild: discord.Guild):
    roles = guild.roles
    options = []
    seen_roles = set()
    unchangeable_roles = [
        x
        for x in roles
        if not x.permissions.administrator
    ]
    # print("sadfasdfasdfasdfasdfasd", [x.name for x in unchangeable_roles])
    # print("sadfasdfasdfasdfasdfasd", [x.name for x in roles])

    for x in roles:
        if x in unchangeable_roles:
            continue
        name = x.name
        if name in seen_roles:
            for i in range(2, len(roles)+2):
                new_name = f"{name}{i}"
                if new_name in seen_roles:
                    continue
                else:
                    name = new_name
                    break
        seen_roles.add(name)
        options.append(discord.SelectOption(label=name, value=name))
    return options


class AdminActions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "data/admins.log"

    @app_commands.command(name="modal")
    async def send_modal(self, interaction: Interaction):
        # all_roles = get_all_selectable_roles(interaction.guild)
        # name = ui.TextInput(label='Name')
        # selectable_roles_dd = ui.Select(options=all_roles, min_values=1, max_values=len(all_roles))
        #
        # view = ui.View()
        # view.add_item(name)
        # view.add_item(selectable_roles_dd)
        #
        # await interaction.channel.send("enter", view=view)
        # # await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)
        await interaction.response.send_modal(WelcomeMessageCreatorModal(interaction))



