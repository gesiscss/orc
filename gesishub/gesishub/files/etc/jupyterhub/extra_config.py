"""
Custom JupyterHub handlers for admin and authenticator.

These handlers are imported in extraConfig in values.yaml
"""
import json
from os.path import join
from urllib.parse import urlencode
from tornado import web
import uuid
import os
from jupyterhub import orm, __version__
from jupyterhub.handlers import BaseHandler, LogoutHandler, LoginHandler
from jupyterhub.utils import admin_only
from jupyterhub.pagination import Pagination
from oauthenticator.oauth2 import OAuthCallbackHandler

ORC_LOGIN_COOKIE_NAME = "user-logged-in"
ORC_LOGIN_COOKIE_EXPIRES_DAYS = 30

current_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(current_dir, '_secret_user_id.json')) as user_id_file:
    uuid_user_claims = json.load(user_id_file)

class TakeoutData(BaseHandler):
    @web.authenticated
    async def get(self):
        html = await self.render_template(
            'takeout.html',
            current_user=self.current_user,
            takeout_url=f"{uuid_user_claims[self.current_user.name]['user_id']}.tar.xz",
            admin_access=self.settings.get('admin_access', False),
            allow_named_servers=self.allow_named_servers,
            named_server_limit_per_user=self.named_server_limit_per_user,
            server_version='{} {}'.format(__version__, self.version_hash),
        )
        self.finish(html)


class OrcAdminHandler(BaseHandler):
    """Render the admin page."""

    @web.authenticated
    @admin_only
    async def get(self):
        pagination = Pagination(url=self.request.uri, config=self.config)
        page, per_page, offset = pagination.get_page_args(self)

        available = {'name', 'admin', 'running', 'last_activity'}
        default_sort = ['last_activity']
        mapping = {'running': orm.Spawner.server_id}
        for name in available:
            if name not in mapping:
                mapping[name] = getattr(orm.User, name)

        default_order = {
            'name': 'asc',
            'last_activity': 'desc',
            'admin': 'desc',
            'running': 'desc',
        }

        sorts = self.get_arguments('sort') or default_sort
        orders = self.get_arguments('order')

        for bad in set(sorts).difference(available):
            self.log.warning("ignoring invalid sort: %r", bad)
            sorts.remove(bad)
        for bad in set(orders).difference({'asc', 'desc'}):
            self.log.warning("ignoring invalid order: %r", bad)
            orders.remove(bad)

        # add default sort as secondary
        for s in default_sort:
            if s not in sorts:
                sorts.append(s)
        if len(orders) < len(sorts):
            for col in sorts[len(orders):]:
                orders.append(default_order[col])
        else:
            orders = orders[: len(sorts)]

        # this could be one incomprehensible nested list comprehension
        # get User columns
        cols = [mapping[c] for c in sorts]
        # get User.col.desc() order objects
        ordered = [getattr(c, o)() for c, o in zip(cols, orders)]

        users = (
            self.db.query(orm.User)
            .outerjoin(orm.Spawner)
            .order_by(*ordered)
            .limit(per_page)
            .offset(offset)
        )
        users = [self._user_from_orm(u) for u in users]

        running = []
        for u in users:
            running.extend(s for s in u.spawners.values() if s.active)
            auth_state = await u.get_auth_state()
            auth_state = auth_state or {}
            oauth_user = auth_state.get('oauth_user', {})
            setattr(u, 'dn', oauth_user.get('name', ''))

        pagination.total = self.db.query(orm.User.id).count()

        html = await self.render_template(
            'admin.html',
            current_user=self.current_user,
            admin_access=self.settings.get('admin_access', False),
            users=users,
            running=running,
            sort={s: o for s, o in zip(sorts, orders)},
            allow_named_servers=self.allow_named_servers,
            named_server_limit_per_user=self.named_server_limit_per_user,
            server_version='{} {}'.format(__version__, self.version_hash),
            pagination=pagination,
        )
        self.finish(html)


class KeycloakLogoutHandler(LogoutHandler):
    """this handler is copied from
    https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues/886#issuecomment-470869625

    https://github.com/InfuseAI/primehub/blob/master/helm/primehub/jupyterhub_primehub.py
    """

    def clear_login_cookie(self, name=None):
        super().clear_login_cookie(name)
        self.clear_cookie(ORC_LOGIN_COOKIE_NAME, path="/")

    async def render_logout_page(self):
        """Render the logout page, if any

        Override this function to set a custom logout page.
        """
        # after logout, redirect user to home page
        site_url = 'https://{}'.format(self.request.host)
        self.redirect(site_url, permanent=False)

    async def get(self):
        # redirect to keycloak logout url and redirect back with kc=true parameters
        # then proceed with the original logout method.
        logout_kc = self.get_argument('kc', '')
        if logout_kc != 'true':
            logout_url = self.request.full_url() + '?kc=true'
            if not logout_url.startswith('https'):
                logout_url = logout_url.replace('http', 'https', 1)
            kc_logout_url = self.request.host.replace('notebooks', 'login', 1)
            kc_logout_url = 'https://{}/realms/gesis/protocol/openid-connect/logout'.format(kc_logout_url)
            self.redirect(kc_logout_url + '?' + urlencode({'redirect_uri': logout_url}))
        else:
            await super().get()


class KeycloakLoginHandler(LoginHandler):
    def set_login_cookie(self, user):
        super().set_login_cookie(user)
        self.set_cookie(name=ORC_LOGIN_COOKIE_NAME, value="true", path="/", expires_days=ORC_LOGIN_COOKIE_EXPIRES_DAYS)


class KeycloakOAuthCallbackHandler(OAuthCallbackHandler):
    def set_login_cookie(self, user):
        super().set_login_cookie(user)
        self.set_cookie(name=ORC_LOGIN_COOKIE_NAME, value="true", path="/", expires_days=ORC_LOGIN_COOKIE_EXPIRES_DAYS)


with open(os.path.join(current_dir, 'extra_config.json')) as extra_config_file:
    template_vars = json.load(extra_config_file)["template_vars"]
template_vars.update({
    "static_version": uuid.uuid4().hex,
    # 'help_url': 'https://www.gesis.org/en/help/',
})
