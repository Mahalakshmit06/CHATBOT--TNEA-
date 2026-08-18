import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.chatbot import get_session, process_message

def test_branch_comparison_does_not_filter_or_show_colleges():
    s=get_session(); r=process_message(s.id,"Which is best CSE or ECE?")
    assert r["intent"]=="branch_compare" and r["records"]==[] and r["profile"]["branch"] is None

def test_college_code_does_not_invent_community():
    s=get_session(); r=process_message(s.id,"college code:1413")
    assert r["intent"]=="college_info" and len(r["records"])>0 and r["profile"]["community"] is None

def test_unordered_recommendation_context():
    s=get_session(); r=process_message(s.id,"I have 166 cutoff, BC, I need autonomous colleges in Chennai")
    assert r["profile"]=={"cutoff":166.0,"community":"BC","district":"CHENNAI","branch":None,"college_type":"Autonomous"}
    assert r["total_records"]==40

def test_branch_information_is_not_a_college_search():
    s=get_session(); process_message(s.id,"I have 166 cutoff, BC, autonomous colleges in Chennai")
    r=process_message(s.id,"What is ECE?")
    assert r["intent"]=="branch_info" and r["records"]==[] and r["profile"]["branch"] is None

def test_followup_branch_changes_only_for_college_search():
    s=get_session(); process_message(s.id,"I have 166 cutoff, BC, autonomous colleges in Chennai")
    r=process_message(s.id,"Show ECE colleges")
    assert r["intent"]=="recommend" and r["profile"]["branch"]=="ELECTRONICS AND COMMUNICATION ENGINEERING" and len(r["records"])>0

def test_unspecified_profile_fields_remain_unknown():
    s=get_session(); r=process_message(s.id,"Tell me about TNEA")
    assert r["profile"]["community"] is None and r["profile"]["district"] is None and r["profile"]["branch"] is None and r["profile"]["college_type"] is None
