from turtle import pd
from typing import Sequence, Optional, Dict, Any, List
import textwrap

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.messages import AIMessage
from IPython.display import HTML, display

import tdfs4ds
from tdfs4ds import logger_safe

import teradataml as tdml
import json
import ast
import re
import sqlparse

from teradataml.context.context import _get_database_username
import pandas as pd

from tdfs4ds.process_store.process_store_catalog_management import get_process_info


def _robust_json_parser(response: str) -> Dict[str, Any]:
    """
    Robustly extract and parse JSON from LLM responses.
    Handles markdown code fences, escaped characters, and formatting variations.
    
    Parameters
    ----------
    response : str
        The raw response string from the LLM.
    
    Returns
    -------
    dict
        The parsed JSON as a dictionary.
    
    Raises
    ------
    ValueError
        If JSON cannot be extracted or parsed from the response.
    """
    if not isinstance(response, str):
        raise ValueError(f"Expected string response, got {type(response)}")
    
    # Try 1: Direct JSON parse (response might already be clean)
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # Try 2: Extract from markdown code fences (most flexible)
    # Match opening backticks (with optional json language specifier) and closing backticks
    # Using non-greedy matching with DOTALL to handle multiline content
    markdown_patterns = [
        r'```(?:json)?\s*\n(.*)\n```',         # ```json\n...\n``` (any content in middle)
        r'```(?:json)?\s*\r?\n(.*?)\r?\n```',  # Handle Windows line endings
        r'```(?:json)?\s*(.*?)\s*```',         # ```...``` (flexible whitespace)
        r'`{3}\s*(?:json)?\s*(.*?)\s*`{3}',    # Alternative triple backticks
    ]
    for pattern in markdown_patterns:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            try:
                extracted = match.group(1).strip()
                # Normalize line endings
                extracted = extracted.replace('\r\n', '\n').replace('\r', '\n')
                if extracted:  # Only try if we got something
                    return json.loads(extracted)
            except (json.JSONDecodeError, IndexError):
                pass
    
    # Try 3: Extract first { ... } block (handles extra text before/after)
    first_brace = response.find('{')
    last_brace = response.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        try:
            extracted = response[first_brace:last_brace+1]
            # Normalize line endings
            extracted = extracted.replace('\r\n', '\n').replace('\r', '\n')
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass
    
    # Try 4: Remove markdown fences and retry
    # Aggressively strip all markdown code fence markers
    cleaned = response.strip()
    cleaned = re.sub(r'^```\s*(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned)
    cleaned = re.sub(r'^`+\s*', '', cleaned)
    cleaned = re.sub(r'\s*`+$', '', cleaned)
    cleaned = cleaned.strip()
    # Normalize line endings
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try 5: As a last resort, try ast.literal_eval (for Python-like dicts)
    try:
        import ast
        # Normalize line endings
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        return ast.literal_eval(cleaned)
    except (ValueError, SyntaxError):
        pass
    
    # If all else fails, raise informative error
    logger_safe('error', f'Failed to parse JSON from LLM response. Full response: {response}')
    raise ValueError(f"Could not extract valid JSON from response. First 200 chars: {response[:200]}")


# HTML Styling Constants
HTML_STYLES = {
    "container": "font-family: Arial, sans-serif; margin: 10px 0;",
    "title": "color: #1f618d; margin-bottom: 6px;",
    "heading": "color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;",
    "heading_margin": "color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; margin-top: 15px;",
    "content": "background-color: #ecf0f1; padding: 10px; border-radius: 5px; line-height: 1.6;",
    "list": "background-color: #ecf0f1; padding: 15px 30px; border-radius: 5px; line-height: 1.8;",
}


def _is_notebook() -> bool:
    """Check if code is running in a Jupyter notebook."""
    try:
        # Check if IPython is available
        from IPython import get_ipython
        ipython = get_ipython()
        if ipython is None:
            return False
        
        # Check for notebook kernel
        if hasattr(ipython, 'kernel') and ipython.kernel is not None:
            return True
        
        # Check config for IPKernelApp (notebook kernel)
        if hasattr(ipython, 'config') and 'IPKernelApp' in ipython.config:
            return True
            
        # Check if it's a ZMQInteractiveShell (notebook shell)
        if ipython.__class__.__name__ == 'ZMQInteractiveShell':
            return True
            
        # Check for ipykernel in sys.modules
        import sys
        if 'ipykernel' in sys.modules:
            return True
            
        return False
    except (ImportError, AttributeError, Exception):
        return False


def _build_provider_llm_caller(llm: ChatOpenAI, provider: str, schema: Optional[Dict] = None):
    """
    Build a provider-specific LLM call wrapper for constrained output.

    Parameters
    ----------
    llm : ChatOpenAI
        The language model interface.
    provider : str
        The LLM provider (vllm, openai, ollama, azure, etc).
    schema : dict, optional
        JSON schema for constrained output.

    Returns
    -------
    callable
        A function that invokes the LLM with appropriate constraints.
    """
    if schema is None:
        return lambda messages: llm.invoke(messages)

    provider_l = provider.lower()

    if provider_l in ("vllm", "openai-compatible"):
        return lambda messages: llm.invoke(messages, extra_body={"guided_json": schema})
    
    if provider_l in ("openai", "azure", "azure-openai"):
        return lambda messages: llm.invoke(messages, response_format=schema)
    
    if provider_l == "ollama":
        return lambda messages: llm.invoke(messages, format=schema)
    
    # Fallback: no constraints
    return lambda messages: llm.invoke(messages)


def _print_documentation(
    documented_sql: str,
    entity_description: str,
    documented_entity_columns: Dict[str, str],
    documented_feature_columns: Dict[str, str],
    process_id: Optional[str] = None,
    view_name: Optional[str] = None,
    explain_analysis: Optional[str] = None,
    optimization_score: Optional[int] = None,
    explain_warnings: Optional[List[str]] = None,
    explain_recommendations: Optional[List[str]] = None,
    sql_query: Optional[str] = None,
    explain_plan: Optional[str] = None,
) -> None:
    """
    Pretty print documentation with context-aware formatting.
    Uses HTML in notebooks, text format in regular scripts.

    Parameters
    ----------
    documented_sql : str
        The query business logic description.
    entity_description : str
        The entity description.
    documented_entity_columns : dict
        Mapping of entity column names to descriptions.
    documented_feature_columns : dict
        Mapping of feature column names to descriptions.
    process_id : str, optional
        The process identifier for the title.
    view_name : str, optional
        The view name for the title.
    explain_analysis : str, optional
        The EXPLAIN plan analysis description.
    optimization_score : int, optional
        Optimization score from 1 to 5.
    explain_warnings : list, optional
        List of warnings from EXPLAIN analysis.
    explain_recommendations : list, optional
        List of recommendations from EXPLAIN analysis.
    sql_query : str, optional
        The original SQL query to display.
    explain_plan : str, optional
        The raw EXPLAIN plan output to display.
    """
    title = ''
    if process_id or view_name:
        title_parts = []
        if process_id:
            title_parts.append(f"Process: {process_id}")
        if view_name:
            title_parts.append(f"View: {view_name}")
        title = ' — '.join(title_parts)

    # Helpers to parse structured items and clean markdown (available in both contexts)
    def _try_parse_structured(value):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if not isinstance(value, str):
            return value
        s = value.strip()
        # Try JSON
        try:
            return json.loads(s)
        except Exception:
            pass
        # Try Python literal
        try:
            return ast.literal_eval(s)
        except Exception:
            pass
        return s

    def _flatten_to_list(parsed):
        if parsed is None:
            return []
        if isinstance(parsed, list):
            out = []
            for it in parsed:
                out.extend(_flatten_to_list(it))
            return out
        if isinstance(parsed, dict):
            # Prefer obvious value keys, else format key: value pairs
            for k in ("issue", "warning", "action", "recommendation", "msg", "message"):
                if k in parsed:
                    return [str(parsed[k])]
            return ["; ".join(f"{kk}: {vv}" for kk, vv in parsed.items())]
        return [str(parsed)]

    def _strip_md(s: str) -> str:
        # Remove **bold** and inline markdown emphasis for plain text
        s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
        s = re.sub(r"\*(.*?)\*", r"\1", s)
        return s

    def _md_to_html(s: str) -> str:
        # Convert **bold** to <strong>
        s = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.*?)\*\*", r"<em>\1</em>", s)
        # Escape simple < and > to avoid broken HTML (keep basic newlines)
        s = s.replace("<", "&lt;").replace(">", "&gt;")
        # Restore our strong/em tags
        s = s.replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
        s = s.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
        return s

    # Build EXPLAIN section if available
    parsed_explain = _try_parse_structured(explain_analysis)
    parsed_warnings = _try_parse_structured(explain_warnings)
    parsed_recs = _try_parse_structured(explain_recommendations)

    warn_list = _flatten_to_list(parsed_warnings)
    rec_list = _flatten_to_list(parsed_recs)

    explain_section = ""
    newline = '\n'
    if parsed_explain or optimization_score or warn_list or rec_list:
        score_color = "#27ae60" if optimization_score and optimization_score >= 4 else "#f39c12" if optimization_score and optimization_score == 3 else "#e74c3c"
        explain_section = f"""
            <h3 style="{HTML_STYLES['heading_margin']}">Query Optimization Analysis</h3>
            <div style="background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <p><strong>Optimization Score:</strong> <span style="color: {score_color}; font-size: 18px; font-weight: bold;">{optimization_score}/5</span></p>
            </div>
            """

        if parsed_explain:
            # Display explanation as plain text, preserving newlines
            explain_text = parsed_explain if isinstance(parsed_explain, str) else str(parsed_explain)
            explain_text_html = explain_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(newline, '<br>')
            explain_section += f'<div style="{HTML_STYLES["content"]}">{explain_text_html}</div>'

        if warn_list:
            warnings_html = '\n'.join(f'<li style="color: #c0392b;">{_md_to_html(w).replace(newline,'<br>')}</li>' for w in warn_list)
            explain_section += f"""
            <h4 style="color: #c0392b; margin-top: 10px;">⚠ Warnings</h4>
            <ul style="{HTML_STYLES['list']}">{warnings_html}</ul>
            """

        if rec_list:
            recommendations_html = '\n'.join(f'<li style="color: #27ae60;">{_md_to_html(r).replace(newline,'<br>')}</li>' for r in rec_list)
            explain_section += f"""
            <h4 style="color: #27ae60; margin-top: 10px;">✓ Recommendations</h4>
            <ul style="{HTML_STYLES['list']}">{recommendations_html}</ul>
            """

    if _is_notebook():
        title_html = f"<h2>{title}</h2>" if title else ""
        entity_items = '\n'.join(f'<li><strong>{col}:</strong> {_md_to_html(desc)}</li>' for col, desc in documented_entity_columns.items())
        feature_items = '\n'.join(f'<li><strong>{col}:</strong> {_md_to_html(desc)}</li>' for col, desc in documented_feature_columns.items())
        
        # Build optional sections
        sql_section = ""
        if sql_query:
            formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case='upper')
            sql_section = f"""
            <h3 style="{HTML_STYLES['heading_margin']}">Original SQL Query</h3>
            <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; font-family: 'Courier New', monospace; font-size: 12px; overflow-x: auto; white-space: pre-wrap;">{formatted_sql}</pre>
            """
        
        explain_plan_section = ""
        if explain_plan:
            explain_plan_section = f"""
            <h3 style="{HTML_STYLES['heading_margin']}">EXPLAIN Plan</h3>
            <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; font-family: 'Courier New', monospace; font-size: 12px; overflow-x: auto; white-space: pre-wrap;">{explain_plan}</pre>
            """
        
        html_content = f"""
        <div style="{HTML_STYLES['container']}">
        {title_html}
        <h3 style="{HTML_STYLES['heading']}">Query Business Logic</h3>
        <p style="{HTML_STYLES['content']}">{documented_sql}</p>
        
        <h3 style="{HTML_STYLES['heading_margin']}">Entity Description</h3>
        <p style="{HTML_STYLES['content']}">{entity_description}</p>
        
        <h3 style="{HTML_STYLES['heading_margin']}">Entity Columns</h3>
        <ul style="{HTML_STYLES['list']}">{entity_items}</ul>
        
        <h3 style="{HTML_STYLES['heading_margin']}">Feature Columns</h3>
        <ul style="{HTML_STYLES['list']}">{feature_items}</ul>
        
        {explain_section}
        {sql_section}
        {explain_plan_section}
        </div>
        """
        display(HTML(html_content))
    else:
        # Text formatting for regular scripts
        print("\n" + "="*100)
        print(title if title else "DOCUMENTATION")
        print("="*100)
        print("\nQuery Business Logic:")
        print(textwrap.fill(documented_sql, width=100))
        
        print("\nEntity Description:")
        print(textwrap.fill(entity_description, width=100))
        
        print("\nEntity Columns Documentation:")
        for col, desc in documented_entity_columns.items():
            print(f"\n  {col}:")
            print(textwrap.fill(desc, width=95, initial_indent="    ", subsequent_indent="    "))
        
        print("\nFeature Columns Documentation:")
        for col, desc in documented_feature_columns.items():
            print(f"\n  {col}:")
            print(textwrap.fill(desc, width=95, initial_indent="    ", subsequent_indent="    "))
        
        # Print EXPLAIN analysis if available
        if explain_analysis or optimization_score or explain_warnings or explain_recommendations:
            print("\n" + "-"*100)
            print("QUERY OPTIMIZATION ANALYSIS")
            print("-"*100)
            
            if optimization_score:
                print(f"Optimization Score: {optimization_score}/5")
            
            # Print parsed explanation, preserving carriage returns.
            if parsed_explain:
                print("\nExplanation:")
                if isinstance(parsed_explain, str):
                    print(parsed_explain)
                else:
                    print(str(parsed_explain))

            # Print warnings (flattened) preserving carriage returns
            if warn_list:
                print("\nWarnings:")
                for w in warn_list:
                    print(f"  - {w}")

            # Print recommendations (flattened) preserving carriage returns
            if rec_list:
                print("\nRecommendations:")
                for r in rec_list:
                    print(f"  - {r}")

        # Print original SQL query if provided
        if sql_query:
            print("\n" + "-"*100)
            print("ORIGINAL SQL QUERY")
            print("-"*100)
            formatted_sql = sqlparse.format(sql_query, reindent=True, keyword_case='upper')
            print(textwrap.indent(formatted_sql, '    '))

        # Print EXPLAIN plan if provided
        if explain_plan:
            print("\n" + "-"*100)
            print("EXPLAIN PLAN")
            print("-"*100)
            print(explain_plan)

        print("\n" + "="*100 + "\n")


