import unittest
from app import nlp
from app.data import DATASET
from app.chatbot import process_message, clear_session

class CampusTests(unittest.TestCase):
    def ask(self,sid,q):
        r=process_message(sid,q); return r['session_id'],r
    def test_unordered_english_profile(self):
        q='BC CSE 185 Chennai'
        self.assertEqual(nlp.detect_cutoff(q),185); self.assertEqual(nlp.detect_community(q),'BC')
        self.assertEqual(nlp.detect_district(q,DATASET.district_set),'CHENNAI')
        self.assertEqual(nlp.detect_branch(q,DATASET.branch_set,DATASET.branch_code_map),'COMPUTER SCIENCE AND ENGINEERING')
    def test_tanglish(self):
        q='En cutoff 185.5, BC. Chennai la CSE venum'
        self.assertEqual(nlp.detect_cutoff(q),185.5); self.assertEqual(nlp.detect_community(q),'BC'); self.assertEqual(nlp.detect_district(q,DATASET.district_set),'CHENNAI')
    def test_no_short_word_false_branch(self):
        self.assertIsNone(nlp.detect_branch('what is it?',DATASET.branch_set,DATASET.branch_code_map))
        self.assertEqual(nlp.detect_branch('IT',DATASET.branch_set,DATASET.branch_code_map),'INFORMATION TECHNOLOGY')
    def test_no_false_cutoff(self):
        self.assertIsNone(nlp.detect_cutoff('college code 101')); self.assertIsNone(nlp.detect_cutoff('TNEA 2026'))
    def test_context(self):
        sid=None
        for q in ['My cutoff is 185','I am BC','CSE','Chennai']:
            sid,r=self.ask(sid,q)
        self.assertEqual(r['profile']['cutoff'],185.0);self.assertEqual(r['profile']['community'],'BC');self.assertEqual(r['profile']['district'],'CHENNAI');self.assertEqual(r['profile']['branch'],'COMPUTER SCIENCE AND ENGINEERING')
        sid,r=self.ask(sid,'government colleges'); self.assertEqual(r['profile']['cutoff'],185.0); self.assertEqual(r['profile']['college_type'],'Government'); self.assertTrue(all('government' in x['college_type'].lower() for x in r['records'])); clear_session(sid)
    def test_specific_college_and_followup(self):
        sid,r=self.ask(None,'Tell me about PSG Tech');self.assertIn('PSG College of Technology',r['colleges'][0]['college_name'])
        sid,r=self.ask(sid,'What branches are available in this college?');self.assertEqual(r['intent'],'college_branch_list');self.assertGreater(len(r['records']),0)
        sid,r=self.ask(sid,'What about ECE?');self.assertEqual(r['intent'],'college_branch_info');clear_session(sid)
    def test_no_college_type_means_all_types(self):
        sid,r=self.ask(None,'200 cutoff CSE');
        self.assertEqual(r['profile']['college_type'],'ALL')
        types={x['college_type'] for x in r['records']}
        self.assertTrue(any('Government' in t for t in types))
        self.assertTrue(any('Private' in t for t in types))
        self.assertTrue(any('University' in t for t in types))
        self.assertIn('No college type was specified',r['reply'])
        clear_session(sid)

    def test_type_filters(self):
        sid,r=self.ask(None,'Show private autonomous colleges in Coimbatore');self.assertEqual(r['intent'],'college_type');self.assertTrue(all('private' in x['college_type'].lower() and 'autonomous' in x['college_type'].lower() for x in r['records']));clear_session(sid)
    def test_marks(self):
        sid,r=self.ask(None,'Maths 95 Physics 90 Chemistry 92');self.assertEqual(r['profile']['cutoff'],186.0);clear_session(sid)
    def test_clear(self):
        sid,r=self.ask(None,'185 BC CSE Chennai');sid,r=self.ask(sid,'clear chat');self.assertIsNone(r['profile']['cutoff']);self.assertEqual(r['profile']['community'],'OC');self.assertEqual(r['profile']['district'],'ALL');self.assertEqual(r['profile']['branch'],'ALL')

if __name__=='__main__':unittest.main()

class ExtendedCampusTests(unittest.TestCase):
    def test_no_false_branch_from_government_query(self):
        q='My cutoff is 169, BC, I need government college in Chennai'
        self.assertIsNone(nlp.detect_branch(q, DATASET.branch_set, DATASET.branch_code_map))
        r=process_message(None,q)
        self.assertEqual(r['profile']['branch'],'ALL')
        self.assertEqual(r['profile']['college_type'],'Government')
        self.assertTrue(all('government' in x['college_type'].lower() for x in r['records']))

    def test_ai_ds_aliases_are_same_but_aiml_is_distinct(self):
        for q in ['AIDS', 'AI & DS', 'Artificial Intelligence and Data Science', 'artificial intelligence or data science']:
            self.assertEqual(nlp.detect_branch(q, DATASET.branch_set, DATASET.branch_code_map), 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE')
        for q in ['AIML', 'AI & ML', 'Artificial Intelligence and Machine Learning']:
            self.assertEqual(nlp.detect_branch(q, DATASET.branch_set, DATASET.branch_code_map), 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING')

    def test_missing_filters_default_to_all(self):
        r=process_message(None,'169 BC government colleges in Chennai')
        self.assertEqual(r['profile']['branch'],'ALL')
        r=process_message(None,'169 BC CSE government colleges')
        self.assertEqual(r['profile']['district'],'ALL')
        r=process_message(None,'169 BC CSE Chennai')
        self.assertEqual(r['profile']['college_type'],'ALL')

    def test_college_code_lookup(self):
        r=process_message(None,'college code 1')
        self.assertEqual(str(r['colleges'][0]['college_code']),'1')
        self.assertGreater(len(r['records']),0)

    def test_branch_info(self):
        r=process_message(None,'Tell me about AI & DS')
        self.assertEqual(r['intent'],'branch_info')
        self.assertIn('AI & Data Science', r['reply'])

if __name__=='__main__':
    unittest.main()
