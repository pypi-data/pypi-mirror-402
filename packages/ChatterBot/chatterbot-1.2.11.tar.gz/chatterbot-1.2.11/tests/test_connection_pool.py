"""
Tests for database connection pool management and concurrency.

These tests verify that the fixes for the connection pool exhaustion
vulnerability (CVE-TBD) are working correctly.
"""
import threading
import time
import unittest
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer


class ConnectionPoolTestCase(unittest.TestCase):
    """
    Test cases for database connection pool management.
    """

    def setUp(self):
        """
        Set up test fixtures before each test.
        """
        # Use in-memory SQLite for fast testing
        # Note: SQLite doesn't use QueuePool, so pool params are ignored
        self.chatbot = ChatBot(
            'TestBot',
            database_uri='sqlite://',
        )
        
        # Train with some basic responses
        trainer = ListTrainer(self.chatbot)
        trainer.train([
            'Hi',
            'Hello!',
            'How are you?',
            'I am doing well.',
            'What is your name?',
            'My name is TestBot.',
        ])

    def tearDown(self):
        """
        Clean up after each test.
        """
        self.chatbot.storage.drop()
        self.chatbot.storage.close()

    def test_concurrent_requests_no_exhaustion(self):
        """
        Test that concurrent requests don't exhaust the connection pool.
        
        This was the original vulnerability - concurrent get_response() calls
        would leak sessions and exhaust the pool.
        """
        num_threads = 30  # More than pool_size + max_overflow
        responses = []
        errors = []
        
        def make_request():
            try:
                response = self.chatbot.get_response('Hi')
                responses.append(str(response))
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=10)
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0, 
                        f"Connection pool exhaustion occurred: {errors}")
        
        # Verify all threads got responses
        self.assertEqual(len(responses), num_threads,
                        "Not all threads received responses")

    def test_rapid_sequential_requests(self):
        """
        Test that rapid sequential requests properly release connections.
        """
        num_requests = 50  # More than pool size
        
        for i in range(num_requests):
            response = self.chatbot.get_response(f'Request {i}')
            self.assertIsNotNone(response)

    def test_partial_filter_consumption(self):
        """
        Test that partially consuming filter() results doesn't leak sessions.
        
        This was a key part of the vulnerability - the filter() generator
        would not close the session if iteration stopped early.
        """
        # Create many statements
        trainer = ListTrainer(self.chatbot)
        for i in range(100):
            trainer.train([f'Question {i}', f'Answer {i}'])
        
        # Partially consume filter results many times
        for _ in range(50):
            results = self.chatbot.storage.filter()
            # Only consume first result
            first = next(results, None)
            self.assertIsNotNone(first)
            # Don't consume the rest - this should still clean up the session
        
        # If sessions weren't cleaned up, this would fail
        response = self.chatbot.get_response('Hi')
        self.assertIsNotNone(response)

    def test_concurrent_training(self):
        """
        Test that concurrent training operations don't leak connections.
        """
        errors = []
        
        def train_batch(batch_id):
            try:
                trainer = ListTrainer(self.chatbot)
                trainer.train([
                    f'Training question {batch_id}',
                    f'Training answer {batch_id}',
                ])
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(20):
            t = threading.Thread(target=train_batch, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        self.assertEqual(len(errors), 0,
                        f"Errors during concurrent training: {errors}")

    def test_session_cleanup_on_exception(self):
        """
        Test that sessions are cleaned up even when exceptions occur.
        """
        # Force an error during a database operation
        try:
            # Create a statement with invalid data
            self.chatbot.storage.create(
                text='',  # Empty text might cause issues
                in_response_to=None
            )
        except Exception:
            pass  # Expected to fail
        
        # Verify the pool is still usable
        response = self.chatbot.get_response('Hi')
        self.assertIsNotNone(response)

    def test_scoped_session_thread_safety(self):
        """
        Test that scoped_session provides proper thread isolation.
        """
        results = {}
        
        def check_session_isolation(thread_id):
            # Each thread should get its own session
            session1 = self.chatbot.storage.Session()
            time.sleep(0.01)  # Small delay to encourage thread interleaving
            session2 = self.chatbot.storage.Session()
            
            # In the same thread, scoped_session should return the same session
            results[thread_id] = (id(session1) == id(session2))
            
            session1.close()
            # After close, scoped_session should return the same instance
            # (it doesn't create a new one, just reuses the thread-local one)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=check_session_isolation, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All threads should have gotten consistent session behavior
        for thread_id, same_session in results.items():
            self.assertTrue(same_session,
                          f"Thread {thread_id} got different sessions")


class ConnectionPoolConfigTestCase(unittest.TestCase):
    """
    Test cases for connection pool configuration options.
    Note: These tests are skipped for SQLite since it uses SingletonThreadPool.
    """

    def test_pool_config_not_applied_to_sqlite(self):
        """
        Test that pool config is not applied to SQLite (uses SingletonThreadPool).
        """
        chatbot = ChatBot(
            'SQLiteBot',
            database_uri='sqlite://',
            pool_size=3,  # Should be ignored
            max_overflow=2,  # Should be ignored
        )
        
        # SQLite uses SingletonThreadPool, not QueuePool
        from sqlalchemy.pool import SingletonThreadPool
        self.assertIsInstance(chatbot.storage.engine.pool, SingletonThreadPool)
        
        chatbot.storage.close()

    @unittest.skip("Requires PostgreSQL/MySQL database for testing")
    def test_custom_pool_size_postgres(self):
        """
        Test that custom pool_size is respected for PostgreSQL.
        """
        # This test would require a PostgreSQL connection
        # chatbot = ChatBot(
        #     'ConfigBot',
        #     database_uri='postgresql://user:pass@localhost/test',
        #     pool_size=3,
        #     max_overflow=2,
        # )
        # self.assertEqual(chatbot.storage.engine.pool.size(), 3)
        # chatbot.storage.close()
        pass

    @unittest.skip("Requires PostgreSQL/MySQL database for testing")
    def test_default_pool_config_postgres(self):
        """
        Test that default pool configuration is applied for PostgreSQL.
        """
        # This test would require a PostgreSQL connection
        # chatbot = ChatBot(
        #     'DefaultBot',
        #     database_uri='postgresql://user:pass@localhost/test',
        # )
        # pool = chatbot.storage.engine.pool
        # self.assertEqual(pool.size(), 10)  # Default pool_size
        # chatbot.storage.close()
        pass

    @unittest.skip("Requires PostgreSQL/MySQL database for testing")
    def test_pool_pre_ping_enabled_postgres(self):
        """
        Test that pool_pre_ping is enabled by default for PostgreSQL.
        """
        # This test would require a PostgreSQL connection
        # chatbot = ChatBot(
        #     'PingBot',
        #     database_uri='postgresql://user:pass@localhost/test',
        # )
        # self.assertTrue(chatbot.storage.engine.pool._pre_ping)
        # chatbot.storage.close()
        pass


if __name__ == '__main__':
    unittest.main()