def build_llm(
    llm_service: str = "https://api-dmproject.myddns.me/v1",
    api_key: str = "YOUR_API_KEY_HERE",
    model_id: str = "mistralai/Ministral-3-14B-Instruct-2512",
    temperature: float = 0.0,
    timeout: int = 120,
) -> ChatOpenAI:
    """
    Build and return a ChatOpenAI client pointed at your vLLM/OpenAI-compatible endpoint.

    Parameters
    ----------
    llm_service : str
        Base URL of the LLM service.
    api_key : str
        API key for authentication.
    model_id : str
        Model identifier.
    temperature : float
        Sampling temperature for response diversity.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    ChatOpenAI
        Configured LLM client.

    Raises
    ------
    Exception
        If LLM client creation fails.
    """
    logger_safe('info', f'build_llm: Using LLM service at {llm_service} with model {model_id}')
    logger_safe('debug', f'build_llm: Temperature={temperature}, Timeout={timeout}s')

    try:
        return ChatOpenAI(
            base_url=llm_service,
            api_key=api_key,
            model=model_id,
            temperature=temperature,
            timeout=timeout,
        )
    except Exception as e:
        logger_safe('error', f'build_llm: Failed to create LLM client: {e}')
        raise


from typing import Sequence

def build_documentation_json_schema(columns: List[str], provider: str = "generic") -> Dict[str, Any]:
    """
    Build a provider-appropriate JSON Schema used to enforce strict JSON output
    for SQL column documentation across multiple LLM backends.

    This function returns different schema shapes depending on the LLM provider,
    because each ecosystem uses a different structured-output mechanism:

    Provider Modes
    --------------
    - provider="openai", "azure"
        Returns the JSON Schema wrapped in OpenAI's `response_format={"type": "json_schema", ...}`
        structure. Supported by GPT-4.1, GPT-4o, GPT-3.5-Turbo, and Azure OpenAI.

    - provider="anthropic", "claude"
        Returns an Anthropic *tool schema* definition. Claude 3.x models use tool
        schemas to enforce strict JSON output.

    - provider="ollama"
        Returns the raw JSON schema that Ollama expects under the `format=` parameter
        of the generate API. (Ollama 0.2+ supports response schemas.)

    - provider="vllm"
        Returns plain JSON Schema for use with vLLM's `guided_json` constrained decoding.

    - provider="bedrock"
        Bedrock Claude follows the Anthropic tool schema format.
        Bedrock Llama / Titan accept plain JSON schema. This function returns the base
        schema and leaves the final wrapping to the caller.

    - provider="generic"
        Returns plain JSON schema. Useful for LLM backends that do not support
        constrained decoding, prompt-only JSON generation, or post-processing repair.

    Parameters
    ----------
    columns : list[str]
        Column names to include as required JSON object keys. Each column will map
        to a string description generated by the model.

    provider : str, optional
        The model provider or backend type. Determines the structural format
        required for constrained generation. One of:
        "openai", "anthropic", "ollama", "vllm", "bedrock", "generic".

    Returns
    -------
    dict
        A dictionary representing the JSON Schema or provider-specific wrapper
        used to enforce strict JSON output during LLM generation.

    Notes
    -----
    - All schemas require that:
        * the output be a JSON object
        * keys match exactly the column names
        * all values be strings
        * additional properties be disallowed

    - Not all providers enforce schemas equally:
        * OpenAI, Claude, and vLLM offer hard guarantees.
        * Ollama enforces schema reasonably well.
        * Generic models may require post-processing.
    """
    # Base JSON schema — used directly by vLLM, Ollama, Bedrock, fallback
    base_schema = {
        "type": "object",
        "properties": {col: {"type": "string"} for col in columns},
        "required": list(columns),
        "additionalProperties": False,
    }

    # --- Provider-specific formats ---

    if provider.lower() in ("openai", "azure", "azure-openai"):
        # OpenAI's required wrapper structure
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ColumnDocumentation",
                "schema": base_schema,
                "strict": True,
            }
        }

    if provider.lower() in ("anthropic", "claude"):
        # Anthropic tool schema
        # You embed this inside the "tools" field when calling the model
        return {
            "name": "column_documentation",
            "description": "Generate documentation for SQL output columns.",
            "input_schema": base_schema
        }

    if provider.lower() == "ollama":
        # Ollama's output format schema (unwrapped JSON schema)
        # Returned directly in: generate(..., format=schema)
        return base_schema

    if provider.lower() in ("vllm", "openai-compatible"):
        # vLLM's guided_json uses *plain JSON Schema*
        # so return base_schema exactly
        return base_schema

    if provider.lower() == "bedrock":
        # Bedrock Claude uses Anthropic schema
        # Bedrock Llama uses plain JSON schema
        # Return base_schema and let caller choose
        return base_schema

    # Fallback: generic JSON schema
    return base_schema


