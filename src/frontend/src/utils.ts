import type { TimeSlot, VideoSession, WorkoutCategory } from "./types";

export function playableYouTubeVideoId(video: VideoSession) {
  const fallbackByCategory: Record<number, string> = {
    1: "HRvFxrFGqA4",
    2: "YyBcMVQylas",
    3: "VWj8ZxCxrYk",
  };
  return video.youtube_video_id && !video.youtube_video_id.startsWith("mock-")
    ? video.youtube_video_id
    : fallbackByCategory[video.workout_category_id];
}

export function videoDebugInfo(video: VideoSession) {
  return {
    id: video.id,
    provider: video.provider,
    status: video.status,
    youtubeVideoId: video.youtube_video_id,
    isMockId: Boolean(video.youtube_video_id?.startsWith("mock-")),
    youtubeUrl: video.youtube_url,
    title: video.title,
    timeSlotId: video.time_slot_id,
    workoutCategoryId: video.workout_category_id,
  };
}

export function demoSlotId(slots: TimeSlot[]) {
  return slots.find((slot) => slot.is_demo)?.id || 0;
}

export function isSlotCurrentlyActive(slots: TimeSlot[], id: number) {
  const slot = slots.find((item) => item.id === id);
  if (!slot) return false;
  if (slot.is_demo) return true;
  const currentHour = new Date().getHours();
  return currentHour >= slot.start_hour && currentHour < slot.end_hour;
}

export function labelForSlot(slots: TimeSlot[], id: number) {
  return slots.find((slot) => slot.id === id)?.label || `Slot ${id}`;
}

export function labelForCategory(categories: WorkoutCategory[], id: number) {
  return categories.find((category) => category.id === id)?.name || `Category ${id}`;
}

export function isAuthFailure(detail: string) {
  const normalized = detail.toLowerCase();
  return (
    normalized.includes("401") ||
    normalized.includes("not authenticated") ||
    normalized.includes("could not validate credentials") ||
    normalized.includes("invalid token") ||
    normalized.includes("session expired")
  );
}
