// Types calqués 1:1 sur api/schemas.py du backend Eleva.
// Toute évolution du backend doit être répercutée ici.

export type Priority = "low" | "medium" | "high" | "critical";
export type IssueType = "problem" | "opportunity";
export type RecommendationStatus = "draft" | "pending_approval" | "approved" | "rejected";

export interface AnalyzeRequestBody {
  company_id: string;
  question: string;
  focus_areas?: string[] | null;
  max_recommendations?: number;
}

export interface KPIOut {
  name: string;
  value: number | string;
  unit?: string | null;
}

export interface SegmentOut {
  name: string;
  size: number;
  percentage: number;
}

export interface IssueOut {
  id: string;
  type: IssueType;
  title: string;
  description: string;
  priority: Priority;
  evidence: string[];
}

export interface RecommendationOut {
  id: string;
  title: string;
  summary: string;
  justification: string;
  priority: Priority;
  status: RecommendationStatus;
  expected_outcomes: string[];
  next_steps: string[];
}

export interface PlaybookOut {
  technique?: string;
  issue_title?: string;
  [key: string]: unknown;
}

export interface ExplanationCompany {
  name?: string;
  industry?: string;
  focus?: string;
  goals?: string[];
}

export interface ExplanationIssue {
  title: string;
  type: string;
  priority: string;
  description: string;
  evidence: string[];
}

export interface ExplanationStrategy {
  name: string;
  description: string;
  playbooks: string[];
  expected_impact?: string;
  effort?: string;
}

export interface ExplanationPlaybook {
  technique?: string;
  for_issue?: string;
}

export interface Explanation {
  recommendation_id: string;
  recommendation_title: string;
  recommendation_summary: string;
  priority: string;
  status: string;
  company: ExplanationCompany;
  user_question: string;
  signals: string[];
  detected_issues: ExplanationIssue[];
  playbooks_used: ExplanationPlaybook[];
  hypotheses: string[];
  strategies: ExplanationStrategy[];
  expected_outcomes: string[];
  next_steps: string[];
  narrative: string;
  gdpr_note: string;
  error?: string;
}

export interface AnalyzeResponse {
  company_id: string;
  company_name?: string | null;
  industry?: string | null;
  current_step: string;
  kpis: KPIOut[];
  segments: SegmentOut[];
  insights: string[];
  issues: IssueOut[];
  playbooks: PlaybookOut[];
  recommendations: RecommendationOut[];
  explanation?: Explanation | null;
  errors: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  service: string;
}

export interface ApiErrorPayload {
  detail?: string | { errors?: string[] } | unknown;
}
