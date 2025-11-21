import openai
import json
import os
from duckduckgo_search import DDGS

def search_web(query):
    """Searches the web for citations."""
    try:
        results = DDGS().text(query, max_results=2)
        return "\n".join([f"- {r['title']}: {r['body']} (Source: {r['href']})" for r in results])
    except Exception as e:
        return ""

def enrich_with_research(text):
    """
    Agent 1: Researcher. Adds citations and data.
    """
    client = openai.OpenAI()
    
    # 1. Plan
    plan_prompt = "You are a Fact-Checker. Identify 2 claims in the text needing verification. Return JSON: {'queries': ['query1', 'query2']}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": plan_prompt}, {"role": "user", "content": text}],
            response_format={"type": "json_object"}
        )
        queries = json.loads(response.choices[0].message.content).get('queries', [])
    except:
        return text 

    # 2. Search
    notes = ""
    for q in queries:
        notes += f"Search: {q}\n{search_web(q)}\n"

    # 3. Edit
    edit_prompt = f"""
    You are an Editor. Rewrite the user text to include facts from the Research Notes.
    Use markdown footnotes like this[^1].
    Append references at the very end: [^1]: Source Title, URL.
    Keep the tone institutional.
    
    Research Notes: {notes}
    """
    
    final = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": edit_prompt}, {"role": "user", "content": text}]
    )
    return final.choices[0].message.content

def analyze_layout_and_data(text):
    """
    Agent 2: Art Director. Splits text into visual sections.
    """
    client = openai.OpenAI()

    system_prompt = """
    You are a Design Director for a UN-style report.
    Split the raw text into logical sections and assign a layout mode.
    
    Layout Modes:
    1. "split": Use for Introductions. (High impact, large text).
    2. "sidebar": Use for technical sections with definitions. Main text goes in 'main_text', definitions/stats in 'side_text'.
    3. "standard": Use for standard body text (2-column dense flow).
    4. "hero": Use for sections focused on a major chart.
    
    Data Extraction:
    If a section contains numbers suitable for a chart, extract them into 'chart': {'title': '...', 'data': {'Label': Value}}.

    Return JSON: 
    {
      "sections": [
        { "layout": "standard", "main_text": "...", "chart": {...} },
        { "layout": "sidebar", "main_text": "...", "side_text": "..." }
      ]
    }
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Layout Error: {e}")
        return {"sections": [{"layout": "standard", "main_text": text}]}
