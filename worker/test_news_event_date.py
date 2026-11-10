"""Regression: an article posted today cannot refresh yesterday's petition."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from news_event_date import validate_event_date


class EventDateEvidence(unittest.TestCase):
    def test_real_rejected_petition_passage_cannot_prove_tuesday(self):
        with self.assertRaisesRegex(ValueError, '2026-11-09'):
            validate_event_date('Na petição, protocolada nesta segunda-feira, 9, eles alegam que o afastamento ocorreu em setembro.',
                                '2026-11-10', '2026-11-10')

    def test_same_day_publication_of_release_is_allowed(self):
        validate_event_date('O órgão divulgou o resultado nesta terça-feira, 10.', '2026-11-10', '2026-11-10')

    def test_weekday_only_is_resolved_from_source_publication(self):
        with self.assertRaises(ValueError):
            validate_event_date('O balanço foi divulgado nesta segunda-feira.', '2026-11-10', '2026-11-10')
        validate_event_date('O balanço foi divulgado nesta segunda-feira.', '2026-11-09', '2026-11-09')

    def test_explicit_dates_and_yesterday(self):
        for text in ('Pedido protocolado em 9 de novembro de 2026.',
                     'Pedido protocolado em 09/11/2026.', 'Pedido protocolado em 2026-11-09.',
                     'A defesa apresentou o pedido ontem.'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_event_date(text, '2026-11-10', '2026-11-10')

    def test_old_reference_period_does_not_reject_current_release(self):
        validate_event_date('Dados de 2026-09-30 foram divulgados nesta terça-feira, 10.', '2026-11-10', '2026-11-10')

    def test_no_explicit_date_still_needs_semantic_review(self):
        validate_event_date('O comunicado informa as condições do resultado.', '2026-11-10', '2026-11-10')


if __name__ == '__main__':
    unittest.main()
