import logging
import threading
import time
from queue import Empty, Queue
from threading import RLock, Semaphore

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from databricks.feature_store.utils.logging_utils import get_logger

_logger = get_logger(__name__, log_level=logging.INFO)
BASE_URL = "postgresql+psycopg://"


class AsyncRefillEngine:
    """
    A PostgreSQL engine that maintains pool of connections and actively refills
    the pool when connections expire.

    Unlike the standard SQLAlchemy engine, the connection pool in this engine
    usually does not create new connections in the critical query path. Instead,
    when aquiring a connection,it skip and discard expired connections from the
    head of the queue to get the next available connection as soon as possible.
    Then it refills the pool with new connections asynchronously.

    The engine also starts a background thread that keeps acquiring and
    releasing connections to keep the pool warm even when there is no active
    query.

    Thread compatible: this engine works in both standard threading and gevent
    environments. When gevent is monkey-patched, threads become greenlets
    automatically.

    Usage:
        Use `acquire` to get a connection from the pool and `release` to return
        it back to the pool. Calling close on the connection object will not
        return it back to the pool.
    """

    def __init__(
        self,
        pool_size,
        pool_recycle,
        pool_warming_interval=5,
        pool_timeout=2,
        pool_init_gap=2,
        creator=None,
    ):
        """
        Initialize an AsyncRefillEngine.

        :param pool_size: The size of the pool.
        :param pool_recycle: The time in seconds before the connection expires.
        :param pool_warming_interval: The interval in seconds at which the pool
          warming thread runs. In the pool warming thread, we recycle connections
          3x of pool_warming_interval before the expiration. So this number
          should be much smaller than 1/3 of pool_recycle to keep the connections
          alive longer. But an extremely small interval can also cause too many
          requests to the connection pool.
        :param pool_timeout: The timeout in seconds for getting a connection from
          the pool.
        :param pool_init_gap: The gap in seconds between initializing connections.
          This is needed to avoid connections expiring at the same time. Also to
          avoid too many requests to hit the auth rate limit for creating
          connections during initialization.
        :param creator: The creator function to use to create the connection.
        """
        self._engine = create_engine(BASE_URL, creator=creator, poolclass=NullPool)
        self._pool = Queue(maxsize=pool_size)
        # Lock for the filed _in_use. Any access to _in_use must be protected by this
        self._in_use_count_lock = Semaphore()
        # Lock for the field _refill_count. Any access to _refill_count must be
        self._refill_count_lock = Semaphore()
        # Reentrant lock for the acquire method. acquire needs to be thread safe
        # because it modifies some internal state of this class. Using RLock because
        # acquire can be called recursively.
        self._connection_acquire_lock = RLock()
        self._pool_size = pool_size
        self._pool_recycle = pool_recycle
        self._pool_timeout = pool_timeout
        self._pool_warming_interval = pool_warming_interval
        # How long before the connection expires should the pool warming thread
        # recycle the connection. this makes sure there is at least one connection
        # in the pool can last until the next warming cycle.
        #
        # Choosing 3x because in production there are at most 2 connections checked
        # out at the same time. Keeping one extra connection for edge cases. This might
        # needs tuning when we support parallel queries for multiple tables.
        self._pre_recycle_time = pool_warming_interval * 3
        # Number of connections currently checked out
        self._in_use = 0
        # Number of connections currently being refilled
        self._refill_count = 0

        # Warm-up pool
        while self._pool.qsize() < self._pool_size:
            try:
                conn = None
                conn = self._create_conn()
                self._pool.put(conn)
            except Exception as e:
                _logger.warning(f"[pool] Retrying to init connection because: {e}")
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
            # Initialize the connections with gaps to avoid expiring them all
            # together.
            time.sleep(pool_init_gap)
        if pool_warming_interval > 0:
            thread = threading.Thread(target=self._pool_warming_thread, daemon=True)
            thread.start()

    def _create_conn(self):
        conn = self._engine.connect()
        conn.starttime = time.time()
        return conn

    def _pool_warming_thread(self):
        """
        The pool warming thread is to keep the pool warm when the endpoint is
        not being queried.
        """
        while True:
            try:
                conn = self._acquire_connection_internal(is_warming=True)
                if conn:
                    self.release(conn)
            except Exception as e:
                _logger.warning(f"[pool] Error warming up connection: {e}")
            time.sleep(self._pool_warming_interval)

    def _is_valid(self, conn, is_warming=False):
        """
        Check if the connection is valid.
        The conn.invalidated field and the starttime both are indicators for
        connection to be recycled. But they are handled differently:
        - When conn.invalidated==True, it means the connection is broken and
            cannot be used at all and we must recycle it immediately.
        - But for starttime, we have 2 expiration time for it. The first one
            is a soft expiration time hinting the pool warming thread to
            recycle it before it actually expires. The second is a hard
            deadline meaning it has to be recycled by either a real request
            or a pool warming thread. Based on is_warming flag, we can determine
            which expiration time to use.
        """
        # First check if the connection is invalidated. If it is, return False.
        if conn.invalidated:
            return False
        # Validate the connection expiration based on if the check is for a
        # connection warming request. For connection warming request, we
        # recycle the connections sooner than normal to make sure a real
        # request doesn't stuck on a stale connection.
        start = getattr(conn, "starttime", None)
        if start and self._pool_recycle > 0:
            recycle_time = (
                self._pool_recycle - self._pre_recycle_time
                if is_warming
                else self._pool_recycle
            )
            if time.time() - start > recycle_time:
                return False
        return True

    def acquire(self):
        """
        Acquires a connection from the pool. This method is thread-safe. It
        blocks until a connection is available.

        :return: A connection from the pool.
        """
        return self._acquire_connection_internal(is_warming=False)

    def _acquire_connection_internal(self, is_warming=False):
        """
        :param is_warming: Whether the connection is being acquired by the pool warming thread.
            If True, it will not guarantee to return a connection. Instead it may return None
            if the connection queue is almost empty.
        """
        with self._connection_acquire_lock:
            if (
                self._pool.qsize() + self.checkedout() + self.refilling()
                < self._pool_size
            ):
                # There are not enough connections in the managed connection pool. This is not
                # expected to happen in normal case but it could happen if any creation of
                # connections during refilling failed. Spawn a refill task immediately to create
                # a new connection in the background.
                thread = threading.Thread(target=self._refill, daemon=True)
                thread.start()

            # Now we know there is at least one connection guaranteed to be available soon.
            # beacuse we spawn a refill task above when there are not enough connections.
            # Try to get a connection from the queue. If it's invalid, dispose it and try
            # again recursively.
            try:
                conn = self._pool.get(timeout=self._pool_timeout)
            except Empty:
                _logger.error(
                    f"[pool] timeout getting connection. checked-in:{self.checkedin()}, checked-out:{self.checkedout()}, refilling:{self.refilling()}"
                )
                raise TimeoutError(f"No available connection in {self._pool_timeout}s")

            if not self._is_valid(conn, is_warming):
                # Invalid connections need to be disposed.

                # First trigger a refill to start creating the replacement connection
                # in the background.
                thread = threading.Thread(target=self._refill, daemon=True)
                thread.start()

                if is_warming and self.checkedin() == 0:
                    # If in the pool warming thread and this is the only connection in the
                    # queue, put it back immediately to avoid blocking the real requests.
                    # The connection might still be valid because _is_valid for warming
                    # thread has a shorter expiration time.
                    # This will lead to one extra connection in total than the pool size.
                    # (because we spawn a new _refill but not closing this connection) but
                    # it's okay because the _put_in_queue will discard any extra
                    # connections.
                    self._put_in_queue(conn)
                    return None
                else:
                    try:
                        conn.close()
                    except Exception:
                        pass
                # Try to acquire a connection again.
                return self._acquire_connection_internal(is_warming=is_warming)

            with self._in_use_count_lock:
                self._in_use += 1
            return conn

    def _put_in_queue(self, conn):
        try:
            self._pool.put_nowait(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    def release(self, conn):
        with self._in_use_count_lock:
            self._in_use -= 1
        self._put_in_queue(conn)

    def _refill(self):
        try:
            with self._refill_count_lock:
                self._refill_count += 1
            conn = self._create_conn()
            self._put_in_queue(conn)
        except Exception as e:
            _logger.error(f"[pool] async refill failed: {e}")
        finally:
            with self._refill_count_lock:
                self._refill_count -= 1

    # Observability
    # How many connections are in the pool.
    def checkedin(self):
        return self._pool.qsize()

    # How many connections are checked out and being used.
    def checkedout(self):
        with self._in_use_count_lock:
            return self._in_use

    # How many connections are currently being refilled.
    def refilling(self):
        with self._refill_count_lock:
            return self._refill_count
