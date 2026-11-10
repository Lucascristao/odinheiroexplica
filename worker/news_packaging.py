"""Attention-first packaging, with literal support in the finished narration."""
import copy
import json


def apply_packaging(episode, proposal):
    speech = ' '.join(s['narration'] for s in episode['segments'])
    options = proposal.get('title_options') or []
    if len(options) != 3 or len({o.get('text') for o in options}) != 3:
        raise ValueError('Packaging requires three distinct title angles')
    for option in options:
        if (not isinstance(option.get('text'), str) or not 20 <= len(option['text']) <= 100
                or type(option.get('editorial_quality')) is not int or not 1 <= option['editorial_quality'] <= 5
                or len(option.get('proof_anchor', '')) < 20 or option['proof_anchor'] not in speech):
            raise ValueError('Title needs valid length, editorial score and literal spoken support')
    selected = next((o for o in options if o['text'] == proposal.get('title')), None)
    if not selected or selected['editorial_quality'] != max(o['editorial_quality'] for o in options):
        raise ValueError('Selected title must be the strongest recorded option')
    headline, proof = proposal.get('thumbnail_headline', ''), proposal.get('thumbnail_proof_anchor', '')
    if not 2 <= len(headline) <= 90 or len(proof) < 20 or proof not in speech:
        raise ValueError('Cover headline needs literal support in the narration')
    if not isinstance(proposal.get('reason'), str) or len(proposal['reason']) < 30:
        raise ValueError('Packaging needs a concrete editorial choice reason')
    result = copy.deepcopy(episode)
    result.update(title=selected['text'], title_options=options, thumbnail_headline=headline)
    result['scorecard'] = {'method': 'attention_first_editorial_comparison_not_ctr_prediction',
        'reason': proposal['reason'], 'criteria': {'curiosity': 'specific', 'tone': 'provocative', 'evidence': 'spoken_literal'}}
    result['packaging_strategy'] = {'policy': 'provocative_language_precise_facts',
        'thumbnail_proof_anchor': proof, 'compared_after_full_narration': True}
    result.pop('editorial_quality', None)
    return result


def improve_packaging(episode):
    from news_editorial_quality import parse_reply
    story = {k: episode.get(k) for k in ('title', 'thumbnail_headline', 'verified_facts', 'segments')}
    proposal = parse_reply(f'''Você é editor de títulos de um canal de notícias que precisa conquistar cliques.
REGRA PERMANENTE DO TITULAR: linguagem exagerada, provocativa, dramática, emocional e com curiosidade é o padrão, inclusive no TEXTO DA CAPA. Não entregar manchete burocrática de agência nem jargão jurídico/econômico. Metáforas, contraste e perguntas fortes são bem-vindos. O exagero é retórico: números, fatos, pessoas, alcance, datas e condições continuam precisos. Não inventar crime, ruína, decisão tomada, efeito universal ou risco que a fala não demonstra. Não prometer viralização/CTR.
Use somente o roteiro concluído: {json.dumps(story, ensure_ascii=False)}
Crie três ângulos DISTINTOS, compare e escolha o mais forte. Focar no que dá vontade de descobrir, na contradição e no conflito real; política não precisa de consequência financeira inventada. Assunto identificável cedo, evitar 'Entenda', 'Saiba mais', 'política monetária restritiva', 'transferência de competência' como gancho. Não forçar a mesma fórmula em toda notícia.
Exemplo de INTENSIDADE, sem copiar para outro assunto: notícia sobre juros altos por mais tempo pode virar 'Juros vão cair? O Banco Central jogou um balde de água fria' + capa 'SEM ALÍVIO!'. O vídeo precisa entregar a expectativa frustrada; não dizer que o BC proibiu cortes para sempre.
A capa usa 2 a4 palavras fortes, legíveis, complementares ao título. Pode usar exclamação e linguagem dramática sustentada. Preserve o documento real e o retrato oficial: não pedir novo rosto, seta, objeto ou símbolo.
Retorne JSON: title_options:[{{text,editorial_quality:inteiro1a5,proof_anchor:"trecho LITERAL do roteiro que sustenta a promessa"}}] com3 itens; title COPIA o vencedor com nota máxima; thumbnail_headline; thumbnail_proof_anchor:"trecho literal do roteiro"; reason:"por que esse par causa curiosidade e onde entrega a promessa".
Cada proof_anchor tem20a160 caracteres e copia fala existente. Esta etapa não aprova fatos: a segunda revisão posterior verificará promessa, roteiro e fontes.''', budget=1400)
    return apply_packaging(episode, proposal)
