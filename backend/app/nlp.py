from __future__ import annotations
import re, unicodedata
from .aliases import BRANCH_ALIASES, COMMUNITY_ALIASES, DISTRICT_ALIASES

TAMIL_CHARS=re.compile(r'[\u0B80-\u0BFF]')

def normalize_text(text:str)->str:
    t=unicodedata.normalize('NFKC',str(text or '')).replace('\u00a0',' ')
    return re.sub(r'\s+',' ',t.strip().lower())

def is_tamil(text:str)->bool:return bool(TAMIL_CHARS.search(text or ''))
def words(text:str)->list[str]:return [w for w in re.split(r'[^a-z0-9\u0B80-\u0BFF&]+',normalize_text(text)) if w]

def similarity(a:str,b:str)->float:
    from difflib import SequenceMatcher
    return SequenceMatcher(None,normalize_text(a),normalize_text(b)).ratio()

def fuzzy_match(q,candidates,threshold=.78):
    best=None; score=0
    for c in candidates:
        s=similarity(q,c)
        if s>score: best,score=c,s
    return (best,score) if best and score>=threshold else None

def _ascii_boundary(n,a): return re.search(rf'(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])',n) is not None

def detect_cutoff(text:str):
    n=normalize_text(text)
    pats=[r'(?:cutoff|cut\s*off|score|mark|cutoff\s*mark|மதிப்பெண்)\s*(?:is|of|=|:|இல்|ஆக|around|about)?\s*(\d{1,3}(?:\.\d+)?)',r'(\d{1,3}(?:\.\d+)?)\s*(?:cutoff|cut\s*off|score|mark|மதிப்பெண்)\b',r'(?:my|got|scored|secured|have|enakku|எனக்கு|எனது)\s*(?:is|=|of)?\s*(\d{1,3}(?:\.\d+)?)\s*(?:cutoff|cut\s*off|mark|score)?\b']
    for p in pats:
        m=re.search(p,n,re.I)
        if m and 0<=float(m.group(1))<=200:return float(m.group(1))
    m=re.search(r'(?<!\d)(\d{1,3}(?:\.\d+)?)(?!\d)',n)
    if not m or len(re.findall(r'(?<!\d)\d{1,3}(?:\.\d+)?(?!\d)',n))!=1:return None
    v=float(m.group(1)); ctx=n[max(0,m.start()-30):m.end()+30]
    if not 0<=v<=200 or re.search(r'(college\s*(code|no|number)|pincode|phone|mobile|year|tnea\s*20\d{2})',ctx):return None
    if re.search(r'\b(bc|bcm|mbc|dnc|sc|sca|st|oc|cse|ece|eee|it|mech|civil|aids|aiml|chennai|coimbatore|trichy|salem|madurai|college|colleges|branch|course|cutoff|eligible|want|show)\b',n):return v
    return None

def detect_marks(text:str):
    n=normalize_text(text); found={}
    labels={'mathematics':[r'math(?:s|ematics)?\b',r'கணிதம்',r'ganitham'],'physics':[r'physics\b',r'இயற்பியல்',r'iyarpathiyal'],'chemistry':[r'chem(?:istry)?\b',r'ரசாயனம்',r'வேதியியல்',r'veedhiyal']}
    for k,pats in labels.items():
        for p in pats:
            m=re.search(p+r'\s*(?:is|of|=|:)?\s*(\d{1,3}(?:\.\d+)?)',n,re.I) or re.search(r'(\d{1,3}(?:\.\d+)?)\s*(?:/100\s*)?-?\s*'+p,n,re.I)
            if m and 0<=float(m.group(1))<=100:found[k]=float(m.group(1));break
    return found or None