def build_sql_documentation_chain(
    llm: ChatOpenAI,
    entity_columns: Sequence[str],
    feature_columns: Sequence[str],
    provider: str = "vllm",
    json_constraint: bool = True,
) -> Runnable:
    """
    Build a LangChain Runnable that generates business-focused documentation
    for lists of entity and feature columns from a SQL query output, with optional provider-specific JSON
    constraints (vLLM, OpenAI, Ollama, etc.).

    The resulting chain expects two input variables:
        - sql_query: str         → the SQL query whose output is being documented
        - columns_str: str       → formatted list of entity and feature columns (e.g. "Entity columns:\n- col1\n\nFeature columns:\n- col2")

    Parameters
    ----------
    llm : ChatOpenAI
        The language model interface (may point to vLLM, OpenAI, Ollama, etc.).
    entity_columns : Sequence[str]
        List of entity/identifier columns that must appear as keys in the output JSON.
    feature_columns : Sequence[str]
        List of feature columns that must appear as keys in the output JSON.
    provider : str, optional (default="vllm")
        Indicates which structured-output mechanism to use.
        Supported values:
            - "vllm"               → uses `guided_json` for strict JSON output
            - "openai" / "azure"   → uses OpenAI JSON Schema via `response_format`
            - "ollama"             → uses Ollama's `format=` schema
            - "openai-compatible"  → alias for vLLM-style guided decoding
            - any other value      → fall back to unconstrained text output
    json_constraint : bool, optional (default=True)
        If True:
            - a JSON Schema is generated from the column lists
            - provider-specific constrained decoding is applied
        If False:
            - the chain does not enforce JSON structure at the LLM level
            - the model is only guided by the prompt (weaker guarantees)

    Returns
    -------
    Runnable
        A LangChain Runnable that executes:
            prompt → LLM (optionally schema-guided) → JSON parser

        When invoked with:
            {
                "sql_query": "...",
                "columns_str": "Entity columns:\n- column1\n\nFeature columns:\n- column2\n..."
            }

        It returns:
            dict[str, str]
                A mapping of each requested column name to a short,
                business-oriented description (≤ 5 sentences), plus a 'query_business_logic' key
                containing a high-level description of the query's business logic (5-10 sentences), and an 'entity_description' key
                with a holistic description of the entity (3-5 sentences).

    Notes
    -----
    - The chain enforces valid JSON when possible:
        * vLLM → `guided_json`
        * OpenAI → `response_format={"type": "json_schema", ...}`
        * Ollama → `format=<schema>`
    - For unsupported providers, the model may emit imperfect JSON.
    - Descriptions focus on business meaning, business logic,
      and optionally technical details only when relevant.
    """
    all_columns = entity_columns + feature_columns + ["query_business_logic", "entity_description"]
    logger_safe('info', f'build_sql_documentation_chain: Building chain for provider {provider}, json_constraint={json_constraint}, entity_columns={list(entity_columns)}, feature_columns={list(feature_columns)}')
    prompt = ChatPromptTemplate.from_template(
        """
You are a data documentation assistant.

Your target audience is business users.
Your explanations must focus primarily on the business meaning and business logic of each column,
and you may add technical details only when they meaningfully clarify the business context.

Given:
1. A SQL query.
2. Lists of entity and feature columns that must be documented.

Your job:
- For entity columns: Provide a brief 1-sentence description of how this column contributes to identifying the entity described holistically under 'entity_description'. Do not repeat the full entity description here.
- For feature columns: Write a clear and concise explanation of what the column represents from a business perspective, describing the business logic behind how the value is derived or used within the context of the SQL query.
- Add technical details only if relevant and only to help a business audience understand the concept.
- Each description must be at most 5 sentences.
- Do not include any columns that are not in the provided lists.
- If a column name is ambiguous, infer its meaning from the SQL query as best as possible and say so.
- If you cannot infer anything meaningful, state that clearly (still within 3 sentences).
- Additionally, provide a high-level description of the business logic of the SQL query itself under the key 'query_business_logic'. This should explain what the query does from a business perspective, including the main purpose, data sources, transformations, and business value. Keep it to 5-10 sentences.
- Additionally, provide a description of the entity as a whole under the key 'entity_description'. This should describe the business object that the entity columns collectively identify, noting that this is the object the features describe. Keep it to 3-5 sentences.
- Avoid using double quotes (") in the explanation text; use single quotes or rephrase to prevent JSON parsing errors.
- Answer in {language}
Output format (very important):
- Return ONLY a valid JSON object.
- Each top-level key must be exactly the column name or 'query_business_logic'.
- Each value must be a single string with the description.

Example of the required format:
{{
  "customer_id": "This column serves as the primary key for identifying individual customers in the entity.",
  "order_date": "The business date when the order was created. It represents the transaction date used for reporting and may reflect the source system's timestamp.",
  "entity_description": "The customer entity represents individual buyers in the business system, identified by customer_id and described by features like order history and demographics. This entity is the core object that the feature columns characterize for analysis and decision-making.",
  "query_business_logic": "This query joins customer and order data to provide a comprehensive view of customer orders. It filters orders from 2024 onwards to focus on recent activity. The result helps business users understand customer purchasing patterns and regional distribution."
}}

Now generate documentation.

SQL query:
```sql
{sql_query}
```
Columns to document (only document these):
{columns_str}
"""
    )
    parser = JsonOutputParser()
    if not json_constraint:
        return prompt | llm | parser

    schema = build_documentation_json_schema(all_columns, provider=provider)
    logger_safe('debug', f'build_sql_documentation_chain: Using provider {provider} with json_constraint={json_constraint}')

    # Use helper to build provider-specific LLM caller
    call_llm = _build_provider_llm_caller(llm, provider, schema)
    constrained_llm = RunnableLambda(call_llm)

    # Final chain: prompt -> LLM (schema-guided) -> JSON parser
    def _parse(ai_msg: AIMessage):
        raw = ai_msg.content
        return parser.parse(raw)

    return prompt | constrained_llm | RunnableLambda(_parse)

def run_sql_documentation(
    chain: Runnable,
    sql_query: str,
    entity_columns: Sequence[str],
    feature_columns: Sequence[str],
    language: str = "English",
) -> Dict[str, str]:
    """
    Execute a previously constructed SQL-documentation chain and return
    business-friendly documentation for the specified SQL output columns.

    This function prepares the chain inputs (SQL query, formatted column list,
    target language) and invokes the chain. The chain itself must have been
    created using `build_sql_documentation_chain()`, which ensures the model
    produces structured JSON suitable for parsing.

    Parameters
    ----------
    chain : Runnable
        A LangChain Runnable returned by `build_sql_documentation_chain()`.
        This Runnable encapsulates:
            - the prompt template
            - a provider-specific LLM invocation (with or without JSON constraints)
            - a JSON output parser

    sql_query : str
        The SQL query whose resulting columns should be documented. This query is
        shown to the model so it can infer business logic, derivation rules, and
        column meaning.

    entity_columns : Sequence[str]
        The list of entity/identifier column names that must appear as keys in the output JSON.
        Only these columns will be documented. The order does not matter.

    feature_columns : Sequence[str]
        The list of feature column names that must appear as keys in the output JSON.
        Only these columns will be documented. The order does not matter.

    language : str, optional (default="English")
        The target output language for the generated documentation.
        This value is passed into the prompt’s `{language}` variable.
        Examples: "English", "French", "German", "Spanish", "Japanese".

    Returns
    -------
    dict[str, str]
        A dictionary mapping each column name to a human-readable, business-oriented
        description generated by the model, plus a 'query_business_logic' key
        with the query's business logic description, and an 'entity_description' key
        with the holistic entity description. Example:
            {
                "customer_id": "Unique customer identifier used for ...",
                "order_date": "Business date when the order was created ...",
                "entity_description": "The customer entity represents...",
                "query_business_logic": "This query provides a view of ..."
            }

    Notes
    -----
    - The output format is determined by the chain's JSON parser. If the model
      fails to produce valid JSON (e.g., due to unsupported constraints),
      a `OutputParserException` may be raised.
    - The resulting descriptions are typically ≤ 5 sentences per column, unless
      modified in the chain's prompt.
    """
    logger_safe('info', f'run_sql_documentation: Starting documentation for {len(entity_columns)} entity columns and {len(feature_columns)} feature columns in {language}')
    columns_str = "Entity columns:\n" + "\n".join(f"- {col}" for col in entity_columns) + "\n\nFeature columns:\n" + "\n".join(f"- {col}" for col in feature_columns)

    try:
        result = chain.invoke({
            "sql_query": sql_query,
            "columns_str": columns_str,
            "language" : language
        })
        logger_safe('info', f'run_sql_documentation: Successfully generated documentation for columns: {list(result.keys())}')
        return result
    except Exception as e:
        logger_safe('error', f'run_sql_documentation: Failed to generate documentation: {e}')
        raise


