import json
import logging
import time
import traceback

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIWrapper:
    def __init__(self, token):
        self.api_key = token
        self.client = OpenAI(api_key=self.api_key)

    def gpt_response(self, context: list, model="gpt-4o", **kwargs):
        logger.debug("GPT ARGS: %s", json.dumps({"model": model, "context": context, **kwargs}, indent=4))
        try:
            tools = []
            text = ""
            response = self.client.chat.completions.create(
                model=model,
                messages=context,
                **kwargs
            )
            choice = response.choices[0]
            if choice.message.tool_calls:
                tool_calls = choice.message.tool_calls
                tools = [
                    {
                        "function": x.function.name,
                        "arguments": json.loads(x.function.arguments),
                    }
                    for x in tool_calls
                ]
            if choice.message.content:
                text = choice.message.content
            return {
                "text": text,
                "tool_calls": tools,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        except Exception as ex:
            logger.exception("Error querying OpenAI")
            message = "An error occurred querying OpenAi"
            if len(ex.args) > 0:
                message += " " + str(ex.args[0])
            return {"error": message}

    def image_generator(self, prompt: str, **kwargs):
        try:
            arguments = {
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "model": "dall-e-3",
            }
            arguments.update(kwargs)
            response = self.client.images.generate(**arguments)
            return {"url": response.data[0].url}
        except Exception as ex:
            logger.exception("Error generating image")
            message = "An error occurred generating an image with OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}

    def create_thread(self):
        return self.client.beta.threads.create()

    def create_agent(self, instructions: str, name: str = "", model: str = "gpt-4o", tools=None):
        if tools is None:
            tools = []
        agent = self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools,
        )
        return agent

    def create_message(self, thread_id: str, content: str):
        try:
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content,
            )
            return message
        except Exception as ex:
            message = "An error occurred querying OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}

    def create_run(self, thread_id: str, agent_id: str, instructions: str = "respond to the prompt"):
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=agent_id,
            instructions=instructions,
        )
        return run

    def wait_for_run(self, run_id: str, thread_id: str, n: int = 20, dt: int = 5):
        strike = 0
        for i in range(n):
            run = self.client.beta.threads.runs.retrieve(
                run_id=run_id,
                thread_id=thread_id,
            )
            if run is None:
                strike += 1
                logger.warning("strike: %d", strike)
                if strike == 3:
                    return None
                else:
                    continue
            logger.debug("Run status: %s", run.status)
            if run.status not in ["queued", "in_progress"]:
                return run
            time.sleep(dt)
        return None

    def submit_tool_to_output(self, run_id: str, thread_id: str, tool_outputs: list):
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
        )
        return run

    def retrieve_messages(self, thread_id):
        return self.client.beta.threads.messages.list(thread_id=thread_id)
