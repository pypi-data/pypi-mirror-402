from .errors import ConnectionError as ConnectionError
from .models import ConnectionOptions as ConnectionOptions

def open_connection(opts: ConnectionOptions): ...