def document_sql_query_columns(
    sql_query: str,
    entity_columns: Sequence[str],
    feature_columns: Sequence[str],
    language: str = "English",
    provider: Optional[str] = None,
    json_constraint: bool = True,
) -> Dict[str, Any]:
    """
    Convenience function to generate business-focused documentation for SQL query output columns
    using the configured instruction model from tdfs4ds settings.

    This function automatically builds the LLM client using the tdfs4ds configuration variables
    (INSTRUCT_MODEL_URL, INSTRUCT_MODEL_API_KEY, INSTRUCT_MODEL_MODEL), constructs the documentation
    chain, and executes it to produce column descriptions.

    Parameters
    ----------
    sql_query : str
        The SQL query whose resulting columns should be documented. This query is
        shown to the model so it can infer business logic, derivation rules, and
        column meaning.

    entity_columns : Sequence[str]
        The list of entity/identifier column names that must appear as keys in the output JSON.
        Only these columns will be documented. The order does not matter.

    feature_columns : Sequence[str]
        The list of feature column names that must appear as keys in the output JSON.
        Only these columns will be documented. The order does not matter.

    language : str, optional (default="English")
        The target output language for the generated documentation.
        This value is passed into the prompt's {language} variable.
        Examples: "English", "French", "German", "Spanish", "Japanese".

    provider : str, optional (default=None)
        Indicates which structured-output mechanism to use for the LLM.
        If None, uses INSTRUCT_MODEL_PROVIDER from tdfs4ds config.
        Supported values:
            - "vllm"               → uses `guided_json` for strict JSON output
            - "openai" / "azure"   → uses OpenAI JSON Schema via `response_format`
            - "ollama"             → uses Ollama's `format=` schema
            - "openai-compatible"  → alias for vLLM-style guided decoding
            - any other value      → fall back to unconstrained text output

    json_constraint : bool, optional (default=True)
        If True:
            - a JSON Schema is generated from the column lists
            - provider-specific constrained decoding is applied
        If False:
            - the chain does not enforce JSON structure at the LLM level
            - the model is only guided by the prompt (weaker guarantees)

    Returns
    -------
    dict
        A dictionary with four keys:
        - "query_business_logic": str containing the high-level business logic description of the query
        - "entity_description": str containing the holistic description of the entity
        - "entity_columns": dict[str, str] mapping each entity column name to its description
        - "feature_columns": dict[str, str] mapping each feature column name to its description

    Raises
    ------
    ValueError
        If any of the required tdfs4ds configuration variables (INSTRUCT_MODEL_URL,
        INSTRUCT_MODEL_API_KEY, INSTRUCT_MODEL_MODEL) are not set.

    Notes
    -----
    - This function requires that the tdfs4ds instruction model configuration is properly set.
    - The resulting descriptions are typically ≤ 5 sentences per column, focusing on
      business meaning and logic.
    - If the model fails to produce valid JSON, an exception will be raised.
    """
    # Import the configuration variables
    from tdfs4ds import INSTRUCT_MODEL_URL, INSTRUCT_MODEL_API_KEY, INSTRUCT_MODEL_MODEL, INSTRUCT_MODEL_PROVIDER

    # Validate configuration
    if not INSTRUCT_MODEL_URL or not INSTRUCT_MODEL_API_KEY or not INSTRUCT_MODEL_MODEL or not INSTRUCT_MODEL_PROVIDER:
        raise ValueError(
            "tdfs4ds instruction model configuration is incomplete. Please ensure "
            "INSTRUCT_MODEL_URL, INSTRUCT_MODEL_API_KEY, INSTRUCT_MODEL_MODEL, and INSTRUCT_MODEL_PROVIDER are set."
        )

    logger_safe('info', f'document_sql_query_columns: Starting documentation for {len(entity_columns)} entity columns and {len(feature_columns)} feature columns in {language}')

    if provider is None:
        provider = INSTRUCT_MODEL_PROVIDER

    # Build the LLM client
    llm = build_llm(
        llm_service=INSTRUCT_MODEL_URL,
        api_key=INSTRUCT_MODEL_API_KEY,
        model_id=INSTRUCT_MODEL_MODEL
    )

    # Build the documentation chain
    sql_doc_chain = build_sql_documentation_chain(llm, entity_columns, feature_columns, provider=provider, json_constraint=json_constraint)

    # Run the documentation
    result = run_sql_documentation(sql_doc_chain, sql_query, entity_columns, feature_columns, language=language)

    # Separate entity columns, feature columns, entity description, and query logic
    entity_docs = {k: v for k, v in result.items() if k in entity_columns}
    feature_docs = {k: v for k, v in result.items() if k in feature_columns}
    entity_desc = result.get("entity_description", "")
    query_logic = result.get("query_business_logic", "")

    logger_safe('info', f'document_sql_query_columns: Successfully completed documentation for {len(entity_docs)} entity columns, {len(feature_docs)} feature columns, entity description and query logic')
    return {
        "query_business_logic": query_logic,
        "entity_description": entity_desc,
        "entity_columns": entity_docs,
        "feature_columns": feature_docs
    }


def build_explain_documentation_chain(
    llm: ChatOpenAI,
    provider: str = "vllm",
    json_constraint: bool = True,
) -> Runnable:
    """
    Build a LangChain Runnable that analyzes SQL EXPLAIN plans and generates
    optimization scores, warnings, and recommendations.

    The resulting chain expects two input variables:
        - sql_query: str       → the original SQL query
        - explain_plan: str    → the EXPLAIN output from the database

    Parameters
    ----------
    llm : ChatOpenAI
        The language model interface (may point to vLLM, OpenAI, Ollama, etc.).
    provider : str, optional (default="vllm")
        Indicates which structured-output mechanism to use.
        Supported values:
            - "vllm"               → uses `guided_json` for strict JSON output
            - "openai" / "azure"   → uses OpenAI JSON Schema via `response_format`
            - "ollama"             → uses Ollama's `format=` schema
            - "openai-compatible"  → alias for vLLM-style guided decoding
            - any other value      → fall back to unconstrained text output
    json_constraint : bool, optional (default=True)
        If True: a JSON Schema is generated and provider-specific constrained decoding is applied.
        If False: the chain does not enforce JSON structure at the LLM level.

    Returns
    -------
    Runnable
        A LangChain Runnable that executes:
            prompt → LLM (optionally schema-guided) → JSON parser

        When invoked with:
            {
                "sql_query": "SELECT ...",
                "explain_plan": "..."
            }

        It returns:
            dict with keys:
                - "explanation": str describing the EXPLAIN plan in business terms
                - "optimization_score": int from 1 (poorly optimized) to 5 (well optimized)
                - "warnings": list[str] of potential issues or concerns
                - "recommendations": list[str] of actionable optimization suggestions
    """
    logger_safe('info', f'build_explain_documentation_chain: Building chain for provider {provider}, json_constraint={json_constraint}')
    
    # JSON schema for EXPLAIN analysis output
    explain_schema = {
        "type": "object",
        "properties": {
            "explanation": {"type": "string"},
            "optimization_score": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "Score from 1 (poorly optimized) to 5 (well optimized)"
            },
            "warnings": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of potential issues or concerns"
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of actionable optimization suggestions"
            }
        },
        "required": ["explanation", "optimization_score", "warnings", "recommendations"],
        "additionalProperties": False
    }

    prompt = ChatPromptTemplate.from_template(
        """
You are an expert SQL query optimization analyst.

Your task is to analyze a SQL EXPLAIN plan and provide optimization guidance.

Provide your analysis in the following JSON format with these exact keys:
- explanation: A clear, plain-text explanation of what the EXPLAIN plan shows. Include analysis of execution strategy, estimated costs, and any visible inefficiencies.
- optimization_score: An integer from 1 to 5 (1 = poorly optimized, 5 = well optimized)
- warnings: An array of warning strings about potential issues
- recommendations: An array of actionable recommendation strings for improvement

Analysis Guidelines:
- Focus on execution strategy, index usage, and join efficiency
- Be detailed but business-friendly, avoiding unnecessary technical jargon
- Consider factors like: full table scans vs index usage, join strategies, data distribution
- Avoid using double quotes (") in the explanation text; use single quotes or rephrase to prevent JSON parsing errors

Scoring Guidelines:
- Score 1: Multiple full table scans, no indexes, inefficient joins
- Score 2: Some index usage but still room for improvement, potentially expensive operations
- Score 3: Reasonable query plan, acceptable performance, some optimization opportunities
- Score 4: Good query plan with mostly optimized joins and indexes, minor improvements possible
- Score 5: Excellent plan with efficient execution, proper use of indexes, optimal join strategies

Warnings should highlight specific concerns (e.g., 'Full table scan on large table ORDERS', 'Missing index on customer_id column').
Recommendations should be specific and actionable (e.g., 'Add index on orders.customer_id', 'Consider using a different join strategy').

Output format (very important):
- Return ONLY a valid JSON object.
- Each top-level key must be exactly 'explanation', 'optimization_score', 'warnings', or 'recommendations'.
- The 'explanation' value must be a single string.
- The 'optimization_score' value must be an integer from 1 to 5.
- The 'warnings' value must be an array of strings.
- The 'recommendations' value must be an array of strings.

Example of the required format:
{{
  "explanation": "The EXPLAIN plan shows a nested loop join between the customers and orders tables. The query performs a full table scan on the orders table, which has an estimated 1 million rows. The join condition uses the customer_id column, but there is no index on this column in the orders table.",
  "optimization_score": 2,
  "warnings": ["Full table scan on large orders table", "Missing index on orders.customer_id"],
  "recommendations": ["Add index on orders.customer_id", "Consider using a hash join instead of nested loop"]
}}

SQL Query:
```sql
{sql_query}
```

EXPLAIN Plan:
```
{explain_plan}
```

Return ONLY valid JSON with the four keys above.
"""
    )
    parser = JsonOutputParser()
    if not json_constraint:
        return prompt | llm | parser

    logger_safe('debug', f'build_explain_documentation_chain: Using provider {provider} with json_constraint={json_constraint}')

    # Wrap schema for OpenAI providers
    if provider.lower() in ("openai", "azure", "azure-openai"):
        wrapped_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "ExplainAnalysis",
                "schema": explain_schema,
                "strict": True,
            }
        }
    else:
        wrapped_schema = explain_schema

    # Use helper to build provider-specific LLM caller
    call_llm = _build_provider_llm_caller(llm, provider, wrapped_schema)
    constrained_llm = RunnableLambda(call_llm)

    # Final chain: prompt -> LLM (schema-guided) -> JSON parser
    def _parse(ai_msg: AIMessage):
        raw = ai_msg.content
        return parser.parse(raw)

    return prompt | constrained_llm | RunnableLambda(_parse)


