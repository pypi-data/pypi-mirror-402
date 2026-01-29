import json
import os
from pathlib import Path




def validate_python(code: str):
    """Fail fast if generated code is invalid"""
    try:
        compile(code, "<generated_agent>", "exec")
    except SyntaxError as e:
        raise RuntimeError(
            f"❌ Generated Python is invalid:\n{e.msg} (line {e.lineno})"
        )


def generate_tools(tools):
    lines = []
    tool_names = []

    for t in tools:
        name = t["name"]
        ttype = t["type"]
        tool_names.append(name)

        if ttype == "http_get":
            lines.extend([
                "@tool",
                f"def {name}(url: str = {json.dumps(t.get('default_url', ''))}) -> str:",
                f'    """{t.get("description", "")}"""',
                f"    headers = {json.dumps(t.get('headers', {}), indent=4)}",
                "    r = requests.get(url, headers=headers, timeout=60)",
                "    r.raise_for_status()",
                "    return r.text",
                "",
            ])

        elif ttype == "file_read":
            lines.extend([
                "@tool",
                f"def {name}(path: str = {json.dumps(t.get('default_path', ''))}) -> str:",
                f'    """{t.get("description", "")}"""',
                '    with open(path, "r", encoding="utf-8") as f:',
                "        return f.read()",
                "",
            ])

    return lines, tool_names


def generate_agent(input_payload: dict,pg_id) -> str:
    code = []

    # ================= Imports =================
    code.extend([
        "import sys",
        "import json",
        "import os",
        "import yaml",
        "import requests",
        "from typing import List",
        "from dotenv import load_dotenv",
        "from pydantic import BaseModel, Field",
        "",
        "from langchain_openai import AzureChatOpenAI",
        "from langchain.tools import tool",
        "from langchain_core.prompts import ChatPromptTemplate",
        "from langchain_core.output_parsers import PydanticOutputParser",
        "",
        'p_id="{0}"'.format(pg_id),
        "",
        'with open("/work/progs/nifi_aut/json_repos/{0}/{0}.json", "r") as f:'.format(pg_id),
        "   config = yaml.safe_load(f)"



    ])

    # ================= Env =================
    code.extend([
        "# =====================================================",
        "# 1️⃣ Load Azure credentials",
        "# =====================================================",
        "load_dotenv()",
        "",
        'AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")',
        'AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")',
        'AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")',
        'AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")',
        "",
    ])

    # ================= Schema =================
    code.extend([
        "# =====================================================",
        "# 2️⃣ Output Schema",
        "# =====================================================",
        "class LLMResponse(BaseModel):",
        "    #session_id: str",
        "    #timestamp: str",
        "    #agent: List[str]",
        "    #sources: List[str] = Field(default_factory=list)",
        "    #status: str",
        "    question: str",
        "    selected_agents: List[str]",
        "    reason: str",
        "",
        "parser = PydanticOutputParser(pydantic_object=LLMResponse)",
        "",
    ])

    # ================= Tools =================
    code.extend([
        "# =====================================================",
        "# 3️⃣ Tools",
        "# =====================================================",
    ])

    tool_lines, tool_names = generate_tools(input_payload.get("tools", []))
    code.extend(tool_lines)
    code.append(f"TOOLS = [{', '.join(tool_names)}]")
    code.append("")

    # ================= LLM =================
    code.extend([
        "# =====================================================",
        "# 4️⃣ LLM",
        "# =====================================================",
        "llm = AzureChatOpenAI(",
        "    azure_endpoint=AZURE_OPENAI_ENDPOINT,",
        "    api_key=AZURE_OPENAI_KEY,",
        "    api_version=AZURE_OPENAI_API_VERSION,",
        "    deployment_name=AZURE_OPENAI_MODEL,",
        "    temperature=0",
        ")",
        "",
        "llm_with_tools = llm.bind_tools(TOOLS)",
        "",
    ])

    # ================= Prompt =================
    code.extend([
        "# =====================================================",
        "# 5️⃣ Prompt",
        "# =====================================================",
        'ag="""No agent regesterd.',
        'any request or question will redirect to no_agent."""',
        "if config[0]['agents_prompte'] is not None:",
        "    ag =config[0]['agents_prompte']",
        "",
        "",
        "prompt = ChatPromptTemplate.from_messages([",
        "    (",
        '        "system",str(config[0]["orch_prompte"]).replace("{{AVAILABLE_AGENTS}}",ag)',
        "    ),",
        '    ("human", "{question}  - session id={session_id}")',
        "]).partial(format_instructions=parser.get_format_instructions())",
        "",
    ])

    # ================= Main =================
    code.extend([
        "# =====================================================",
        "# 6️⃣ Main",
        "# =====================================================",
        "def main():",
        "    try:",
        "        input_data = json.loads(sys.stdin.read())",
        "",
        "        question = input_data['question']",
        "        session_id = input_data['session_id']",
        "        timestamp = input_data['timestamp']",
        "",
        "        chain = prompt | llm_with_tools | parser",
        "        result = chain.invoke({'question': question,'session_id':session_id})",
        "",
        "        output = result.model_dump(exclude_none=True)",
        "        output['session_id'] = session_id",
        "        output['timestamp'] = timestamp",
        "        output['status'] = 'SUCCESS'",
        "        output['question'] = input_data['question']",
        "",
        "        print(json.dumps(output, ensure_ascii=False))",
        "",
        "    except Exception as e:",
        "        print(json.dumps({",
        "            'session_id': input_data.get('session_id', 'UNKNOWN'),",
        "            'timestamp': input_data.get('timestamp', ''),",
        "            'agent': [],",
        "            'sources': [],",
        "            'status': f'ERROR: {str(e)}'",
        "        }))",
        "",
        "",
        "if __name__ == '__main__':",
        "    main()",
    ])

    generated_code = "\n".join(code)
    print(generated_code)
    validate_python(generated_code)
    return generated_code

