import { Activity, CalendarClock, Heart, Trash2, UserPlus } from "lucide-react";
import type { FeedbackSummary, Occupancy, UserRead, VideoCacheEntry } from "../types";

type AdminDashboardProps = {
  user: UserRead | null;
  occupancy: Occupancy[];
  feedbackSummary: FeedbackSummary[];
  users: UserRead[];
  videoCache: VideoCacheEntry[];
  updateUserStatus: (userId: number, isActive: boolean) => void;
  deleteUser: (userId: number) => void;
  runVideoCurator: () => void;
  refresh: () => void;
  busy: boolean;
};

export function AdminDashboard({
  user,
  occupancy,
  feedbackSummary,
  users,
  videoCache,
  updateUserStatus,
  deleteUser,
  runVideoCurator,
  refresh,
  busy,
}: AdminDashboardProps) {
  return (
    <section className="workspace">
      <div className="dashboard-title-panel">
        <div>
          <p className="eyebrow">Admin dashboard</p>
          <h2>{user?.email || "Admin"}</h2>
        </div>
      </div>
      <div className="workspace__grid">
        <section className="tool-panel tool-panel--wide">
          <div className="panel-title">
            <UserPlus size={20} />
            <h3>Member accounts</h3>
            <button className="ghost-button" onClick={refresh} disabled={busy}>
              Refresh
            </button>
          </div>
          {users.length === 0 ? (
            <p className="muted">No member accounts yet.</p>
          ) : (
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((member) => (
                    <tr key={member.id}>
                      <td>{member.name}</td>
                      <td>{member.email || "No email"}</td>
                      <td>{member.is_active ? "Active" : "Paused"}</td>
                      <td>
                        <div className="table-actions">
                          <button
                            className={member.is_active ? "ghost-button danger-button" : "ghost-button"}
                            type="button"
                            disabled={busy}
                            onClick={() => updateUserStatus(member.id, !member.is_active)}
                          >
                            {member.is_active ? "Pause" : "Reactivate"}
                          </button>
                          <button
                            className="ghost-button danger-button"
                            type="button"
                            disabled={busy}
                            onClick={() => deleteUser(member.id)}
                          >
                            <Trash2 size={16} />
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="tool-panel tool-panel--wide">
          <div className="panel-title">
            <Activity size={20} />
            <h3>Video cache</h3>
            <div className="button-row">
              <button className="ghost-button blue-button" onClick={runVideoCurator} disabled={busy}>
                Run curator
              </button>
              <button className="ghost-button" onClick={refresh} disabled={busy}>
                Refresh
              </button>
            </div>
          </div>
          {videoCache.length === 0 ? (
            <p className="muted">No confirmed or pending cache entries yet.</p>
          ) : (
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Video</th>
                    <th>Status</th>
                    <th>Plays</th>
                  </tr>
                </thead>
                <tbody>
                  {videoCache.map((entry) => (
                    <tr key={entry.id}>
                      <td>{entry.workout_category_id}</td>
                      <td>{entry.title}</td>
                      <td>{entry.status}</td>
                      <td>{entry.play_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="tool-panel tool-panel--wide">
          <div className="panel-title">
            <CalendarClock size={20} />
            <h3>Slot occupancy</h3>
          </div>
          <div className="table-shell">
            <table>
              <thead>
                <tr>
                  <th>Slot</th>
                  <th>Reserved</th>
                  <th>Remaining</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {occupancy.map((slot) => (
                  <tr key={slot.time_slot_id}>
                    <td>{slot.label}</td>
                    <td>
                      {slot.current_occupancy}/{slot.capacity}
                    </td>
                    <td>{slot.remaining_capacity}</td>
                    <td>{slot.is_full ? "Full" : "Open"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="tool-panel">
          <div className="panel-title">
            <Heart size={20} />
            <h3>Feedback summary</h3>
          </div>
          {feedbackSummary.length === 0 ? (
            <p className="muted">No feedback yet.</p>
          ) : (
            <ul className="stack-list">
              {feedbackSummary.map((item) => (
                <li key={item.video_session_id}>
                  <span>
                    {item.title || "Video"} · {item.likes} like / {item.dislikes} dislike
                  </span>
                  <strong>{item.score}</strong>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </section>
  );
}
