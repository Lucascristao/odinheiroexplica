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
  created_at: string;
  updated_at: string;
  published_at: string | null;
};

export type Database = {
  public: {
    Tables: {
      video_projects: {
        Row: VideoProjectRow;
        Insert: Partial<VideoProjectRow> & Pick<VideoProjectRow, "subject">;
        Update: Partial<VideoProjectRow>;
        Relationships: [];
      };
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
    };
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
};