def generate_agent_pg_mem(input_payload: dict, pg_id: str) -> str:
    """
    Generates a fully self-contained Python agent with:
    - PostgreSQL memory (chat + agent memory)
    - Dynamic tools
    - Azure OpenAI LLM
    - RunnableWithMessageHistory
    - Safe prompt variable handling (avoids INVALID_PROMPT_INPUT)
    """

    code = []

    # ================= Imports =================
    code.extend([
        "import sys",
        "import os",
        "import json",
        "import yaml",
        "import requests",
        "import psycopg2",
        "from typing import List",
        "from dotenv import load_dotenv",
        "from pydantic import BaseModel, Field",
        "",
        "from langchain_openai import AzureChatOpenAI",
        "from langchain.tools import tool",
        "from langchain_core.prompts import ChatPromptTemplate",
        "from langchain_core.output_parsers import PydanticOutputParser",
        "from langchain_core.messages import HumanMessage, AIMessage",
        "from langchain_core.runnables.history import RunnableWithMessageHistory",
        "",
        f'p_id = "{pg_id}"',
        f'with open("/work/progs/nifi_aut/json_repos/{pg_id}/{pg_id}.json","r") as f:',
        "    config = yaml.safe_load(f)",
        "",
        "load_dotenv()",
        "AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')",
        "AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')",
        "AZURE_OPENAI_MODEL = os.getenv('AZURE_OPENAI_MODEL')",
        "AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_API_KEY')",
        "PG_DSN = os.getenv('PG_DSN','dbname=llm user=llm password=llm host=localhost port=5432')",
        "",
    ])

    # ================= PostgreSQL Memory =================
    code.extend([
        "# ================= PostgreSQL Chat History =================",
        "class PostgresChatHistory:",
        "    def __init__(self, session_id: str):",
        "        self.session_id = session_id",
        "        self._ensure_table()",
        "",
        "    def _get_conn(self):",
        "        return psycopg2.connect(PG_DSN)",
        "",
        "    def _ensure_table(self):",
        "        with self._get_conn() as conn:",
        "            with conn.cursor() as cur:",
        "                cur.execute(\"\"\"",
        "                CREATE TABLE IF NOT EXISTS chat_history (",
        "                    id BIGSERIAL PRIMARY KEY,",
        "                    session_id TEXT NOT NULL,",
        "                    role TEXT NOT NULL,",
        "                    content TEXT NOT NULL,",
        "                    created_at TIMESTAMPTZ DEFAULT NOW()",
        "                );",
        "                \"\"\")",
        "                conn.commit()",
        "",
        "    @property",
        "    def messages(self):",
        "        with self._get_conn() as conn:",
        "            with conn.cursor() as cur:",
        "                cur.execute(",
        "                    'SELECT role, content FROM chat_history WHERE session_id=%s ORDER BY created_at',",
        "                    (self.session_id,),",
        "                )",
        "                rows = cur.fetchall()",
        "        msgs = []",
        "        for role, content in rows:",
        "            if role == 'human':",
        "                msgs.append(HumanMessage(content=content))",
        "            else:",
        "                msgs.append(AIMessage(content=content))",
        "        return msgs",
        "",
        "    def add_message(self, message):",
        "        role = 'human' if isinstance(message, HumanMessage) else 'ai'",
        "        with self._get_conn() as conn:",
        "            with conn.cursor() as cur:",
        "                cur.execute(",
        "                    'INSERT INTO chat_history (session_id, role, content) VALUES (%s,%s,%s)',",
        "                    (self.session_id, role, message.content)",
        "                )",
        "                conn.commit()",
        "",
        "    def clear(self):",
        "        pass",
        "",
        "# ================= Agent memory =================",
        "def save_agent_memory(session_id: str, question: str, selected_agents: List[str], reason: str):",
        "    with psycopg2.connect(PG_DSN) as conn:",
        "        with conn.cursor() as cur:",
        "            cur.execute(\"\"\"",
        "            CREATE TABLE IF NOT EXISTS llm_agent_memory (",
        "                id BIGSERIAL PRIMARY KEY,",
        "                session_id TEXT NOT NULL,",
        "                question TEXT NOT NULL,",
        "                selected_agents JSONB,",
        "                reason TEXT,",
        "                created_at TIMESTAMPTZ DEFAULT NOW()",
        "            );",
        "            \"\"\")",
        "            cur.execute(",
        "                'INSERT INTO llm_agent_memory (session_id, question, selected_agents, reason) VALUES (%s,%s,%s,%s)',",
        "                (session_id, question, json.dumps(selected_agents), reason)",
        "            )",
        "            conn.commit()",
        "",
    ])

    # ================= Output Schema =================
    code.extend([
        "class LLMResponse(BaseModel):",
        "    question: str",
        "    selected_agents: List[str]",
        "    reason: str",
        "",
        "parser = PydanticOutputParser(pydantic_object=LLMResponse)",
        "",
    ])

    # ================= Tools =================
    code.append("# ================= Tools =================")
    for t in input_payload.get("tools", []):
        name = t["name"]
        ttype = t["type"]
        desc = t.get("description", "")
        if ttype == "http_get":
            code.extend([
                f"@tool",
                f"def {name}(url: str = '{t.get('default_url','')}') -> str:",
                f"    '''{desc}'''",
                f"    headers = {t.get('headers',{})}",
                f"    r = requests.get(url, headers=headers, timeout=60)",
                f"    r.raise_for_status()",
                f"    return r.text",
                "",
            ])
        elif ttype == "file_read":
            code.extend([
                f"@tool",
                f"def {name}(path: str = '{t.get('default_path','')}') -> str:",
                f"    '''{desc}'''",
                "    with open(path,'r',encoding='utf-8') as f:",
                "        return f.read()",
                "",
            ])
    tool_list = [t["name"] for t in input_payload.get("tools", [])]
    code.append(f"TOOLS = [{', '.join(tool_list)}]")
    code.append("")

    # ================= LLM =================
    code.extend([
        "llm = AzureChatOpenAI(",
        "    azure_endpoint=AZURE_OPENAI_ENDPOINT,",
        "    api_key=AZURE_OPENAI_KEY,",
        "    api_version=AZURE_OPENAI_API_VERSION,",
        "    deployment_name=AZURE_OPENAI_MODEL,",
        "    temperature=0",
        ")",
        "llm_with_tools = llm.bind_tools(TOOLS)",
        "",
    ])

    # ================= Prompt =================
    ag_prompt = "No agent registered. Any request will redirect to no_agent."
    code.append(f'ag = "{ag_prompt}"')
    code.append("if config[0].get('agents_prompte'):\n    ag = config[0]['agents_prompte']")

    # Escape any invalid variable placeholders
    code.extend([
        "system_prompt = str(config[0]['orch_prompte']).replace('{{AVAILABLE_AGENTS}}', ag)",
        "system_prompt = system_prompt.replace('\\n',' ').replace('\"','')",  # remove newlines and quotes
        "",
        "prompt = ChatPromptTemplate.from_messages([",
        "    ('system', system_prompt),",
        "    ('system', 'Conversation history:\\n{chat_history}'),",
        "    ('human', '{question}')",
        "]).partial(format_instructions=parser.get_format_instructions())",
        "",
    ])

    # ================= Main =================
    code.extend([
        "def main():",
        "    try:",
        "        input_data = json.loads(sys.stdin.read())",
        "        session_id = input_data['session_id']",
        "        question = input_data['question']",
        "        timestamp = input_data['timestamp']",
        "",
        "        base_chain = prompt | llm_with_tools | parser",
        "        chain = RunnableWithMessageHistory(",
        "            base_chain,",
        "            lambda sid: PostgresChatHistory(sid),",
        "            input_messages_key='question',",
        "            history_messages_key='chat_history'",
        "        )",
        "",
        "        result = chain.invoke(",
        "            {'question': question},",
        "            config={'configurable': {'session_id': session_id}}",
        "        )",
        "",
        "        save_agent_memory(",
        "            session_id=session_id,",
        "            question=question,",
        "            selected_agents=result.selected_agents,",
        "            reason=result.reason",
        "        )",
        "",
        "        output = result.model_dump(exclude_none=True)",
        "        output.update({'session_id': session_id,'timestamp': timestamp,'status':'SUCCESS'})",
        "        output.update({'plan':json.loads(str(config[0]['plan']))})",
        "        print(json.dumps(output, ensure_ascii=False))",
        "",
        "    except Exception as e:",
        "        print(json.dumps({",
        "            'session_id': input_data.get('session_id','UNKNOWN'),",
        "            'timestamp': input_data.get('timestamp',''),",
        "            'agent': [],",
        "            'sources': [],",
        "            'status': f'ERROR: {str(e)}'",
        "        }))",
        "",
        "if __name__ == '__main__':",
        "    main()",
    ])

    return "\n".join(code)

