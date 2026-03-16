def calculate_rev_share_offer(base_price: float, current_revenue: float, target_growth: float = 0.2):
    """
    Изчислява Grand Slam оферта базирана на растеж.
    """
    projected_growth = current_revenue * target_growth
    gg_cut = projected_growth * 0.20 # 20% Rev Share пример
    
    return {
        "setup_fee": base_price,
        "performance_bonus": gg_cut,
        "total_estimated_value": base_price + gg_cut
    }