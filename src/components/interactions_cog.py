import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View



class RoleSelectDD(Select):
    def __init__(self, guild):
        roles = self.__get_all_selectable_roles(guild)
        super().__init__(options=roles, max_values=len(roles), placeholder="Roles")


    async def callback(self, interaction: discord.Interaction):
        print(f"Setting your new roles")
        print(type(self.values[0]))
        await interaction.response.send_message(f"roles selected are: {self.values}")
        roles = interaction.guild.roles
        new_roles = [x for x in interaction.guild.roles if x.name in self.values]
        print(new_roles)
        print(new_roles[0].__dir__())
        print(type(new_roles[0]))
        await interaction.user.add_roles(new_roles)


    def __get_all_selectable_roles(self, guild: discord.Guild):
        # todo allow an admin set these
        roles = guild.roles
        options = []
        seen_roles = set()
        unchangeable_roles = [
            x
            for x in roles
            if x.permissions.administrator
        ] + ["@everyone"]

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



# class RoleSelectDDView(View):
#     def __init__(self, guild):
#         super().__init__()
#         print("here in create")
#         self.add_item(RoleSelectDD(guild))
#         print("done creating")



class Interactions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_file = "/opt/bot/data/interactions.log"


    @app_commands.command(name="invite")
    async def generate_invite_link(self, interaction: discord.Interaction):
        """
        generate an invite link
        """
        invite_link = await interaction.channel.create_invite(max_age=0)
        await interaction.response.send_message(
            invite_link,
            ephemeral=True
        )



    @app_commands.command(name="roles")
    async def roles(self, interaction: discord.Interaction):
        """
        select user roles
        """
        v = View()
        v.add_item(RoleSelectDD(interaction.guild))
        # https://guide.pycord.dev/interactions/ui-components/buttons
        v.add_item()
        # v = RoleSelectDDView(interaction.guild)
        await interaction.response.send_message(
            "Here are some roles for you to select",
            view=v
        )



