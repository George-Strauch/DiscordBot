"""
Every cog must only call logic from here since cogs are not callable directly
This way, we can have access to the logic that would otherwise go directly in the cog itself since cogs are not callable
"""