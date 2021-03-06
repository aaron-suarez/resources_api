from .helpers import (
    update_resource, get_api_key, assert_wrong_type,
    assert_correct_response
)

from ..test_auth_jwt import GOOD_AUTH


def test_update_votes(module_client, module_db, fake_auth_from_oc, fake_algolia_save):
    client = module_client
    UPVOTE = 'upvote'
    DOWNVOTE = 'downvote'
    USER_VOTE_DIRECTION = 'user_vote_direction'
    id = 1
    apikey = get_api_key(client)

    data = client.get(f"api/v1/resources/{id}").json['resource']
    response = client.put(
                        f"/api/v1/resources/{id}/{UPVOTE}",
                        follow_redirects=True,
                        headers={'x-apikey': apikey})
    initial_upvotes = data.get(f"{UPVOTE}s")
    initial_downvotes = data.get(f"{DOWNVOTE}s")

    assert (response.status_code == 200)
    assert (response.json['resource'].get(f"{UPVOTE}s") == initial_upvotes + 1)
    assert (response.json['resource'].get(USER_VOTE_DIRECTION) == UPVOTE)

    response = client.put(
                        f"/api/v1/resources/{id}/{DOWNVOTE}",
                        follow_redirects=True,
                        headers={'x-apikey': apikey})
    # Simple limit vote per user test
    assert (response.status_code == 200)
    assert (response.json['resource'].get(f"{UPVOTE}s") == initial_upvotes)
    assert (response.json['resource'].get(f"{DOWNVOTE}s") == initial_downvotes + 1)
    assert (response.json['resource'].get(USER_VOTE_DIRECTION) == DOWNVOTE)

    response = client.put(
                        f"/api/v1/resources/{id}/{DOWNVOTE}",
                        follow_redirects=True,
                        headers={'x-apikey': apikey})
    assert (response.status_code == 200)
    assert (response.json['resource'].get(f"{DOWNVOTE}s") == initial_downvotes)
    assert (response.json['resource'].get(USER_VOTE_DIRECTION) is None)


def test_update_votes_invalid(
        module_client, module_db, fake_auth_from_oc, fake_algolia_save):
    client = module_client
    id = 'waffles'
    apikey = get_api_key(client)

    response = client.put(
                        f"/api/v1/resources/{id}/upvote",
                        follow_redirects=True,
                        headers={'x-apikey': apikey})
    assert_correct_response(response, 404)
    response = client.put(
                        f"/api/v1/resources/{id}/downvote",
                        follow_redirects=True,
                        headers={'x-apikey': apikey})
    assert_correct_response(response, 404)


def test_update_votes_out_of_bounds(
        module_client, module_db, fake_auth_from_oc, fake_algolia_save):
    client = module_client
    apikey = get_api_key(client)
    too_high = 99999999
    response = client.put(
                        f"/api/v1/resources/{too_high}/upvote",
                        follow_redirects=True,
                        headers={'x-apikey': apikey})
    assert_correct_response(response, 404)
    response = client.put(
                        f"/api/v1/resources/{too_high}/downvote",
                        follow_redirects=True,
                        headers={'x-apikey': apikey})
    assert_correct_response(response, 404)


def test_add_click(module_client, module_db):
    client = module_client

    # Check clicking on a valid resource
    id = 1
    data = client.get(f"api/v1/resources/{id}").json['resource']
    response = client.put(f"/api/v1/resources/{id}/click", follow_redirects=True)
    initial_click_count = data.get("times_clicked")

    assert (response.status_code == 200)
    assert (response.json['resource'].get("times_clicked") == initial_click_count + 1)

    # Check clicking on an invalid resource
    id = 'pancakes'
    response = client.put(f"/api/v1/resources/{id}/click", follow_redirects=True)
    assert_correct_response(response, 404)

    # Check clicking on a resource that doesn't exist
    too_high = 99999999
    response = client.put(f"/api/v1/resources/{too_high}/click", follow_redirects=True)
    assert_correct_response(response, 404)


