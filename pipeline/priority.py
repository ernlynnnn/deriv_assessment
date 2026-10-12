from .common import write_json

BASE = {'critical':40,'high':25,'medium':10,'low':3}

def score_priorities(tickets, classified, retrieved, output_path):
    ticket_map = {t['ticket_id']:t for t in tickets}
    retrieval_map = {r['ticket_id']:r for r in retrieved}
    scored = []
    for c in classified:
        tid = c['ticket_id']
        tier = ticket_map[tid]['customer_tier']
        if tier not in ('vip','standard'):
            raise ValueError(f'Unknown customer tier for {tid}: {tier}')
        top_score = retrieval_map[tid]['retrieved_articles'][0]['score']
        factors = {
            'urgency_base':BASE[c['urgency']],
            'tier_bonus':10 if tier == 'vip' else 0,
            'funds_blocked_bonus':20 if c['mentions_funds_blocked'] else 0,
            'regulatory_legal_bonus':25 if c['mentions_regulator_or_legal_threat'] else 0,
            'specialist_bonus':10 if c['requires_specialist_handling'] else 0,
            'retrieval_weakness_bonus':8 if top_score < 0.55 else 0,
        }
        scored.append({'ticket_id':tid,'priority_score':sum(factors.values()),
                       'score_breakdown':factors,'top_retrieval_score':top_score})
    # Tie-break by original ticket ID for reproducibility; never use input order.
    scored.sort(key=lambda r:(-r['priority_score'],r['ticket_id']))
    for rank,item in enumerate(scored, start=1):
        item['rank'] = rank
        item['expedited_routing'] = rank <= 5
    write_json(output_path,scored)
    return scored
