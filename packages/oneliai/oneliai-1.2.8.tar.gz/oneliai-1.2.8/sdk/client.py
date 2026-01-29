import requests
import jwt
import datetime

# URL="https://apis.oneli.chat"
URL="http://localhost:8085"
class AICustomerClient:
    def __init__(self, client_id, client_secret, base_url=f'{URL}/v1/strategy'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        response = requests.post(
            f'{self.base_url}/auth/token',
            json={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }
        )
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            raise Exception('Failed to get access token')

    def generate_response(self, template_id, variables):
        response = requests.post(
            f'{self.base_url}/dynamic-response',
            json={
                'template_id': template_id,
                'variables': variables
            },
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        if response.status_code == 200:
            return response.json().get('response')
        else:
            return response.json()
            # raise Exception('Failed to generate response')

    def query_data(self, arg, template_id):
        response = requests.post(
            f'{self.base_url}/query-data',
            json={
                'arg': arg,
                'template_id': template_id
            },
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            res=response.json()
            raise Exception(res['error'])
        

    def query_intention(self, question):
        response = requests.post(
            f'{self.base_url}/query-intention',
            json={
                'question': question
             
            },
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception('Failed to start intention query')
        
    def registEndpoint(self,  name,endpointpath):
        response = requests.post(
            f'{self.base_url}/createEndpoints',
            json={
                "endpointpath": endpointpath,
                "method": "POST",
                "name":name
            },
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception('Failed to createEndpoints')
        


    def createRoles(self, role_name, description):
        response = requests.post(
            f'{self.base_url}/createRoles',
            json={
                "role_name": role_name,
                "description":description
            },
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception('Failed to createRoles')
        
    def roles_endpoint(self, role_id, endpoint_id):
        response = requests.post(
            f'{self.base_url}/roles/{role_id}/endpoints',
            json={
                "endpoint_id": endpoint_id
            },
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception('Failed to roles_endpoint')
        

    def user_roles(self, user_id, role_id):
        response = requests.post(
            f'{self.base_url}/users/{user_id}/roles',
            json={
                "role_id": role_id
            },
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception('Failed to user_roles')