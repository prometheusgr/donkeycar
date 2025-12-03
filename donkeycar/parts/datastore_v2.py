import atexit
import weakref
import json
import mmap
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

NEWLINE = '\n'
NEWLINE_STRIP = '\r\n'


class Seekable(object):
    """
    A seekable file reader, writer which deals with newline delimited
    records. \n
    This reader maintains an index of line lengths, so seeking a line is a
    O(1) operation.
    """

    def __init__(self, file, read_only=False, line_lengths=None):
        if line_lengths is None:
            line_lengths = list()
        self.line_lengths = list()
        self.cumulative_lengths = list()
        self.method = 'r' if read_only else 'a+'
        # Keep a reference to the underlying file object so we can close it
        # deterministically on Windows. When read-only, create an mmap on the
        # file descriptor and keep both the mmap and the backing file around
        # so they can be closed properly later.
        # Specify an explicit encoding to avoid relying on the system default.
        self._backing_file = open(
            file, self.method, newline=NEWLINE, encoding='utf-8')
        # If file is read only improve performance by memory mapping the file.
        # On Windows memory-mapped files can keep the underlying file locked
        # even after closing which interferes with test cleanup. Avoid mmap on
        # Windows to ensure temp files can be removed during tests.
        if self.method == 'r' and os.name != 'nt':
            self.file = mmap.mmap(self._backing_file.fileno(), length=0,
                                  access=mmap.ACCESS_READ)
        else:
            # For non-mmap or on Windows, use the standard file object for
            # simpler semantics and predictable closing behavior.
            self.file = self._backing_file
        self.total_length = 0
        if len(line_lengths) <= 0:
            self._read_contents()
        else:
            self.line_lengths.extend(line_lengths)
            for line_length in self.line_lengths:
                self.total_length += line_length
                self.cumulative_lengths.append(self.total_length)

    def _read_contents(self):
        self.line_lengths.clear()
        self.cumulative_lengths.clear()
        self.total_length = 0
        self.file.seek(0)
        contents = self.file.readline()
        while len(contents) > 0:
            line_length = len(contents)
            self.line_lengths.append(line_length)
            self.total_length += line_length
            self.cumulative_lengths.append(self.total_length)
            contents = self.file.readline()
        self.seek_end_of_file()

    def __enter__(self):
        return self

    def writeline(self, contents):
        ''' Write a line to the seekable file. '''
        if self.method == 'r':
            raise RuntimeError(f'Seekable {self.file} is read-only.')

        has_newline = contents[-1] == NEWLINE
        if has_newline:
            line = contents
        else:
            line = f'{contents}{NEWLINE}'

        offset = len(line)
        self.total_length += offset
        self.line_lengths.append(offset)
        self.cumulative_lengths.append(self.total_length)
        self.file.write(line)
        self.file.flush()

    def _line_start_offset(self, line_number):
        return self._offset_until(line_number - 1)

    def _line_end_offset(self, line_number):
        return self._offset_until(line_number)

    def _offset_until(self, line_index):
        end_index = line_index - 1
        return self.cumulative_lengths[end_index] \
            if 0 <= end_index < len(self.cumulative_lengths) else 0

    def readline(self):
        contents = self.file.readline()
        # When Seekable is a memory mapped file, readline() returns a `bytes`
        if isinstance(contents, bytes):
            contents = contents.decode(encoding='utf-8')
        return contents.rstrip(NEWLINE_STRIP)

    def seek_line_start(self, line_number):
        self.file.seek(self._line_start_offset(line_number))

    def seek_end_of_file(self):
        self.file.seek(self.total_length)

    def truncate_until_end(self, line_number):
        self.line_lengths = self.line_lengths[:line_number]
        self.cumulative_lengths = self.cumulative_lengths[:line_number]
        self.total_length = self.cumulative_lengths[-1] \
            if len(self.cumulative_lengths) > 0 else 0
        self.seek_end_of_file()
        self.file.truncate()

    def read_from(self, line_number):
        current_offset = self.file.tell()
        self.seek_line_start(line_number)
        lines = list()
        contents = self.readline()
        while len(contents) > 0:
            lines.append(contents)
            contents = self.readline()

        self.file.seek(current_offset)
        return lines

    def update_line(self, line_number, contents):
        lines = self.read_from(line_number)
        length = len(lines)
        self.truncate_until_end(line_number - 1)
        self.writeline(contents)
        if length > 1:
            for line in lines[1:]:
                self.writeline(line)

    def lines(self):
        return len(self.line_lengths)

    def has_content(self):
        return self.lines() > 0

    def close(self):
        try:
            # Close mmap or file-like object first
            if hasattr(self, 'file') and self.file is not None:
                try:
                    self.file.close()
                except Exception:
                    pass
        finally:
            # Ensure backing file is closed as well (if present)
            if hasattr(self, '_backing_file') and self._backing_file is not None:
                try:
                    self._backing_file.close()
                except Exception:
                    pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __exit__(self, type, value, traceback):
        self.close()


