/** Domain types mirroring the FastAPI response schemas. */

export type UserRole = 'admin' | 'member';

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

export interface IssueUpdatePayload {
  title?: string;
  description?: string;
  status?: IssueStatus;
  priority?: IssuePriority;
  assignee_id?: number | null;
}

export interface CommentCreatePayload {
  content: string;
}
