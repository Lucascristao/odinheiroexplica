import { z } from "zod";

const sourceSchema = z
  .object({
    id: z.string().min(1),
    title: z.string().optional(),
    url: z.string().url(),
    publisher: z.string().optional(),
    source_type: z.enum(["primary", "secondary", "context"]).optional(),
    published_at: z.string().optional(),
    license: z.string().optional(),
    notes: z.string().optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  })
  .passthrough();

const claimSchema = z
  .object({
    id: z.string().min(1),
    text: z.string().min(1),
    source_ids: z.array(z.string()).default([]),
    confidence: z.enum(["low", "medium", "high"]).default("medium"),
    verification_status: z
      .enum(["unverified", "verified", "conflicting", "rejected"])
      .default("unverified"),
    metadata: z.record(z.string(), z.unknown()).optional(),
  })
  .passthrough();

const sceneSchema = z
  .object({
    index: z.number().int().nonnegative(),
    title: z.string().optional(),
    narration: z.string().default(""),
    visual: z
      .object({
        type: z.string().min(1),
        payload: z.record(z.string(), z.unknown()).optional(),
      })
      .passthrough(),
    claim_ids: z.array(z.string()).default([]),
  })
  .passthrough();

export const videoProjectSchema = z
  .object({
    version: z.literal("1.0"),
    story: z
      .object({
        subject: z.string().min(3),
        angle: z.string().optional(),
        promise: z.string().optional(),
        why_now: z.string().optional(),
        category: z.enum(["news", "company", "economy", "money", "evergreen"]),
      })
      .passthrough(),
    editorial: z
      .object({
        viral_score: z.number().int().min(0).max(100).optional(),
        strengths: z.array(z.string()).default([]),
        risk_flags: z.array(z.string()).default([]),
        youtube_suitability: z
          .object({
            risk_level: z.enum(["low", "medium", "high"]).default("low"),
            sensitive_topics: z.array(z.string()).default([]),
            context_notes: z.string().default(""),
            title_thumbnail_safe: z.boolean().default(true),
            monetization_notes: z.string().default(""),
          })
          .default({
            risk_level: "low",
            sensitive_topics: [],
            context_notes: "",
            title_thumbnail_safe: true,
            monetization_notes: "",
          }),
      })
      .passthrough(),
    sources: z.array(sourceSchema).default([]),
    claims: z.array(claimSchema).default([]),
    packaging: z
      .object({
        strategy: z.object({
          click_reason: z.string().min(1),
          visual_focus: z.string().min(1),
          curiosity_gap: z.string().min(1),
          mobile_readability: z.string().min(1),
          anti_clickbait_check: z.string().min(1),
          repetition_check: z.string().min(1),
          youtube_safety_check: z.string().min(1),
        }),
        titles: z
          .array(
            z
              .object({
                id: z.string().min(1),
                text: z.string().min(1),
                rationale: z.string().optional(),
              })
              .passthrough(),
          )
          .length(1),
        thumbnails: z
          .array(
            z
              .object({
                id: z.string().min(1),
                headline: z.string().min(1),
                concept: z.string().min(1),
                visual_prompt: z.string().optional(),
              })
              .passthrough(),
          )
          .length(1),
      })
      .passthrough(),
    script: z
      .object({
        hook: z.string().min(1),
        beats: z.array(z.unknown()).default([]),
        scenes: z.array(sceneSchema).min(1),
        closing: z.string().optional(),
      })
      .passthrough(),
    publication: z
      .object({
        description: z.string().min(1),
        seo: z.object({
          primary_keyword: z.string().min(1),
          secondary_keywords: z.array(z.string()).max(8).default([]),
          search_intent: z.string().min(1),
          description_strategy: z.string().min(1),
        }),
        tags: z.array(z.string()).max(12).default([]),
        chapters: z.array(z.unknown()).default([]),
        disclosure_ai: z.boolean().default(false),
      })
      .passthrough(),
  })
  .passthrough()
  .superRefine((project, ctx) => {
    const sourceIds = new Set<string>();
    project.sources.forEach((source, index) => {
      if (sourceIds.has(source.id)) {
        ctx.addIssue({
          code: "custom",
          path: ["sources", index, "id"],
          message: "ID de fonte duplicado.",
        });
      }
      sourceIds.add(source.id);
    });

    const claimIds = new Set<string>();
    project.claims.forEach((claim, index) => {
      if (claimIds.has(claim.id)) {
        ctx.addIssue({
          code: "custom",
          path: ["claims", index, "id"],
          message: "ID de claim duplicado.",
        });
      }
      claimIds.add(claim.id);

      claim.source_ids.forEach((sourceId) => {
        if (!sourceIds.has(sourceId)) {
          ctx.addIssue({
            code: "custom",
            path: ["claims", index, "source_ids"],
            message: `Claim referencia fonte inexistente: ${sourceId}`,
          });
        }
      });
    });

    const sceneIndexes = new Set<number>();
    project.script.scenes.forEach((scene, index) => {
      if (sceneIndexes.has(scene.index)) {
        ctx.addIssue({
          code: "custom",
          path: ["script", "scenes", index, "index"],
          message: "Índice de cena duplicado.",
        });
      }
      sceneIndexes.add(scene.index);

      scene.claim_ids.forEach((claimId) => {
        if (!claimIds.has(claimId)) {
          ctx.addIssue({
            code: "custom",
            path: ["script", "scenes", index, "claim_ids"],
            message: `Cena referencia claim inexistente: ${claimId}`,
          });
        }
      });
    });
  });

export type VideoProject = z.infer<typeof videoProjectSchema>;

export const hardRiskFlags = new Set([
  "RUMOR_NAO_CONFIRMADO",
  "FONTE_INSUFICIENTE",
  "TITULO_NAO_SUPORTADO_PELOS_FATOS",
  "RECOMENDACAO_FINANCEIRA",
  "PROMESSA_DE_GANHO",
  "URGENCIA_ARTIFICIAL",
  "RISCO_COPYRIGHT",
  "DADO_CONFLITANTE",
  "YOUTUBE_POLICY_RISK",
]);
