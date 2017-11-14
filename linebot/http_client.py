# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

"""linebot.http_client module."""

from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod, abstractproperty

import requests
from future.utils import with_metaclass

from ..LineThrift.ttypes import Message
import json, requests, tempfile, shutil
import unicodedata
from random import randint

class HttpClient(with_metaclass(ABCMeta)):
    """Abstract Base Classes of HttpClient."""

    DEFAULT_TIMEOUT = 5

    def __init__(self, timeout=DEFAULT_TIMEOUT):
        """__init__ method.

        :param timeout: (optional) How long to wait for the server
            to send data before giving up, as a float,
            or a (connect timeout, readtimeout) float tuple.
            Default is :py:attr:`DEFAULT_TIMEOUT`
        :type timeout: float | tuple(float, float)
        :rtype: T <= :py:class:`HttpResponse`
        :return: HttpResponse instance
        """
        self.timeout = timeout

    @abstractmethod
    def get(self, url, headers=None, params=None, stream=False, timeout=None):
        """GET request.

        :param str url: Request url
        :param dict headers: (optional) Request headers
        :param dict params: (optional) Request query parameter
        :param bool stream: (optional) get content as stream
        :param timeout: (optional), How long to wait for the server
            to send data before giving up, as a float,
            or a (connect timeout, readtimeout) float tuple.
            Default is :py:attr:`self.timeout`
        :type timeout: float | tuple(float, float)
        :rtype: T <= :py:class:`HttpResponse`
        :return: HttpResponse instance
        """
        raise NotImplementedError

    @abstractmethod
    def post(self, url, headers=None, data=None, timeout=None):
        """POST request.

        :param str url: Request url
        :param dict headers: (optional) Request headers
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body
        :param timeout: (optional), How long to wait for the server
            to send data before giving up, as a float,
            or a (connect timeout, readtimeout) float tuple.
            Default is :py:attr:`self.timeout`
        :type timeout: float | tuple(float, float)
        :rtype: T <= :py:class:`HttpResponse`
        :return: HttpResponse instance
        """
        raise NotImplementedError


class RequestsHttpClient(HttpClient):
    """HttpClient implemented by requests."""

    def __init__(self, timeout=HttpClient.DEFAULT_TIMEOUT):
        """__init__ method.

        :param timeout: (optional) How long to wait for the server
            to send data before giving up, as a float,
            or a (connect timeout, readtimeout) float tuple.
            Default is :py:attr:`DEFAULT_TIMEOUT`
        :type timeout: float | tuple(float, float)
        """
        super(RequestsHttpClient, self).__init__(timeout)

    def get(self, url, headers=None, params=None, stream=False, timeout=None):
        """GET request.

        :param str url: Request url
        :param dict headers: (optional) Request headers
        :param dict params: (optional) Request query parameter
        :param bool stream: (optional) get content as stream
        :param timeout: (optional), How long to wait for the server
            to send data before giving up, as a float,
            or a (connect timeout, readtimeout) float tuple.
            Default is :py:attr:`self.timeout`
        :type timeout: float | tuple(float, float)
        :rtype: :py:class:`RequestsHttpResponse`
        :return: RequestsHttpResponse instance
        """
        if timeout is None:
            timeout = self.timeout

        response = requests.get(
            url, headers=headers, params=params, stream=stream, timeout=timeout
        )

        return RequestsHttpResponse(response)

    def post(self, url, headers=None, data=None, timeout=None):
        """POST request.

        :param str url: Request url
        :param dict headers: (optional) Request headers
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body
        :param timeout: (optional), How long to wait for the server
            to send data before giving up, as a float,
            or a (connect timeout, readtimeout) float tuple.
            Default is :py:attr:`self.timeout`
        :type timeout: float | tuple(float, float)
        :rtype: :py:class:`RequestsHttpResponse`
        :return: RequestsHttpResponse instance
        """
        if timeout is None:
            timeout = self.timeout

        response = requests.post(
            url, headers=headers, data=data, timeout=timeout
        )

        return RequestsHttpResponse(response)


class HttpResponse(with_metaclass(ABCMeta)):
    """HttpResponse."""

    @abstractproperty
    def status_code(self):
        """Get status code."""
        raise NotImplementedError

    @abstractproperty
    def headers(self):
        """Get headers."""
        raise NotImplementedError

    @abstractproperty
    def text(self):
        """Get request body as text-decoded."""
        raise NotImplementedError

    @abstractproperty
    def content(self):
        """Get request body as binary."""
        raise NotImplementedError

    @abstractproperty
    def json(self):
        """Get request body as json-decoded."""
        raise NotImplementedError

    @abstractmethod
    def iter_content(self, chunk_size=1024, decode_unicode=False):
        """Get request body as iterator content (stream).

        :param int chunk_size:
        :param bool decode_unicode:
        """
        raise NotImplementedError


