# pyright: reportUnknownArgumentType=false, reportUnusedImport=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportTypedDictNotRequiredAccess=false, reportUnknownMemberType=false, reportArgumentType=false, reportPrivateUsage=false
import unittest
from unittest.mock import (
    Mock,
    patch,
    MagicMock,
    call,
)
from datetime import datetime
from crossmark_jotform_api.jotForm import JotForm, JotFormSubmission


class TestJotFormAdvanced(unittest.TestCase):
    """More comprehensive tests for JotForm functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.form_id = "123456"
        self.mock_response_data = {
            "content": [
                {
                    "id": "1001",
                    "form_id": self.form_id,
                    "ip": "192.168.1.1",
                    "created_at": "2024-01-01 12:00:00",
                    "status": "ACTIVE",
                    "new": "1",
                    "flag": "0",
                    "notes": "",
                    "updated_at": "2024-01-01 12:00:00",
                    "answers": {
                        "1": {
                            "name": "fullName",
                            "answer": "John Doe",
                            "text": "Full Name",
                            "type": "control_textbox",
                        }
                    },
                }
            ],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_set_get_submission_data(self, mock_get):
        """Test the _set_get_submission_data class method"""
        submissions = self.mock_response_data["content"]

        result = JotForm._set_get_submission_data(submissions, self.api_key)

        self.assertEqual(len(result), 1)
        self.assertIn("1001", result)
        self.assertIsInstance(result["1001"], JotFormSubmission)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_set_get_submission_data_exclude_deleted(self, mock_get):
        """Test excluding deleted submissions"""
        submissions = [
            {
                "id": "1001",
                "form_id": self.form_id,
                "status": "ACTIVE",
                "answers": {},
                "ip": "192.168.1.1",
                "created_at": "2024-01-01 12:00:00",
                "new": "1",
                "flag": "0",
                "notes": "",
                "updated_at": "2024-01-01 12:00:00",
            },
            {
                "id": "1002",
                "form_id": self.form_id,
                "status": "DELETED",
                "answers": {},
                "ip": "192.168.1.1",
                "created_at": "2024-01-01 12:00:00",
                "new": "1",
                "flag": "0",
                "notes": "",
                "updated_at": "2024-01-01 12:00:00",
            },
        ]

        result = JotForm._set_get_submission_data(
            submissions, self.api_key, include_deleted=False
        )

        self.assertEqual(len(result), 1)
        self.assertIn("1001", result)
        self.assertNotIn("1002", result)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_set_get_submission_data_include_deleted(self, mock_get):
        """Test including deleted submissions"""
        submissions = [
            {
                "id": "1001",
                "form_id": self.form_id,
                "status": "ACTIVE",
                "answers": {},
                "ip": "192.168.1.1",
                "created_at": "2024-01-01 12:00:00",
                "new": "1",
                "flag": "0",
                "notes": "",
                "updated_at": "2024-01-01 12:00:00",
            },
            {
                "id": "1002",
                "form_id": self.form_id,
                "status": "DELETED",
                "answers": {},
                "ip": "192.168.1.1",
                "created_at": "2024-01-01 12:00:00",
                "new": "1",
                "flag": "0",
                "notes": "",
                "updated_at": "2024-01-01 12:00:00",
            },
        ]

        result = JotForm._set_get_submission_data(
            submissions, self.api_key, include_deleted=True
        )

        self.assertEqual(len(result), 2)
        self.assertIn("1001", result)
        self.assertIn("1002", result)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_get_submission_data_by_query_with_dict(self, mock_get):
        """Test getting submission data by query with dict filter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_response_data
        mock_get.return_value = mock_response

        filter_dict = {"3:matches": "Will VanSaders"}

        result = JotForm.get_submission_data_by_query(
            filter_dict, self.api_key, self.form_id
        )

        self.assertEqual(len(result), 1)
        self.assertIn("1001", result)
        mock_get.assert_called_once()

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_get_submission_data_by_query_with_string(self, mock_get):
        """Test getting submission data by query with string filter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_response_data
        mock_get.return_value = mock_response

        filter_str = '{"q3:matches": "Will VanSaders"}'

        result = JotForm.get_submission_data_by_query(
            filter_str, self.api_key, self.form_id
        )

        self.assertEqual(len(result), 1)
        self.assertIn("1001", result)
        mock_get.assert_called_once()

    def test_get_submission_data_by_query_invalid_input(self):
        """Test get_submission_data_by_query with invalid input"""
        with self.assertRaises(ValueError):
            JotForm.get_submission_data_by_query("", self.api_key, self.form_id)

        with self.assertRaises(ValueError):
            JotForm.get_submission_data_by_query(None, self.api_key, self.form_id)

        with self.assertRaises(ValueError):
            JotForm.get_submission_data_by_query(123, self.api_key, self.form_id)


class TestJotFormSubmissionAdvanced(unittest.TestCase):
    """More comprehensive tests for JotFormSubmission"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.sample_submission = {
            "id": "123456789",
            "form_id": "987654321",
            "ip": "192.168.1.1",
            "created_at": "2024-01-01 12:00:00",
            "status": "ACTIVE",
            "new": "1",
            "flag": "0",
            "notes": "",
            "updated_at": "2024-01-01 12:00:00",
            "answers": {
                "1": {
                    "name": "fullName",
                    "answer": "John Doe",
                    "text": "Full Name",
                    "type": "control_textbox",
                },
                "2": {
                    "name": "email",
                    "answer": "john@example.com",
                    "text": "Email Address",
                    "type": "control_email",
                },
                "3": {
                    "name": "colors",
                    "answer": ["red", "blue", "green"],
                    "text": "Favorite Colors",
                    "type": "control_checkbox",
                },
                "4": {
                    "name": "singleSelect",
                    "answer": ["option1"],
                    "text": "Single Selection",
                    "type": "control_radio",
                },
            },
        }

    def test_get_answer_by_text_not_found(self):
        """Test getting answer by text when not found"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        with self.assertRaises(ValueError) as context:
            submission.get_answer_by_text("Non-existent Question")

        self.assertIn("not found", str(context.exception))

    def test_get_answer_by_name_not_found(self):
        """Test getting answer by name when not found"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        with self.assertRaises(ValueError) as context:
            submission.get_answer_by_name("nonExistentName")

        self.assertIn("not found", str(context.exception))

    def test_get_answer_by_key_not_found(self):
        """Test getting answer by key when not found"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        with self.assertRaises(ValueError) as context:
            submission.get_answer_by_key("999")

        self.assertIn("not found", str(context.exception))

    def test_get_answer_with_list_single_item(self):
        """Test getting answer that is a list with single item"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        answer = submission.get_answer_by_key("4")  # singleSelect has ["option1"]
        self.assertEqual(answer["answer"], "option1")  # Should extract single item

    def test_get_answer_with_list_multiple_items(self):
        """Test getting answer that is a list with multiple items"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        answer = submission.get_answer_by_key(
            "3"
        )  # colors has ["red", "blue", "green"]
        self.assertEqual(
            answer["answer"], ["red", "blue", "green"]
        )  # Should keep as list

    def test_get_answer_case_insensitive_text(self):
        """Test that get_answer_by_text is case insensitive"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        answer = submission.get_answer_by_text("full name")  # lowercase
        self.assertEqual(answer["answer"], "John Doe")

        answer = submission.get_answer_by_text("FULL NAME")  # uppercase
        self.assertEqual(answer["answer"], "John Doe")

    def test_text_to_html(self):
        """Test text to HTML conversion"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Test with None
        result = submission.text_to_html(None)
        self.assertIsNone(result)

        # Test with simple text
        result = submission.text_to_html("Hello World")
        self.assertEqual(result, "<p>Hello World</p>")

        # Test with line breaks
        result = submission.text_to_html("Line 1\nLine 2\rLine 3\r\nLine 4")
        self.assertEqual(result, "<p>Line 1<br>Line 2<br>Line 3<br>Line 4</p>")

        # Test with paragraphs
        result = submission.text_to_html("Para 1\n\nPara 2")
        self.assertEqual(result, "<p>Para 1</p><p>Para 2</p>")

    def test_split_domain_from_email_edge_cases(self):
        """Test split_domain_from_email with edge cases"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Test with None
        result = submission.split_domain_from_email(None)
        self.assertIsNone(result)

        # Test with empty string
        result = submission.split_domain_from_email("")
        self.assertIsNone(result)

        # Test with string without @
        result = submission.split_domain_from_email("noatsign")
        self.assertEqual(result, "noatsign")

    def test_get_value_edge_cases(self):
        """Test get_value with various edge cases"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Test with None
        result = submission.get_value(None)
        self.assertIsNone(result)

        # Test with string with whitespace
        result = submission.get_value("  test string  ")
        self.assertEqual(result, "test string")

        # Test with dict with answer that's a list
        test_dict = {"answer": ["item1", "item2"]}
        result = submission.get_value(test_dict)
        self.assertEqual(result, "item1")

        # Test with single-item dict
        test_dict = {"single_key": "single_value"}
        result = submission.get_value(test_dict)
        self.assertEqual(result, "single_value")

    def test_make_array_edge_cases(self):
        """Test make_array with edge cases"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Test with None
        result = submission.make_array(None)
        self.assertEqual(result, [])

        # Test with empty string
        result = submission.make_array("")
        self.assertEqual(result, [])

        # Test with whitespace-only string
        result = submission.make_array("   ")
        self.assertEqual(result, [])

        # Test with dict containing answer
        test_dict = {"answer": "value1, value2"}
        result = submission.make_array(test_dict)
        self.assertEqual(result, ["value1", "value2"])

        # Test with non-string, non-list, non-dict
        result = submission.make_array(123)
        self.assertEqual(result, [123])

    def test_tide_answer_for_list(self):
        """Test tide_answer_for_list method"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Test with list
        test_list = ["apple", "banana", "cherry"]
        result = submission.tide_answer_for_list(test_list)
        self.assertEqual(result, "Apple, Banana, Cherry")

        # Test with dict
        test_dict = {"1": "apple", "2": "banana", "3": "cherry"}
        result = submission.tide_answer_for_list(test_dict)
        self.assertEqual(result, "Apple, Banana, Cherry")

    def test_answer_for_html(self):
        """Test answer_for_html method"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Test with list
        test_list = ["apple", "banana"]
        result = submission.answer_for_html(test_list)
        self.assertEqual(result, "*Apple<br>*Banana")

        # Test with dict
        test_dict = {"1": "apple", "2": "banana"}
        result = submission.answer_for_html(test_dict)
        self.assertEqual(result, "*Apple<br>*Banana")

        # Test with string
        result = submission.answer_for_html("apple")
        self.assertEqual(result, "*Apple")

        # Test with None
        result = submission.answer_for_html(None)
        self.assertEqual(result, "*None")

    def test_turn_into_american_datetime_format(self):
        """Test datetime format conversion"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)

        # Test with string
        result = submission.turn_into_american_datetime_format("2024-01-01 14:30:00")
        self.assertEqual(result, "01/01/2024 02:30 PM")

        # Test with datetime object
        dt = datetime(2024, 1, 1, 14, 30, 0)
        result = submission.turn_into_american_datetime_format(dt)
        self.assertEqual(result, "01/01/2024 02:30 PM")

        # Test with dict
        test_dict = {"answer": "2024-01-01 14:30:00"}
        result = submission.turn_into_american_datetime_format(test_dict)
        self.assertEqual(result, "01/01/2024 02:30 PM")

        # Test with invalid input
        with self.assertRaises(ValueError):
            submission.turn_into_american_datetime_format(123)

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_by_key(self, mock_post):
        """Test setting answer by key"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        submission.set_answer("1", "Jane Doe")

        # Verify the answer was updated in answers_arr
        updated_answer = submission.get_answer_by_key("1")
        self.assertEqual(updated_answer["answer"], "Jane Doe")

        # Verify the answer was updated in answers dict
        self.assertEqual(submission.answers["1"]["answer"], "Jane Doe")

        # Verify update_submission was called (via the post request)
        mock_post.assert_called_once()

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_by_text(self, mock_post):
        """Test setting answer by text"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        submission.set_answer_by_text("Full Name", "Jane Doe")

        # Verify the answer was updated
        updated_answer = submission.get_answer_by_text("Full Name")
        self.assertEqual(updated_answer["answer"], "Jane Doe")

        # Verify update_submission was called
        mock_post.assert_called_once()

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_by_name(self, mock_post):
        """Test setting answer by name"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        submission.set_answer_by_name("fullName", "Jane Doe")

        # Verify the answer was updated
        updated_answer = submission.get_answer_by_name("fullName")
        self.assertEqual(updated_answer["answer"], "Jane Doe")

        # Verify update_submission was called
        mock_post.assert_called_once()

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_with_list_value(self, mock_post):
        """Test setting answer with a list value"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        new_colors = ["yellow", "purple", "orange"]
        submission.set_answer("3", new_colors)

        # Verify the answer was updated
        updated_answer = submission.get_answer_by_key("3")
        self.assertEqual(updated_answer["answer"], new_colors)

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_updates_both_storage_locations(self, mock_post):
        """Test that set_answer updates both answers_arr and answers dict"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        new_value = "test@example.com"
        submission.set_answer("2", new_value)

        # Check answers_arr
        found_in_arr = False
        for answer in submission.answers_arr:
            if answer["key"] == "2":
                self.assertEqual(answer["answer"], new_value)
                found_in_arr = True
                break
        self.assertTrue(found_in_arr, "Answer not found in answers_arr")

        # Check answers dict
        self.assertEqual(submission.answers["2"]["answer"], new_value)

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_by_text_case_insensitive(self, mock_post):
        """Test that set_answer_by_text works with case variations"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        submission.set_answer_by_text("FULL NAME", "Test User")

        # Verify the answer was updated
        updated_answer = submission.get_answer_by_text("full name")
        self.assertEqual(updated_answer["answer"], "Test User")

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_nonexistent_key(self, mock_post):
        """Test setting answer with non-existent key raises error"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with self.assertRaises(KeyError):
            submission.set_answer("999", "test_value")

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_by_text_nonexistent(self, mock_post):
        """Test setting answer by non-existent text raises error"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with self.assertRaises(ValueError) as context:
            submission.set_answer_by_text("Non-existent Field", "test_value")

        self.assertIn("not found", str(context.exception))

    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_set_answer_by_name_nonexistent(self, mock_post):
        """Test setting answer by non-existent name raises error"""
        submission = JotFormSubmission(self.sample_submission, self.api_key)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with self.assertRaises(ValueError) as context:
            submission.set_answer_by_name("nonExistentField", "test_value")

        self.assertIn("not found", str(context.exception))


class TestJotFormUpdateAnswers(unittest.TestCase):
    """Tests for updating submission answers"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.form_id = "123456"
        self.submission_id = "1001"
        self.sample_submission = {
            "id": self.submission_id,
            "form_id": self.form_id,
            "ip": "192.168.1.1",
            "created_at": "2024-01-01 12:00:00",
            "status": "ACTIVE",
            "new": "1",
            "flag": "0",
            "notes": "",
            "updated_at": "2024-01-01 12:00:00",
            "answers": {
                "1": {
                    "name": "fullName",
                    "text": "Full Name",
                    "answer": "John Doe",
                    "type": "control_textbox",
                },
                "2": {
                    "name": "colors",
                    "text": "Favorite Colors",
                    "answer": ["red", "blue"],
                    "type": "control_checkbox",
                },
            },
        }

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_update_submission_answer_success(self, mock_post, mock_get):
        """Test successfully updating a single submission answer"""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "content": [self.sample_submission],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.update_submission_answer(
                self.submission_id, "1", "Jane Doe"
            )

        self.assertTrue(result)
        # Verify the submission was updated
        self.assertEqual(
            jotform.submission_data[self.submission_id].answers["1"]["answer"],
            "Jane Doe",
        )

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_update_submission_answer_with_list(self, mock_post, mock_get):
        """Test updating submission answer with list value"""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "content": [self.sample_submission],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            new_colors = ["green", "yellow", "purple"]
            result = jotform.update_submission_answer(
                self.submission_id, "2", new_colors
            )

        self.assertTrue(result)
        # Verify the submission was updated with the list
        self.assertEqual(
            jotform.submission_data[self.submission_id].answers["2"]["answer"],
            new_colors,
        )

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_update_submission_answer_failure(self, mock_post, mock_get):
        """Test failing to update submission answer"""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "content": [self.sample_submission],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 400
        mock_post.return_value = mock_post_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.update_submission_answer(
                self.submission_id, "1", "Jane Doe"
            )

        self.assertFalse(result)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_update_submission_answers_batch_success(self, mock_post, mock_get):
        """Test successfully updating multiple submission answers in batch"""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "content": [self.sample_submission],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            answers = {"1": "Jane Doe", "2": ["green", "yellow"]}
            result = jotform.update_submission_answers_batch(
                self.submission_id, answers
            )

        self.assertTrue(result)
        # Verify both answers were updated
        self.assertEqual(
            jotform.submission_data[self.submission_id].answers["1"]["answer"],
            "Jane Doe",
        )
        self.assertEqual(
            jotform.submission_data[self.submission_id].answers["2"]["answer"],
            ["green", "yellow"],
        )

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_update_submission_answers_batch_failure(self, mock_post, mock_get):
        """Test failing to update multiple answers in batch"""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "content": [self.sample_submission],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 400
        mock_post.return_value = mock_post_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            answers = {"1": "Jane Doe", "2": ["green", "yellow"]}
            result = jotform.update_submission_answers_batch(
                self.submission_id, answers
            )

        self.assertFalse(result)


