from __future__ import annotations
import re
OFFICIAL='https://www.tneaonline.org/'
BROCHURE='https://static.tneaonline.org/docs/2_Information_Brochure_2026.pdf'
SCHEDULE='https://static.tneaonline.org/docs/TNEA_Tentative_Schedule_2026.pdf'
KNOWLEDGE={
'process':f'TNEA 2026 uses an online process covering registration/application, payment and document upload, certificate verification, rank publication, choice filling, allotment, confirmation and reporting/admission according to the applicable allotment option. Use the current official portal for live rules and dates: {OFFICIAL}',
'documents':f'''For TNEA 2026, the official brochure/instructions list uploads including: 10th marksheet; HSC +1 marksheet; HSC +2/equivalent marksheet; Transfer Certificate; Government-school study details for candidates claiming the 7.5% Government School Students reservation; permanent Community Certificate for ST/SC/SCA/MBC&DNC/BC/BCM candidates; Nativity Certificate when applicable; Income Certificate when applicable; First Graduate Certificate and Joint Declaration when applicable; Sri Lankan Tamil Refugee Certificate when applicable; and relevant special-reservation certificates for Ex-Servicemen, Differently Abled and Eminent Sports Persons. Photo/signature and any other portal-requested files must also be uploaded in the required format/size. The exact applicable list depends on the candidate, so verify the current portal/brochure before submission: {BROCHURE}''',
'eligibility':f'Eligibility depends on the current TNEA qualification and subject rules. Campus AI can calculate the cutoff and match the supplied dataset, but formal eligibility must be confirmed from the current official brochure: {BROCHURE}',
'reservation':f'TNEA publishes community and special-reservation rules in its current brochure. Campus AI uses OC, BC, BCM, MBC, SC, SCA and ST for the supplied cutoff dataset. Government-school 7.5% and other special reservations are separate provisions: {BROCHURE}',
'registration':f'TNEA registration/application is online. Candidates complete application details, payment and required uploads and then follow verification and counselling instructions. Use the live official portal rather than an old date: {OFFICIAL}',
'rank':f'TNEA publishes random number/rank information after the relevant application and verification stages. The current schedule should be checked for the applicable dates and grievance period: {SCHEDULE}',
'choice':f'Choice filling is the stage where candidates order institution/branch preferences. Preference order matters, so choices should reflect the student’s actual priorities. Follow the current round instructions on {OFFICIAL}',
'allotment':f'TNEA uses tentative/provisional allotment and confirmation stages. The exact confirmation options and dates are round-specific, so follow the current instructions shown in the official portal: {OFFICIAL}',
'reporting':f'After the applicable confirmation/provisional-allotment stage, candidates must follow the reporting/joining instructions for the allotted college or TNEA Facilitation Centre as applicable. Use the current round schedule: {SCHEDULE}',
'cutoff':f'Campus AI uses the 200-mark formula Mathematics + Physics/2 + Chemistry/2. A historical closing cutoff is a threshold for a particular college, branch and community; meeting it does not guarantee a future allotment. Current rules: {BROCHURE}',
'fees':f'Application/counselling payment rules are year-specific. College tuition, hostel and transport fees should only be reported when supported by project data or an official institution source; Campus AI will not invent a fee. Current official source: {OFFICIAL}',
'special':f'TNEA has separate special-reservation provisions including applicable government-school 7.5%, differently abled, ex-servicemen and sports categories. These require the current official rules/seat matrix and should not be inferred from ordinary community cutoffs: {BROCHURE}',
'dates':f'TNEA dates are year- and round-specific. Use the current official schedule and live portal before acting: {SCHEDULE}',
}
KEYS={
'process':['tnea','counselling','counseling','process','procedure','steps'],
'documents':['document','documents','certificate','upload','marksheet','tc','needed','proof'],
'eligibility':['eligibility','eligible','qualification','criteria','who can apply'],
'reservation':['reservation','quota','community','bc','bcm','mbc','dnc','sc','sca','st','oc'],
'registration':['registration','register','apply','application','candidate login'],
'rank':['rank list','rank','random number','community rank','grievance'],
'choice':['choice filling','choices','preference order','branch preference'],
'allotment':['allotment','tentative','provisional','round','accept','decline','upward'],
'reporting':['reporting','join college','tfc','joining date'],
'cutoff':['cutoff','cut off','closing cutoff','calculate cutoff'],
'fees':['fee','fees','tuition','payment','hostel','cost'],
'special':['special reservation','differently abled','sports','ex servicemen','7.5','government school'],
'dates':['important dates','deadline','last date','schedule','counselling date']}
def answer_tnea_question(text):
 n=text.lower();best=None;score=0
 for topic,ks in KEYS.items():
  s=sum(1 for k in ks if re.search(re.escape(k),n))
  if s>score:best,score=topic,s
 return KNOWLEDGE.get(best) if best else None
