import { Activity, CalendarClock, Dumbbell, Heart, ThumbsDown, ThumbsUp } from "lucide-react";
import type { Reservation, TimeSlot, UserRead, VideoSession, WorkoutCategory } from "../types";
import { labelForCategory, labelForSlot } from "../utils";

type MemberDashboardProps = {
  user: UserRead | null;
  slots: TimeSlot[];
  categories: WorkoutCategory[];
  reservations: Reservation[];
  activeVideos: VideoSession[];
  selectedSlot: string;
  selectedCategory: string;
  sessionStatus: string;
  setSelectedSlot: (value: string) => void;
  setSelectedCategory: (value: string) => void;
  reserveSlot: (useDemoSlot?: boolean) => void;
  cancelReservation: (id: number) => void;
  sendFeedback: (videoSessionId: number, value: "like" | "dislike") => void;
  feedbackByVideo: Record<number, "like" | "dislike">;
  refresh: () => void;
  busy: boolean;
};

export function MemberDashboard({
  user,
  slots,
  categories,
  reservations,
  activeVideos,
  selectedSlot,
  selectedCategory,
  sessionStatus,
  setSelectedSlot,
  setSelectedCategory,
  reserveSlot,
  cancelReservation,
  sendFeedback,
  feedbackByVideo,
  refresh,
  busy,
}: MemberDashboardProps) {
  return (
    <section className="workspace">
      <div className="dashboard-title-panel">
        <p className="eyebrow">Member dashboard</p>
        <h2>{user?.name || "Member"}</h2>
      </div>
      <div className="workspace__grid">
        <section id="slots" className="tool-panel">
          <div className="panel-title">
            <CalendarClock size={20} />
            <h3>Reserve a workout</h3>
          </div>
          <label>
            Time slot
            <select value={selectedSlot} onChange={(event) => setSelectedSlot(event.target.value)}>
              <option value="demo-now">Demo time slot (Starts now)</option>
              {slots.filter((slot) => !slot.is_demo).map((slot) => (
                <option key={slot.id} value={slot.id}>
                  {slot.label} - {slot.current_occupancy}/{slot.capacity}
                </option>
              ))}
            </select>
          </label>
          <label>
            Workout category
            <select
              value={selectedCategory}
              onChange={(event) => setSelectedCategory(event.target.value)}
            >
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <button
            className="primary-button"
            onClick={() => reserveSlot(selectedSlot === "demo-now")}
            disabled={busy}
          >
            <Dumbbell size={18} />
            Reserve slot
          </button>
        </section>

        <section className="tool-panel">
          <div className="panel-title">
            <Activity size={20} />
            <h3>Your reservations</h3>
          </div>
          {reservations.length === 0 ? (
            <p className="muted">No reservations yet.</p>
          ) : (
            <ul className="stack-list">
              {reservations.map((reservation) => (
                <li key={reservation.id}>
                  <span>
                    {labelForSlot(slots, reservation.time_slot_id)} ·{" "}
                    {labelForCategory(categories, reservation.workout_category_id)}
                  </span>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => cancelReservation(reservation.id)}
                  >
                    Cancel
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="tool-panel tool-panel--wide session-panel" aria-live="polite">
          <div className="panel-title">
            <Activity size={20} />
            <h3>Session status</h3>
          </div>
          <p>{sessionStatus}</p>
        </section>

        <section id="broadcast" className="tool-panel tool-panel--wide">
          <div className="panel-title">
            <Heart size={20} />
            <h3>Workout broadcast</h3>
            <button className="ghost-button" onClick={refresh} disabled={busy}>
              Refresh
            </button>
          </div>
          {activeVideos.length === 0 ? (
            <p className="muted">No active broadcast loaded. Select a time slot to prepare the session.</p>
          ) : (
            <div className="video-grid">
              {activeVideos.map((video) => (
                <article key={video.id} className="video-item">
                  <span className="status">{video.provider}</span>
                  <h4>{video.title || "Workout video"}</h4>
                  <p>{video.safety_notes}</p>
                  <p className="muted">{video.agent_summary}</p>
                  <div className="button-row">
                    <button
                      onClick={() => sendFeedback(video.id, "like")}
                      className={feedbackByVideo[video.id] === "like" ? "icon-text icon-text--liked" : "icon-text"}
                    >
                      <ThumbsUp size={17} />
                      Like
                    </button>
                    <button
                      onClick={() => sendFeedback(video.id, "dislike")}
                      className={
                        feedbackByVideo[video.id] === "dislike"
                          ? "icon-text icon-text--disliked"
                          : "icon-text"
                      }
                    >
                      <ThumbsDown size={17} />
                      Dislike
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </section>
  );
}