def run_explain_documentation(
    chain: Runnable,
    sql_query: str,
    explain_plan: str,
) -> Dict[str, Any]:
    """
    Execute an EXPLAIN-documentation chain and return optimization analysis.

    Parameters
    ----------
    chain : Runnable
        A LangChain Runnable returned by `build_explain_documentation_chain()`.
    sql_query : str
        The original SQL query.
    explain_plan : str
        The EXPLAIN output from the database.

    Returns
    -------
    dict
        A dictionary with keys: "explanation", "optimization_score", "warnings", "recommendations"
    """
    logger_safe('info', 'run_explain_documentation: Starting EXPLAIN analysis')
    
    try:
        result = chain.invoke({
            "sql_query": sql_query,
            "explain_plan": explain_plan
        })
        logger_safe('info', f'run_explain_documentation: Successfully analyzed EXPLAIN plan. Score: {result.get("optimization_score", "N/A")}/5')
        return result
    except Exception as e:
        logger_safe('error', f'run_explain_documentation: Failed to analyze EXPLAIN plan: {e}')
        raise


def document_sql_query_explain(
    sql_query: str,
    provider: Optional[str] = None,
    json_constraint: bool = True,
) -> Dict[str, Any]:
    """
    Analyze a SQL query's EXPLAIN plan and return optimization recommendations.

    This function automatically builds the LLM client using tdfs4ds configuration,
    constructs the EXPLAIN analysis chain, and executes it.

    Parameters
    ----------
    sql_query : str
        The original SQL query.
    explain_plan : str
        The EXPLAIN output from the database.
    provider : str, optional (default=None)
        Indicates which structured-output mechanism to use for the LLM.
        If None, uses INSTRUCT_MODEL_PROVIDER from tdfs4ds config.
        Supported values: "vllm", "openai", "azure", "ollama", etc.
    json_constraint : bool, optional (default=True)
        If True: use provider-specific constrained decoding.
        If False: rely on prompt guidance only.

    Returns
    -------
    dict
        A dictionary with keys:
        - "explanation": str describing the EXPLAIN plan
        - "optimization_score": int from 1 to 5
        - "warnings": list[str] of potential issues
        - "recommendations": list[str] of actionable suggestions

    Raises
    ------
    ValueError
        If tdfs4ds instruction model configuration is incomplete.
    """
    from tdfs4ds import INSTRUCT_MODEL_URL, INSTRUCT_MODEL_API_KEY, INSTRUCT_MODEL_MODEL, INSTRUCT_MODEL_PROVIDER

    if not INSTRUCT_MODEL_URL or not INSTRUCT_MODEL_API_KEY or not INSTRUCT_MODEL_MODEL or not INSTRUCT_MODEL_PROVIDER:
        raise ValueError(
            "tdfs4ds instruction model configuration is incomplete. Please ensure "
            "INSTRUCT_MODEL_URL, INSTRUCT_MODEL_API_KEY, INSTRUCT_MODEL_MODEL, and INSTRUCT_MODEL_PROVIDER are set."
        )

    logger_safe('info', 'document_sql_query_explain: Starting EXPLAIN analysis')

    if provider is None:
        provider = INSTRUCT_MODEL_PROVIDER

    # Build the LLM client
    llm = build_llm(
        llm_service=INSTRUCT_MODEL_URL,
        api_key=INSTRUCT_MODEL_API_KEY,
        model_id=INSTRUCT_MODEL_MODEL
    )

    # get the explain plan:
    explain_plan = get_the_explain(sql_query)
    # Build and run the EXPLAIN analysis chain
    explain_chain = build_explain_documentation_chain(llm, provider=provider, json_constraint=json_constraint)
    result = run_explain_documentation(explain_chain, sql_query, explain_plan)

    logger_safe('info', f'document_sql_query_explain: Successfully completed EXPLAIN analysis. Score: {result.get("optimization_score", "N/A")}/5')
    return result

def documentation_tables_creation():
    """
    Create the necessary documentation tables in the database if they do not already exist.
    tdml: The tdfs4ds TDML connection object."""
    query_process_table = f"""
    CREATE MULTISET TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_BUSINESS_LOGIC} ,FALLBACK ,
         NO BEFORE JOURNAL,
         NO AFTER JOURNAL,
         CHECKSUM = DEFAULT,
         DEFAULT MERGEBLOCKRATIO,
         MAP = TD_MAP1
         (
          PROCESS_ID VARCHAR(36) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
          BUSINESS_LOGIC_DESCRIPTION VARCHAR(32000) CHARACTER SET LATIN NOT CASESPECIFIC,
          ENTITY_DESCRIPTION VARCHAR(32000) CHARACTER SET LATIN NOT CASESPECIFIC,
          ENTITY_COLUMNS_JSON VARCHAR(32000) CHARACTER SET LATIN NOT CASESPECIFIC,
          ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
          ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
          PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME)
    PRIMARY INDEX ( PROCESS_ID )
    """

    query_process_features_table = f"""
    CREATE MULTISET TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_FEATURES} ,FALLBACK ,
         NO BEFORE JOURNAL,
         NO AFTER JOURNAL,
         CHECKSUM = DEFAULT,
         DEFAULT MERGEBLOCKRATIO,
         MAP = TD_MAP1
         (
          PROCESS_ID VARCHAR(36) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
          FEATURE_ID BIGINT NOT NULL,
          FEATURE_NAME VARCHAR(255) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
          FEATURE_DESCRIPTION VARCHAR(32000) CHARACTER SET LATIN NOT CASESPECIFIC,
          ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
          ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
          PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME)
    PRIMARY INDEX ( PROCESS_ID, FEATURE_ID )
    """

    query_process_explain_table = f"""
    CREATE MULTISET TABLE {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_EXPLAIN} ,FALLBACK ,
         NO BEFORE JOURNAL,
         NO AFTER JOURNAL,
         CHECKSUM = DEFAULT,
         DEFAULT MERGEBLOCKRATIO,
         MAP = TD_MAP1
         (
          PROCESS_ID VARCHAR(36) CHARACTER SET LATIN NOT CASESPECIFIC NOT NULL,
          EXPLAIN_ANALYSIS VARCHAR(32000) CHARACTER SET LATIN NOT CASESPECIFIC,
          OPTIMIZATION_SCORE INT,
          WARNINGS VARCHAR(32000) CHARACTER SET LATIN NOT CASESPECIFIC,
          RECOMMENDATIONS VARCHAR(32000) CHARACTER SET LATIN NOT CASESPECIFIC,
          ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
          ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
          PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME)
    PRIMARY INDEX ( PROCESS_ID )
    """

    try:
        tdml.execute_sql(query_process_table)
        logger_safe('info', f'documentation_tables_creation: Created table {tdfs4ds.DOCUMENTATION_PROCESS_BUSINESS_LOGIC}')
    except Exception as e:
        logger_safe('error', f'documentation_tables_creation: Failed to create table {tdfs4ds.DOCUMENTATION_PROCESS_BUSINESS_LOGIC}: {e}')
        if 'already exists' in str(e).lower():
            logger_safe('info', f'documentation_tables_creation: Table {tdfs4ds.DOCUMENTATION_PROCESS_BUSINESS_LOGIC} already exists. Skipping creation.')
            pass
        else:
            raise
    try:
        tdml.execute_sql(query_process_features_table)
        logger_safe('info', f'documentation_tables_creation: Created table {tdfs4ds.DOCUMENTATION_PROCESS_FEATURES}')
    except Exception as e:
        logger_safe('error', f'documentation_tables_creation: Failed to create table {tdfs4ds.DOCUMENTATION_PROCESS_FEATURES}: {e}')
        if 'already exists' in str(e).lower():
            logger_safe('info', f'documentation_tables_creation: Table {tdfs4ds.DOCUMENTATION_PROCESS_FEATURES} already exists. Skipping creation.')
            pass
        else:
            raise

    try:
        tdml.execute_sql(query_process_explain_table)
        logger_safe('info', f'documentation_tables_creation: Created table {tdfs4ds.DOCUMENTATION_PROCESS_EXPLAIN}')
    except Exception as e:
        logger_safe('error', f'documentation_tables_creation: Failed to create table {tdfs4ds.DOCUMENTATION_PROCESS_EXPLAIN}: {e}')
        if 'already exists' in str(e).lower():
            logger_safe('info', f'documentation_tables_creation: Table {tdfs4ds.DOCUMENTATION_PROCESS_EXPLAIN} already exists. Skipping creation.')
            pass
        else:
            raise
    
    logger_safe('info', 'documentation_tables_creation: Documentation tables creation process completed.')
    return

