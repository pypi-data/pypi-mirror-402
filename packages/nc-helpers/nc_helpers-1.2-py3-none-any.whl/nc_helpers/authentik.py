import os
import requests
import logging
import json
from distutils.version import StrictVersion

class Authentik():
    def __init__(self, host = None, api_token = None, port=443, secure=True):
        self.port = port
        self.secure = secure
        if host and api_token:
            self.host = host
            self.api_token = api_token
        else:
            from dotenv import load_dotenv
            load_dotenv()

            self.api_token=os.environ.get('AUTHENTIK_TOKEN')
            self.host=os.environ.get('AUTHENTIK_HOST')
        logging.basicConfig(filename='inflator-authentik.log', level=logging.DEBUG)

        self.logger = logging.getLogger("inflator-authentik")

        self.version = StrictVersion(self._get('admin/version/').get('version_current'))

        self.logger.info(f"version: {self.version}")

    def _get(self,path,params=None):
        r = requests.get(
            f'https://{self.host}/api/v3/{path}', 
            headers = {'Authorization': f"Bearer {self.api_token}", 
                       'accept': 'application/json',
                       'Content-Type': 'application/json'
                       },
            params=params
        )
        if r.status_code == 200:
            self.logger.debug(f"Got data: {json.dumps(r.json())}")
            return r.json()
        else:
            return {}

    def _post(self,path,data):
        self.logger.debug(f"Post request to: {path} with data: {data}")
        r = requests.post(
            f'https://{self.host}/api/v3/{path}', 
            headers = {'Authorization': f"Bearer {self.api_token}",
                       'accept': 'application/json',
                       'Content-Type': 'application/json'
                       },
            json = data
        )
        if r.status_code == 201:
            self.logger.debug(json.dumps(r.json()))
            return r.json()
        elif r.status_code == 400:
            self.logger.error(f"Error on post: {json.dumps(r.json())}")
            raise Exception("HTTP error")
        else:
            return {}
        
    def get_authorization_flow(self):
        self._get('flows/instances/', params={'designation': 'authorization'})

    def get_certificate(self):
        certs = self._get('/crypto/certificatekeypairs/')['results']
        return certs[0]
  
    def create_application(self, appname, auth_method=None, external_url=None, internal_url=None):
        if not external_url: external_url = f"https://{self.host.replace('authentik',appname)}"
        if not internal_url: internal_url = external_url
        
        application = self._get(f'core/applications/{appname}')
        if not application:
            if auth_method:            
                provider= self.create_provider(appname, auth_method)
                
            data = {
                    'name': appname,
                    'slug': appname,
                    'provider': provider.get('pk',None),
                    'open_in_new_tab': True,
                    "meta_launch_url": external_url,
                    "meta_description": "unknown",
                    "meta_publisher": "ncubed",
                    "group": "Tools"
                    }
                
            application = self._post('core/applications/',data)
            # TODO: figure out where we push the images
            #icon_status = self._post(f'core/applications/{appname}/set_icon_url/',{"url": f"/{appname}.png"})
            urls = self._get(f"providers/oauth2/{provider['pk']}/setup_urls/")
        return (application, provider, urls)

    def create_group(self, group_name):
        data = {
                'name': group_name,
                'is_superuser': False,
                # 'attributes': None,
                }
            
        group = self._post('core/groups/',data)
        return group

    def get_default_property_mappings(self):
        results = [x['pk'] for x in self._get('propertymappings/all/')['results'] if x['managed'] == 'goauthentik.io/providers/oauth2/scope-openid' or x['managed'] == 'goauthentik.io/providers/oauth2/scope-profile' or x['managed'] == 'goauthentik.io/providers/oauth2/scope-email']
        return results
        
    def create_provider(self, appname, auth_method=None):
        provider_name = f"{appname}_oauth2"
        
        if auth_method == 'oauth2':
            self.logger.debug('Getting existing provider')
            provider = self._get('providers/oauth2/',params={'name':provider_name}).get('results')
            self.logger.debug(f"Got providers: {provider}")
            cert = self.get_certificate()
            
            if not provider:
                self.logger.debug(f"Found no provider, creating one...")
                data = {
                "name": f"{appname}_oauth2",
                "authorization_flow": self._get('flows/instances/default-provider-authorization-explicit-consent/').get('pk'),
                "invalidation_flow": self._get('/flows/instances/default-invalidation-flow/').get('pk'),
                "include_claims_in_id_token": True,
                "property_mappings": self.get_default_property_mappings(),
                "sub_mode": "user_email",
                "signing_key": cert['pk'],
                }
                if self.version > StrictVersion('2024.8.0'):
                    data['redirect_uris'] = [
                    {
                    "matching_mode": "strict",
                    "url": f"https://{self.host.replace('authentik',appname)}/oauth/complete/oidc/"
                    }
                ]
                
                provider = self._post('providers/oauth2/',data)
            else:
                provider = provider[0]

            
        
        return provider