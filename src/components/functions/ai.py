import asyncio
import json
import time

from openai import OpenAI


class OpenAIwrapper:
    """
    Wrapper to open AI library
    """
    def __init__(self, token):
        self.api_key = token
        self.client = OpenAI(api_key=self.api_key)


    def gpt_response(
            self,
            context: list,
            model="gpt-4",
            **kwargs
    ):
        print(f"GPT ARGS:\n{json.dumps({'model': model, 'context':context, **kwargs}, indent=4)}")
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
                        'function': x.function.name,
                        'arguments': json.loads(x.function.arguments),
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
                "total_tokens": response.usage.total_tokens
            }
        except Exception as ex:
            import traceback
            print(traceback.format_exc())
            message = "An error occurred querying OpenAi"
            if len(ex.args) > 0:
                message += " " + str(ex.args[0])
            return {"error": message}



    def image_generator(
            self,
            prompt: str,
            **kwargs
    ):
        try:
            arguments = {
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "model": "dall-e-3"
            }
            arguments.update(kwargs)
            response = self.client.images.generate(
                **arguments
            )
            return {
                "url": response['data'][0]['url'],
            }
        except Exception as ex:
            message = "An error occurred generating an image with OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}

    def create_thread(self):
        return self.client.beta.threads.create()


    def create_agent(
            self,
            instructions: str,
            name: str = "",
            model: str = "gpt-4-1106-preview",
            tools: list = []
    ):
        agent = self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools
        )
        return agent


    def create_message(
            self,
            thread_id: str,
            content: str,
    ):
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


    def create_run(
            self,
            thread_id: str,
            agent_id: str,
            instructions: str = "respond to the prompt"
    ):
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=agent_id,
            instructions=instructions
        )
        return run


    def wait_for_run(
            self,
            run_id: str,
            thread_id: str,
            n: int = 20,
            dt: int = 5
    ):
        """
        todo try catch
        waits for a run object to complete
        :param run_id:
        :param thread_id:
        :param n:
        :param dt:
        :return:
        """
        strike = 0
        for i in range(n):
            run = self.client.beta.threads.runs.retrieve(
                run_id=run_id,
                thread_id=thread_id
            )
            # print(run)
            if run is None:
                strike += 1
                print(f"strike: {strike}")
                if strike == 3:
                    return None
                else:
                    continue
            print(run.status)
            if run.status not in ["queued", "in_progress"]:
                print(run)
                return run
            time.sleep(dt)
            # await asyncio.sleep(dt)
        return None


    def submit_tool_to_output(
            self,
            run_id: str,
            thread_id: str,
            tool_outputs: list,
    ):
        run = self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
        return run

    def retrieve_messages(
            self,
            thread_id
    ):
        return self.client.beta.threads.messages.list(
            thread_id=thread_id
        )


if __name__ == '__main__':
    pass
