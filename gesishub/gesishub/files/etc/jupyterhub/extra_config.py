"""
Custom handlers for GESIS Hub deployment.

These handlers are imported in extraConfig in values.yaml
"""

from urllib.parse import urlencode
from tornado import web

from jupyterhub import orm
from jupyterhub.handlers import BaseHandler, LogoutHandler
from jupyterhub.utils import admin_only

from oauthenticator.generic import GenericOAuthenticator


class OrcAdminHandler(BaseHandler):
    """Render the admin page."""

    @web.authenticated
    @admin_only
    async def get(self):
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

        users = self.db.query(orm.User).outerjoin(orm.Spawner).order_by(*ordered)
        users = [self._user_from_orm(u) for u in users]

        running = []
        for u in users:
            running.extend(s for s in u.spawners.values() if s.active)
            auth_state = await u.get_auth_state()
            auth_state = auth_state or {}
            oauth_user = auth_state.get('oauth_user', {})
            setattr(u, 'dn', oauth_user.get('name', ''))

        html = self.render_template(
            'admin.html',
            current_user=self.current_user,
            admin_access=self.settings.get('admin_access', False),
            users=users,
            running=running,
            sort={s: o for s, o in zip(sorts, orders)},
            allow_named_servers=self.allow_named_servers,
            named_server_limit_per_user=self.named_server_limit_per_user,
        )
        self.finish(html)


class KeycloakLogoutHandler(LogoutHandler):
    """this handler is copied from
    https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues/886#issuecomment-470869625

    https://github.com/InfuseAI/primehub/blob/master/helm/primehub/jupyterhub_primehub.py
    """

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
            kc_logout_url = self.request.host.replace('notebooks', 'login')
            kc_logout_url = 'https://{}/realms/gesis/protocol/openid-connect/logout'.format(kc_logout_url)
            self.redirect(kc_logout_url + '?' + urlencode({'redirect_uri': logout_url}))
        else:
            await super().get()


class KeycloakOAuthenticator(GenericOAuthenticator):
    logout_handler = KeycloakLogoutHandler

    def get_handlers(self, app):
        return super().get_handlers(app) + [(r'/logout', self.logout_handler)]
