"""Acceptance regressions. Run with DATABASE_URL pointing to a disposable database."""
import json
import pytest
import httpx
from fastapi.testclient import TestClient
from main import app
from db.database import SessionLocal
from config import settings
from models.diagnostic import DiagnosticQuestion
from models.skill import SkillDependency, Skill
from models.mastery import Mastery
from services.ai_service import get_fallback_dag_for_goal
from services.dag_validator import is_acyclic

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture
def goal(monkeypatch):
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', '')
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    data = client.post('/api/goals', json={'title':'Frontend Developer Internship', 'hours_per_week':7, 'duration_weeks':8, 'budget':0}).json()
    assert data['id']
    return data['id']


def graph(goal):
    res = client.post(f'/api/goals/{goal}/generate-graph')
    assert res.status_code == 200, res.text
    return res.json()


def quiz_answers(goal, skill=None, correct=True):
    with SessionLocal() as db:
        query = db.query(DiagnosticQuestion).filter(DiagnosticQuestion.goal_id == goal)
        query = query.filter(DiagnosticQuestion.skill_slug == f'verif_{skill}') if skill else query.filter(~DiagnosticQuestion.skill_slug.startswith('verif_'))
        return [{'question_id':q.id, 'selected_option':q.correct_index if correct else (q.correct_index+1)%4} for q in query.all()]


@pytest.mark.parametrize('payload', [
    {'title':'   '}, {'title':'ab'}, {'title':'X'*301}, {'title':'Frontend', 'hours_per_week':0},
    {'title':'Frontend', 'duration_weeks':0}, {'title':'Frontend', 'budget':-1}])
def test_invalid_goal(payload):
    assert client.post('/api/goals', json=payload).status_code == 422


def test_journey_persistence_and_replan(goal):
    g = graph(goal)
    root = next(s for s in g['skills'] if s['status']=='AVAILABLE')
    child_slug = next(d['to'] for d in g['dependencies'] if d['from']==root['id'])
    diag = client.post(f'/api/goals/{goal}/diagnostic').json()
    assert diag['questions']
    assert all('correct_index' not in q for q in diag['questions'])
    answers = quiz_answers(goal, correct=False)
    answers[0]['selected_option'] = quiz_answers(goal)[0]['selected_option']
    result = client.post(f'/api/goals/{goal}/diagnostic/submit', json={'answers':answers})
    assert result.status_code == 200
    assert client.get(f'/api/goals/{goal}/diagnostic/mastery').json()['mastery']
    states = client.get(f'/api/goals/{goal}/graph').json()['skills']
    assert next(s for s in states if s['db_id']==root['db_id'])['status']=='IN_PROGRESS'
    assert next(s for s in states if s['id']==child_slug)['status']=='LOCKED'
    initial = client.get(f'/api/goals/{goal}/route').json()
    assert initial['version']==1
    assert initial['prerequisite_safe']
    assert initial['feasible'] or 'Infeasible' in initial['feasibility_message']
    sid = root['db_id']
    questions = client.post(f'/api/goals/{goal}/skills/{sid}/verification').json()['questions']
    assert questions and all('correct_index' not in q for q in questions)
    fail = client.post(f'/api/goals/{goal}/skills/{sid}/verify', json={'answers':quiz_answers(goal,sid,False)}).json()
    assert fail['passed'] is False and fail['skill']['status']!='VERIFIED' and fail['newly_unlocked']==[]
    passed = client.post(f'/api/goals/{goal}/skills/{sid}/verify', json={'answers':quiz_answers(goal,sid)}).json()
    assert passed['passed'] and passed['skill']['status']=='VERIFIED'
    assert any(s['id']==child_slug and s['status']=='AVAILABLE' for s in passed['newly_unlocked'])
    current = client.get(f'/api/goals/{goal}/route').json()
    replan = client.post(f'/api/goals/{goal}/replan', json={'hours_per_week':4}).json()
    assert replan['previous_version']==current['version']
    assert replan['new_version']==current['version']+1
    assert root['name'] in replan['preserved_verified_skills']
    assert client.get(f'/api/goals/{goal}').json()['hours_per_week']==4
    assert client.get(f'/api/goals/{goal}/route').json()==replan['route']
    assert json.loads(client.get(f'/api/goals/{goal}/routes/latest').json()['route_json'])==replan['route']
    regenerated = graph(goal)
    assert [(s['id'],s['db_id']) for s in regenerated['skills']]==[(s['id'],s['db_id']) for s in g['skills']]
    assert next(s for s in regenerated['skills'] if s['db_id']==sid)['status']=='VERIFIED'
    # A failed retake and another diagnostic cannot revoke verified progress.
    client.post(f'/api/goals/{goal}/skills/{sid}/verify', json={'answers':quiz_answers(goal,sid,False)})
    client.post(f'/api/goals/{goal}/diagnostic')
    client.post(f'/api/goals/{goal}/diagnostic/submit', json={'answers':quiz_answers(goal,correct=False)})
    assert next(s for s in client.get(f'/api/goals/{goal}/graph').json()['skills'] if s['db_id']==sid)['status']=='VERIFIED'


@pytest.mark.parametrize('model_text', ['not JSON', '{}', '{"skills":[],"dependencies":[]}'])
def test_malformed_gemini_falls_back(goal, monkeypatch, model_text):
    monkeypatch.setattr(settings,'GEMINI_API_KEY','test-key')
    original_post = httpx.Client.post
    def response(self, url, *args, **kwargs):
        if 'generativelanguage.googleapis.com' not in str(url):
            return original_post(self, url, *args, **kwargs)
        return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':model_text}]}}]})
    monkeypatch.setattr(httpx.Client,'post',response)
    data = graph(goal)
    assert data['source']=='fallback' and data['warning']
    assert data['skills'] and data['validation']['acyclic']


