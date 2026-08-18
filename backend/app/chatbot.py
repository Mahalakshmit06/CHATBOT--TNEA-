from __future__ import annotations
import json, os, re, time, uuid
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from dotenv import load_dotenv
load_dotenv()
from . import nlp
from .aliases import BRANCH_ALIASES
from .data import DATASET,calculate_cutoff
from .knowledge import answer_tnea_question

GROQ_URL='https://api.groq.com/openai/v1/chat/completions'; GROQ_MODEL=os.getenv('GROQ_MODEL','llama-3.3-70b-versatile'); GROQ_KEY=os.getenv('GROQ_API_KEY','').strip(); OFFICIAL_TNEA='https://www.tneaonline.org/'
SYSTEM=f'''You are Campus AI, a professional TNEA counselling assistant. Understand English, Tamil and Tanglish, spelling variations, abbreviations, incomplete sentences and follow-ups. College/branch/cutoff facts must come from retrieved dataset evidence. Never invent data. A student's cutoff meeting a historical closing cutoff is not a guaranteed allotment. For current TNEA procedures, use official TNEA information. Official portal: {OFFICIAL_TNEA}'''

class Session:
    def __init__(self,sid=None):
        self.id=sid or uuid.uuid4().hex[:12]; self.profile={'cutoff':None,'community':None,'district':None,'branch':None,'college_type':None}; self.history=[]; self.created_at=time.time(); self.last_intent=None; self.last_records=[]; self.last_colleges=[]
STORE={}; MAX_HISTORY=40

def get_session(sid=None,profile=None,history=None):
    if sid and sid in STORE:s=STORE[sid]
    else:s=Session(sid); STORE[s.id]=s
    if profile:
        for k in s.profile:
            if profile.get(k) not in (None,''):s.profile[k]=profile[k]
        if s.profile.get('community') is not None: s.profile['community']=str(s.profile['community']).upper()
        if s.profile.get('district') is not None: s.profile['district']=str(s.profile['district']).upper()
        if s.profile.get('branch') is not None: s.profile['branch']=str(s.profile['branch']).upper()
        if s.profile.get('college_type') is not None: s.profile['college_type']=str(s.profile['college_type'])
    if history and not s.history:s.history=[x for x in history[-MAX_HISTORY:] if isinstance(x,dict) and x.get('role') in {'user','assistant'}]
    return s

def clear_session(sid):
    if sid:STORE.pop(sid,None)

def _lang(t):return 'ta' if nlp.is_tamil(t) else 'en'
def _community_label(c):return {'OC':'OC (Open Competition)','BC':'BC (Backward Class)','BCM':'BCM (Backward Class Muslim)','MBC':'MBC (Most Backward Class)','SC':'SC (Scheduled Caste)','SCA':'SCA (Arunthathiyar)','ST':'ST (Scheduled Tribe)'}.get(c,c)

def _groq(prompt):
    if not GROQ_KEY:return None
    body={'model':GROQ_MODEL,'temperature':.1,'max_tokens':1200,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}]}
    try:
        req=Request(GROQ_URL,data=json.dumps(body,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+GROQ_KEY,'Content-Type':'application/json'})
        with urlopen(req,timeout=20) as r:return json.loads(r.read().decode())['choices'][0]['message']['content'].strip()
    except (HTTPError,URLError,TimeoutError,KeyError,ValueError,OSError):return None

def _evidence(records=None,colleges=None):
    out=[]
    for r in (records or [])[:250]:out.append(f"{r.get('college_code')} | {r.get('college_name')} | {r.get('district')} | {r.get('branch')} | type={r.get('college_type')} | cutoffs={r.get('cutoffs')} | closing={r.get('closing_cutoff')}")
    for c in (colleges or [])[:8]:out.append('COLLEGE '+c['college_name']+' | '+c['district']+' | type='+c['college_type']+' | '+json.dumps(c.get('branches',[]),ensure_ascii=False))
    return '\n'.join(out)