class TestJotFormQueryMethods(unittest.TestCase):
    """Tests for query and search methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.form_id = "123456"
        self.sample_submission = {
            "id": "1001",
            "form_id": self.form_id,
            "ip": "192.168.1.1",
            "created_at": "2024-01-01 12:00:00",
            "status": "ACTIVE",
            "new": "1",
            "flag": "0",
            "notes": "",
            "updated_at": "2024-01-01 12:00:00",
            "answers": {
                "1": {
                    "name": "caseid",
                    "text": "Case ID",
                    "answer": "CASE-12345",
                    "type": "control_textbox",
                },
                "2": {
                    "name": "email",
                    "text": "Email",
                    "answer": "john@example.com",
                    "type": "control_email",
                },
            },
        }

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_request_submission_by_case_id_success(self, mock_get):
        """Test requesting submission by case ID successfully"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [self.sample_submission],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_response

        with patch.object(JotForm, "update"):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.request_submission_by_case_id("CASE-12345")

        self.assertIsNotNone(result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["id"], "1001")

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_request_submission_by_case_id_failure(self, mock_get):
        """Test requesting submission by case ID with failure"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with patch.object(JotForm, "update"):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.request_submission_by_case_id("NONEXISTENT")

        self.assertIsNone(result)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_get_user_data_by_email_found(self, mock_get):
        """Test getting user data by email"""
        sample_submission_with_email = self.sample_submission.copy()
        sample_submission_with_email["answers"]["2"] = {
            "name": "email",
            "text": "Email",
            "answer": "john@example.com",
            "type": "control_email",
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [sample_submission_with_email],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.get_user_data_by_email("john@example.com")

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "1001")

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_get_user_data_by_email_case_insensitive(self, mock_get):
        """Test getting user data by email with case insensitivity"""
        sample_submission_with_email = self.sample_submission.copy()
        sample_submission_with_email["answers"]["2"] = {
            "name": "email",
            "text": "Email",
            "answer": "john@example.com",
            "type": "control_email",
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [sample_submission_with_email],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.get_user_data_by_email("JOHN@EXAMPLE.COM")

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_get_user_data_by_email_not_found(self, mock_get):
        """Test getting user data by email when not found"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [self.sample_submission],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.get_user_data_by_email("nonexistent@example.com")

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_get_user_data_by_email_none(self, mock_get):
        """Test getting user data with empty email"""
        with patch.object(JotForm, "update"):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.get_user_data_by_email("")

        self.assertIsNone(result)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_create_submission_using_another_success(self, mock_post, mock_get):
        """Test creating submission using another as template"""
        # Mock questions endpoint
        questions_response = Mock()
        questions_response.status_code = 200
        questions_response.json.return_value = {
            "content": {
                "1": {"name": "fullName", "type": "control_textbox"},
                "2": {"name": "email", "type": "control_email"},
            }
        }

        # Mock new submission response
        new_submission = self.sample_submission.copy()
        new_submission["id"] = "9999"
        new_submission["answers"]["1"]["answer"] = "Jane Doe"
        new_submission["answers"]["2"]["answer"] = "jane@example.com"

        submissions_response = Mock()
        submissions_response.status_code = 200
        submissions_response.json.return_value = {
            "content": [self.sample_submission],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }

        get_submission_response = Mock()
        get_submission_response.status_code = 200
        get_submission_response.json.return_value = {"content": new_submission}

        # Set up side effect to return different responses based on URL
        def get_side_effect(url, *args, **kwargs):
            if "questions" in url:
                return questions_response
            elif "submission/9999" in url:
                return get_submission_response
            return submissions_response

        mock_get.side_effect = get_side_effect

        # Mock post for creation
        post_response = Mock()
        post_response.status_code = 200
        post_response.json.return_value = {"content": {"submissionID": "9999"}}
        mock_post.return_value = post_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            template_submission = JotFormSubmission(
                self.sample_submission, self.api_key
            )

            submission_data = {"fullName": "Jane Doe", "email": "jane@example.com"}
            result = jotform.create_submission_using_another(
                submission_data, template_submission
            )

        self.assertEqual(result, "9999")

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.post")
    def test_create_submission_using_another_no_questions(self, mock_post, mock_get):
        """Test creating submission using another when questions fetch fails"""
        # Mock failed questions endpoint
        questions_response = Mock()
        questions_response.status_code = 404
        mock_get.return_value = questions_response

        with patch.object(JotForm, "update"):
            jotform = JotForm(self.api_key, self.form_id)
            template_submission = JotFormSubmission(
                self.sample_submission, self.api_key
            )

            submission_data = {"fullName": "Jane Doe"}
            result = jotform.create_submission_using_another(
                submission_data, template_submission
            )

        self.assertFalse(result)


