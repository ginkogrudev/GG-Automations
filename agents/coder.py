# agents/coder.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from core.state import GGState

_CODER_PROMPT = """
Ти си Senior Frontend Developer и Marketing Architect в GG Solutions.
Твоята задача е да генерираш висококонвертиращи HTML/CSS Landing страници.

ПРАВИЛА ЗА ДИЗАЙН:
1. Използвай "Dark Mode" естетика: Тъмен фон (#191919), чист текст (#e8e8e8) и премиум акценти (Gold #dcae1d или Blue #003580).
2. Структурата задължително трябва да следва Hormozi: 
   - Hero Section (The Dream Outcome)
   - Проблемът (The Bleeding Neck)
   - Value Stack (Какво получават)
   - Risk Reversal (Гаранция)
3. CSS трябва да е inline в <style> тага. Кодът трябва да е готов за директно отваряне в браузър.

ВЪРНИ САМО ВАЛИДЕН HTML КОД. Без markdown (```html), без обяснителен текст преди или след кода.
"""

def coder_agent(state: GGState) -> GGState:
    state.log_agent("coder")
    
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("CODER_MODEL", "gemini-1.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2 # Малко креативност за дизайна, но строгост в кода
    )
    
    response = llm.invoke([
        ("system", _CODER_PROMPT),
        ("human", f"Създай Landing страница за: {state.user_input}")
    ])
    
    # Почистване: Ако Gemini все пак сложи Markdown тагове, ги премахваме
    html_code = response.content.replace("```html", "").replace("```", "").strip()
    
    state.final_output = html_code
    
    # ВАЖНО: Казваме на State-а, че това вече не е Markdown, а HTML!
    # Така doc_generator.py (от твоята схема) ще го запази като .html файл.
    state.output_format = "html" 
    
    return state