def _llm(sess,q,evidence,fallback):
    hist='\n'.join(f"{x['role']}: {x['content']}" for x in sess.history[-10:]); profile=json.dumps(sess.profile,ensure_ascii=False)
    prompt=f"PROFILE: {profile}\nHISTORY:\n{hist}\nQUESTION: {q}\nEVIDENCE:\n{evidence or '(none)'}\nAnswer directly in the user's language. Use only evidence for college-specific facts. If evidence is absent, give general guidance and say what should be verified officially."
    return _groq(prompt) or fallback

def _type_ok(r,w):
    ct=(r.get('college_type') or '').lower()
    if w=='Autonomous':return 'autonomous' in ct
    if w=='Government':return ct in {'government','government + autonomous'} or ct.startswith('government / university college')
    if w=='Government + Autonomous':return 'autonomous' in ct and (ct.startswith('government') or 'government / university college' in ct or ct.startswith('university department'))
    if w=='Private':return ct.startswith('private')
    if w=='Private + Autonomous':return ct.startswith('private') and 'autonomous' in ct
    if w=='Government-aided':return 'government-aided' in ct
    if w=='Government-aided + Autonomous':return 'government-aided' in ct and 'autonomous' in ct
    if w=='University Department':return ct.startswith('university department')
    if w=='University':return ct.startswith('university department') or 'university college' in ct
    return True

def _catalog(s,district,branch,wanted=None):
    out=[]
    for r in DATASET.records:
        if district!='ALL' and r['district']!=district:continue
        if branch!='ALL' and not DATASET.branch_matches(branch,r['branch']):continue
        x=DATASET._serialize(r,None,na=True)
        if wanted and not _type_ok(x,wanted):continue
        out.append(x)
    out.sort(key=lambda x:(x['college_name'],x['branch']));return out

def _effective_profile(s):
    return {
        'cutoff': s.profile.get('cutoff'),
        'community': s.profile.get('community') or 'OC',
        'district': s.profile.get('district') or 'ALL',
        'branch': s.profile.get('branch') or 'ALL',
        'college_type': s.profile.get('college_type') or 'ALL',
    }

def _render(result,s):
    p=_effective_profile(s); loc=p['district'] if p['district']!='ALL' else 'all districts'; br=p['branch'] if p['branch']!='ALL' else 'all branches'; ctype=p.get('college_type','ALL')
    type_text = '' if ctype == 'ALL' else f', {ctype} colleges'
    scope_text = ' No college type was specified, so all college types in the dataset were included.' if ctype == 'ALL' else ''
    msg=f"For cutoff {p['cutoff']:g}, {_community_label(result['community'])}, {loc}, {br}{type_text}, I found **{result['eligible_count']} eligible college-branch matches** in the dataset." + scope_text
    if result['na_count']:msg+=f" {result['na_count']} additional matching records have no published {result['community']} cutoff and are shown separately."
    if not result['eligible_count']:msg+=' No published closing cutoff is at or below your score for those filters.'
    return msg+' These are dataset matches, not guaranteed allotments.'

