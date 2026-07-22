export interface User {
  id: number;
  email: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  user_id: number;
  resume_markdown: string;
  summary: string | null;
  skills: string[];
  projects: string[];
  education: string[];
  certifications: string[];
  created_at: string;
  updated_at: string;
}

export interface RequirementMatch {
  name: string;
  requirement_type: string;
  is_required: boolean;
  importance: number;
  matched: boolean;
  evidence: string;
  profile_evidence: string | null;
}

export interface PreparationAction {
  skill: string;
  priority: "high" | "medium";
  reason: string;
  action: string;
}

export interface JobAnalysis {
  source_url: string | null;
  page_title: string | null;
  input_method: "url" | "content";
  analysis_method: "llm" | "deterministic";
  fallback_reason: string | null;
  extracted_text: string;
  match_score: number;
  requirements: RequirementMatch[];
  matched_skills: string[];
  missing_skills: string[];
  action_plan: PreparationAction[];
  warnings: string[];
}