def detect_community(text:str):
    n=normalize_text(text)
    if re.search(r'\b(any|all|no|irrespective of)\s+(community|category|reservation)\b',n):return None
    for a,v in sorted(COMMUNITY_ALIASES.items(),key=lambda x:len(normalize_text(x[0])),reverse=True):
        a=normalize_text(a)
        if a and (_ascii_boundary(n,a) if re.search('[a-z0-9]',a) else a in n):return v
    for t,v in {'bc':'BC','bcm':'BCM','mbc':'MBC','dnc':'MBC','sc':'SC','sca':'SCA','st':'ST','oc':'OC'}.items():
        if _ascii_boundary(n,t):return v
    if 'arunthathiyar' in n:return 'SCA'
    if 'backward class muslim' in n or ('muslim' in n and 'backward' in n):return 'BCM'
    if 'most backward' in n:return 'MBC'
    if 'scheduled tribe' in n:return 'ST'
    if 'scheduled caste' in n:return 'SC'
    return None

def detect_district(text,districts):
    n=normalize_text(text)
    if re.search(r'\b(all|any|every)\s+(district|districts|city|cities|place|places)\b|all over tamil nadu|anywhere in tamil nadu|whole tamil nadu|எல்லா மாவட்ட|அனைத்து மாவட்ட|எங்கும்',n,re.I):return 'ALL'
    for a,v in sorted(DISTRICT_ALIASES.items(),key=lambda x:len(normalize_text(x[0])),reverse=True):
        a=normalize_text(a)
        if v in districts and a and (_ascii_boundary(n,a) if re.search('[a-z0-9]',a) else a in n):return v
    for tok in re.findall(r'[a-z]{4,}',n):
        h=fuzzy_match(tok,districts,.80)
        if h:return h[0]
    return None