def _branch_explain(branch,lang):
    b=branch.upper(); d={
    'COMPUTER SCIENCE':('CSE focuses on programming, algorithms, data structures, databases, operating systems, networks and software systems. It is a broad computing branch for software and technology careers.','CSE-ல் programming, algorithms, data structures, databases, operating systems, networks மற்றும் software systems முக்கியம்.'),
    'ELECTRONICS AND COMMUNICATION':('ECE combines electronics, communication systems, embedded systems, signal processing and programming. It suits students interested in both hardware and technology.','ECE-ல் electronics, communication systems, embedded systems, signal processing மற்றும் programming முக்கியம்.'),
    'ELECTRICAL AND ELECTRONICS':('EEE covers electrical systems, power, machines, control and electronics. It is more core-electrical than CSE.','EEE-ல் electrical systems, power, machines, control மற்றும் electronics முக்கியம்.'),
    'MECHANICAL':('Mechanical covers mechanics, design, manufacturing, thermal systems, materials and automation.','Mechanical-ல் mechanics, design, manufacturing, thermal systems, materials மற்றும் automation முக்கியம்.'),
    'CIVIL':('Civil covers structures, construction, transportation, geotechnical and environmental engineering.','Civil-ல் structures, construction, transportation, geotechnical மற்றும் environmental engineering முக்கியம்.'),
    'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE':('AI & Data Science combines programming, statistics, data analysis, machine learning and AI systems.','AI & Data Science-ல் programming, statistics, data analysis, machine learning மற்றும் AI systems முக்கியம்.'),
    'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING':('AI & ML focuses on programming, mathematics, machine learning and AI model development.','AI & ML-ல் programming, mathematics, machine learning மற்றும் AI model development முக்கியம்.'),
    'INFORMATION TECHNOLOGY':('IT focuses on software applications, databases, networking, web systems and IT infrastructure, with strong overlap with CSE careers.','IT-ல் software applications, databases, networking, web systems மற்றும் IT infrastructure முக்கியம்.')}
    for k,v in d.items():
        if k in b:return v[1] if lang=='ta' else v[0]
    return f'{branch} is an engineering specialisation. Its exact curriculum and career outcomes depend on the institution and current syllabus; I will not invent college-specific claims.'

def _compare_names(text):
    for pat in [r'compare\s+(.+?)\s+(?:and|vs\.?|versus)\s+(.+?)(?:\?|$)',r'(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\?|$)']:
        m=re.search(pat,text,re.I)
        if m:return [m.group(1).strip(' ,'),m.group(2).strip(' ,')]
    return []

def _branch_names(text):
    n=nlp.normalize_text(text);out=[]
    for a,c in sorted(BRANCH_ALIASES.items(),key=lambda x:len(nlp.normalize_text(x[0])),reverse=True):
        a=nlp.normalize_text(a)
        if a and re.search(rf'(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])',n) and c not in out:out.append(c)
    for code,c in DATASET.branch_code_map.items():
        if code.lower() not in {'bc','bcm','mbc','sc','sca','st','oc'} and re.search(rf'(?<![a-z0-9]){re.escape(code.lower())}(?![a-z0-9])',n) and c not in out:out.append(c)
    return out[:4]

def _context_college(text):return bool(re.search(r'\b(this|that|the|same)\s+college\b|\b(what about|tell me more|more details)\b|இந்த|அந்த|அதே',text,re.I))

def _explicit_college_query(text):
    n=nlp.normalize_text(text)
    return bool(re.search(r'\b(college|college code|code|campus|university)\b', n, re.I))

def _college_code_from_query(text):
    n=nlp.normalize_text(text)
    m=re.search(r'\b(?:college\s*code|college\s*(?:no|number)|code)\s*[:#-]?\s*(\d{1,5})\b', n, re.I)
    if m: return m.group(1)
    # A bare 1-5 digit token is accepted only when the surrounding text clearly
    # identifies it as a college/code query; never treat it as a cutoff.
    if re.fullmatch(r'\d{1,5}', n): return n
    return None

