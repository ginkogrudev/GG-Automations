from langgraph.graph import StateGraph, END
from core.state import GGState
from rich.console import Console

def call_model(state: GGState):
    # Логика за комуникация с Claude 3.5 Sonnet
    # ...
    return {"messages": ["Ето твоята Grand Slam Offer стратегия..."]}

# Инициализиране на графа
workflow = StateGraph(GGState)

# Добавяне на възли
workflow.add_node("strategist", call_model)

# Дефиниране на връзки
workflow.set_entry_point("strategist")
workflow.add_edge("strategist", END)

# КРИТИЧНАТА СТЪПКА: Компилация
# Без .compile(), обектът workflow няма атрибут .invoke()
app = workflow.compile()