def detect_branch(text,branches,codes=None):
    """Resolve a branch only when there is positive evidence.

    IMPORTANT: never fuzzy-match arbitrary words against the 100+ dataset branch
    names. That caused words such as ``government`` to become a random branch.
    Exact aliases, full branch phrases and high-confidence typo matches against
    the alias vocabulary are allowed; generic prose is never treated as a branch.
    """
    n=normalize_text(text)
    if re.search(r'\b(all|any|every)\s+(branch|branches|course|courses|stream|streams|department|departments)\b|எல்லா கிளை|அனைத்து கிளை',n,re.I):
        return 'ALL'

    # Canonical aliases are the first and strongest signal.
    branch_signal = bool(re.search(r'\b(branch|branches|course|courses|stream|streams|department|departments|college|colleges|study|engineering|what|explain|scope|career|jobs|subjects|want|need|prefer|venum|படிக்க|கிளை|பாடப்பிரிவு)\b', n, re.I))
    short_branch_signal = branch_signal or bool(re.search(r'\b(about)\b', n, re.I))
    known_code_aliases = {'cse','ece','eee','it','cs','aids','aiml','csbs','csd','iot','bme','aero','vlsi','me','ce','ee','ec','ad','al'}
    if re.fullmatch(r'what\s+is\s+it[?!.]?', n, re.I):
        return None
    for a,v in sorted(BRANCH_ALIASES.items(), key=lambda x:len(normalize_text(x[0])), reverse=True):
        a=normalize_text(a)
        if not a: continue
        if re.search('[a-z0-9]',a):
            # Very short aliases are ambiguous in ordinary prose. They are accepted
            # only when the whole message is that code or the sentence clearly talks
            # about branches/courses/colleges. This prevents ``what is it?`` -> IT.
            if not (re.fullmatch(re.escape(a), n) or branch_signal or short_branch_signal or (a in known_code_aliases)):
                continue
            if _ascii_boundary(n,a):
                return v
        elif a in n:
            return v

    # Explicit full-name/phrase matching against the actual dataset.
    for b in sorted(branches,key=lambda x:len(normalize_text(x)),reverse=True):
        bn=normalize_text(b)
        if len(bn)>=6 and re.search(rf'(?<![a-z0-9]){re.escape(bn)}(?![a-z0-9])',n):
            return b.upper()

    # Branch-code matching is intentionally strict. A code by itself is a branch
    # only when it is a known dataset branch code and is not a community code.
    if codes:
        for code,canon in codes.items():
            cl=normalize_text(code)
            if cl in {'bc','bcm','mbc','sc','sca','st','oc'}: continue
            if re.fullmatch(r'[a-z]{2,4}',cl) and _ascii_boundary(n,cl):
                # Avoid interpreting ordinary words (e.g. ``in``) as codes.
                if len(cl)>=2 and (len(cl)>=3 or re.fullmatch(r'(it|cs|ec|ee|me|ce|ad|al|by|ai)',cl)) and (len(cl)>=3 or re.fullmatch(re.escape(cl), n) or branch_signal):
                    return canon

    # Natural-language branch names. Keep these explicit rather than fuzzy so
    # unrelated words can never create a false branch.
    natural={
        'computer science':'COMPUTER SCIENCE AND ENGINEERING',
        'computer':'COMPUTER SCIENCE AND ENGINEERING',
        'electronics and communication':'ELECTRONICS AND COMMUNICATION ENGINEERING',
        'electronics':'ELECTRONICS AND COMMUNICATION ENGINEERING',
        'electrical':'ELECTRICAL AND ELECTRONICS ENGINEERING',
        'mechanical':'MECHANICAL ENGINEERING',
        'civil':'CIVIL ENGINEERING',
        'information technology':'INFORMATION TECHNOLOGY',
        'data science':'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE',
        'machine learning':'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING',
        'artificial intelligence and data science':'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE',
        'artificial intelligence & data science':'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE',
        'artificial intelligence and machine learning':'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING',
        'artificial intelligence & machine learning':'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING',
        'cyber security':'COMPUTER SCIENCE AND ENGINEERING (CYBER SECURITY)',
        'cybersecurity':'COMPUTER SCIENCE AND ENGINEERING (CYBER SECURITY)',
        'robotics':'ROBOTICS AND AUTOMATION',
        'mechatronics':'MECHATRONICS ENGINEERING',
        'biomedical':'BIO MEDICAL ENGINEERING',
        'biotechnology':'BIO TECHNOLOGY',
        'chemical':'CHEMICAL ENGINEERING',
        'food technology':'FOOD TECHNOLOGY',
        'aerospace':'AEROSPACE ENGINEERING',
        'aeronautical':'AERONAUTICAL ENGINEERING',
        'automobile':'AUTOMOBILE ENGINEERING',
        'industrial biotechnology':'INDUSTRIAL BIO TECHNOLOGY',
        'industrial bio technology':'INDUSTRIAL BIO TECHNOLOGY',
        'instrumentation and control':'INSTRUMENTATION AND CONTROL ENGINEERING',
        'electronics and instrumentation':'ELECTRONICS AND INSTRUMENTATION ENGINEERING',
        'vlsi':'ELECTRONICS ENGINEERING (VLSI DESIGN AND TECHNOLOGY)',
        'computer and communication':'COMPUTER AND COMMUNICATION ENGINEERING',
        'computer science and business systems':'COMPUTER SCIENCE AND BUSSINESS SYSTEM',
    }
    for phrase,canon in sorted(natural.items(),key=lambda x:len(x[0]),reverse=True):
        if re.search(rf'(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])',n) and (branch_signal or re.fullmatch(rf'.*{re.escape(phrase)}.*', n)):
            return canon.upper()

    # Controlled typo tolerance: compare ONLY against known branch aliases and
    # only when the user has a branch/course signal. Never compare arbitrary prose
    # tokens to the entire branch catalogue.
    explicit=bool(re.search(r'\b(branch|course|stream|department|speciali[sz]ation|study|engineering|want|need|prefer|venum|venum|padikanum|படிக்க|கிளை|பாடப்பிரிவு)\b',n,re.I))
    if explicit:
        alias_candidates=[normalize_text(a) for a in BRANCH_ALIASES if len(normalize_text(a))>=4 and re.search('[a-z]',normalize_text(a))]
        for tok in re.findall(r'[a-z]{4,}',n):
            h=fuzzy_match(tok,alias_candidates,.92)
            if h:
                return BRANCH_ALIASES[h[0].upper()] if h[0].upper() in BRANCH_ALIASES else BRANCH_ALIASES.get(h[0],None)
    return None