class RequestsHttpResponse(HttpResponse):
    """HttpResponse implemented by requests lib's response."""

    def __init__(self, response):
        """__init__ method.

        :param response: requests lib's response
        """
        self.response = response

    @property
    def status_code(self):
        """Get status code."""
        return self.response.status_code

    @property
    def headers(self):
        """Get headers."""
        return self.response.headers

    @property
    def text(self):
        """Get request body as text-decoded."""
        return self.response.text

    @property
    def content(self):
        """Get request body as binary."""
        return self.response.content

    @property
    def json(self):
        """Get request body as json-decoded."""
        return self.response.json()

    def iter_content(self, chunk_size=1024, decode_unicode=False):
        """Get request body as iterator content (stream).

        :param int chunk_size:
        :param bool decode_unicode:
        """
        return self.response.iter_content(chunk_size=chunk_size, decode_unicode=decode_unicode)
    
    def post_content(self, urls, data=None, files=None):
        return self._session.post(urls, headers=self._headers, data=data, files=files)

    """Image"""

    
    def sendImage(self, to_, path):
        M = Message(to=to_, text=None, contentType = 1)
        M.contentMetadata = None
        M.contentPreview = None
        M2 = self._client.sendMessage(0,M)
        M_id = M2.id
        files = {
            'file': open(path, 'rb'),
        }
        params = {
            'name': 'media',
            'oid': M_id,
            'size': len(open(path, 'rb').read()),
            'type': 'image',
            'ver': '1.0',
        }
        data = {
            'params': json.dumps(params)
        }
        r = self.post_content('https://obs-sg.line-apps.com/talk/m/upload.nhn', data=data, files=files)
        if r.status_code != 201:
            raise Exception('Upload image failure.')
        return True

    
    def sendImageWithURL(self, to_, url):
        path = '%s/pythonLine-%i.data' % (tempfile.gettempdir(), randint(0, 9))
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(path, 'w') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            raise Exception('Download image failure.')
        try:
            self.sendImage(to_, path)
        except Exception as e:
            raise e
    """User"""

    
    def getProfile(self):
        return self._client.getProfile()

    
    def getSettings(self):
        return self._client.getSettings()

    
    def getUserTicket(self):
        return self._client.getUserTicket()

    
    def updateProfile(self, profileObject):
        return self._client.updateProfile(0, profileObject)

    
    def updateSettings(self, settingObject):
        return self._client.updateSettings(0, settingObject)

    """Operation"""

    
    def fetchOperation(self, revision, count):
        return self._client.fetchOperations(revision, count)

    
    def getLastOpRevision(self):
        return self._client.getLastOpRevision()

    """Message"""

    
    def sendEvent(self, messageObject):
        return self._client.sendEvent(0, messageObject)

    
    def sendMessage(self, messageObject):
        return self._client.sendMessage(0,messageObject)

    def getLastReadMessageIds(self, chatId):
        return self._client.getLastReadMessageIds(0,chatId)

    """Image"""

    
    def post_content(self, url, data=None, files=None):
        return self._session.post(url, headers=self._headers, data=data, files=files)

    """Contact"""

    
    def blockContact(self, mid):
        return self._client.blockContact(0, mid)

    
    def unblockContact(self, mid):
        return self._client.unblockContact(0, mid)

    
    def findAndAddContactsByMid(self, mid):
        return self._client.findAndAddContactsByMid(0, mid)

    
    def findAndAddContactsByUserid(self, userid):
        return self._client.findAndAddContactsByUserid(0, userid)

    
    def findContactsByUserid(self, userid):
        return self._client.findContactByUserid(userid)

    
    def findContactByTicket(self, ticketId):
        return self._client.findContactByUserTicket(ticketId)

    
    def getAllContactIds(self):
        return self._client.getAllContactIds()

    
    def getBlockedContactIds(self):
        return self._client.getBlockedContactIds()

    
    def getContact(self, mid):
        return self._client.getContact(mid)

    
    def getContacts(self, midlist):
        return self._client.getContacts(midlist)

    
    def getFavoriteMids(self):
        return self._client.getFavoriteMids()

    
    def getHiddenContactMids(self):
        return self._client.getHiddenContactMids()


    """Group"""

    
    def acceptGroupInvitation(self, groupId):
        return self._client.acceptGroupInvitation(0, groupId)

    
    def acceptGroupInvitationByTicket(self, groupId, ticketId):
        return self._client.acceptGroupInvitationByTicket(0, groupId, ticketId)

    
    def cancelGroupInvitation(self, groupId, contactIds):
        return self._client.cancelGroupInvitation(0, groupId, contactIds)

    
    def createGroup(self, name, midlist):
        return self._client.createGroup(0, name, midlist)

    
    def getGroup(self, groupId):
        return self._client.getGroup(groupId)

    
    def getGroups(self, groupIds):
        return self._client.getGroups(groupIds)

    
    def getGroupIdsInvited(self):
        return self._client.getGroupIdsInvited()

    
    def getGroupIdsJoined(self):
        return self._client.getGroupIdsJoined()

    
    def inviteIntoGroup(self, groupId, midlist):
        return self._client.inviteIntoGroup(0, groupId, midlist)

    
    def kickoutFromGroup(self, groupId, midlist):
        return self._client.kickoutFromGroup(0, groupId, midlist)

    
    def leaveGroup(self, groupId):
        return self._client.leaveGroup(0, groupId)

    
    def rejectGroupInvitation(self, groupId):
        return self._client.rejectGroupInvitation(0, groupId)

    
    def reissueGroupTicket(self, groupId):
        return self._client.reissueGroupTicket(groupId)

    
    def updateGroup(self, groupObject):
        return self._client.updateGroup(0, groupObject)

    """Room"""

    
    def createRoom(self, midlist):
        return self._client.createRoom(0, midlist)

    
    def getRoom(self, roomId):
        return self._client.getRoom(roomId)

    
    def inviteIntoRoom(self, roomId, midlist):
        return self._client.inviteIntoRoom(0, roomId, midlist)

    
    def leaveRoom(self, roomId):
        return self._client.leaveRoom(0, roomId)

    """unknown function"""

    
    def noop(self):
return self._client.noop()
