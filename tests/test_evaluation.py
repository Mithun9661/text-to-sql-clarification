"""Regression tests for the evaluation harness; no model scores are fabricated."""
import unittest

from evaluation.evaluate import evaluate, normalized


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.gold = {
            'clear': {'ambiguous': False, 'expected_answer': '3'},
            'ambiguous': {'ambiguous': True, 'expected_answer': 'Priya'},
        }

    def test_normalization(self):
        self.assertEqual(normalized('  PRIYA\n '), 'priya')

    def test_perfect_clarification(self):
        predictions = {
            'clear': {'needs_clarification': False, 'answer': '3'},
            'ambiguous': {'needs_clarification': True, 'answer': 'Priya'},
        }
        metrics = evaluate(self.gold, predictions, 'clarification')
        self.assertEqual(metrics['answer_accuracy'], 1.0)
        self.assertEqual(metrics['ambiguity_detection_accuracy'], 1.0)
        self.assertEqual(metrics['ambiguous_answer_accuracy'], 1.0)

    def test_wrong_baseline(self):
        predictions = {
            'clear': {'needs_clarification': False, 'answer': '3'},
            'ambiguous': {'needs_clarification': False, 'answer': 'Rahul'},
        }
        metrics = evaluate(self.gold, predictions, 'baseline')
        self.assertEqual(metrics['answer_accuracy'], 0.5)
        self.assertEqual(metrics['ambiguous_answer_accuracy'], 0.0)

    def test_missing_predictions_are_not_counted_as_failures(self):
        with self.assertRaises(ValueError):
            evaluate(self.gold, {'clear': {'answer': '3'}}, 'baseline')

    def test_extra_predictions_rejected(self):
        predictions = {key: {'answer': item['expected_answer']} for key, item in self.gold.items()}
        predictions['unknown'] = {'answer': 'extra'}
        with self.assertRaises(ValueError):
            evaluate(self.gold, predictions, 'clarification')

    def test_empty_dataset_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({}, {}, 'baseline')


if __name__ == '__main__':
    unittest.main()
