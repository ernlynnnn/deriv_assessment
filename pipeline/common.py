import json
import os
from pathlib import Path
from datetime import datetime, timezone

INTENTS = {'withdrawal_issue','deposit_issue','login_access','verification_kyc','account_restriction','product_behavior','privacy_request','statement_export','api_support','other'}
URGENCIES = {'critical','high','medium','low'}
SENTIMENTS = {'calm','frustrated','angry','neutral'}
QUEUES = {'General Support','Payments','Compliance','Risk','Engineering','Product','Privacy','Developer Support'}
SAFETY = {'safe_to_send_after_review','needs_specialist_review','needs_legal_or_compliance_review'}
STAGES = ['TICKETS_LOADED','PREPROCESSING_COMPLETE','TICKETS_CLASSIFIED','KB_RETRIEVAL_COMPLETE','PRIORITY_SCORES_COMPUTED','ROUTING_COMPLETE','REPLY_DRAFTS_GENERATED','VALIDATION_COMPLETE','RESULTS_FINALISED']


def read_json(path):
    with Path(path).open(encoding='utf-8') as f:
        return json.load(f)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp.replace(path)


def log_event(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps({'timestamp':datetime.now(timezone.utc).isoformat(), **data}, ensure_ascii=False) + '\n')


def ids_match(records, expected):
    if not isinstance(records, list) or len(records) != len(expected):
        raise ValueError('Incorrect number of ticket records')
    ids = [r.get('ticket_id') for r in records if isinstance(r, dict)]
    if len(ids) != len(records) or len(set(ids)) != len(ids) or set(ids) != set(expected):
        raise ValueError('Ticket IDs missing, duplicated, or invented')
    return {r['ticket_id']: r for r in records}


def llm_json(stage, payload, instruction, log_path, model):
    # Logging input/output locally supports audit and replay. Treat the log as sensitive.
    messages = [
        {'role':'system','content':instruction},
        {'role':'user','content':json.dumps(payload, ensure_ascii=False)},
    ]
    try:
        from openai import OpenAI
        response = OpenAI().chat.completions.create(
            model=model, temperature=0,
            response_format={'type':'json_object'}, messages=messages,
        )
        raw = response.choices[0].message.content or ''
        result = json.loads(raw)
        log_event(log_path, {'stage':stage,'model':model,'messages':messages,'response':raw,
                             'usage':response.usage.model_dump() if response.usage else None,
                             'status':'ok'})
        if not isinstance(result, dict):
            raise ValueError('Model output must be a JSON object')
        return result
    except Exception as exc:
        log_event(log_path, {'stage':stage,'model':model,'messages':messages,
                             'status':'error','error':str(exc)})
        raise
