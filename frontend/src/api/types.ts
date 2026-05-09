/** Mirrors backend ``app/schema/user.py`` and ``app/schema/auth.py``. */

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  full_name?: string | null;
}

export interface UserLogin {
  /** Email address or username (must match registration). */
  login: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterResponse {
  user: UserResponse;
  detail: string;
}

export interface MessageResponse {
  detail: string;
}
