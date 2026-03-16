# agents/strategist.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from core.state import GGState
from prompts.strategist import STRATEGIST_SYSTEM_PROMPT

def strategist_agent(state: GGState) -> GGState:
    state.log_agent("strategist")
    
    # Инициализираме безплатния модел на Google
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("STRATEGIST_MODEL", "gemini-1.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

    # Вземаме контекста от търсенето (ако има такова)
    context = state.enriched_context if state.enriched_context else "Няма допълнителен контекст."
    
    full_prompt = f"""
    Клиентска заявка: {state.user_input}
    Контекст от проучване: {context}
    
    Използвай примерите на GG Solutions (Tsetkovi, Elit Konstrukshun), за да генерираш Markdown документ.
    """

    response = llm.invoke([
        ("system", STRATEGIST_SYSTEM_PROMPT),
        ("human", full_prompt)
    ])
    
    state.final_output = response.content
    return state