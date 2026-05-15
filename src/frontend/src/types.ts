import type { FormEvent } from "react";

export type Role = "member" | "admin";

export type TokenResponse = {
  access_token: string;
  token_type: string;
  role: Role;
};

export type UserRead = {
  id: number;
  name: string;
  email: string | null;
  role: Role;
  is_active: boolean;
};

export type TimeSlot = {
  id: number;
  label: string;
  start_hour: number;
  end_hour: number;
  capacity: number;
  current_occupancy: number;
  is_demo: boolean;
};

export type WorkoutCategory = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
};

export type Reservation = {
  id: number;
  time_slot_id: number;
  workout_category_id: number;
};

export type VideoSession = {
  id: number;
  time_slot_id: number;
  workout_category_id: number;
  title: string | null;
  youtube_video_id: string | null;
  youtube_url: string | null;
  duration_seconds: number | null;
  provider: string;
  status: string;
  safety_notes: string | null;
  agent_summary: string | null;
};

export type VideoCacheEntry = {
  id: number;
  workout_category_id: number;
  title: string;
  youtube_video_id: string;
  status: string;
  play_count: number;
  curator_summary: string | null;
};

export type Occupancy = {
  time_slot_id: number;
  label: string;
  capacity: number;
  current_occupancy: number;
  remaining_capacity: number;
  is_full: boolean;
};

export type FeedbackSummary = {
  video_session_id: number;
  title: string | null;
  likes: number;
  dislikes: number;
  total_feedback: number;
  score: number;
};

export type Mode = "login" | "register";

export type BroadcastSession = {
  video_session_id: number;
  time_slot_id: number;
  workout_category_id: number;
  started_at: string;
  server_time: string;
  playback_offset_seconds: number;
  duration_seconds: number | null;
  participant_count: number;
  exited_participant_count: number;
  status: string;
};

export type ApiStatus = {
  debug_enabled: boolean;
};

export type AuthSubmitHandler = (event: FormEvent<HTMLFormElement>) => void;
