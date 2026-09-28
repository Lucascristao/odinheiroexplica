export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type VideoProjectRow = {
  id: string;
  owner_id: string;
  schema_version: string;
  status: string;
  subject: string;
  angle: string | null;
  promise: string | null;
  category: string | null;
  viral_score: number | null;
  risk_flags: string[];
  raw_payload: Json;
  duration_seconds: number | null;
  drive_file_id: string | null;
  youtube_video_id: string | null;
  tts_voice: string;
  created_at: string;
  updated_at: string;
  published_at: string | null;
};

export type ProjectSourceRow = {
  id: string;
  project_id: string;
  owner_id: string;
  source_key: string | null;
  title: string | null;
  url: string;
  publisher: string | null;
  source_type: string | null;
  published_at: string | null;
  accessed_at: string;
  license: string | null;
  notes: string | null;
  metadata: Json;
  created_at: string;
};

export type ProjectClaimRow = {
  id: string;
  project_id: string;
  owner_id: string;
  claim_key: string | null;
  claim_text: string;
  confidence: string;
  verification_status: string;
  source_keys: string[];
  metadata: Json;
  created_at: string;
};

export type ProjectSceneRow = {
  id: string;
  project_id: string;
  owner_id: string;
  scene_index: number;
  title: string | null;
  narration: string;
  visual_type: string | null;
  visual_payload: Json;
  claim_keys: string[];
  audio_duration_seconds: number | null;
  audio_path: string | null;
  audio_voice: string | null;
  narration_sha256: string | null;
  audio_generated_at: string | null;
  created_at: string;
  updated_at: string;
};

export type RenderJobRow = {
  id: string;
  project_id: string;
  owner_id: string;
  status: string;
  stage: string | null;
  progress: number;
  github_run_id: string | null;
  error_message: string | null;
  output_metadata: Json;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type PublicationRow = {
  id: string;
  project_id: string;
  owner_id: string;
  status: string;
  title: string | null;
  description: string | null;
  thumbnail_variant: string | null;
  youtube_video_id: string | null;
  youtube_url: string | null;
  published_at: string | null;
  metadata: Json;
  created_at: string;
  updated_at: string;
};

type TableDef<Row, Insert = Partial<Row>, Update = Partial<Row>> = {
  Row: Row;
  Insert: Insert;
  Update: Update;
  Relationships: [];
};

export type Database = {
  public: {
    Tables: {
      video_projects: TableDef<
        VideoProjectRow,
        Partial<VideoProjectRow> & Pick<VideoProjectRow, "subject">,
        Partial<VideoProjectRow>
      >;
      project_sources: TableDef<
        ProjectSourceRow,
        Partial<ProjectSourceRow> & Pick<ProjectSourceRow, "project_id" | "url">,
        Partial<ProjectSourceRow>
      >;
      project_claims: TableDef<
        ProjectClaimRow,
        Partial<ProjectClaimRow> & Pick<ProjectClaimRow, "project_id" | "claim_text">,
        Partial<ProjectClaimRow>
      >;
      project_scenes: TableDef<
        ProjectSceneRow,
        Partial<ProjectSceneRow> &
          Pick<ProjectSceneRow, "project_id" | "scene_index">,
        Partial<ProjectSceneRow>
      >;
      render_jobs: TableDef<
        RenderJobRow,
        Partial<RenderJobRow> & Pick<RenderJobRow, "project_id">,
        Partial<RenderJobRow>
      >;
      publications: TableDef<
        PublicationRow,
        Partial<PublicationRow> & Pick<PublicationRow, "project_id">,
        Partial<PublicationRow>
      >;
    };
    Views: Record<string, never>;
    Functions: {
      import_video_project: {
        Args: { payload: Json };
        Returns: string;
      };
      transition_video_project_status: {
        Args: {
          p_project_id: string;
          p_expected_status: string;
          p_new_status: string;
        };
        Returns: VideoProjectRow;
      };
      apply_scene_audio_result: {
        Args: {
          p_scene_id: string;
          p_project_id: string;
          p_expected_narration_sha256: string;
          p_audio_path: string;
          p_audio_duration_seconds: number;
          p_audio_voice: string;
        };
        Returns: ProjectSceneRow;
      };
      recalculate_project_duration: {
        Args: { p_project_id: string };
        Returns: number;
      };
    };
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
};