class Catalog(object):
    '''
    A new line delimited file that has records delimited by newlines. \n

    [ json object record ] \n
    [ json object record ] \n
    ...
    '''

    def __init__(self, path, read_only=False, start_index=0):
        self.path = Path(os.path.expanduser(path))
        self.manifest = CatalogMetadata(self.path,
                                        read_only=read_only,
                                        start_index=start_index)
        self.seekable = Seekable(self.path.as_posix(),
                                 line_lengths=self.manifest.line_lengths(),
                                 read_only=read_only)

    def _exit_handler(self):
        self.close()

    def write_record(self, record):
        # Add record and update manifest
        contents = json.dumps(record, allow_nan=False, sort_keys=True)
        self.seekable.writeline(contents)
        line_lengths = self.seekable.line_lengths
        self.manifest.update_line_lengths(line_lengths)

    def close(self):
        self.manifest.close()
        self.seekable.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class CatalogMetadata(object):
    '''
    Manifest for a Catalog
    '''

    def __init__(self, catalog_path, read_only=False, start_index=0):
        path = Path(catalog_path)
        manifest_name = f'{path.stem}.catalog_manifest'
        self.manifest_path = Path(os.path.join(path.parent.as_posix(),
                                               manifest_name))
        self.seekeable = Seekable(self.manifest_path, read_only=read_only)
        has_contents = False
        if os.path.exists(self.manifest_path) and self.seekeable.has_content():
            self.seekeable.seek_line_start(1)
            contents = self.seekeable.readline()
            if contents:
                self.contents = json.loads(contents)
                has_contents = True

        if not has_contents:
            # New catalog metadata entry
            self.contents = dict()
            self.contents['path'] = self.manifest_path.name
            created_at = time.time()
            self.contents['created_at'] = created_at
            self.contents['start_index'] = start_index
            self.contents['line_lengths'] = list()
            self._update()

    def update_line_lengths(self, new_lengths):
        self.contents['line_lengths'] = new_lengths
        self._update()

    def line_lengths(self):
        return self.contents['line_lengths']

    def start_index(self):
        return self.contents['start_index']

    def _update(self):
        contents = json.dumps(self.contents, allow_nan=False, sort_keys=True)
        self.seekeable.truncate_until_end(0)
        self.seekeable.writeline(contents)

    def close(self):
        self.seekeable.close()


