from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from codeppr.git_helper import get_diff_file
from codeppr.tools import build_diff_line_map
from codeppr.configure import read_config
from codeppr.auth.keys import get_api_key
from pydantic import BaseModel, Field, SecretStr
from typing import List, Type, TypeVar, Sequence, Any
import asyncio
import click

MAX_PARALLEL = 4
MAX_OUTPUT_TOKENS = 2000

semaphore = asyncio.Semaphore(MAX_PARALLEL)

# Strucutured output for llms
class Issue(BaseModel):
    line: str
    description: str
    suggestion: str | None = None

class IssuesBySeverity(BaseModel):
    critical: List[Issue] = Field(default_factory=list)
    high: List[Issue] = Field(default_factory=list)
    low: List[Issue] = Field(default_factory=list)

class FileReview(BaseModel):
    issues: IssuesBySeverity

prompt = ChatPromptTemplate.from_messages([
("system", """
You are an expert senior software engineer performing a pre-commit code review.

You will be given a unified diff for EXACTLY ONE FILE.
The diff represents the staged Git changes that will be committed.
Your task is to analyze the diff and identify any potential issues.

Rules:
- Focus on correctness, security, performance, and reliability.
- Ignore purely stylistic issues unless they affect maintainability or correctness.

Classify issues into these severity levels ONLY:
- critical: will cause bugs, crashes, security issues, or data loss
- high: very likely to cause incorrect behavior or hard-to-debug issues
- low: minor risks, maintainability concerns, or best-practice improvements
- Each issue's descriptions must be concise and to the point.
- Each issue's suggestion should be a clear actionable fix or improvement in one or two sentences.
- In the lines field, include only the line/lines from the diff where the issue occurs. Prefix it with '+' only if it is an added line.

If no issues exist in a category, return an empty list. Do not make up issues.

IMPORTANT: Follow the output schema strictly.
"""),
("user", """
File path: {path}
Change status type: {status}

DIFF:
{diff}
""")])

async def safe_invoke(chain, input):
    async with semaphore:
        try:
            return await chain.ainvoke(input)
        except Exception as e:
            return e
        
async def run_review_async(chain, inputs):
    tasks = [safe_invoke(chain, i) for i in inputs]
    return await asyncio.gather(*tasks)

async def run_review(files: list[dict]) -> list[dict]:
    if not files or len(files) == 0:
        return []

    try:
        config = read_config()
        provider = config.get('provider')
        model = config.get('model')

        if not provider or not model:
            raise ValueError("Model provider and model must be configured before running review.")
        try:
            llm = create_chat_model(provider, model)
        except ValueError as e:
            click.secho(str(e), fg="red", bold=True)
            return []
        
        llm = llm.with_structured_output(FileReview)

        chain = prompt | llm

        inputs = []

        for file in files:
            diff = get_diff_file(file['path'])
            inputs.append({
                "path": file['path'],
                "status": file['status'],
                "diff": diff,
            })

        raw_results = await run_review_async(chain, inputs)
    except Exception as e:
        click.secho("Error during AI review: " + str(e), fg="red", bold=True)
        return []
    
    good_results = []
    for input,result in zip(inputs, raw_results):
        if isinstance(result, Exception):
            msg = extract_error_message(result)
            click.secho(f"\nError during AI review for {input['path']}: {msg}", fg="red", bold=True)
        else:
            good_results.append(result)

    reviews: list[FileReview] = normalize_structured_batch(
        good_results,
        FileReview,
    )

    final_result = []
    for idx, res in enumerate(reviews):
        file = inputs[idx]
        try:
            res_dict = res.model_dump()
            convert_line_number(file['diff'], res_dict['issues'])
            res_dict['path'] = file['path']
            res_dict['diff'] = file['diff']
            final_result.append(res_dict)
        except Exception as e:
            click.secho(f"Failed to parse LLM response for file {file['path']}: {str(e)}", fg="red", bold=True)
            continue
    
    return final_result

def convert_line_number(diff: str, issues: dict):
    """
    Converts the line numbers in the parsed JSON issues from diff-relative
    to absolute line numbers in the new file.
    """
    line_map = build_diff_line_map(diff)

    for severity in ['critical', 'high', 'low']:
        for issue in issues.get(severity, []):
            diff_line = issue['line']
            for line_str,line_num in line_map.items():
                if diff_line == line_str:
                    issue['line'] = str(line_num)
                    break

    return issues

def create_chat_model(provider:str, model:str):
    provider = provider.lower()

    if provider == "openai":
        api_key = get_api_key("openai")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please login using 'codeppr auth login openai' command.")
        return ChatOpenAI(
            model=model,
            max_completion_tokens=MAX_OUTPUT_TOKENS,
            api_key=SecretStr(api_key)
        )
    
    elif provider == "anthropic":
        api_key = get_api_key("anthropic")
        if not api_key:
            raise ValueError("Anthropic API key not found. Please login using 'codeppr auth login anthropic' command.")
        return ChatAnthropic(
            model_name=model,
            max_tokens_to_sample=MAX_OUTPUT_TOKENS,
            timeout=100,
            api_key=SecretStr(api_key),
            stop=["\n\n"]
        )
    
    elif provider == "gemini":
        api_key = get_api_key("gemini")
        if not api_key:
            raise ValueError("Google API key not found. Please login using 'codeppr auth login google' command.")
        return ChatGoogleGenerativeAI(
            model=model,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            api_key=SecretStr(api_key),
        )
    
    raise ValueError(f"Unsupported model provider: {provider}")

T = TypeVar("T", bound=BaseModel)

def normalize_structured_batch(
    results: Sequence[Any],
    model_cls: Type[T],
) -> list[T]:
    normalized: list[T] = []

    for item in results:
        if isinstance(item, model_cls):
            normalized.append(item)
        elif isinstance(item, dict):
            normalized.append(model_cls.model_validate(item))  # pydantic v2
        else:
            raise TypeError(f"Unexpected result type: {type(item)}")

    return normalized


def extract_error_message(err: Exception) -> str:
    """Best-effort short message compatible with OpenAI/Anthropic/Gemini errors."""
    if hasattr(err, "message") and getattr(err, "message"):
        return str(getattr(err, "message"))

    if getattr(err, "args", None):
        for arg in err.args:
            if isinstance(arg, str) and arg.strip():
                return arg.strip().splitlines()[0]

    text = str(err)
    if text:
        line = text.splitlines()[0]
        if "Error calling model" in line and "{" in line:
            line = line.split("{", 1)[0].rstrip()
        if len(line) > 200:
            line = line[:200].rstrip() + "…"
        return line

    return repr(err)