def detect_college_type(text):
    n=normalize_text(text); auto=bool(re.search(r'\b(autonom(?:ous|us)|auto\.?(?:nomous|nomus))\b|தன்னாட்சி',n)); gov=bool(re.search(r'\b(government|govt|arasu)\b|அரசு',n)); private=bool(re.search(r'\b(private|self[- ]?financ(?:ing|e)|thaniyar)\b|தனியார்',n)); aided=bool(re.search(r'\b(government[- ]?aided|aided college)\b',n)); uni_dep=bool(re.search(r'\buniversity\s+department[s]?\b',n)); uni=bool(re.search(r'\buniversity\s+(college|campus|institution|colleges)\b',n))
    if gov and auto:return 'Government + Autonomous'
    if private and auto:return 'Private + Autonomous'
    if aided and auto:return 'Government-aided + Autonomous'
    if uni_dep:return 'University Department'
    if uni:return 'University'
    if re.search(r'\b(only\s+university|university\s+colleges?|university\s+institutions?)\b',n,re.I):return 'University'
    if auto:return 'Autonomous'
    if gov:return 'Government'
    if aided:return 'Government-aided'
    if private:return 'Private'
    return None

def classify_intent(text):
    n=normalize_text(text)
    if not n:return 'empty'
    if re.search(r'\b(clear|reset|start over|restart|new chat|new conversation)\b|அழி|மீண்டும் தொடங்கு',n,re.I):return 'reset'
    if re.fullmatch(r'(hi|hii+|hello|hey|hai|vanakkam|vanakam|வணக்கம்)[!. ]*',n,re.I):return 'greeting'
    if re.search(r'\b(thanks|thank you|nandri|நன்றி)\b',n,re.I):return 'thanks'
    if re.search(r'\b(bye|goodbye|see you)\b',n,re.I):return 'bye'
    if re.search(r'\b(tnea|counsell?ing|registration|register|documents?|certificate|eligib|choice\s*filling|allotment|rank\s*list|random\s*number|reporting|reservation|quota|round|upward|confirm|application|apply|deadline)\b',n,re.I):return 'tnea_info'
    if re.search(r'\b(compare|comparison|vs\.?|versus|difference between|which is better|which .* better|which is best|which .* best|better than)\b|ஒப்பிட|சிறந்தது',n,re.I):return 'compare'
    if re.search(r'\b(government|govt|private|self[- ]?financ|autonomous|university\s+department|university\s+college|aided)\b|அரசு|தனியார்|தன்னாட்சி',n,re.I):return 'college_type'
    if re.search(r'\b(what is|explain|about|scope|career|subjects|jobs|meaning|difference)\b.*\b(branch|course|cse|ece|eee|it|mech|civil|aids|aiml|cyber|robotics|mechatronics)\b|\b(branch|course)\b.*\b(explain|details|scope|career|jobs)\b',n,re.I):return 'branch_info'
    if re.search(r'\b(what branches|which branches|branches available|courses available|courses offered|list branches)\b',n,re.I):return 'branch_list'
    if re.search(r'\b(districts|list districts|which districts)\b',n,re.I):return 'district_list'
    if re.search(r'\b(calculate cutoff|calculate my cutoff|cutoff formula|math.*physics.*chem|physics.*chem.*math)\b',n,re.I):return 'calculate_cutoff'
    if re.search(r'\b(cutoff|cut off|eligible|eligible colleges|what colleges can i get|which colleges|show colleges|find colleges|recommend|suggest|college list|college finder)\b|கல்லூரி|கட்',n,re.I):return 'recommend'
    if re.search(r'\b(college|details|about|information|branches|courses)\b',n,re.I):return 'college_info'
    return 'fallback'
