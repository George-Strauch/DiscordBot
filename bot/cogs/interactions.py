import logging

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View

logger = logging.getLogger(__name__)


class RoleSelectDD(Select):
    def __init__(self, guild):
        roles = self.__get_all_selectable_roles(guild)
        super().__init__(options=roles, max_values=len(roles), placeholder="Roles")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"roles selected are: {self.values}")
        new_roles = [x for x in interaction.guild.roles if x.name in self.values]
        await interaction.user.add_roles(*new_roles)

    def __get_all_selectable_roles(self, guild: discord.Guild):
        roles = guild.roles
        options = []
        seen_roles = set()
        unchangeable_roles = [x for x in roles if x.permissions.administrator] + ["@everyone"]

        for x in roles:
            if x in unchangeable_roles:
                continue
            name = x.name
            if name in seen_roles:
                for i in range(2, len(roles) + 2):
                    new_name = f"{name}{i}"
                    if new_name in seen_roles:
                        continue
                    else:
                        name = new_name
                        break
            seen_roles.add(name)
            options.append(discord.SelectOption(label=name, value=name))
        return options


class Interactions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="roles")
    async def roles(self, interaction: discord.Interaction):
        """
        select user roles
        """
        v = View()
        v.add_item(RoleSelectDD(interaction.guild))
        await interaction.response.send_message("Here are some roles for you to select", view=v)