def test_update_resource_wrong_type(
        module_client, module_db, fake_auth_from_oc, fake_algolia_save):
    client = module_client
    apikey = get_api_key(client)
    response = client.put('/api/v1/resources/1',
                          json=[{"expected_error": "This should be a dict"}],
                          headers={'x-apikey': apikey})
    assert_wrong_type(response, "array")

    response = client.put('/api/v1/resources/1',
                          json=1,
                          headers={'x-apikey': apikey})
    assert_wrong_type(response, "int")

    response = client.put('/api/v1/resources/1',
                          json=4.2,
                          headers={'x-apikey': apikey})
    assert_wrong_type(response, "number")

    response = client.put('/api/v1/resources/1',
                          json=True,
                          headers={'x-apikey': apikey})
    assert_wrong_type(response, "boolean")

    response = client.put('/api/v1/resources/1',
                          json="This should be a dict",
                          headers={'x-apikey': apikey})
    assert_wrong_type(response, "string")


def test_update_resource(
        module_client, module_db, fake_auth_from_oc, fake_algolia_save):
    client = module_client
    apikey = get_api_key(client)

    # Happy Path
    response = update_resource(client, apikey)
    assert (response.status_code == 200)
    assert (response.json['resource'].get('name') == "New name")

    # free parameter as "FALSE" instead of False
    response = update_resource(client, apikey, name="New name 2", free="FALSE")
    assert (response.status_code == 200)
    assert (response.json['resource'].get('name') == "New name 2")

    # Bogus Data
    name = False
    url = "htt://bad_url.doesnotexist"
    category = True
    languages = False
    free = "Bad Data"
    notes = True
    response = update_resource(client,
                               apikey,
                               name,
                               url,
                               category,
                               languages,
                               free,
                               notes)
    assert (response.status_code == 422)

    # Boolean strings that can be parsed to true or False
    name = "StringsForBools"
    url = None
    category = None
    languages = None
    free = "FaLsE"
    notes = "Some notes"
    response = update_resource(client,
                               apikey,
                               name,
                               url,
                               category,
                               languages,
                               free,
                               notes)
    assert (response.status_code == 200)
    assert response.json['resource'].get('free') is False
    name = "StringsForBools"
    url = None
    category = None
    languages = None
    free = "TrUe"
    notes = "Some notes"
    response = update_resource(client,
                               apikey,
                               name,
                               url,
                               category,
                               languages,
                               free,
                               notes)
    assert (response.status_code == 200)
    assert response.json['resource'].get('free') is True

    # Bad "free" data
    free = "PERHAPS"
    response = update_resource(client,
                               apikey,
                               name,
                               url,
                               category,
                               languages,
                               free,
                               notes)
    assert (response.status_code == 422)

    # A String to Big for the DB
    long_string = "x" * 6501
    name = long_string
    url = long_string
    category = long_string
    languages = long_string
    free = True
    notes = long_string
    response = update_resource(client,
                               apikey,
                               name,
                               url,
                               category,
                               languages,
                               free,
                               notes)
    assert (response.status_code == 422)

    # Unicode Characters
    name = "😀"
    url = None
    category = None
    languages = None
    free = True
    notes = "∞"
    response = update_resource(client,
                               apikey,
                               name,
                               url,
                               category,
                               languages,
                               free,
                               notes)
    assert (response.status_code == 200)

    # Empty languages list given removes all languages of resource
    response = update_resource(client, apikey, languages=[])
    assert (response.status_code == 200)
    assert (response.json['resource'].get('languages') == [])

    # Resource not found
    response = client.put("/api/v1/resources/0",
                          json=dict(name="New name"),
                          headers={'x-apikey': apikey},
                          follow_redirects=True
                          )
    assert_correct_response(response, 404)


