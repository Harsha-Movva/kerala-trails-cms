from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def staff_headers():
    response = client.post('/api/auth/login', json={
        'email': 'admin@keralatrails.demo',
        'password': 'TrailDemo!2026',
    })
    assert response.status_code == 200
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def package_payload():
    suffix = uuid4().hex[:8]
    return {
        'code': f'TEST-{suffix}',
        'slug': f'test-journey-{suffix}',
        'title': 'Test Journey Original',
        'destination': 'Kerala',
        'duration_days': 3,
        'summary': 'A small test itinerary for version history.',
        'hero_image': '',
        'hotel_category': '4 star',
        'status': 'draft',
        'itinerary': [{'day': 1, 'title': 'Arrive', 'description': 'Check in.'}],
        'inclusions': ['Breakfast'],
        'seasons': [{'season': 'All year', 'start_month': 1, 'end_month': 12, 'price_per_person': 15000}],
    }


def test_draft_preview_is_staff_only_and_not_public():
    headers = staff_headers()
    payload = package_payload()
    created = client.post('/api/admin/packages', json=payload, headers=headers)
    assert created.status_code == 200
    package_id = created.json()['id']

    preview = client.get(f'/api/admin/packages/{package_id}/preview', headers=headers)
    assert preview.status_code == 200
    assert preview.json()['preview'] is True
    assert preview.json()['status'] == 'draft'

    public = client.get(f"/api/packages/{payload['slug']}")
    assert public.status_code == 404


def test_restore_creates_new_version_without_erasing_history():
    headers = staff_headers()
    payload = package_payload()
    created = client.post('/api/admin/packages', json=payload, headers=headers)
    assert created.status_code == 200
    package_id = created.json()['id']

    changed = {**payload, 'title': 'Test Journey Updated'}
    updated = client.put(f'/api/admin/packages/{package_id}', json=changed, headers=headers)
    assert updated.status_code == 200
    assert updated.json()['title'] == 'Test Journey Updated'

    restored = client.post(f'/api/admin/packages/{package_id}/versions/1/restore', headers=headers)
    assert restored.status_code == 200
    assert restored.json()['restored_from'] == 1
    assert restored.json()['created_version'] == 3
    assert restored.json()['package']['title'] == 'Test Journey Original'

    history = client.get(f'/api/admin/packages/{package_id}/versions', headers=headers)
    assert history.status_code == 200
    assert [v['version_number'] for v in history.json()] == [3, 2, 1]


def test_admin_routes_reject_anonymous_requests():
    assert client.get('/api/admin/packages').status_code == 401


def test_public_search_only_returns_published_matches():
    response = client.get('/api/packages?q=Munnar')
    assert response.status_code == 200
    assert response.json()
    assert all('munnar' in (p['title'] + p['destination']).lower() for p in response.json())
    assert all(p['status'] == 'published' for p in response.json())
    leaked = client.get('/api/packages?published_only=false')
    assert all(p['status'] == 'published' for p in leaked.json())


def test_package_changes_are_written_to_activity_log():
    headers = staff_headers()
    payload = package_payload()
    created = client.post('/api/admin/packages', json=payload, headers=headers)
    assert created.status_code == 200
    package_id = created.json()['id']
    activity = client.get('/api/admin/activity', headers=headers)
    assert activity.status_code == 200
    assert any(row['entity_id'] == package_id and row['action'] == 'package.created' for row in activity.json())


def test_sample_enquiry_runs_extraction_and_returns_package_suggestions():
    headers = staff_headers()
    response = client.post('/api/enquiries', json={
        'name': 'Demo Traveller',
        'email': 'traveller@example.test',
        'phone': '+91 9000000000',
        'message': 'Hi, 2 adults and 1 kid, Kerala 5-6 nights in December, budget around 1.2 lakh total, houseboat a must',
        'whatsapp_consent': False,
    })
    assert response.status_code == 200
    rows = client.get('/api/admin/enquiries', headers=headers)
    enquiry = next(row for row in rows.json() if row['id'] == response.json()['id'])
    assert enquiry['extracted']['destination'] == 'Kerala'
    assert enquiry['extracted']['total_budget_inr'] == 120000
    assert enquiry['extracted']['needs_manual_review'] is True
    assert enquiry['ai_suggestions']
    assert enquiry['ai_suggestions'][0]['title'].lower().find('munnar') >= 0

    corrected = {**enquiry['extracted'], 'destination': 'Kerala'}
    reviewed = client.patch(f"/api/admin/enquiries/{enquiry['id']}", json={
        'status': 'reviewing', 'extracted': corrected,
    }, headers=headers)
    assert reviewed.status_code == 200
    after_review = client.get('/api/admin/enquiries', headers=headers).json()
    saved = next(row for row in after_review if row['id'] == enquiry['id'])
    assert saved['extracted']['reviewed_by_staff'] is True
    assert saved['extracted']['needs_manual_review'] is False


def test_enquiry_rejects_invalid_email_and_phone():
    invalid = client.post('/api/enquiries', json={
        'name': 'Demo Traveller', 'email': 'not-an-email', 'phone': 'call-me',
        'message': 'We would like to plan a family holiday.',
    })
    assert invalid.status_code == 422
