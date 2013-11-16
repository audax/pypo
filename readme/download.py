from collections import namedtuple
import requests


class DownloadException(Exception):

    def __init__(self, message, *args, parent=None, **kwargs):
        self.parent = parent
        self.message = message
        super(DownloadException, self).__init__(*args, **kwargs)

DownloadedContent = namedtuple('DownloadedContent', ('text', 'content', 'content_type'))

def download(url, max_content_length=1000):
    """
    Download content with an upper bound for the content_length
    :param url: Url
    :param max_content_length: length in bytes
    :return: DownloadedContent
    :raise DownloadException: for all errors
    """
    try:
        req = requests.get(url, stream=True)
    except requests.RequestException as e:
        raise DownloadException("Request failed", parent=e)

    try:
        content_length = int(req.headers.get('content-length', 0))
    except ValueError as e:
        # no valid content length set
        raise DownloadException("Could not convert: content-length = {}".format(
            req.headers.get('content-length')), parent=e)
    else:
        # if content is too long, abort.
        if content_length > max_content_length:
            raise DownloadException('Aborting: content-length {} is larger than max content length {}'.format(
                content_length, max_content_length))
        # In case content_length lied to us
        content = next(req.iter_content(max_content_length))
        text = None
        # only decode text requests
        content_type = req.headers.get('content-type', '')
        if content_type.startswith('text/'):
            text = content.decode(req.encoding, errors='ignore')
        return DownloadedContent(content=content, text=text, content_type=content_type)