class Manifest(object):
    '''
    A newline delimited file, with the following format.

    [ json array of inputs ]\n
    [ json array of types ]\n
    [ json object with user metadata ]\n
    [ json object with manifest metadata ]\n
    [ json object with catalog metadata ]\n
    '''

    def __init__(self, base_path, inputs=[], types=[], metadata=[],
                 max_len=1000, read_only=False):
        self.base_path = Path(os.path.expanduser(base_path)).absolute()
        self.manifest_path = Path(os.path.join(
            self.base_path, 'manifest.json'))
        self.inputs = inputs
        self.types = types
        self._read_metadata(metadata)
        self.manifest_metadata = dict()
        self.max_len = max_len
        self.read_only = read_only
        # Do not keep a persistent Catalog object open. Open catalogs
        # on-demand for reads/writes to avoid lingering file handles on
        # platforms such as Windows.
        self.current_catalog = None
        self.current_index = 0
        self.catalog_paths = list()
        self.catalog_metadata = dict()
        self.deleted_indexes = set()
        self._updated_session = False
        self._is_closed = False
        has_catalogs = False

        if self.manifest_path.exists():
            # Open manifest transiently to read contents; do not keep the
            # file handle open for the life of Manifest to avoid locking
            # issues on Windows.
            with Seekable(self.manifest_path, read_only=self.read_only) as s:
                if s.has_content():
                    self._read_contents(seekeable=s)
            has_catalogs = len(self.catalog_paths) > 0
            logger.info(f'Found datastore at {self.base_path.as_posix()}')
        else:
            created_at = time.time()
            self.manifest_metadata['created_at'] = created_at
            if not self.base_path.exists():
                self.base_path.mkdir(parents=True, exist_ok=True)
                logger.info(f'Creating a new datastore at'
                            f' {self.base_path.as_posix()}')
            self.seekeable = Seekable(self.manifest_path,
                                      read_only=self.read_only)
            logger.info(f'Creating a new manifest at '
                        f'{self.manifest_path.as_posix()}')

        if not has_catalogs:
            self._write_contents()
            # create first catalog on disk
            self._add_catalog()
        else:
            last_known_catalog = os.path.join(self.base_path,
                                              self.catalog_paths[-1])
            logger.info(f'Using last catalog {last_known_catalog}')
            # Do not open the catalog here; open on demand when needed.
        # Create a new session_id, which will be added to each record in the
        # tub, when Tub.write_record() is called.
        self.session_id = self.create_new_session_id()

        # Use weakref.finalize so we don't create a strong reference cycle
        # that would prevent the Manifest instance from being garbage
        # collected during test teardown. When the Manifest is GC'd the
        # finalizer will call close().
        weakref.finalize(self, self.close)

    def write_record(self, record):
        new_catalog = self.current_index > 0 and \
            (self.current_index % self.max_len) == 0

        if new_catalog:
            # create and initialize a new catalog file (Catalog will write
            # its manifest entries); we close it immediately after creation
            self._add_catalog()

        # Determine the current catalog path (always append to the last)
        catalog_name = self.catalog_paths[-1]
        catalog_path = os.path.join(self.base_path, catalog_name)
        # Open, write, and close the catalog to avoid keeping file handles
        cat = Catalog(catalog_path,
                      start_index=self.current_index,
                      read_only=self.read_only)
        try:
            cat.write_record(record)
        finally:
            try:
                cat.close()
            except Exception:
                pass

        self.current_index += 1
        # Update metadata to keep track of the last index
        self._update_catalog_metadata(update=True)
        # Set session_id update status to True if this method is called at
        # least once. Then session id metadata  will be updated when the
        # session gets closed
        if not self._updated_session:
            self._updated_session = True

    def delete_records(self, record_indexes):
        # Does not actually delete the record, but marks it as deleted.
        if isinstance(record_indexes, int):
            record_indexes = {record_indexes}
        self.deleted_indexes.update(record_indexes)
        self._update_catalog_metadata(update=True)
        if record_indexes:
            logger.info(f'Deleting {len(record_indexes)} records: '
                        f'{min(record_indexes)} - {max(record_indexes)}')

    def restore_records(self, record_indexes):
        # Does not actually delete the record, but marks it as deleted.
        if isinstance(record_indexes, int):
            record_indexes = {record_indexes}
        self.deleted_indexes.difference_update(record_indexes)
        self._update_catalog_metadata(update=True)
        if record_indexes:
            logger.info(f'Restored records {min(record_indexes)} - '
                        f'{max(record_indexes)}')

    def _add_catalog(self):
        current_length = len(self.catalog_paths)
        catalog_name = f'catalog_{current_length}.catalog'
        catalog_path = os.path.join(self.base_path, catalog_name)
        # Create and initialize the new catalog (manifest) then close it.
        tmp_cat = Catalog(catalog_path,
                          start_index=self.current_index,
                          read_only=self.read_only)
        try:
            tmp_cat.close()
        except Exception:
            pass
        # Store relative paths
        self.catalog_paths.append(catalog_name)
        self._update_catalog_metadata(update=True)

    def _read_metadata(self, metadata=[]):
        self.metadata = dict()
        for kv in metadata:
            kvs = kv.split(":")
            if len(kvs) == 2:
                self.metadata[kvs[0]] = kvs[1]
            else:
                logger.error(f'Metadata item needs to be a key value pair of '
                             f'format key:value, ignore entry {kv}')

    def _read_contents(self, seekeable=None):
        # Read manifest contents from the provided Seekable or by opening
        # it transiently.
        if seekeable is None:
            with Seekable(self.manifest_path, read_only=self.read_only) as s:
                self._read_contents(seekeable=s)
            return

        seekeable.seek_line_start(1)
        manifest_inputs = json.loads(seekeable.readline())
        manifest_types = json.loads(seekeable.readline())
        if not self.inputs and not self.types:
            self.inputs = manifest_inputs
            self.types = manifest_types
        else:
            assert self.inputs == manifest_inputs \
                and self.types == manifest_types, \
                f'Trying to create a tub with different inputs/types than ' \
                f'the stored tub. This is only allowed when new tub ' \
                f'specifies no inputs. New inputs: {self.inputs} vs ' \
                f'stored inputs: {manifest_inputs}, new types {self.types}'\
                f' vs stored types: {manifest_types}'
        # Continue reading manifest lines from the provided Seekable
        self.metadata = json.loads(seekeable.readline())
        self.manifest_metadata = json.loads(seekeable.readline())
        # Catalog metadata
        catalog_metadata = json.loads(seekeable.readline())
        self.catalog_paths = catalog_metadata['paths']
        self.current_index = catalog_metadata['current_index']
        self.max_len = catalog_metadata['max_len']
        self.deleted_indexes = set(catalog_metadata['deleted_indexes'])

    def _write_contents(self):
        # Open the manifest file transiently to write initial contents.
        with Seekable(self.manifest_path, read_only=self.read_only) as s:
            s.truncate_until_end(0)
            s.writeline(json.dumps(self.inputs))
            s.writeline(json.dumps(self.types))
            s.writeline(json.dumps(self.metadata))
            s.writeline(json.dumps(self.manifest_metadata))
            # update catalog metadata in the same file
            # (this writes the 5th line)
            s.writeline(json.dumps({}))
        # Now update the catalog metadata properly
        self._update_catalog_metadata(update=False)

    def _update_catalog_metadata(self, update=True):
        # Update the manifest file's catalog metadata (line 5).
        catalog_metadata = dict()
        catalog_metadata['paths'] = self.catalog_paths
        catalog_metadata['current_index'] = self.current_index
        catalog_metadata['max_len'] = self.max_len
        catalog_metadata['deleted_indexes'] = sorted(
            list(self.deleted_indexes))
        self.catalog_metadata = catalog_metadata

        # Open manifest transiently and update the 5th line.
        with Seekable(self.manifest_path, read_only=self.read_only) as s:
            if update:
                s.truncate_until_end(4)
            s.writeline(json.dumps(catalog_metadata))

    def _update_session_info(self):
        """ Creates a new session id and appends it to the metadata."""
        sessions = self.manifest_metadata.get('sessions', {})
        if not sessions:
            sessions['all_full_ids'] = []
        this_id, this_full_id = self.session_id
        sessions['last_id'] = this_id
        sessions['last_full_id'] = this_full_id
        sessions['all_full_ids'].append(this_full_id)
        self.manifest_metadata['sessions'] = sessions

    def create_new_session_id(self):
        """ Creates a new session id and appends it to the metadata."""
        sessions = self.manifest_metadata.get('sessions', {})
        new_id = sessions['last_id'] + 1 if sessions else 0
        new_full_id = f"{time.strftime('%y-%m-%d')}_{new_id}"
        return new_id, new_full_id

    def add_deleted_indexes(self, indexes):
        if isinstance(indexes, int):
            indexes = {indexes}
        self.deleted_indexes.update(indexes)
        self._update_catalog_metadata(update=True)

    def close(self):
        """ Closing tub closes open files for catalog, catalog manifest and
            manifest.json"""
        # If manifest file no longer exists (e.g., removed during test
        # teardown), avoid trying to write/update it to prevent errors at
        # interpreter shutdown.
        if not self.manifest_path.exists():
            self._is_closed = True
            return
        # If records were received, write updated session_id dictionary into
        # the metadata, otherwise keep the session_id information unchanged
        if self._updated_session:
            logger.info(f'Saving new session {self.session_id[1]}')
            self._update_session_info()
            self.write_metadata()
        # Close current_catalog if it was left open (most code opens/ closes
        # catalogs on demand). Be defensive in case it's None.
        try:
            if getattr(self, 'current_catalog', None) is not None:
                try:
                    self.current_catalog.close()
                except Exception:
                    pass
        except Exception:
            pass
        # Close any transient seekable opened for newly-created manifests.
        if hasattr(self, 'seekeable') and self.seekeable is not None:
            try:
                self.seekeable.close()
            except Exception:
                pass
        self._is_closed = True
        logger.info(f'Closing manifest {self.base_path}')

    def __del__(self):
        try:
            if not getattr(self, '_is_closed', False):
                self.close()
        except Exception:
            pass

    def write_metadata(self):
        # Update manifest lines 3 and 4 transiently.
        with Seekable(self.manifest_path, read_only=self.read_only) as s:
            s.update_line(3, json.dumps(self.metadata))
            s.update_line(4, json.dumps(self.manifest_metadata))

    def __iter__(self):
        return ManifestIterator(self)

    def __len__(self):
        # current_index is already pointing to the next index
        return self.current_index - len(self.deleted_indexes)


