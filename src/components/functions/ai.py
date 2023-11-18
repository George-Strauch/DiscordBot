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
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=context,
                **kwargs
            )
            # print(json.dumps(response, indent=4))
            return {
                "content": response["choices"][0]["message"]["content"],
                "input_tokens": response["usage"]["prompt_tokens"],
                "output_tokens": response["usage"]["completion_tokens"],
                "total_tokens": response["usage"]["total_tokens"]
            }
        except Exception as ex:
            message = "An error occurred querying OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
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
                # "input_tokens": response["usage"]["prompt_tokens"],
                # "output_tokens": response["usage"]["completion_tokens"],
                # "total_tokens": response["usage"]["total_tokens"]
            }
        except Exception as ex:
            message = "An error occurred generating an image with OpenAi"
            if len(ex.args) > 0:
                message = ex.args[0]
            return {"error": message}


    def function_caller(self, _input, tools, model="gpt-4"):
        # "gpt-3.5-turbo-0613"
        try:
            # model = "gpt-3.5-turbo-1106"
            message = self.context + [{"role": "user", "content": _input}]
            chat = self.client.chat.completions.create(
                model=model,
                messages=message,
                tools=tools
            )
            tokens = chat["usage"]["total_tokens"]
            choice = chat.choices[0]
            print(f"------------------------------- Tokens used: {tokens}")
            if "tool_calls" in choice.message:
                reply = chat.choices[0].message.tool_calls
                func = reply[0]["function"]
                func["arguments"] = json.loads(func["arguments"])
                print("function call \n", json.dumps(func, indent=4))
                return True, func
            else:
                reply = choice.message.content
                print("Text response \n", reply)

                return False, reply
        except Exception as ire:
            print("issues")
            print(ire.args)
            return False, "OpenAI rejected the prompt"


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
            n: int = 10,
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
        for i in range(n):
            run = self.client.beta.threads.runs.retrieve(
                run_id=run_id,
                thread_id=thread_id
            )
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
