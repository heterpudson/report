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
    1. "chapter": Use for the start of a new major section/chapter. Title is the Chapter Name.
    2. "front_matter": Use for Foreword, Preface, Introduction.
    3. "executive_summary": Use for Executive Summary (prominent front matter).
    4. "abbreviations": Use for List of Abbreviations or Acronyms.
    5. "acknowledgements": Use for Acknowledgements section.
    6. "split": Use for high-impact intro pages (Title + Text + Quote).
    7. "sidebar": Use for technical sections needing a sidebar for definitions/context.
    8. "standard": Use for standard dense content (2-column).
    9. "hero": Use for data-heavy sections (Title + Chart + Key Metrics).
    10. "box": Use for case studies or callouts (Title + Content).
    11. "references": Use for Bibliography/References.
    12. "annex": Use for Appendices/Annexes./appendices.
    
    Content Features:
    - If a section has a key insight, extract it as a 'pull_quote'.
    - If a section would benefit from an image/illustration, add 'image':
      {
        'caption': 'Figure I.1: Description',
        'generate': true,
        'prompt': 'Professional illustration showing...'
      }
      Use generate:true for AI-generated illustrations when no specific image exists.
    - If a section contains numbers suitable for a chart, extract them into 'chart': 
      {
        'title': '...', 
        'type': 'bar'|'line'|'scatter'|'horizontal_bar'|'stacked_bar',
        'data': {'Label': Value} OR [{'name': 'Series1', 'values': [...], 'labels': [...]}],
        'x_label': '...',
        'y_label': '...'
      }
      Use 'line' for time-series data, 'bar' for categorical comparisons, 'horizontal_bar' for ranked lists,
      'scatter' for correlation data, 'stacked_bar' for part-to-whole comparisons.

    Return JSON: 
    {
      "sections": [
        { "layout": "chapter", "title": "Chapter 1: The Digital Divide" },
        { "layout": "standard", "main_text": "...", "pull_quote": "Key insight...", "chart": {...} },
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