class ManifestIterator(object):
    """
    An iterator for the Manifest type. \n

    Returns catalog entries lazily when a consumer calls __next__().
    """

    def __init__(self, manifest):
        self.manifest = manifest
        self.has_catalogs = len(self.manifest.catalog_paths) > 0
        self.current_index = 0
        self.current_catalog_index = 0
        self.current_catalog = None

    def __next__(self):
        while True:
            if not self.has_catalogs:
                # No catalogs -> close manifest resources and finish.
                try:
                    self.manifest.close()
                except Exception:
                    pass
                raise StopIteration('No catalogs')

            if self.current_catalog_index >= len(self.manifest.catalog_paths):
                # If we have an open catalog, close it before finishing,
                # and close the manifest so files are released promptly.
                try:
                    if self.current_catalog is not None:
                        self.current_catalog.close()
                except Exception:
                    pass
                try:
                    self.manifest.close()
                except Exception:
                    pass
                raise StopIteration('No more catalogs')

            if self.current_catalog is None:
                current_catalog_path = os.path.join(
                    self.manifest.base_path,
                    self.manifest.catalog_paths[self.current_catalog_index])
                self.current_catalog = Catalog(current_catalog_path,
                                               read_only=self.manifest.read_only)
                self.current_catalog.seekable.seek_line_start(1)

            contents = self.current_catalog.seekable.readline()
            if contents is not None and len(contents) > 0:
                # Check for current_index when we are ready to advance the
                # underlying iterator.
                current_index = self.current_index
                self.current_index += 1
                if current_index in self.manifest.deleted_indexes:
                    # Skip over index, because it has been marked deleted
                    continue
                else:
                    try:
                        record = json.loads(contents)
                        return record
                    except Exception:
                        logger.error(f'Failed loading record {current_index}')
                        continue
            else:
                # Close the current catalog explicitly so file handles are
                # released promptly (helps Windows cleanup during tests).
                try:
                    if self.current_catalog is not None:
                        self.current_catalog.close()
                except Exception:
                    pass
                self.current_catalog = None
                self.current_catalog_index += 1

    next = __next__

    def __len__(self):
        return self.manifest.__len__()
