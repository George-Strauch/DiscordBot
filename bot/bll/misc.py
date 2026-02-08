import logging

logger = logging.getLogger(__name__)


class MiscBll:
    def __init__(self):
        pass

    async def generate_invite_link(self, channel):
        invite_link = await channel.create_invite(max_age=0)
        return {"content": invite_link, "ephemeral": True}
