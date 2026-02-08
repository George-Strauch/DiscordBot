import discord
from discord import ui, Interaction


class WelcomeMessageCreatorModal(ui.Modal):
    def __init__(self, interaction: Interaction):
        super().__init__(title="Create a Welcome Message")
        msg = ui.TextInput(label="Answer", style=discord.TextStyle.paragraph, max_length=2000)
        self.add_item(msg)

    async def on_submit(self, interaction: Interaction):
        await interaction.response.send_message(f"Thanks for your response, {self.name}!", ephemeral=True)


def get_all_selectable_roles(guild: discord.Guild):
    roles = guild.roles
    options = []
    seen_roles = set()
    unchangeable_roles = [x for x in roles if not x.permissions.administrator]

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
