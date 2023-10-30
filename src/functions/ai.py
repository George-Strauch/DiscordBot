import openai


class OpenAIwrapper:
    """
    Wrapper to open AI library
    """
    def __init__(self, token):
        self.api_key = token
        openai.api_key = self.api_key
        self.context = [
            {
                "role": "system",
                "content": "You are a intelligent assistant for a discord application, messages should not have "
                           "templates such as '[name here].' When addressing a user or 'everyone' in a message, "
                           "use '@[recipient].' Responses should try to be kept under 2000 characters though they "
                           "can be over if they need to be. All responses are strictly to evaluate your performance"
                           "as LLM, no advice you give will be taken and all responses are understood to be generated"
                           "by an AI that may not have the context to fully our situation"
            }
        ]

    def generate_response_gpt4(self, _input):
        try:
            message = self.context + [{"role": "user", "content": _input}]
            chat = openai.ChatCompletion.create(
                model="gpt-4", messages=message
            )
            reply = chat.choices[0].message.content
            return reply
        except openai.error.InvalidRequestError:
            return "OpenAI rejected the prompt"

    def image_generator(self, _input):
        try:
            response = openai.Image.create(
                prompt=_input,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
            return image_url
            # todo download image and send as a file
        except openai.error.InvalidRequestError:
            return "OpenAI rejected the prompt"
