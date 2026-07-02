export interface User {
  username: string;
}

export interface Video {
  id: number;
  filename: string;
  title: string | null;
  duration_seconds: number;
  file_size_bytes: number;
  file_path: string;
  created_at: string;
  expires_at: string;
  is_deleted: boolean;
}

export interface ApiError {
  detail: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}
