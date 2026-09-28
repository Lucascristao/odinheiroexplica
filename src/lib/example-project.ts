import type { VideoProject } from "./video-project-schema";

export const exampleVideoProject: VideoProject = {
  version: "1.0",
  story: {
    subject: "Projeto de teste: como uma empresa fictícia ganha dinheiro",
    angle: "Explicar as fontes de receita sem recomendar investimento.",
    promise: "Mostrar de forma simples de onde vem o dinheiro da empresa.",
    why_now: "Pacote usado apenas para validar o fluxo do sistema.",
    category: "company",
  },
  editorial: {
    viral_score: 62,
    strengths: ["Tema fácil de visualizar", "Estrutura explicativa"],
    risk_flags: [],
  },
  sources: [
    {
      id: "src_01",
      title: "Fonte de demonstração",
      url: "https://example.com",
      publisher: "Example",
      source_type: "primary",
    },
  ],
  claims: [
    {
      id: "claim_01",
      text: "Este é um claim fictício usado apenas para testar o importador.",
      source_ids: ["src_01"],
      confidence: "high",
      verification_status: "verified",
    },
  ],
  packaging: {
    titles: [
      {
        id: "title_a",
        text: "Como essa empresa realmente ganha dinheiro?",
      },
      {
        id: "title_b",
        text: "O negócio por trás dos números dessa empresa",
      },
      {
        id: "title_c",
        text: "De onde vem o dinheiro dessa empresa?",
      },
    ],
    thumbnails: [
      {
        id: "thumb_a",
        headline: "DE ONDE VEM?",
        concept: "Fluxo visual de receitas em três blocos.",
      },
      {
        id: "thumb_b",
        headline: "O NEGÓCIO REAL",
        concept: "Empresa ao centro com três fontes de receita.",
      },
      {
        id: "thumb_c",
        headline: "R$ ?",
        concept: "Número grande com elementos financeiros minimalistas.",
      },
    ],
  },
  script: {
    hook:
      "A parte mais óbvia desse negócio não é necessariamente a que coloca mais dinheiro no caixa.",
    beats: [],
    scenes: [
      {
        index: 0,
        title: "Gancho",
        narration:
          "A parte mais óbvia desse negócio não é necessariamente a que coloca mais dinheiro no caixa.",
        visual: {
          type: "BIG_NUMBER",
          payload: { label: "Projeto de teste" },
        },
        claim_ids: [],
      },
      {
        index: 1,
        title: "Explicação",
        narration:
          "Neste projeto fictício, usamos uma fonte de demonstração para testar a ligação entre claims, cenas e fontes.",
        visual: {
          type: "EXPLAINER",
          payload: { steps: ["Fonte", "Claim", "Cena"] },
        },
        claim_ids: ["claim_01"],
      },
    ],
    closing: "Fim do projeto de teste.",
  },
  publication: {
    description: "Projeto fictício utilizado para testar o painel.",
    chapters: [],
    disclosure_ai: false,
  },
};