def document_process(process_id: str, language: str = "English", json_constraint: bool = True, show_sql_query: bool = False, show_explain_plan: bool = False, display: bool = True, upload: bool = True) -> Optional[Dict[str, Any]]:
    """
    Generate and store documentation for a data process identified by process_id.
    This function retrieves the SQL query and output columns for the process,
    generates business-focused documentation using an LLM, and stores the results
    in the appropriate documentation tables.

    Parameters
    ----------
    process_id : str
        The unique identifier of the data process to document.

    language : str, optional (default="English")
        The target output language for the generated documentation. This value is   
        passed into the prompt’s `{language}` variable. Examples: "English", "French", "German", "Spanish", "Japanese".
    provider : str, optional (default=None)
        Indicates which structured-output mechanism to use for the LLM.
        If None, uses INSTRUCT_MODEL_PROVIDER from tdfs4ds config.
        Supported values:
            - "vllm"               → uses `guided_json` for strict JSON output
            - "openai" / "azure"   → uses OpenAI JSON Schema via `response_format`
            - "ollama"             → uses Ollama's `format=` schema
            - "openai-compatible"  → alias for vLLM-style guided decoding
            - any other value      → fall back to unconstrained text output
    json_constraint : bool, optional (default=True)
        If True:
            - a JSON Schema is generated from the column list
            - provider-specific constrained decoding is applied 
        If False:
            - the chain does not enforce JSON structure at the LLM level
            - the model is only guided by the prompt (weaker guarantees)
    show_sql_query : bool, optional (default=False)
        If True, display the original SQL query at the end of the documentation report.
    show_explain_plan : bool, optional (default=False)
        If True, display the raw EXPLAIN plan output at the end of the documentation report.
    display : bool, optional (default=True)
        If True, print the generated documentation to the console.
    upload_documentation : bool, optional (default=True)
        If True, upload the generated documentation to the documentation tables.

    Returns
    -------
    dict or None
        A dictionary containing the generated documentation and analysis, or None if an error occurred.
        The dictionary includes keys:
            - PROCESS_ID
            - DOCUMENTED_SQL
            - ENTITY_DESCRIPTION
            - DOCUMENTED_ENTITY_COLUMNS
            - DOCUMENTED_FEATURE_COLUMNS
            - EXPLAIN_ANALYSIS (if show_explain_plan is True)
            - OPTIMIZATION_SCORE (if show_explain_plan is True)
            - EXPLAIN_WARNINGS (if show_explain_plan is True)
            - EXPLAIN_RECOMMENDATIONS (if show_explain_plan is True)
            - RAW_EXPLAIN_PLAN (if show_explain_plan is True)
    Notes
    -----
    - This function requires that the tdfs4ds instruction model configuration is properly set.
    - If the model fails to produce valid JSON, an exception will be raised.
    - The resulting descriptions are typically ≤ 5 sentences per column, focusing on
      business meaning and logic.
    """
    logger_safe('info', f'document_process: Starting documentation for process_id {process_id} in {language}')

    # Retrieve process SQL and columns
    try:
        process_info = tdfs4ds.process_store.process_store_catalog_management.get_process_info(process_id)
    except Exception as e:
        logger_safe('error', f"document_process: Error retrieving process info for process_id {process_id}: {e}")
        return  
    
    documentation = document_sql_query_columns(
            sql_query       = process_info['PROCESS_SQL'],
            entity_columns  = process_info['ENTITY_COLUMNS'],
            feature_columns = process_info['FEATURE_COLUMNS']
        )
    
    process_info['DOCUMENTED_SQL']             = documentation['query_business_logic']
    process_info['ENTITY_DESCRIPTION']         = documentation['entity_description']
    process_info['DOCUMENTED_ENTITY_COLUMNS']  = documentation['entity_columns']
    process_info['DOCUMENTED_FEATURE_COLUMNS'] = documentation['feature_columns']

    if True:
        explain_documentation = document_sql_query_explain(
                sql_query = process_info['PROCESS_SQL']
            )
        
        process_info['EXPLAIN_ANALYSIS'] = explain_documentation['explanation']
        process_info['OPTIMIZATION_SCORE'] = explain_documentation['optimization_score']
        process_info['EXPLAIN_WARNINGS'] = explain_documentation['warnings']       
        process_info['EXPLAIN_RECOMMENDATIONS'] = explain_documentation['recommendations']
        
        # Store the raw EXPLAIN plan if needed for display
        if show_explain_plan:
            process_info['RAW_EXPLAIN_PLAN'] = get_the_explain(process_info['PROCESS_SQL'])
    
    # Upload the generated documentation to the documentation tables:
    if upload:
        upload_documentation(process_info)
        logger_safe('info', f'document_process: Uploaded documentation for process_id {process_id} to documentation tables.')
        upload_documentation_explain(process_info)
        logger_safe('info', f'document_process: Uploaded EXPLAIN analysis for process_id {process_id} to documentation tables.')

    # pretty print documentation for info:
    logger_safe('info', f"document_process: Documentation for process_id {process_id}:")

    if display:
        _print_documentation(
            documented_sql             = process_info.get('DOCUMENTED_SQL', None),
            entity_description         = process_info.get('ENTITY_DESCRIPTION', None),
            documented_entity_columns  = process_info.get('DOCUMENTED_ENTITY_COLUMNS', None),
            documented_feature_columns = process_info.get('DOCUMENTED_FEATURE_COLUMNS', None),
            process_id                 = process_info.get('PROCESS_ID', process_id),
            view_name                  = process_info.get('VIEW_NAME', None),
            explain_analysis           = process_info.get('EXPLAIN_ANALYSIS', None),
            optimization_score         = process_info.get('OPTIMIZATION_SCORE', None),
            explain_warnings           = process_info.get('EXPLAIN_WARNINGS', None),
            explain_recommendations    = process_info.get('EXPLAIN_RECOMMENDATIONS', None),
            sql_query                  = process_info.get('PROCESS_SQL', None) if show_sql_query else None,
            explain_plan               = process_info.get('RAW_EXPLAIN_PLAN', None) if show_explain_plan else None,
        ) 

    return process_info

