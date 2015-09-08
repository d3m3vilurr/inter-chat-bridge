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
        self._storage = Storage(credentials_dat)
        self._credentials = self._storage.get()
        if self._credentials is None or self._credentials.invalid:
            flow = flow_from_clientsecrets(client_secret,
                                           scope=PICASA_OAUTH_SCOPE,
                                           redirect_uri=PICASA_REDIRECT_URI)
            uri = flow.step1_get_authorize_url()
            print 'open to browser:'
            print uri
            code = raw_input('Enter the authentication code: ').strip()
            self._credentials = flow.step2_exchange(code)
        client = PhotosService()
        client.email = email
        client.source = 'inter-chat-bridge'
        self.client = client
        self.albums = {}
        self._refresh_auth_token()

    def _refresh_auth_token(self):
        if (self._credentials.token_expiry - datetime.utcnow()) < \
                timedelta(minutes=5):
            http = httplib2.Http()
            http = credentials.authorize(http)
            self._credentials.refresh(http)
        self._storage.put(self._credentials)
        self.client.additional_headers['Authorization'] = \
            'Bearer %s' % self._credentials.access_token

    def _find_or_create_album(self, name):
        self._refresh_auth_token()
        albums = self.client.GetUserFeed()
        for album in albums.entry:
            if album.title.text == name:
                return album
        return self.client.InsertAlbum(title=name, summary='',
                                       access='protected')

    def post(self, image_path, album='inter-chat-bridge'):
        self._refresh_auth_token()
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
        image_url = photo.GetMediaURL()
        if not image_url:
            return 'not found image link'
        paths = image_url.split('/')
        paths.insert(len(paths) - 1, 's0')
        return '/'.join(paths)


if __name__ == '__main__':
    if not os.path.exists('client_secret.json'):
        raise SystemError('not found client_secret.json')
    email = raw_input('Enter your email address: ').strip()
    c = Picasa(email, 'client_secret.json', 'gauth_credentials.dat')
    image_path = raw_input('Enter image path: ').strip()
    print c.post(image_path)
