import unittest
import time
from blocks.utils import bash, PartialOutput


class TestBackgroundCommandPolling(unittest.TestCase):
    """Tests for background command output polling functionality"""

    def test_get_output_during_execution(self):
        """Test get_output() returns accumulated output during execution"""
        bg = bash("echo 'Line 1' && sleep 0.5 && echo 'Line 2'", background=True)

        # Wait a bit for first line to appear
        time.sleep(0.3)

        # Get output while still running
        output = bg.get_output()
        self.assertIsInstance(output, PartialOutput)
        self.assertIn('Line 1', output.stdout)
        self.assertFalse(output.is_complete)

        # Wait for completion
        final = bg.wait()
        self.assertTrue(final.is_success)
        self.assertIn('Line 2', final.stdout)

    def test_get_output_after_completion(self):
        """Test get_output() after command completes"""
        bg = bash("echo 'Hello World'", background=True)
        final = bg.wait()

        output = bg.get_output()
        self.assertIsInstance(output, PartialOutput)
        self.assertEqual(output.stdout, final.stdout)
        self.assertEqual(output.stderr, final.stderr)
        self.assertTrue(output.is_complete)

    def test_get_output_stream_filtering(self):
        """Test get_output() with stream parameter"""
        bg = bash("echo 'stdout text' && echo 'stderr text' >&2", background=True)
        final = bg.wait()

        # Test stdout only
        stdout_only = bg.get_output(stream='stdout')
        self.assertIsInstance(stdout_only, PartialOutput)
        self.assertIn('stdout text', stdout_only.stdout)
        self.assertEqual(stdout_only.stderr, '')

        # Test stderr only
        stderr_only = bg.get_output(stream='stderr')
        self.assertIsInstance(stderr_only, PartialOutput)
        self.assertEqual(stderr_only.stdout, '')
        self.assertIn('stderr text', stderr_only.stderr)

        # Test both
        both = bg.get_output(stream='both')
        self.assertIsInstance(both, PartialOutput)
        self.assertIn('stdout text', both.stdout)
        self.assertIn('stderr text', both.stderr)

    def test_get_output_since_position_incremental_polling(self):
        """Test get_output_since_position() for incremental polling"""
        bg = bash("echo 'Line 1' && sleep 0.3 && echo 'Line 2' && sleep 0.3 && echo 'Line 3'", background=True)

        pos = None
        collected_output = []

        # Poll multiple times
        for _ in range(10):
            result, pos = bg.get_output_since_position(pos)
            if result.stdout:
                collected_output.append(result.stdout)

            if result.is_complete:
                break
            time.sleep(0.2)

        # Verify we got all lines
        full_output = ''.join(collected_output)
        self.assertIn('Line 1', full_output)
        self.assertIn('Line 2', full_output)
        self.assertIn('Line 3', full_output)

    def test_get_output_since_position_typed_result(self):
        """Test that get_output_since_position() returns typed PartialOutput"""
        bg = bash("echo 'test'", background=True)
        result, pos = bg.get_output_since_position()

        # Verify it's a PartialOutput instance
        self.assertIsInstance(result, PartialOutput)
        self.assertTrue(hasattr(result, 'stdout'))
        self.assertTrue(hasattr(result, 'stderr'))
        self.assertTrue(hasattr(result, 'is_complete'))

        bg.wait()

    def test_get_output_since_position_no_duplicate_output(self):
        """Test that get_output_since_position() doesn't return duplicate output"""
        bg = bash("echo 'Line 1' && echo 'Line 2' && echo 'Line 3'", background=True)

        # First poll - should get all current output
        result1, pos1 = bg.get_output_since_position()

        # Wait a bit
        time.sleep(0.2)

        # Second poll with position - should only get new output
        result2, pos2 = bg.get_output_since_position(pos1)

        # Third poll with old position - should get everything since first poll
        result3, pos3 = bg.get_output_since_position(pos1)

        bg.wait()

        # Verify no duplicates between result1 and result2
        if result2.stdout:
            self.assertNotIn(result2.stdout, result1.stdout)

    def test_get_output_since_position_position_tracking(self):
        """Test that position dict is properly updated"""
        bg = bash("echo 'stdout1' && echo 'stderr1' >&2", background=True)

        result1, pos1 = bg.get_output_since_position()
        self.assertIsInstance(pos1, dict)
        self.assertIn('stdout', pos1)
        self.assertIn('stderr', pos1)
        self.assertIsInstance(pos1['stdout'], int)
        self.assertIsInstance(pos1['stderr'], int)

        # Second call should have advanced positions
        result2, pos2 = bg.get_output_since_position(pos1)
        self.assertGreaterEqual(pos2['stdout'], pos1['stdout'])
        self.assertGreaterEqual(pos2['stderr'], pos1['stderr'])

        bg.wait()

    def test_polling_with_stderr(self):
        """Test polling works correctly with stderr output"""
        bg = bash("echo 'out1' && echo 'err1' >&2 && sleep 0.3 && echo 'out2' && echo 'err2' >&2", background=True)

        pos = None
        stdout_parts = []
        stderr_parts = []

        for _ in range(10):
            result, pos = bg.get_output_since_position(pos)
            if result.stdout:
                stdout_parts.append(result.stdout)
            if result.stderr:
                stderr_parts.append(result.stderr)

            if result.is_complete:
                break
            time.sleep(0.1)

        stdout_full = ''.join(stdout_parts)
        stderr_full = ''.join(stderr_parts)

        self.assertIn('out1', stdout_full)
        self.assertIn('out2', stdout_full)
        self.assertIn('err1', stderr_full)
        self.assertIn('err2', stderr_full)

    def test_thread_safety_rapid_polling(self):
        """Test thread safety with rapid polling"""
        bg = bash("for i in {1..20}; do echo 'Line '$i; sleep 0.05; done", background=True)

        # Rapidly poll without sleeping
        pos = None
        for _ in range(50):
            result, pos = bg.get_output_since_position(pos)
            # Just verify no exceptions occur
            if result.is_complete:
                break

        bg.wait()
        self.assertTrue(bg.is_complete())

    def test_polling_after_completion(self):
        """Test polling behavior after command completion"""
        bg = bash("echo 'Completed'", background=True)
        final = bg.wait()

        # Poll after completion
        result, pos = bg.get_output_since_position()
        self.assertTrue(result.is_complete)
        self.assertIn('Completed', result.stdout)

        # Poll again with position - should get no new output
        result2, pos2 = bg.get_output_since_position(pos)
        self.assertTrue(result2.is_complete)
        self.assertEqual(result2.stdout, '')

    def test_multiline_output_streaming(self):
        """Test streaming of multiline output"""
        bg = bash("printf 'Line 1\\nLine 2\\nLine 3\\n'", background=True)

        result, pos = bg.get_output_since_position()

        # Wait for completion to ensure all output is captured
        bg.wait()

        # Get final output
        final_result, _ = bg.get_output_since_position()
        full_output = result.stdout + final_result.stdout

        self.assertIn('Line 1', full_output)
        self.assertIn('Line 2', full_output)
        self.assertIn('Line 3', full_output)


if __name__ == '__main__':
    unittest.main()
