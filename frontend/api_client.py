from __future__ import annotations
import requests
import streamlit as st
from core.settings import get_settings

class ApiClient:
    def __init__(self, base_url:str|None=None):
        self.base_url=(base_url or get_settings().API_BASE_URL).rstrip('/')
    def _headers(self):
        token=st.session_state.get('api_access_token')
        return {'Authorization': f'Bearer {token}'} if token else {}
    def request(self, method:str, path:str, **kwargs):
        resp=requests.request(method, self.base_url+path, headers={**self._headers(), **kwargs.pop('headers',{})}, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()
    def login(self,email:str,password:str):
        data=self.request('POST','/auth/login',json={'email':email,'password':password})
        st.session_state['api_access_token']=data['access_token']; st.session_state['api_refresh_token']=data['refresh_token']
        return data
    def me(self): return self.request('GET','/auth/me')
    def guests(self,event_id:int,limit:int=100,offset:int=0): return self.request('GET',f'/guests?event_id={event_id}&limit={limit}&offset={offset}')
    def forms(self,event_id:int): return self.request('GET',f'/forms?event_id={event_id}')
    def insights(self,event_id:int): return self.request('GET',f'/insights?event_id={event_id}')
    def campaigns(self,event_id:int): return self.request('GET',f'/campaigns?event_id={event_id}')

api_client=ApiClient()
