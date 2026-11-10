import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from news_packaging import apply_packaging


class AttentionFirstPackaging(unittest.TestCase):
    def setUp(self):
        self.ep = {'title': 'Título factual anterior', 'thumbnail_headline': 'Antes',
            'segments': [{'narration': 'Os juros precisam permanecer elevados por mais tempo para conter a inflação.'}]}
        proof = self.ep['segments'][0]['narration']
        self.proposal = {'title': 'Juros vão cair? O Banco Central jogou um balde de água fria',
            'title_options': [{'text': text, 'editorial_quality': 5-i, 'proof_anchor': proof}
                for i, text in enumerate(('Juros vão cair? O Banco Central jogou um balde de água fria',
                    'Juros altos: por que o alívio ficou para depois?', 'A economia freia e o alívio dos juros continua distante'))],
            'thumbnail_headline': 'SEM ALÍVIO!', 'thumbnail_proof_anchor': proof,
            'reason': 'A metáfora dramatiza a expectativa frustrada; o roteiro entrega a manutenção dos juros por mais tempo.'}

    def test_dramatic_language_is_accepted_without_neutralizing_the_title(self):
        updated = apply_packaging(self.ep, self.proposal)
        self.assertEqual(updated['title'], self.proposal['title'])
        self.assertEqual(updated['thumbnail_headline'], 'SEM ALÍVIO!')
        self.assertEqual(self.ep['thumbnail_headline'], 'Antes')

    def test_invented_spoken_proof_is_not_accepted(self):
        self.proposal['title_options'][0]['proof_anchor'] = 'O Banco Central proibiu cortes para sempre.'
        with self.assertRaisesRegex(ValueError, 'literal'):
            apply_packaging(self.ep, self.proposal)

    def test_cover_must_also_have_spoken_support(self):
        self.proposal['thumbnail_proof_anchor'] = 'O Brasil vai falir nas próximas horas.'
        with self.assertRaisesRegex(ValueError, 'Cover'):
            apply_packaging(self.ep, self.proposal)

    def test_old_review_does_not_approve_new_packaging(self):
        self.ep['editorial_quality'] = {'review': {'approved': True}}
        self.assertNotIn('editorial_quality', apply_packaging(self.ep, self.proposal))


if __name__ == '__main__':
    unittest.main()
