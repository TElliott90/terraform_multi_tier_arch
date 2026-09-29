import io
import json
import tempfile
import unittest
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

import server


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.object(server, 'DB_PATH', Path(self.temp.name) / 'test.db')
        patcher.start()
        self.addCleanup(patcher.stop)
        server.initialize()

    def call(self, route, data=None, cookie='', origin=None):
        handler = object.__new__(server.Handler)
        handler.path = '/api/' + route
        raw = json.dumps(data).encode()
        handler.headers = {'Content-Type': 'application/json', 'Content-Length': str(len(raw)), 'Cookie': cookie, 'Host': 'localhost:5173'}
        if origin:
            handler.headers['Origin'] = origin
        handler.rfile = io.BytesIO(raw)
        result = {}
        handler.reply = lambda status, body, cookie=None: result.update(status=status, body=body, cookie=cookie)
        (handler.do_GET if data is None else handler.do_POST)()
        return result

    def test_registration_session_login_and_logout(self):
        account = {'name': 'Alex', 'email': 'Alex@example.com', 'password': 'safe-password'}
        registered = self.call('register', account)
        self.assertEqual(registered['status'], HTTPStatus.CREATED)
        cookie = 'session=' + registered['cookie']
        self.assertEqual(self.call('me', cookie=cookie)['body']['user']['email'], 'alex@example.com')
        with server.connect() as db:
            user = db.execute('SELECT * FROM users').fetchone()
            self.assertNotEqual(user['password_hash'], account['password'])
            self.assertNotEqual(db.execute('SELECT token_hash FROM sessions').fetchone()[0], registered['cookie'])
        self.assertEqual(self.call('register', account)['status'], 409)
        self.assertEqual(self.call('login', {**account, 'password': 'wrong'})['status'], 401)
        self.assertEqual(self.call('logout', {}, cookie)['status'], 200)
        self.assertIsNone(self.call('me', cookie=cookie)['body']['user'])
        login = self.call('login', account)
        self.assertEqual(login['status'], 200)
        with server.connect() as db:
            db.execute('UPDATE sessions SET expires = 0')
        self.assertIsNone(self.call('me', cookie='session=' + login['cookie'])['body']['user'])

    def test_validation_and_origin(self):
        self.assertEqual(self.call('register', {'name': '', 'email': 'a@b.com', 'password': 'short'})['status'], 400)
        self.assertEqual(self.call('login', {'email': 123, 'password': []})['status'], 400)
        self.assertEqual(self.call('login', [], origin='http://evil.example')['status'], 403)
        self.assertEqual(self.call('login', [])['status'], 400)
        self.assertIsNone(self.call('me')['body']['user'])


if __name__ == '__main__':
    unittest.main()
