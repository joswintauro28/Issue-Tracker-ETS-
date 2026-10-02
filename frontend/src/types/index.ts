/** Domain types mirroring the FastAPI response schemas. */

export type UserRole = 'admin' | 'user';

export type IssueStatus = 'open' | 'in_progress' | 'closed';

export type IssuePriority = 'low' | 'medium' | 'high';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface Issue {
  id: number;
  title: string;
  description: string;
  status: IssueStatus;
  priority: IssuePriority;
  reporter_id: number;
  assignee_id: number | null;
  created_at: string;
  updated_at: string;
  reporter: User;
  assignee: User | null;
}

export interface Comment {
  id: number;
  issue_id: number;
  user_id: number;
  content: string;
  created_at: string;
  author: User;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface IssueCreatePayload {
  title: string;
  description: string;
  priority: IssuePriority;
  assignee_id?: number | null;
}

/** Full replacement of an issue's editable fields (PUT /api/issues/{id}). */
export interface IssueEditPayload {
  title: string;
  description: string;
  priority: IssuePriority;
  status?: IssueStatus;
  assignee_id: number | null;
}

/** Values collected by the reusable IssueForm. */
export interface IssueFormValues {
  title: string;
  description: string;
  priority: IssuePriority;
  assignee_id: number | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardSummary {
  total_issues: number;
  open_issues: number;
  in_progress_issues: number;
  closed_issues: number;
  recent_issues: Issue[];
  my_assigned_issues: Issue[];
}

export interface CommentCreatePayload {
  content: string;
}
