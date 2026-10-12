import math
import re
from collections import Counter
from .common import write_json

# Deterministic, dependency-free TF-IDF cosine retrieval.
TOKEN_RE = re.compile(r'[a-z0-9]+', re.IGNORECASE)

def tokens(text):
    return TOKEN_RE.findall(text.lower().replace('_',' '))

def vectors(documents):
    tok_docs = [tokens(s) for s in documents]
    n = len(documents)
    df = Counter(word for words in tok_docs for word in set(words))
    idf = {word:math.log((n+1)/(num+1))+1 for word,num in df.items()}
    result = []
    for words in tok_docs:
        counts = Counter(words)
        v = {w:(1+math.log(c))*idf[w] for w,c in counts.items()}
        norm = math.sqrt(sum(x*x for x in v.values())) or 1
        result.append({w:x/norm for w,x in v.items()})
    return result, idf

def retrieve(processed, classified, kb, output_path):
    if not isinstance(kb,list) or len(kb)<2:
        raise ValueError('At least two KB articles required to return top two')
    seen = set()
    for article in kb:
        if not isinstance(article,dict) or any(field not in article for field in ('article_id','title','category','body','tags')):
            raise ValueError('Invalid KB article schema')
        if not all(isinstance(article[k],str) for k in ('article_id','title','category','body')) or not isinstance(article['tags'],list) or not all(isinstance(tag,str) for tag in article['tags']):
            raise ValueError('Invalid KB article types')
        if article['article_id'] in seen:
            raise ValueError('Duplicate KB article ID')
        seen.add(article['article_id'])
    by_class = {r['ticket_id']:r for r in classified}
    # Include KB fields and ticket metadata for relevance; no hardcoded article IDs.
    docs = [f"{a['title']} {a['title']} {a['category']} {' '.join(a['tags'])*2} {a['body']}" for a in kb]
    queries = [f"{t['subject_for_processing']} {t['message_for_processing']} "
               f"{by_class[t['ticket_id']]['intent'].replace('_',' ')}" for t in processed]
    vecs, idf = vectors(docs+queries)
    article_vecs = vecs[:len(docs)]
    query_vecs = vecs[len(docs):]
    output = []
    for ticket, qv in zip(processed,query_vecs):
        ranked = []
        for article, av in zip(kb,article_vecs):
            score = sum(weight*av.get(term,0.0) for term,weight in qv.items())
            ranked.append((score,article))
        ranked.sort(key=lambda entry:(-entry[0],entry[1]['article_id']))
        output.append({'ticket_id':ticket['ticket_id'],
                       'retrieved_articles':[{'article_id':a['article_id'],'title':a['title'],
                                               'score':round(score,6)} for score,a in ranked[:2]]})
    write_json(output_path,output)
    return output