class TestJotFormErrorHandling(unittest.TestCase):
    """Tests for error handling and edge cases"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.form_id = "123456"

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_debug_print_enabled(self, mock_get):
        """Test that debug print works when enabled"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [],
            "resultSet": {"offset": 0, "limit": 1000},
        }
        mock_get.return_value = mock_response

        with patch("builtins.print") as mock_print:
            with patch.object(JotForm, "_fetch_submissions_count", return_value=0):
                jotform = JotForm(self.api_key, self.form_id)
                jotform.debug = True
                jotform._print("Test message")

            mock_print.assert_called_with("Test message")

    @patch("crossmark_jotform_api.jotForm.requests.get")
    def test_debug_print_disabled(self, mock_get):
        """Test that debug print doesn't print when disabled"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [],
            "resultSet": {"offset": 0, "limit": 1000},
        }
        mock_get.return_value = mock_response

        with patch("builtins.print") as mock_print:
            with patch.object(JotForm, "_fetch_submissions_count", return_value=0):
                jotform = JotForm(self.api_key, self.form_id)
                jotform.debug = False
                jotform._print("Test message")

            mock_print.assert_not_called()

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.delete")
    def test_delete_submission_success(self, mock_delete, mock_get):
        """Test successful submission deletion"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [
                {
                    "id": "1001",
                    "form_id": self.form_id,
                    "status": "ACTIVE",
                    "answers": {},
                    "ip": "192.168.1.1",
                    "created_at": "2024-01-01 12:00:00",
                    "new": "1",
                    "flag": "0",
                    "notes": "",
                    "updated_at": "2024-01-01 12:00:00",
                }
            ],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_response

        delete_response = Mock()
        delete_response.status_code = 200
        mock_delete.return_value = delete_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.delete_submission("1001")

        self.assertTrue(result)
        self.assertNotIn("1001", jotform.submission_data)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.delete")
    def test_delete_submission_failure(self, mock_delete, mock_get):
        """Test failed submission deletion"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [
                {
                    "id": "1001",
                    "form_id": self.form_id,
                    "status": "ACTIVE",
                    "answers": {},
                    "ip": "192.168.1.1",
                    "created_at": "2024-01-01 12:00:00",
                    "new": "1",
                    "flag": "0",
                    "notes": "",
                    "updated_at": "2024-01-01 12:00:00",
                }
            ],
            "resultSet": {"offset": 0, "limit": 1000, "count": 1},
        }
        mock_get.return_value = mock_response

        delete_response = Mock()
        delete_response.status_code = 404
        mock_delete.return_value = delete_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=1):
            jotform = JotForm(self.api_key, self.form_id)
            result = jotform.delete_submission("1001")

        self.assertFalse(result)
        # Submission should still be in data
        self.assertIn("1001", jotform.submission_data)

    @patch("crossmark_jotform_api.jotForm.requests.get")
    @patch("crossmark_jotform_api.jotForm.requests.delete")
    def test_delete_submission_empty_id(self, mock_delete, mock_get):
        """Test deleting submission with empty ID"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [],
            "resultSet": {"offset": 0, "limit": 1000},
        }
        mock_get.return_value = mock_response

        with patch.object(JotForm, "_fetch_submissions_count", return_value=0):
            jotform = JotForm(self.api_key, self.form_id)

            with self.assertRaises(ValueError):
                jotform.delete_submission("")


if __name__ == "__main__":
    unittest.main()