def agent_generate_mcp_script(tool_names: list[str], mcp_url: str, output_file: str,system_prompts:str):
    """
    Generate a Python script that wraps MCP tools with LangChain and Azure OpenAI.
    Robustly handles tools missing args_schema.

    Args:
        tool_names (List[str]): List of MCP tool names to include.
        mcp_url (str): URL of the MCP server (e.g., "http://192.168.1.220:8333").
        output_file (str): File path to save the generated script.
    """

    script_template = f'''import os
import json
import asyncio
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import AzureChatOpenAI
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# =====================================================
# 1️⃣ Load environment variables
# =====================================================
load_dotenv()
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")

# =====================================================
# 2️⃣ MCP helper class (robust)
# =====================================================
class SyncStringMCPTool:
    \"\"\"Wrap a MCP tool so it always returns a string.\"\"\"
    def __init__(self, tool):
        self.tool = tool
        self.name = tool.name

    def run(self, text: str) -> str:
        return asyncio.run(self.arun(text))

    async def arun(self, text: str) -> str:
        # Check if the tool has args_schema
        if hasattr(self.tool, "args_schema") and self.tool.args_schema.get("properties"):
            arg_name = list(self.tool.args_schema["properties"].keys())[0]
            payload = {{arg_name: text}}
        else:
            # Fallback: assume tool takes single argument called "input"
            payload = {{"input": text}}

        result = await self.tool.arun(payload)

        # Convert dict or list output to string safely
        if isinstance(result, dict):
            return result.get("res", str(result))
        if isinstance(result, list):
            return " ".join(item.get("text", str(item)) for item in result)
        return str(result)

# =====================================================
# 3️⃣ Load MCP tools dynamically
# =====================================================
def load_mcp_tools_sync(url: str, tool_names: List[str]):
    tools = []

    async def _load():
        client = MultiServerMCPClient({{
            "main": {{"transport": "sse", "url": f"{{url}}/sse"}}
        }})
        available_tools = await client.get_tools()
        #print("Available tools on MCP server:", [t.name for t in available_tools])
        for t in available_tools:
            if t.name in tool_names:
                tools.append(t)
        return tools

    return asyncio.run(_load())

# =====================================================
# 4️⃣ Define strict output schema
# =====================================================
class LLMResponse(BaseModel):
    session_id: str
    timestamp: str
    status: str
    answer: str

parser = PydanticOutputParser(pydantic_object=LLMResponse)

# =====================================================
# 5️⃣ Helper to wrap MCP tool as LangChain tool
# =====================================================
def make_generic_mcp_tool(sync_tool: SyncStringMCPTool):
    @tool(return_direct=True)
    def generic_mcp_tool(question: str) -> str:
        \"\"\"Call the MCP tool and return its string output\"\"\"
        return sync_tool.run(question)
    return generic_mcp_tool

# =====================================================
# 6️⃣ Load MCP tools and wrap them
# =====================================================
TOOL_NAMES = {tool_names}
mcp_tools = load_mcp_tools_sync("{mcp_url}", TOOL_NAMES)
wrapped_tools = [make_generic_mcp_tool(SyncStringMCPTool(t)) for t in mcp_tools]

#print("Wrapped MCP tools for LangChain:", [t.name for t in wrapped_tools])

# =====================================================
# 7️⃣ Initialize Azure OpenAI LLM
# =====================================================
llm = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    deployment_name=AZURE_OPENAI_MODEL,
    temperature=0
)
llm_with_tools = llm.bind_tools(wrapped_tools)

# =====================================================
# 8️⃣ Create prompt with schema instructions
# =====================================================
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """>>>system_prompts<<<.
Return output strictly in JSON format following this schema:
{{format_instructions}}"""
    ),
    ("human", "{{question}}")
]).partial(format_instructions=parser.get_format_instructions())

# =====================================================
# 9️⃣ Main execution
# =====================================================
def main():
    input_data = json.loads(sys.stdin.read())
    try:
        chain = prompt | llm_with_tools | parser
        result = chain.invoke({{"question": input_data["question"]}})
        output = result.model_dump(exclude_none=True)
        output["session_id"] = input_data["session_id"]
        output["timestamp"] = input_data["timestamp"]
        output["status"] = "SUCCESS"
        output["question"] = input_data["question"]
        print(json.dumps(output, ensure_ascii=False))

    except Exception as e:
        #print("LLM chain failed, falling back to first MCP tool:", e)
        fallback_tool = SyncStringMCPTool(mcp_tools[0])
        answer_text = fallback_tool.run(input_data["question"])
        output = {{
            "session_id": input_data["session_id"],
            "timestamp": input_data["timestamp"],
            "status": "SUCCESS",
            "answer": answer_text
        }}
        print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
'''
    script_template=script_template.replace(">>>system_prompts<<<",system_prompts)
    print(f"""script_template

    {script_template}

""")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(script_template)
    print(f"Script generated and saved to {output_file}")

