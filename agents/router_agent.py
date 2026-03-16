# agents/router_agent.py
import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from core.state import GGState

logger = logging.getLogger(__name__)

# Separation of Concerns: Промптът е фокусиран само върху класификация
_ROUTER_PROMPT = """
Ти си диспечер (Router) в GG AI Factory.
Твоята задача е да категоризираш заявката на потребителя в ТОЧНО ЕДНА от следните категории:
- strategy (за бизнес предложения, Hormozi оферти, маркетингови одити)
- code (за създаване на уеб страници, HTML, CSS лендинг пейджове)
- prompt_engineer (за писане или подобряване на системни промптове)
- search (за проучване на пазара, намиране на данни или обобщаване на тема)
- unknown (ако заявката е неясна или не попада в горните)

ОТГОВОРИ САМО С ЕДНА ДУМА (напр. strategy). Без никакви обяснения.
"""

def router_agent(state: GGState) -> GGState:
    state.log_agent("router")
    
    # Използваме безплатния модел (config in .env)
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("ROUTER_MODEL", "gemini-1.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.0 # Искаме нулева креативност тук, само детерминиран избор
    )
    
    try:
        response = llm.invoke([
            ("system", _ROUTER_PROMPT),
            ("human", state.user_input)
        ])
        
        # Почистване на отговора (в случай че AI добави точка или интервал)
        decision = response.content.strip().lower()
        
        valid_types = ["strategy", "code", "prompt_engineer", "search", "unknown"]
        if decision not in valid_types:
            logger.warning(f"[Router] AI върна невалиден тип: {decision}. Задавам 'unknown'.")
            decision = "unknown"
            
        state.task_type = decision
        state.routing_reason = f"AI Classified as: {decision}"
        
    except Exception as e:
        logger.error(f"[Router] Грешка: {e}")
        state.task_type = "unknown"
        state.add_error(f"Router failed: {str(e)}")
        
    return state