def get_the_explain(sql_query: str) -> str:
    """
    Get the EXPLAIN plan for a given SQL query using the tdfs4ds TDML connection.

    Parameters
    ----------
    sql_query : str
        The SQL query to explain.

    Returns
    -------
    str
        The EXPLAIN plan as a formatted string.
    """
    def _extract_inner_query_from_view(query: str) -> str:
        """
        If the provided SQL is a CREATE/REPLACE VIEW (or REPLACE VIEW), extract and
        return the inner SELECT/definition. Otherwise return the original query.

        This helps when running EXPLAIN: we want to analyze the query inside the
        view definition rather than the DDL wrapper.
        """
        if not isinstance(query, str):
            return query
        pattern = r'^\s*(?:CREATE\s+(?:OR\s+REPLACE\s+)?|REPLACE\s+)?VIEW\b.*?\bAS\b\s*(?P<body>.*)$'
        m = re.search(pattern, query, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return query
        body = m.group('body').strip()
        # Strip outer parentheses if the definition is wrapped
        if body.startswith('(') and body.endswith(')'):
            body = body[1:-1].strip()
        # Remove trailing semicolon
        if body.endswith(';'):
            body = body[:-1].strip()
        # Remove trailing LOCK ROW FOR ACCESS (or similar) clauses that may appear
        # in view definitions (e.g., "LOCK ROW FOR ACCESS") so EXPLAIN focuses
        # on the inner SELECT statement.
        body = re.sub(r"\bLOCK\s+ROW\s+FOR\s+ACCESS\b\s*;?\s*$", "", body, flags=re.IGNORECASE)
        logger_safe('debug', 'get_the_explain: Extracted inner query from CREATE/REPLACE VIEW for EXPLAIN.')
        return body

    inner_sql = _extract_inner_query_from_view(sql_query)
    try:
        explain_result = tdml.execute_sql(f"EXPLAIN {inner_sql}").fetchall()
        explain_lines = [row[0] for row in explain_result]
        explain_text = "\n".join(explain_lines)
        logger_safe('info', 'get_the_explain: Successfully retrieved EXPLAIN plan.')
        return explain_text
    except Exception as e:
        logger_safe('error', f'get_the_explain: Failed to retrieve EXPLAIN plan: {e}')
        raise

def upload_documentation(process_info: Dict[str, Any]) -> None:
    """
    Upload the generated documentation for a data process into the documentation tables.

    Parameters
    ----------
    process_info : dict
        A dictionary containing the process documentation information.
        Expected keys:
            - PROCESS_ID: str
            - DOCUMENTED_SQL: str
            - ENTITY_DESCRIPTION: str
            - DOCUMENTED_ENTITY_COLUMNS: dict[str, str]
            - DOCUMENTED_FEATURE_COLUMNS: dict[str, str]
    """

    process_id          = process_info['PROCESS_ID']
    documented_sql      = process_info['DOCUMENTED_SQL']
    entity_description  = process_info['ENTITY_DESCRIPTION']
    entity_columns_json = json.dumps(process_info['DOCUMENTED_ENTITY_COLUMNS'])
    feature_columns     = process_info['DOCUMENTED_FEATURE_COLUMNS']

    # build a pandas dataframe containing the data to be uploaded in DOCUMENTATION_PROCESS_BUSINESS_LOGIC
    # that contains PROCESS_ID, BUSINESS_LOGIC_DESCRIPTION, ENTITY_DESCRIPTION, ENTITY_COLUMNS_JSON
    df_business_logic = pd.DataFrame([{
        'PROCESS_ID': process_id,
        'BUSINESS_LOGIC_DESCRIPTION': documented_sql,
        'ENTITY_DESCRIPTION': entity_description,
        'ENTITY_COLUMNS_JSON': entity_columns_json
    }])

    # build a pandas dataframe containing the data to be uploaded in DOCUMENTATION_PROCESS_FEATURES
    # that contains PROCESS_ID, FEATURE_ID, FEATURE_DESCRIPTION
    # at this stage, FEATURE_ID is not known, so we will use the FEATURE_NAME as a placeholder
    # and later replace it with the actual FEATURE_ID after insertion with a join with the FS_FEATURE_CATALOG
    # here we need to explode the feature_columns dict into multiple rows
    feature_rows = []
    for feature_name, feature_description in feature_columns.items():
        feature_rows.append({
            'PROCESS_ID': process_id,
            'FEATURE_NAME': feature_name,  # placeholder for FEATURE_ID
            'FEATURE_DESCRIPTION': feature_description
        })
    df_features = pd.DataFrame(feature_rows)

    # Determine end period based on tdfs4ds configuration
    if tdfs4ds.END_PERIOD == 'UNTIL_CHANGED':
        end_period_ = '9999-01-01 00:00:00' 
    else:
        end_period_ = tdfs4ds.END_PERIOD
    
    # upload the df_business_logic dataframe into a staging volatile table
    logger_safe('info', f'upload_documentation: Uploading documentation for process_id {process_id} into staging tables.')
    tdml.copy_to_sql(
        df_business_logic,
        table_name = "DOCUMENTATION_PROCESS_BUSINESS_LOGIC_STAGING",
        if_exists  = 'replace',
        temporary  = True
    )
    logger_safe('info', f'upload_documentation: Uploaded business logic documentation for process_id {process_id} into staging table.')

    # upload the df_features dataframe into a staging volatile table
    logger_safe('info', f'upload_documentation: Uploading feature documentation for process_id {process_id} into staging tables.')
    tdml.copy_to_sql(
        df_features,
        table_name = "DOCUMENTATION_PROCESS_FEATURES_STAGING",
        if_exists  = 'replace',
        temporary  = True
    )
    logger_safe('info', f'upload_documentation: Uploaded feature documentation for process_id {process_id} into staging table.')

    # merge into DOCUMENTATION_PROCESS_BUSINESS_LOGIC from staging table
    query_insert_business_logic =  f"""
    CURRENT VALIDTIME
    MERGE INTO {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_BUSINESS_LOGIC} EXISTING
    USING (
        SELECT
            PROCESS_ID,
            BUSINESS_LOGIC_DESCRIPTION,
            ENTITY_DESCRIPTION,
            ENTITY_COLUMNS_JSON
        FROM {_get_database_username()}.DOCUMENTATION_PROCESS_BUSINESS_LOGIC_STAGING
    ) UPDATED
    ON EXISTING.PROCESS_ID = UPDATED.PROCESS_ID
    WHEN MATCHED THEN
        UPDATE
        SET
            BUSINESS_LOGIC_DESCRIPTION = UPDATED.BUSINESS_LOGIC_DESCRIPTION,
            ENTITY_DESCRIPTION         = UPDATED.ENTITY_DESCRIPTION,
            ENTITY_COLUMNS_JSON       = UPDATED.ENTITY_COLUMNS_JSON
    WHEN NOT MATCHED THEN
    INSERT (
        UPDATED.PROCESS_ID,
        UPDATED.BUSINESS_LOGIC_DESCRIPTION,
        UPDATED.ENTITY_DESCRIPTION,
        UPDATED.ENTITY_COLUMNS_JSON
        )   
    """

    # merge into DOCUMENTATION_PROCESS_FEATURES from staging table
    query_insert_features =  f"""
    CURRENT VALIDTIME
    MERGE INTO {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_FEATURES} EXISTING
    USING (
        SELECT
            A.PROCESS_ID,
            FC.FEATURE_ID,
            A.FEATURE_NAME,
            A.FEATURE_DESCRIPTION
        FROM {_get_database_username()}.DOCUMENTATION_PROCESS_FEATURES_STAGING A
        INNER JOIN {tdfs4ds.SCHEMA}.{tdfs4ds.FEATURE_CATALOG_NAME} FC
        ON UPPER(FC.FEATURE_NAME) = UPPER(A.FEATURE_NAME)
        AND UPPER(FC.DATA_DOMAIN) = '{process_info['DATA_DOMAIN'].upper()}'
    ) UPDATED
    ON EXISTING.PROCESS_ID = UPDATED.PROCESS_ID
    AND EXISTING.FEATURE_ID = UPDATED.FEATURE_ID
    WHEN MATCHED THEN
        UPDATE
        SET
            FEATURE_DESCRIPTION = UPDATED.FEATURE_DESCRIPTION,
            FEATURE_NAME        = UPDATED.FEATURE_NAME
    WHEN NOT MATCHED THEN
        INSERT (
            UPDATED.PROCESS_ID,
            UPDATED.FEATURE_ID,
            UPDATED.FEATURE_NAME,
            UPDATED.FEATURE_DESCRIPTION
        )
    """

    # Remove features that are no longer present in the documentation
    query_delete_missing_features = f"""
    CURRENT VALIDTIME
    DELETE FROM {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_FEATURES}
    WHERE PROCESS_ID = '{process_id}'
    AND FEATURE_ID NOT IN (
        SELECT FC.FEATURE_ID
        FROM {_get_database_username()}.DOCUMENTATION_PROCESS_FEATURES_STAGING A
        INNER JOIN {tdfs4ds.SCHEMA}.{tdfs4ds.FEATURE_CATALOG_NAME} FC
        ON UPPER(FC.FEATURE_NAME) = UPPER(A.FEATURE_NAME)
        AND UPPER(FC.DATA_DOMAIN) = '{process_info['DATA_DOMAIN'].upper()}'
    )
    """

    # Execute the merges
    try:
        tdml.execute_sql(query_insert_business_logic)
        logger_safe('info', f'upload_documentation: Merged business logic documentation for process_id {process_id} into main table.')
    except Exception as e:
        logger_safe('error', f'upload_documentation: Failed to merge business logic documentation for process_id {process_id}: {e}')
        print(query_insert_business_logic)
        raise
    try:
        tdml.execute_sql(query_insert_features)
        logger_safe('info', f'upload_documentation: Merged feature documentation for process_id {process_id} into main table.') 
    except Exception as e:
        logger_safe('error', f'upload_documentation: Failed to merge feature documentation for process_id {process_id}: {e}')
        print(query_insert_features)
        raise
    try:
        tdml.execute_sql(query_delete_missing_features)
        logger_safe('info', f'upload_documentation: Removed missing features for process_id {process_id} from main table.') 
    except Exception as e:
        logger_safe('error', f'upload_documentation: Failed to remove missing features for process_id {process_id}: {e}')
        print(query_delete_missing_features)
        raise

    # remove staging tables
    tdml.execute_sql(f"DROP TABLE {_get_database_username()}.DOCUMENTATION_PROCESS_BUSINESS_LOGIC_STAGING")
    tdml.execute_sql(f"DROP TABLE {_get_database_username()}.DOCUMENTATION_PROCESS_FEATURES_STAGING")
    logger_safe('info', f'upload_documentation: Successfully uploaded documentation for process_id {process_id}.')

    return

def retrieve_documentation(process_id: str) -> Dict[str, Any]:
    """
    Retrieve the documentation for a data process from the documentation tables.

    Parameters
    ----------
    process_id : str
        The unique identifier of the data process.

    Returns
    -------
    dict
        A dictionary containing the documentation information with keys:
            - documented_sql: str
            - entity_description: str
            - documented_entity_columns: dict[str, str]
            - documented_feature_columns: dict[str, str]
    """
    logger_safe('info', f'retrieve_documentation: Retrieving documentation for process_id {process_id}.')

    # Retrieve business logic documentation
    query_business_logic = f"""
    CURRENT VALIDTIME
    SELECT
        BUSINESS_LOGIC_DESCRIPTION,
        ENTITY_DESCRIPTION,
        ENTITY_COLUMNS_JSON
    FROM {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_BUSINESS_LOGIC}
    WHERE PROCESS_ID = '{process_id}'
    """
    result_bl = tdml.execute_sql(query_business_logic).fetchone()
    if not result_bl:
        logger_safe('warning', f'retrieve_documentation: No business logic documentation found for process_id {process_id}.')
        return {}

    documented_sql      = result_bl[0]
    entity_description  = result_bl[1]
    entity_columns_json = result_bl[2]
    documented_entity_columns = json.loads(entity_columns_json) if entity_columns_json else {}

    # Retrieve feature documentation
    query_features = f"""
    CURRENT VALIDTIME
    SELECT
        FC.FEATURE_NAME,
        DPF.FEATURE_DESCRIPTION
    FROM {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_FEATURES} DPF
    INNER JOIN {tdfs4ds.SCHEMA}.{tdfs4ds.FEATURE_CATALOG_NAME} FC
    ON DPF.FEATURE_ID    = FC.FEATURE_ID
    WHERE DPF.PROCESS_ID = '{process_id}'
    """
    result_features = tdml.execute_sql(query_features).fetchall()
    documented_feature_columns = {
        row[0]: row[1] for row in result_features
    }

    logger_safe('info', f'retrieve_documentation: Successfully retrieved documentation for process_id {process_id}.')
    return {
        "DOCUMENTED_SQL"             : documented_sql,
        "ENTITY_DESCRIPTION"         : entity_description,
        "DOCUMENTED_ENTITY_COLUMNS"  : documented_entity_columns,
        "DOCUMENTED_FEATURE_COLUMNS" : documented_feature_columns
    }

def retrieve_explain_documentation(process_id: str) -> Dict[str, Any]:
    """
    Retrieve the EXPLAIN documentation for a data process from the documentation tables.

    Parameters
    ----------
    process_id : str
        The unique identifier of the data process.

    Returns
    -------
    dict
        A dictionary containing the EXPLAIN documentation information with keys:
            - explanation: str
            - optimization_score: int
            - warnings: list[str]
            - recommendations: list[str]
    """
    logger_safe('info', f'retrieve_explain_documentation: Retrieving EXPLAIN documentation for process_id {process_id}.')

    query_explain = f"""
    CURRENT VALIDTIME
    SELECT
        EXPLAIN_ANALYSIS,
        OPTIMIZATION_SCORE,
        WARNINGS,
        RECOMMENDATIONS
    FROM {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_EXPLAIN}
    WHERE PROCESS_ID = '{process_id}'
    """
    result_explain = tdml.execute_sql(query_explain).fetchone()
    if not result_explain:
        logger_safe('warning', f'retrieve_explain_documentation: No EXPLAIN documentation found for process_id {process_id}.')
        return {}

    explanation         = result_explain[0]
    optimization_score  = result_explain[1]
    warnings            = json.loads(result_explain[2]) if result_explain[2] else []
    recommendations     = json.loads(result_explain[3]) if result_explain[3] else []

    logger_safe('info', f'retrieve_explain_documentation: Successfully retrieved EXPLAIN documentation for process_id {process_id}.')
    return {
        "EXPLAIN_ANALYSIS"        : explanation,
        "OPTIMIZATION_SCORE"      : optimization_score,
        "EXPLAIN_WARNINGS"        : warnings,
        "EXPLAIN_RECOMMENDATIONS" : recommendations
    }

def upload_documentation_explain(process_info: Dict[str, Any]) -> None:
    """
    Upload the EXPLAIN documentation for a data process into the documentation tables.

    Parameters
    ----------
    process_id : str
        The unique identifier of the data process.
    explain_documentation : dict
        A dictionary containing the EXPLAIN documentation information with keys:
            - explanation: str
            - optimization_score: int
            - warnings: list[str]
            - recommendations: list[str]
    """

    explanation         = process_info['EXPLAIN_ANALYSIS']
    optimization_score  = process_info['OPTIMIZATION_SCORE']
    warnings_json       = json.dumps(process_info['EXPLAIN_WARNINGS'])
    recommendations_json= json.dumps(process_info['EXPLAIN_RECOMMENDATIONS'])
    process_id          = process_info['PROCESS_ID']

    # merge into DOCUMENTATION_PROCESS_EXPLAIN
    query_insert_explain =  f"""
    CURRENT VALIDTIME
    MERGE INTO {tdfs4ds.SCHEMA}.{tdfs4ds.DOCUMENTATION_PROCESS_EXPLAIN} EXISTING
    USING (
        SELECT
            '{process_id}' AS PROCESS_ID,
            '{explanation.replace("'", "''")}' AS EXPLAIN_ANALYSIS,
            {optimization_score} AS OPTIMIZATION_SCORE,
            '{warnings_json.replace("'", "''")}' AS WARNINGS,
            '{recommendations_json.replace("'", "''")}' AS RECOMMENDATIONS
    ) UPDATED
    ON EXISTING.PROCESS_ID = UPDATED.PROCESS_ID
    WHEN MATCHED THEN
        UPDATE
        SET
            EXPLAIN_ANALYSIS   = UPDATED.EXPLAIN_ANALYSIS,
            OPTIMIZATION_SCORE = UPDATED.OPTIMIZATION_SCORE,
            WARNINGS           = UPDATED.WARNINGS,
            RECOMMENDATIONS    = UPDATED.RECOMMENDATIONS
    WHEN NOT MATCHED THEN
        INSERT (
            UPDATED.PROCESS_ID,
            UPDATED.EXPLAIN_ANALYSIS,
            UPDATED.OPTIMIZATION_SCORE,
            UPDATED.WARNINGS,
            UPDATED.RECOMMENDATIONS
        )
    """

    # Execute the merge
    try:
        tdml.execute_sql(query_insert_explain)
        logger_safe('info', f'upload_documentation_explain: Uploaded EXPLAIN documentation for process_id {process_id}.')
    except Exception as e:
        logger_safe('error', f'upload_documentation_explain: Failed to upload EXPLAIN documentation for process_id {process_id}: {e}')
        raise

    return

def display_process_info(process_info: Dict[str, Any] = None, process_id : str = None) -> None:
    """
    Pretty print the documentation and EXPLAIN analysis for a data process from process_info dict or by retrieving it using process_id.

    Parameters
    ----------
    process_info : dict, optional (default=None)
        A dictionary containing the process documentation information.
        If None, process_id must be provided to retrieve the information.
    process_id : str, optional (default=None)
        The unique identifier of the data process.
        If process_info is None, this parameter is used to retrieve the documentation.
    -----------
    Returns
    None
    """

    if process_info is None:
        if process_id is None:
            raise ValueError("Either process_info or process_id must be provided.")
        logger_safe('info', f'display_process_info: Retrieving documentation for process_id {process_id}.')
        process_info = get_process_info(process_id)

    # pretty print documentation for info:
    _print_documentation(
        documented_sql             = process_info.get('DOCUMENTED_SQL', None),
        entity_description         = process_info.get('ENTITY_DESCRIPTION', None),
        documented_entity_columns  = process_info.get('DOCUMENTED_ENTITY_COLUMNS', None),
        documented_feature_columns = process_info.get('DOCUMENTED_FEATURE_COLUMNS', None),
        process_id                 = process_info.get('PROCESS_ID', None),
        view_name                  = process_info.get('VIEW_NAME', None),
        explain_analysis           = process_info.get('EXPLAIN_ANALYSIS', None),
        optimization_score         = process_info.get('OPTIMIZATION_SCORE', None),
        explain_warnings           = process_info.get('EXPLAIN_WARNINGS', None),
        explain_recommendations    = process_info.get('EXPLAIN_RECOMMENDATIONS', None),
        sql_query                  = process_info.get('PROCESS_SQL', None),
    ) 
    return