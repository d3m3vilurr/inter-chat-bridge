from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
import httplib2
from datetime import datetime, timedelta
from gdata.photos.service import PhotosService
from gdata.photos import PhotoEntry
import atom
import mimetypes
import os.path


PICASA_OAUTH_SCOPE = 'https://picasaweb.google.com/data/'
PICASA_REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'


class Picasa(object):
    def __init__(self, email, client_secret, credentials_dat):
        storage = Storage(credentials_dat)
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            flow = flow_from_clientsecrets(client_secret,
                                           scope=PICASA_OAUTH_SCOPE,
                                           redirect_uri=PICASA_REDIRECT_URI)
            uri = flow.step1_get_authorize_url()
            print 'open to browser:'
            print uri
            code = raw_input('Enter the authentication code: ').strip()
            credentials = flow.step2_exchange(code)
        if (credentials.token_expiry - datetime.utcnow()) < timedelta(minutes=5):
            http = httplib2.Http()
            http = credentials.authorize(http)
            credentials.refresh(http)
        storage.put(credentials)
        client = PhotosService()
        client.email = email
        client.source = 'inter-chat-bridge'
        client.additional_headers = \
            dict(Authorization='Bearer %s' % credentials.access_token)
        self.client = client
        self.albums = {}

    def _find_or_create_album(self, name):
        albums = self.client.GetUserFeed()
        for album in albums.entry:
            if album.title.text == name:
                return album
        return self.client.InsertAlbum(title=name, summary='',
                                       access='protected')

    def post(self, image_path, album='inter-chat-bridge'):
        _album = self.albums.get(album)
        if not _album:
            _album = self._find_or_create_album(album)
            self.albums[album] = _album
        album_url = '/data/feed/api/user/%s/albumid/%s' % \
                    (self.client.email, _album.gphoto_id.text)
        filename = os.path.basename(image_path)
        ext = os.path.splitext(filename)[1].lower()
        content_type = mimetypes.types_map[ext]
        if content_type.startswith('image/'):
            photo_entry = PhotoEntry()
        else:
            return 'unknown image format:' + content_type
        photo_entry.title = atom.Title(text=filename)
        photo_entry.summary = atom.Summary(text='', summary_type='text')
        photo = self.client.InsertPhoto(album_url, photo_entry, image_path,
                                        content_type)
        if not photo.link or not len(photo.link):
            return 'not found link'
        for link in photo.link:
            if 'lh/photo' in link.href:
                return link.href
        return 'not found link'

if __name__ == '__main__':
    if not os.path.exists('client_secret.json'):
        raise SystemError('not found client_secret.json')
    email = raw_input('Enter your email address: ').strip()
    c = Picasa(email, 'client_secret.json', 'gauth_credentials.dat')
    image_path = raw_input('Enter image path: ').strip()
    c.post(image_path)