def agent_generate_mcp_script_mem(
    tool_names: list[str],
    mcp_url: str,
    output_file: str,
    system_prompts: str
):
    """
    Generate a Python MCP agent script with:
    - Azure OpenAI
    - LangChain
    - PostgreSQL persistent memory (llm_agent_memory)
    - Proper LLMResponse schema with selected_agents
    """
    import json

    tool_names_str = json.dumps(tool_names)

    # Use triple quotes and placeholders for dynamic replacement
    script_template = f'''import os
import json
import asyncio
import sys
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
import psycopg2
import psycopg2.extras

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import AzureChatOpenAI
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# =====================================================
# 1️⃣ Environment
# =====================================================
load_dotenv()

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_MODEL = os.getenv("AZURE_OPENAI_MODEL")
PG_DSN = os.getenv("PG_DSN")

if not PG_DSN:
    raise RuntimeError("PG_DSN is not set")

# =====================================================
# 2️⃣ PostgreSQL helpers
# =====================================================
def get_conn():
    return psycopg2.connect(PG_DSN)

def load_memory(session_id: str, limit: int = 5) -> str:
    sql = """
        SELECT question, selected_agents, reason
        FROM llm_agent_memory
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, (session_id, limit))
            rows = cur.fetchall()

    if not rows:
        return "No previous context."

    history = []
    for r in reversed(rows):
        history.append(
            f"User: {{r['question']}}\\nSelected agents: {{r['selected_agents']}}\\nReason: {{r['reason']}}"
        )
    return "\\n---\\n".join(history)

def save_memory(session_id: str, question: str, selected_agents: List[str], reason: str):
    sql = """
        INSERT INTO llm_agent_memory
        (session_id, question, selected_agents, reason)
        VALUES (%s, %s, %s, %s)
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                session_id,
                question,
                json.dumps(selected_agents),
                reason
            ))
            conn.commit()

# =====================================================
# 3️⃣ MCP Tool Wrapper
# =====================================================
class SyncStringMCPTool:
    def __init__(self, tool):
        self.tool = tool
        self.name = tool.name

    def run(self, text: str) -> str:
        return asyncio.run(self.arun(text))

    async def arun(self, text: str) -> str:
        if hasattr(self.tool, "args_schema") and self.tool.args_schema.get("properties"):
            arg_name = list(self.tool.args_schema["properties"].keys())[0]
            payload = {{arg_name: text}}
        else:
            payload = {{"input": text}}

        result = await self.tool.arun(payload)
        if isinstance(result, dict):
            return result.get("res", str(result))
        if isinstance(result, list):
            return " ".join(item.get("text", str(item)) for item in result)
        return str(result)

# =====================================================
# 4️⃣ Load MCP tools
# =====================================================
def load_mcp_tools_sync(url: str, tool_names: List[str]):
    tools = []
    async def _load():
        client = MultiServerMCPClient({{"main": {{"transport": "sse", "url": f"{{url}}/sse"}}}})
        available = await client.get_tools()
        for t in available:
            if t.name in tool_names:
                tools.append(t)
        return tools
    return asyncio.run(_load())

# =====================================================
# 5️⃣ Output schema
# =====================================================
class LLMResponse(BaseModel):
    session_id: str
    timestamp: str
    status: str
    answer: str
    selected_agents: List[str] = []

parser = PydanticOutputParser(pydantic_object=LLMResponse)

# =====================================================
# 6️⃣ Wrap MCP tools dynamically
# =====================================================
def make_mcp_langchain_tool(sync_tool: SyncStringMCPTool):
    tool_name = sync_tool.name.replace("-", "_")
    def _tool(question: str) -> str:
        """MCP tool: {{sync_tool.name}} - forwards input and returns response verbatim"""
        return sync_tool.run(question)
    _tool.__name__ = tool_name
    return tool(return_direct=True)(_tool)

TOOL_NAMES = {tool_names_str}
mcp_tools = load_mcp_tools_sync("{mcp_url}", TOOL_NAMES)

wrapped_tools = [
    make_mcp_langchain_tool(SyncStringMCPTool(t))
    for t in mcp_tools
]

# =====================================================
# 7️⃣ LLM
# =====================================================
llm = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    deployment_name=AZURE_OPENAI_MODEL,
    temperature=0
)

llm_with_tools = llm.bind_tools(wrapped_tools)

# =====================================================
# 8️⃣ Prompt
# =====================================================
prompt = ChatPromptTemplate.from_messages([
    ("system", """{{system_prompt}}

You MUST return ONLY valid JSON following this schema:
{{format_instructions}}
Do NOT include explanations, markdown, or text outside JSON.
Do NOT wrap the JSON in code blocks.

If you use a tool, place the tool's output in the "answer" field."""),
    ("system", "Conversation history:\\n{{memory}}"),
    ("human", """{{question}}

Fill the JSON fields as follows:
- session_id: use the provided session_id
- timestamp: use the provided timestamp
- status: always "SUCCESS"
- answer: the final answer text (tool output if used)
- selected_agents: list of tool names used (empty if none)""")
])

# =====================================================
# 9️⃣ Main execution
# =====================================================
def main():
    try:
        input_data = json.loads(sys.stdin.read())
        session_id = input_data["session_id"]
        question = input_data["question"]
        timestamp = input_data["timestamp"]

        ##print(f"Processing session: {{session_id}}, question: {{question}}", file=sys.stderr)
        memory = load_memory(session_id)
        ##print(f"Loaded memory: {{memory[:100]}}...", file=sys.stderr)

        chain = prompt.partial(
            system_prompt="""{system_prompts}""",
            format_instructions=parser.get_format_instructions()
        ) | llm_with_tools | parser

        result = chain.invoke({{
            "question": question,
            "memory": memory,
            "session_id": session_id,
            "timestamp": timestamp
        }})

        save_memory(session_id, question, result.selected_agents, result.answer)

        response = {{
            "session_id": session_id,
            "timestamp": timestamp,
            "status": result.status,
            "answer": result.answer,
            "selected_agents": result.selected_agents
        }}
        ##print(json.dumps(response, ensure_ascii=False, indent=2))

    except Exception as e:
        import traceback
        #traceback.##print_exc(file=sys.stderr)
        try:
            if mcp_tools:
                fallback_tool = SyncStringMCPTool(mcp_tools[0])
                answer = fallback_tool.run(question)
                selected_agents = [mcp_tools[0].name]
            else:
                answer = f"Error: {{str(e)}}"
                selected_agents = []

            save_memory(session_id, question, selected_agents, answer)
            response = {{
                "session_id": session_id,
                "timestamp": timestamp,
                "status": "SUCCESS",
                "answer": answer,
                "selected_agents": selected_agents
            }}
            print(json.dumps(response, ensure_ascii=False, indent=2))
        except Exception as fallback_error:
            error_response = {{
                "session_id": session_id,
                "timestamp": timestamp,
                "status": "ERROR",
                "answer": f"Error processing request: {{str(e)}}",
                "selected_agents": []
            }}
            print(json.dumps(error_response, ensure_ascii=False, indent=2))
            sys.exit(1)

if __name__ == "__main__":
    main()
'''
    ##print(script_template)
    # Write to output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(script_template)

    ##print(f"✅ MCP agent script with PostgreSQL memory generated at: {output_file}")