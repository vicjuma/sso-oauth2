from django.test import TestCase, SimpleTestCase, Client
from django.urls import resolve, reverse
from users.views import login, logout, authorize, token
from users.models import Users, Apps, Resources
from urllib.parse import urlparse, parse_qs
import json

# Create your tests here.

class TestUrls(TestCase):

    def test_login_url_is_resolved(self):
        url = reverse("login")
        self.assertEquals(resolve(url).func, login)

    def test_logout_url_is_resolved(self):
        url = reverse("logout")
        self.assertEquals(resolve(url).func, logout)

    def test_authorize_url_is_resolved(self):
        url = reverse("authorize")
        self.assertEquals(resolve(url).func, authorize)

class TestViews(TestCase):

    def test_login_fail(self):
        Users.objects.create(
            username = "user_test",
            password = "pass_test"
        )
        client = Client()
        response = client.get(reverse("login"), {
            'username': 'user_bad',
            'password': 'pass_bad',
            'response_type': 'code',
            'client_id': 1,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
        })

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed('login_fail.html')

    def test_login_ok(self):
        Users.objects.create(
            username = "user_test",
            password = "pass_test"
        )
        client = Client()
        response = client.get(reverse("login"), {
            'username': 'user_test',
            'password': 'pass_test',
            'response_type': 'code',
            'client_id': 1,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
        })
        self.assertEquals(response.status_code, 302)

    def test_logout(self):
        client = Client()
        response = client.get(reverse("logout"))
        self.assertEquals(response.status_code, 200)

    def test_authorize_to_permisions(self):

        user = Users.objects.create(
            username = "user_test",
            password = "pass_test"
        )

        app1 = Apps.objects.create(
            name = "App1"
        )

        app2 = Apps.objects.create(
            name = "App2"
        )

        resource1 = Resources.objects.create(
            name = "Resource1"
        )

        resource2 = Resources.objects.create(
            name = "Resource2"
        )

        user.app.add(app1)
        resource1.app.add(app1)

        client = Client()
        response = client.get(reverse("login"), {
            'username': 'user_test',
            'password': 'pass_test',
            'response_type': 'code',
            'client_id': 1,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
        })
        self.assertEquals(response.status_code, 302)
        
        response = client.get(reverse("authorize"), {
            'response_type': 'code',
            'client_id': 1,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
        })

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed('permisions.html')

    def test_authorize_to_login(self):
        
        client = Client()
        response = client.get(reverse("authorize"), {
            'response_type': 'code',
            'client_id': 1,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
        })

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed('login.html')

    def test_authorize_to_app_does_not_exist(self):

        Users.objects.create(
            username = "user_test",
            password = "pass_test"
        )
        client = Client()
        response = client.get(reverse("login"), {
            'username': 'user_test',
            'password': 'pass_test',
            'response_type': 'code',
            'client_id': 1,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
        })
        self.assertEquals(response.status_code, 302)
        
        response = client.get(reverse("authorize"), {
            'response_type': 'code',
            'client_id': 2,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
        })

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed('error.html')

    def test_authorize_and_get_token(self):

        user = Users.objects.create(
            username = "user_test",
            password = "pass_test"
        )

        app1 = Apps.objects.create(
            name = "App1",
            secret = "1029384756"
        )

        app2 = Apps.objects.create(
            name = "App2"
        )

        resource1 = Resources.objects.create(
            name = "Resource1"
        )

        resource2 = Resources.objects.create(
            name = "Resource2"
        )

        user.app.add(app1)
        resource1.app.add(app1)

        client = Client()
        response = client.get(reverse("login"), {
            'username': 'user_test',
            'password': 'pass_test',
            'response_type': 'code',
            'client_id': 1,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
        })
        self.assertEquals(response.status_code, 302)
        
        response = client.get(reverse("authorize"), {
            'response_type': 'code',
            'client_id': 1,
            'resource_id': 1,
            'redirect_uri': 'http://www.google.com',
            'state': 'xyz',
            'scope': 'all',
            'granted': 'yes',
        })

        self.assertEquals(response.status_code, 302)

        code = parse_qs(urlparse(response.url).query)['code'][0]
        state = parse_qs(urlparse(response.url).query)['state'][0]

        self.assertEquals(state, "xyz")

        response = client.get(reverse("token"), {
            'client_id': 1,
            'app_secret': '1029384756',
            'code': code,
        })

        self.assertEqual(response.status_code, 200)

class TestModels(TestCase):
    
    def test_apps_names_list(self):

        user = Users.objects.create(
            username = "pepito",
            password = "123"
        )
        
        app1 = Apps.objects.create(
            name = "app1"
        )

        app2 = Apps.objects.create(
            name = "app2"
        )

        user.app.add(app1)
        user.app.add(app2)

        self.assertEquals(user.str_apps, ['app1','app2'])
