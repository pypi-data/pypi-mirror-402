import os
from datetime import datetime
from typing import Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, load_prompt, PromptTemplate
from langchain_core.prompts.string import PromptTemplateFormat
from langfuse import get_client
from langfuse.langchain import CallbackHandler


def create_tool_message(messages, content="done", tool_call_index=0, tool_call_message_index=-1):
    tool_calls = messages[tool_call_message_index].tool_calls
    return {"role": "tool", "content": content, "tool_call_id": tool_calls[tool_call_index]['id']}


def create_ai_message(content: str | list[str | dict] | None = None):
    return AIMessage(content=content)


def create_user_message(content: str | list[str | dict] | None = None):
    return HumanMessage(content=content)


def create_system_message(content: str | list[str | dict] | None = None):
    return SystemMessage(content=content)


def dump_flow_result(result, user_content_block=False):
    if isinstance(result, dict):
        for m in result["messages"]:
            if user_content_block:
                for content_blocks in m.content_blocks:
                    print("---------------------------------------------------")
                    print(content_blocks)
            else:
                m.pretty_print()
    else:
        for e in result:
            if isinstance(e, tuple):
                e[0].pretty_print()
            else:
                messages = e.get("messages")
                if messages is not None:
                    messages[-1].pretty_print()


def create_run_config(run_name: str, thread_id_pattern="%Y%m%d-%H%M%S", recursion_limit=13, user_id="dev"):
    thread_id = datetime.now().strftime(thread_id_pattern)

    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [CallbackHandler()],
        "recursion_limit": recursion_limit,
        "run_name": run_name,
        "metadata": {
            "langfuse_session_id": thread_id,
            "langfuse_user_id": user_id
        }
    }


def get_prompt(template_name: str, role: Literal["system", "ai", "human"] = "system",
               source: Literal["local", "langfuse"] = "langfuse",
               local_dir: str = None, local_ext=".yml",
               local_format: Literal["mustache", "f-string"] = "mustache",
               langfuse_type: Literal["chat", "text"] = "text", langfuse_label: Optional[str] = None,
               langfuse_cache: Optional[int] = 86400,
               langfuse_format: PromptTemplateFormat = "mustache",
               langfuse_version: Optional[int] = None,
               save_to_local=False) -> ChatPromptTemplate:
    match source:
        case "langfuse":
            langfuse_prompt = get_client().get_prompt(template_name, type=langfuse_type,
                                                      label=langfuse_label,
                                                      cache_ttl_seconds=langfuse_cache,
                                                      version=langfuse_version)
            chat_prompt = ChatPromptTemplate.from_messages(
                messages=[(role, langfuse_prompt.prompt)],
                template_format=langfuse_format
            )
            chat_prompt.metadata = {"langfuse_prompt": langfuse_prompt}

            if save_to_local:
                template_base_dir = os.getenv("KOSMOS_TEMPLATE_DIR",
                                              default="./templates") if local_dir is None else local_dir
                os.makedirs(f"{template_base_dir}/{template_name[0:template_name.rindex("/")]}",
                            exist_ok=True)
                with open(f"{template_base_dir}/{template_name}{local_ext}", "w",
                          encoding="utf-8") as output_file:
                    output_file.write(f"_type: prompt\ntemplate_format: {local_format}\ntemplate: |-\n  ")
                    output_file.write(langfuse_prompt.prompt.replace("\n", "\n  "))

            return chat_prompt
        case _:
            template_base_dir = os.getenv("KOSMOS_TEMPLATE_DIR",
                                          default="./templates") if local_dir is None else local_dir
            prompt: PromptTemplate = load_prompt(f"{template_base_dir}/{template_name}{local_ext}",
                                                 encoding="utf8")
            chat_prompt = ChatPromptTemplate.from_messages(
                messages=[(role, prompt.template)],
                template_format=prompt.template_format)
            return chat_prompt