def process_message(session_id,message,client_profile=None,client_history=None):
    s=get_session(session_id,client_profile,client_history); raw=(message or '').strip(); text=nlp.normalize_text(raw); intent=nlp.classify_intent(text)
    if intent=='reset':
        clear_session(s.id); f=get_session(); return _response(f,'Started a new counselling conversation. Previous cutoff, community, district, branch, college-type and college context have been cleared.',[],intent)
    s.history.append({'role':'user','content':raw});s.history=s.history[-MAX_HISTORY:]
    detected={}; marks=nlp.detect_marks(text) or {}; cutoff=nlp.detect_cutoff(text)
    if cutoff is None and re.fullmatch(r'\d{1,3}(?:\.\d+)?',text):cutoff=float(text)
    if cutoff is not None:s.profile['cutoff']=cutoff;detected['cutoff']=cutoff
    comm=nlp.detect_community(text)
    if comm:s.profile['community']=comm;detected['community']=comm
    dist=nlp.detect_district(text,DATASET.district_set)
    if dist is not None:s.profile['district']=dist;detected['district']=dist
    branch=nlp.detect_branch(text,DATASET.branch_set,DATASET.branch_code_map)
    comparison_intent = intent == 'compare'
    informational_branch = intent == 'branch_info'
    contextual_branch_followup = bool(
        branch and s.last_intent in {'recommend','college_type','catalog','branch_info'}
        and re.search(r'\b(what about|how about|then|instead|only|show|find|give me|i want|need)\b|வேண்டும்|மட்டும்', text, re.I)
    )
    if branch and not comparison_intent and not informational_branch:
        s.profile['branch']=branch;detected['branch']=branch
    elif branch and contextual_branch_followup:
        s.profile['branch']=branch;detected['branch']=branch
    typ=nlp.detect_college_type(text)
    # Do not let the word ``university`` inside a named college hijack a college
    # detail query. A type filter is stored only when the user is clearly asking
    # for a category (e.g. ``only university colleges``).
    named_hits_for_type = DATASET.search_colleges(raw, 3) if _explicit_college_query(raw) else []
    clear_type_filter = bool(re.search(r'\b(only|just|show|list|find|want|need|government|govt|private|autonomous|aided|university\s+department|university\s+colleges?|university\s+institutions?)\b|மட்டும்|வேண்டும்', text, re.I))
    if typ and (clear_type_filter or not named_hits_for_type):
        s.profile['college_type']=typ
        detected['college_type']=typ
    # Entity-aware intent correction: once a branch is positively resolved,
    # interpret natural questions such as ``explain AIDS`` as branch information
    # rather than falling through to generic chat.
    if intent != 'compare' and branch and re.search(r'\b(what is|explain|about|scope|career|jobs|subjects|salary|difference)\b|என்ன|விளக்க|பற்றி', text, re.I):
        intent='branch_info'
    elif intent != 'compare' and branch and re.search(r'\b(colleges?|college list|where can i study|which colleges)\b|கல்லூரி', text, re.I) and not re.search(r'\b(what is|explain|about)\b',text,re.I):
        intent='recommend'
    if re.search(r'\b(all|any|every)\s+(district|districts|city|cities|place|places)\b|all over tamil nadu|anywhere in tamil nadu|எல்லா மாவட்ட|அனைத்து மாவட்ட',text,re.I):s.profile['district']='ALL';detected['district']='ALL'
    if re.search(r'\b(all|any|every)\s+(branch|branches|course|courses|stream|streams|department|departments)\b|எல்லா கிளை|அனைத்து கிளை',text,re.I):s.profile['branch']='ALL';detected['branch']='ALL'
    if len(marks)==3:
        v=calculate_cutoff(marks['mathematics'],marks['physics'],marks['chemistry']);s.profile['cutoff']=v;detected['cutoff']=v
        res=DATASET.recommend(v,_effective_profile(s)['community'],_effective_profile(s)['district'],_effective_profile(s)['branch'],limit=10000);return _response(s,f"Your TNEA cutoff is **{v:g}** = {marks['mathematics']:g} + ({marks['physics']:g}/2) + ({marks['chemistry']:g}/2).\n\n"+_render(res,s),res['records']+res['na_records'],'calculate_cutoff',detected)
    if marks and len(marks)<3 and re.search(r'math|physics|chem|கணித|இயற்பியல்|ரசாய',text,re.I):
        missing=[x.title() for x in ('mathematics','physics','chemistry') if x not in marks];return _response(s,'Please provide the missing mark(s): **'+', '.join(missing)+'**. Formula: Mathematics + Physics/2 + Chemistry/2.',[],'calculate_cutoff',detected)
    college_hits=[]
    if _context_college(text) and s.last_colleges:college_hits=s.last_colleges
    elif re.search(r'\b(college|about|details?|info|information|tell me|branches?|courses?|cutoff|fee|fees|hostel|placement|transport|campus)\b|கல்லூரி|விவரம்',text,re.I) and not (detected.get('college_type') and intent in {'recommend','college_type'}):
        code=_college_code_from_query(raw)
        if code:
            hits=[c for c in DATASET.colleges if str(c.get('college_code'))==str(code)]
        else:
            hits=DATASET.search_colleges(raw,8)
        college_hits=[DATASET.college_detail(h['college_name']) for h in hits];college_hits=[x for x in college_hits if x]
    if college_hits and _context_college(text):
        d=college_hits[0]; req=branch if branch not in (None,'ALL') else None
        if req:
            m=[r for r in d['branches'] if DATASET.branch_matches(req,r['branch'])]
            if m:return _response(s,f"Yes. **{d['college_name']}** has the requested branch in the supplied dataset.",m,'college_branch_info',detected,colleges=[d])
            return _response(s,f"I couldn't find **{req}** among the branches listed for **{d['college_name']}**.",d['branches'],'college_branch_info',detected,colleges=[d])
        return _response(s,f"**{d['college_name']}** has **{len(d['branches'])} listed branch records**. The records below include branch-wise community cutoffs where available.",d['branches'],'college_branch_list',detected,colleges=[d])
    if intent in {'compare'}:
        names=_compare_names(raw)
        if not names:
            names=[]
            qn=nlp.normalize_text(raw)
            for alias in sorted(DATASET.COLLEGE_ALIASES,key=len,reverse=True):
                if re.search(rf'(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])',qn): names.append(alias)
        comp=DATASET.compare_colleges(names,s.profile['community']) if names else []
        if len(comp)>=2:return _response(s,_llm(s,raw,_evidence(colleges=comp),'Here is a dataset-grounded comparison of the colleges and their listed branches/cutoffs.'),[b for c in comp for b in c['branches']],'college_compare',detected,colleges=comp)
        bs=_branch_names(raw)
        if len(bs)>=2:return _response(s,_llm(s,raw,'Branches: '+' | '.join(bs),_branch_explain(bs[0],_lang(raw))+'\n\n'+_branch_explain(bs[1],_lang(raw))+'\n\nThere is no universal best branch.'),[],'branch_compare',detected)
    if college_hits and intent in {'college_info','fallback'}:
        d=college_hits[0];fallback=f"### {d['college_name']}\n**College code:** {d['college_code']}\n**District:** {d['district']}\n**Type:** {d['college_type']}\n\nThe dataset lists **{len(d['branches'])} branch records** with community cutoffs where available."
        return _response(s,_llm(s,raw,_evidence(colleges=[d]),fallback),d['branches'],'college_info',detected,colleges=[d])
    if intent=='greeting':return _response(s,"Vanakkam! 👋 Ask naturally about cutoff, community, district, branch, eligible colleges, government/private/autonomous colleges, a specific college, comparisons or TNEA counselling. English, தமிழ் and Tanglish are supported.",[],intent,detected)
    if intent=='thanks':return _response(s,'You are welcome! 😊 Your counselling context remains until you clear the chat.',[],intent,detected)
    if intent=='bye':return _response(s,'All the best for your TNEA counselling! 🎓',[],intent,detected)
    if intent=='help':return _response(s,'You can type information in any order, such as **185 BC CSE Chennai**, **government colleges**, **only autonomous**, **CSE or ECE which is better?**, **tell me about PSG Tech**, or **what documents are needed for TNEA?**.',[],intent,detected)
    if intent=='branch_info':
        bs=_branch_names(raw)
        requested = bs[0] if bs else s.profile.get('branch')
        if not requested:
            return _response(s,'Tell me the branch you want to know about, for example **CSE, ECE, EEE, IT, AI & DS or AIML**.',[],'branch_info',detected)
        # Informational branch questions must never trigger college recommendations.
        return _response(s,_llm(s,raw,
            'Branch reference: '+ ' | '.join(bs or [requested]),
            _branch_explain(requested,_lang(raw)) + '\n\nIf you want eligible colleges for this branch, ask me to **show colleges** and I will use your saved counselling profile.'),
            [],'branch_info',detected)
    if intent=='tnea_info':
        kb=answer_tnea_question(text) or f'For current TNEA procedures, rules and dates use the official portal: {OFFICIAL_TNEA}'
        return _response(s,_llm(s,raw,kb,kb),[],'tnea_info',detected,tnea=True)
    if intent=='branch_list':return _response(s,f"The dataset contains **{len(DATASET.branch_set)} distinct branch names**. You can ask using CSE/CS, ECE/EC, EEE/EE, IT, ME/MECH, CE/Civil, AI&DS/AD, AI&ML/AL, Cyber Security, IoT, VLSI, Robotics, Mechatronics and more.",[],intent,detected)
    if intent=='district_list':return _response(s,f"The dataset contains colleges across **{len(DATASET.district_set)} districts**. If you do not specify a district, I use **all districts**.",[],intent,detected)
    if typ and s.profile['cutoff'] is None:
        ep=_effective_profile(s); cat=_catalog(s,ep['district'],ep['branch'],typ)
        if cat:return _response(s,f"I found **{len({r['college_code'] for r in cat})} {typ.lower()} colleges** and **{len(cat)} college-branch records**. Because no cutoff is stored, this is an availability list, not an eligibility result.",cat,'college_type',detected)
        return _response(s,f"I couldn't find any {typ.lower()} colleges matching your current filters in the dataset.",[],'college_type',detected)
    if intent in {'recommend','college_type'} and (detected.get('district') is not None or detected.get('branch') is not None) and s.profile['cutoff'] is None:
        ep=_effective_profile(s); cat=_catalog(s,ep['district'],ep['branch'],typ)
        if cat:return _response(s,f"I found **{len(cat)} college-branch records** for your request. This is an availability list. Give your cutoff for eligibility; community defaults to **OC**, district and branch default to **all**.",cat,'catalog',detected)
    if s.profile['cutoff'] is not None and (detected or intent in {'recommend','college_type','fallback'}):
        res=DATASET.recommend(s.profile['cutoff'],_effective_profile(s)['community'],_effective_profile(s)['district'],_effective_profile(s)['branch'],limit=10000,include_na=False)
        active_type=_effective_profile(s)['college_type']
        if active_type and active_type != 'ALL':
            res['records']=[r for r in res['records'] if _type_ok(r,active_type)]
            res['eligible_count']=len(res['records'])
        res['na_records']=[]; res['na_count']=0
        return _response(s,_render(res,s),res['records'],'recommend',detected)
    if intent=='recommend':return _response(s,'I can find eligible colleges once I know your **TNEA cutoff out of 200**. Community defaults to **OC**, district to **all districts**, and branch to **all branches** unless you specify them.',[],'recommend',detected)
    return _response(s,_llm(s,raw,_evidence(colleges=college_hits),'I can help with TNEA counselling, cutoff, community, district, branch, college details, comparisons, eligibility and admission procedures.'),[],'fallback',detected)

def _response(s,reply,records,intent,detected=None,tnea=False,colleges=None):
    s.last_intent=intent;s.last_records=records;s.last_colleges=colleges or [];s.history.append({'role':'assistant','content':reply});s.history=s.history[-MAX_HISTORY:]
    return {'session_id':s.id,'reply':reply,'profile':dict(s.profile),'detected':detected or {},'records':records,'total_records':len(records),'colleges':colleges or [],'intent':intent,'grounded':True,'tnea_fact':tnea,'source':'TNEA dataset + deterministic NLP + optional Groq','official_tnea':OFFICIAL_TNEA,'llm_enabled':bool(GROQ_KEY)}
