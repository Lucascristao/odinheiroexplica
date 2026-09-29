import { z } from "zod";

const sourceSchema = z
  .object({
    id: z.string().min(1),
    title: z.string().optional(),
    url: z.string().url(),
    publisher: z.string().optional(),
    source_type: z.enum(["primary", "secondary", "context"]).optional(),
    publisher_class: z.enum([
      "official",
      "independent_journalism",
      "technical",
      "industry",
      "academic",
      "fact_check",
      "company",
      "other",
    ]).default("other"),
    editorial_role: z.enum([
      "primary_document",
      "independent_reporting",
      "technical_analysis",
      "industry_view",
      "fact_check",
      "data_context",
      "company_position",
      "other",
    ]).default("other"),
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
    framing: z.enum([
      "verified_fact",
      "official_position",
      "reported_claim",
      "analysis",
      "context",
    ]).default("verified_fact"),
    attribution_required: z.boolean().default(false),
    metadata: z.record(z.string(), z.unknown()).optional(),
  })
  .passthrough();

const visualAssetSchema = z
  .object({
    id: z.string().min(1),
    type: z.enum(["photo_cutout", "photo", "graphic"]),
    subject: z.string().min(1),
    narrative_role: z.string().min(1),
    country_context: z.enum(["BR", "global", "neutral"]).default("BR"),
    source_page_url: z.string().url(),
    image_url: z.string().url(),
    license: z.string().min(1),
    attribution: z.string().optional(),
    needs_cutout: z.boolean().default(true),
  })
  .passthrough();

const visualBeatSchema = z
  .object({
    anchor: z.string().min(1).optional(),
    at: z.number().min(0).max(1).optional(),
    kind: z
      .enum([
        "fact",
        "number",
        "date",
        "money",
        "bank",
        "flow",
        "process",
        "warning",
        "compare",
        "trend_up",
        "trend_down",
        "fuel",
        "block",
      ])
      .default("fact"),
    headline: z.string().min(1),
    detail: z.string().optional(),
    value: z.string().optional(),
    from: z.string().optional(),
    to: z.string().optional(),
    behavior: z
      .enum(["cut", "transform", "reframe", "overlay"])
      .default("cut"),
    treatment: z
      .enum([
        "kinetic_type",
        "giant_number",
        "flow_diagram",
        "timeline",
        "split_compare",
        "meter",
        "spotlight",
        "equation",
        "stack",
        "signal",
      ])
      .default("kinetic_type"),
    transition: z
      .enum(["cut", "fade", "slide_left", "slide_up", "zoom", "wipe"])
      .default("cut"),
    placement: z
      .enum(["left", "center", "right", "full"])
      .default("full"),
    medium: z
      .enum(["motion_graphic", "photo_cutout", "photo", "mixed"])
      .default("motion_graphic"),
    asset_id: z.string().optional(),
    sound: z
      .enum(["none", "tick", "impact", "whoosh", "alert"])
      .default("none"),
  })
  .passthrough()
  .superRefine((beat, ctx) => {
    if (!beat.anchor && beat.at === undefined) {
      ctx.addIssue({
        code: "custom",
        message: "Beat visual precisa de anchor ou at.",
      });
    }
  });

const visualDirectionSchema = z
  .object({
    concept: z.string().min(3),
    world: z.enum([
      "minimal",
      "digital",
      "industrial",
      "documentary",
      "market",
      "network",
      "paper",
    ]),
    secondary_color: z.string().regex(/^#[0-9a-fA-F]{6}$/).default("#ff7a1a"),
    motifs: z.array(z.string().min(1)).min(2).max(6),
    motion_language: z.array(z.string().min(1)).min(2).max(6),
    avoid: z.array(z.string().min(1)).min(2).max(8),
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
        beats: z.array(visualBeatSchema).max(12).optional(),
        transition: z
          .enum(["cut", "fade", "slide_left", "slide_up", "zoom", "wipe"])
          .default("cut"),
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
    visual_assets: z.array(visualAssetSchema).default([]),
    visual_direction: visualDirectionSchema.default({
      concept: "Editorial financeiro",
      world: "minimal",
      secondary_color: "#ff7a1a",
      motifs: ["tipografia", "dados"],
      motion_language: ["cut", "reframe"],
      avoid: ["cards repetitivos", "layout fixo"],
    }),
    editorial: z
      .object({
        viral_score: z.number().int().min(0).max(100).optional(),
        strengths: z.array(z.string()).default([]),
        risk_flags: z.array(z.string()).default([]),
        source_balance: z
          .object({
            requires_diversity: z.boolean().default(false),
            public_policy_or_regulation: z.boolean().default(false),
            official_sources_role: z.string().default(""),
            independent_sources_role: z.string().default(""),
            counterpoint_summary: z.string().default(""),
            official_claims_attributed: z.boolean().default(false),
          })
          .default({
            requires_diversity: false,
            public_policy_or_regulation: false,
            official_sources_role: "",
            independent_sources_role: "",
            counterpoint_summary: "",
            official_claims_attributed: false,
          }),
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

    const visualAssetIds = new Set<string>();
    project.visual_assets.forEach((asset, index) => {
      if (visualAssetIds.has(asset.id)) {
        ctx.addIssue({
          code: "custom",
          path: ["visual_assets", index, "id"],
          message: "ID de recurso visual duplicado.",
        });
      }
      visualAssetIds.add(asset.id);
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

      const beats = scene.visual.beats ?? [];
      beats.forEach((beat, beatIndex) => {
        if (beat.asset_id && !visualAssetIds.has(beat.asset_id)) {
          ctx.addIssue({
            code: "custom",
            path: ["script", "scenes", index, "visual", "beats", beatIndex, "asset_id"],
            message: `Beat referencia recurso visual inexistente: ${beat.asset_id}`,
          });
        }

        if (beat.anchor) {
          const occurrences = scene.narration.split(beat.anchor).length - 1;
          if (occurrences !== 1) {
            ctx.addIssue({
              code: "custom",
              path: ["script", "scenes", index, "visual", "beats", beatIndex, "anchor"],
              message:
                "Anchor precisa aparecer exatamente uma vez na narração da cena.",
            });
          }
        }
      });

      const overlayCount = beats.filter((beat) => beat.behavior === "overlay").length;
      if (overlayCount > 1) {
        ctx.addIssue({
          code: "custom",
          path: ["script", "scenes", index, "visual", "beats"],
          message: "Use no máximo um overlay por cena; prefira cut, transform ou reframe.",
        });
      }

      for (let beatIndex = 2; beatIndex < beats.length; beatIndex += 1) {
        const current = beats[beatIndex];
        const previous = beats[beatIndex - 1];
        const beforePrevious = beats[beatIndex - 2];
        if (
          current.treatment === previous.treatment &&
          previous.treatment === beforePrevious.treatment
        ) {
          ctx.addIssue({
            code: "custom",
            path: ["script", "scenes", index, "visual", "beats", beatIndex, "treatment"],
            message: "Não repita o mesmo tratamento visual em três beats consecutivos.",
          });
        }
      }
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