def test_cyclic_generated_graph_repaired(goal, monkeypatch):
    raw=get_fallback_dag_for_goal('frontend')
    raw['dependencies'].append({'from':'react_basics','to':'html_css'})
    monkeypatch.setattr('routes.graph.generate_skill_dag_with_gemini',lambda **kw:raw)
    g=graph(goal)
    assert g['validation']['acyclic'] and g['validation']['repaired']
    assert is_acyclic(g['skills'],g['dependencies'])[0]


def test_route_orders_shuffled_skills_by_prerequisites(goal, monkeypatch):
    raw=get_fallback_dag_for_goal('frontend')
    raw['skills'].reverse()
    monkeypatch.setattr('routes.graph.generate_skill_dag_with_gemini',lambda **kw:raw)
    g=graph(goal)
    route=client.get(f'/api/goals/{goal}/route').json()
    order=[r['skill_id'] for p in route['phases'] for r in p['resources']]
    ids={s['id']:s['db_id'] for s in g['skills']}
    assert all(order.index(ids[d['from']])<order.index(ids[d['to']]) for d in g['dependencies'])
    assert route['total_weeks']*route['hours_per_week'] >= route['total_hours']


def test_diagnostic_error_has_no_partial_mastery_and_retry_works(goal):
    graph(goal)
    original=client.post(f'/api/goals/{goal}/diagnostic').json()
    assert client.post(f'/api/goals/{goal}/diagnostic').json()==original
    for answers in [[], [{'question_id':999999,'selected_option':0}], [{'question_id':original['questions'][0]['id'],'selected_option':99}]]:
        res=client.post(f'/api/goals/{goal}/diagnostic/submit',json={'answers':answers})
        assert res.status_code==422 and 'Traceback' not in res.text
    assert client.get(f'/api/goals/{goal}/diagnostic/mastery').json()['mastery']==[]
    assert client.post(f'/api/goals/{goal}/diagnostic/submit',json={'answers':quiz_answers(goal)}).status_code==200


def test_diagnostic_cannot_bypass_locked_prerequisite(goal):
    g=graph(goal)
    client.post(f'/api/goals/{goal}/diagnostic')
    client.post(f'/api/goals/{goal}/diagnostic/submit',json={'answers':quiz_answers(goal)})
    states=client.get(f'/api/goals/{goal}/graph').json()['skills']
    assert not any(s['status']=='VERIFIED' for s in states)
    locked=next(s for s in states if s['status']=='LOCKED')
    assert client.post(f'/api/goals/{goal}/skills/{locked["db_id"]}/verification').status_code==409


def test_infeasible_budget_and_missing_resource(goal, monkeypatch):
    graph(goal)
    short=client.post(f'/api/goals/{goal}/replan',json={'hours_per_week':1}).json()['route']
    assert not short['feasible'] and 'Infeasible' in short['feasibility_message']
    monkeypatch.setattr('services.resource_service.find_verified_resource_for_skill',lambda *args:None)
    missing=client.get(f'/api/goals/{goal}/route').json()
    assert not missing['feasible'] and missing['missing_resources']
    assert all(r['url'] is None and not r['has_resource'] for p in missing['phases'] for r in p['resources'])


def test_replan_failure_rolls_back_goal_and_route(goal, monkeypatch):
    graph(goal)
    before=client.get(f'/api/goals/{goal}/route').json()
    routes_before=client.get(f'/api/goals/{goal}/routes').json()
    # Fail at persistence, after the new route is built.
    monkeypatch.setattr('routes.routes._save',lambda *args: (_ for _ in ()).throw(RuntimeError('private internal stack trace')))
    res=client.post(f'/api/goals/{goal}/replan',json={'hours_per_week':4})
    assert res.status_code==500
    assert res.json()=={'detail':'We could not complete that request. Please try again.'}
    assert client.get(f'/api/goals/{goal}').json()['hours_per_week']==7
    assert client.get(f'/api/goals/{goal}/routes').json()==routes_before
    assert client.get(f'/api/goals/{goal}/route').json()==before


def test_concurrent_diagnostic_requests_are_idempotent(goal):
    from concurrent.futures import ThreadPoolExecutor
    g = graph(goal)
    skill_count = len(g['skills'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post(f'/api/goals/{goal}/diagnostic'), range(2)))
    assert all(r.status_code == 200 for r in results)
    assert results[0].json() == results[1].json()
    questions = results[0].json()['questions']
    # Goal-aware quick assessment: one question per skill (capped) with full coverage
    assert len(questions) == min(skill_count, 10)
    assert {q['skill_db_id'] for q in questions} == {s['db_id'] for s in g['skills']}


def test_concurrent_verification_and_route_requests_are_idempotent(goal):
    from concurrent.futures import ThreadPoolExecutor
    g=graph(goal)
    sid=next(s['db_id'] for s in g['skills'] if s['status']=='AVAILABLE')
    with ThreadPoolExecutor(max_workers=2) as pool:
        quizzes=list(pool.map(lambda _: client.post(f'/api/goals/{goal}/skills/{sid}/verification'), range(2)))
    assert all(r.status_code==200 for r in quizzes)
    assert quizzes[0].json()==quizzes[1].json()
    assert len(quizzes[0].json()['questions'])==5
    with ThreadPoolExecutor(max_workers=2) as pool:
        routes=list(pool.map(lambda _: client.get(f'/api/goals/{goal}/route'), range(2)))
    assert all(r.status_code==200 for r in routes)
    assert routes[0].json()==routes[1].json()
    assert len(client.get(f'/api/goals/{goal}/routes').json())==1