def test_update_votes_authorization_header(
        module_client, module_db, fake_auth_from_oc, fake_algolia_save):
    client = module_client
    id = 1
    UPVOTE = 'upvote'
    DOWNVOTE = 'downvote'
    USER_VOTE_DIRECTION = 'user_vote_direction'

    data = client.get(f"api/v1/resources/{id}").json['resource']
    response = client.put(
                        f"/api/v1/resources/{id}/upvote",
                        follow_redirects=True,
                        headers={'authorization': GOOD_AUTH})
    initial_upvotes = data.get(f"{UPVOTE}s")
    initial_downvotes = data.get(f"{DOWNVOTE}s")

    assert (response.status_code == 200)
    assert (response.json['resource'].get(f"{UPVOTE}s") == initial_upvotes + 1)
    assert (response.json['resource'].get(USER_VOTE_DIRECTION) == UPVOTE)

    response = client.put(
                        f"/api/v1/resources/{id}/downvote",
                        follow_redirects=True,
                        headers={'authorization': GOOD_AUTH})

    assert (response.status_code == 200)
    assert (response.json['resource'].get(f"{UPVOTE}s") == initial_upvotes)
    assert (response.json['resource'].get(f"{DOWNVOTE}s") == initial_downvotes + 1)
    assert (response.json['resource'].get(USER_VOTE_DIRECTION) == DOWNVOTE)


def test_delete_unused_languages(module_client, module_db,
                                 fake_auth_from_oc, fake_algolia_save):
    client = module_client
    apikey = get_api_key(client)

    # Happy Path
    response = update_resource(client, apikey)
    assert (response.status_code == 200)
    assert (response.json['resource'].get('name') == "New name")

    # Initial Data
    name = "Language Test"
    url = None
    category = None
    # Random Language DS/AI
    languages = ["Python", "DS/AI"]
    paid = None
    notes = None

    # Update response
    response = update_resource(client,
                               apikey,
                               name,
                               url,
                               category,
                               languages,
                               paid,
                               notes)
    # Check update
    assert (response.status_code == 200)
    assert (response.json['resource'].get('name') == "Language Test")
    languages_response = response.json['resource'].get('languages')
    assert ("Python" in languages_response)
    assert ("DS/AI" in languages_response)

    # Update Languages remove DS/AI and add JavaScript and HTML
    languages.append("JavaScript")
    languages.append("HTML")
    languages.remove("DS/AI")
    response = update_resource(client, apikey, name, url,
                               category, languages, paid, notes)

    # Check Update of Languages
    assert (response.status_code == 200)
    languages_response = response.json['resource'].get('languages')
    assert ("Python" in languages_response)
    assert ("JavaScript" in languages_response)
    assert ("HTML" in languages_response)
    assert ("DS/AI" not in languages_response)

    db_languages = client.get('api/v1/languages')
    db_languages = [language.get('name') for language in db_languages.json['languages']]

    assert ("DS/AI" not in db_languages)


def test_delete_unused_categories(module_client, module_db,
                                  fake_auth_from_oc, fake_algolia_save):
    client = module_client
    apikey = get_api_key(client)

    # Happy Path
    response = update_resource(client, apikey)
    assert (response.status_code == 200)
    assert (response.json['resource'].get('name') == "New name")

    # Test Categories
    test_cat_1 = 'Holy hand grenades'
    test_cat_2 = 'News'

    # Initial Data
    name = "Category Test"
    url = None
    category = test_cat_1
    languages = None
    paid = None
    notes = None

    # Update response
    response = update_resource(client,
                               apikey,
                               name,
                               url,
                               category,
                               languages,
                               paid,
                               notes)
    # Check update
    assert (response.status_code == 200)
    assert (response.json['resource'].get('name') == "Category Test")
    category_response = response.json['resource'].get('category')
    assert (category_response == test_cat_1)

    # Update category to something else
    category = test_cat_2
    response = update_resource(client, apikey, name, url,
                               category, languages, paid, notes)

    # Check Update of category
    assert (response.status_code == 200)
    category_response = response.json['resource'].get('category')
    assert (category_response == test_cat_2)

    db_categories = client.get('api/v1/categories')
    db_categories = [category.get('name')
                     for category in db_categories.json['categories']]

    assert (test_cat_1 not in db_categories)
