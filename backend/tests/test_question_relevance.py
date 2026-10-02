import copy
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from main import app
from config import settings
from db.database import SessionLocal
from models.skill import Skill
from services.question_service import validate_proposals, questions_for_skills

client = TestClient(app)

@pytest.fixture(autouse=True)
def no_live_calls(monkeypatch):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', '')
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)

def create(title):
    goal=client.post('/api/goals',json={'title':title}).json()['id']
    graph=client.post(f'/api/goals/{goal}/generate-graph').json()
    return goal, graph

def test_unrelated_goals_have_distinct_content_and_truthful_coverage():
    records=[]
    for title in ['Frontend Developer Internship','Machine Learning Engineer']:
        goal,graph=create(title)
        questions=client.post(f'/api/goals/{goal}/diagnostic').json()
        assert client.post(f'/api/goals/{goal}/diagnostic').json()==questions
        assert all(q['source']=='curated' for q in questions['questions'])
        assert all('core prerequisite concept' not in q['question'] for q in questions['questions'])
        assert len({q['question'] for q in questions['questions']})==len(questions['questions'])
        records.append(questions)
    a,b=records
    assert not {q['question'] for q in a['questions']} & {q['question'] for q in b['questions']}
    assert len(a['questions'])==6
    assert 'Model Serving & MLOps' in b['unassessed_skills']
    assert any('jest.fn' in q['question'] for q in a['questions'])
    assert any('overfitting in deep learning' in q['question'] for q in b['questions'])

@pytest.fixture
def proposal():
    return {'skill_id':1,'target_level':'Proficient','question':'In Python, which expression creates a list of squared values?',
        'options':['[x*x for x in range(3)]','list.square(3)','range(3).square()','square.list(3)'],
        'correct_index':0,'answer_text':'[x*x for x in range(3)]','explanation':'A Python list comprehension evaluates the expression for each item.'}

@pytest.mark.parametrize('change',[
    {'correct_index':4}, {'correct_index':True}, {'answer_text':'wrong'},
    {'options':['a','A','b','c']}, {'options':['a','','b','c']},
    {'skill_id':100}, {'target_level':'Beginner'},
    {'question':'Which HTML element defines a navigation region?','options':['nav','div','p','section'],'answer_text':'nav'},
    {'question':'What is a core prerequisite concept in Python?'},
])
def test_malformed_and_unrelated_proposals_rejected(proposal,change):
    with pytest.raises(ValueError):
        validate_proposals({'questions':[{**proposal,**change}]},[SimpleNamespace(id=1,name='Python',slug='python',target_level='Proficient')],{1:1},[])

def test_duplicates_rejected(proposal):
    skill=SimpleNamespace(id=1,name='Python',slug='python',target_level='Proficient')
    with pytest.raises(ValueError):validate_proposals({'questions':[proposal,copy.deepcopy(proposal)]},[skill],{1:2},[])
    with pytest.raises(ValueError):validate_proposals({'questions':[proposal]},[skill],{1:1},[proposal['question'].upper()])

def test_validated_ai_questions_persist_and_grading_stays_server_side(monkeypatch,proposal):
    goal,_=create('Machine Learning Engineer')
    with SessionLocal() as db:
        skill=db.query(Skill).filter(Skill.goal_id==goal,Skill.slug=='python').one()
        proposal['skill_id']=skill.id
    calls=[]
    def propose(goal,skills,counts,previous,purpose):
        calls.append((goal.title,purpose,counts,previous))
        return validate_proposals({'questions':[proposal]},skills,counts,previous)
    monkeypatch.setattr('services.question_service.propose_questions',propose)
    first=client.post(f'/api/goals/{goal}/diagnostic').json()
    assert first['questions'][0]['source']=='gemini'
    assert 'correct_index' not in first['questions'][0]
    assert client.post(f'/api/goals/{goal}/diagnostic').json()==first
    assert len(calls)==1 and calls[0][0]=='Machine Learning Engineer'
    answer=[{'question_id':q['id'],'selected_option':0} for q in first['questions']]
    result=client.post(f'/api/goals/{goal}/diagnostic/submit',json={'answers':answer})
    assert result.status_code==200
    assert not any(s['status']=='VERIFIED' for s in client.get(f'/api/goals/{goal}/graph').json()['skills'])

def test_unknown_skill_cannot_be_verified_with_generic_trivia():
    goal,_=create('Pottery Studio Practice')
    graph=client.get(f'/api/goals/{goal}/graph').json()
    questions=client.post(f'/api/goals/{goal}/diagnostic').json()
    assert questions['questions']==[] and questions['unassessed_skills']
    root=next(s for s in graph['skills'] if s['status']=='AVAILABLE')
    response=client.post(f'/api/goals/{goal}/skills/{root["db_id"]}/verification')
    assert response.status_code==503
    assert client.get(f'/api/goals/{goal}/mastery').json()==[]

@pytest.mark.parametrize('failure', ['malformed', 'timeout', 'http'])
def test_question_transport_failure_is_safe_and_falls_back(monkeypatch, caplog, failure):
    import httpx
    from services.question_service import questions_for_skills
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'test-only-secret')
    class Transport:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, **kwargs):
            prompt=kwargs['json']['contents'][0]['parts'][0]['text']
            assert 'Machine Learning Engineer' in prompt and 'Proficient' in prompt
            assert 'exclude_questions' in prompt and 'question_count' in prompt
            if failure == 'timeout': raise httpx.ReadTimeout('test-only-secret')
            request=httpx.Request('POST', url)
            if failure == 'http': return httpx.Response(503, request=request, text='test-only-secret')
            return httpx.Response(200, request=request, json={'candidates':[{'content':{'parts':[{'text':'not JSON'}]}}]})
    monkeypatch.setattr('services.question_service.httpx.Client', Transport)
    skill=SimpleNamespace(id=1,name='Python Programming',slug='python',target_level='Proficient')
    result=questions_for_skills(SimpleNamespace(title='Machine Learning Engineer'),[skill],{1:1},[],'diagnostic')
    assert result[1][0]['explanation'].startswith('[orbit-assessment:curated]')
    assert 'test-only-secret' not in caplog.text
