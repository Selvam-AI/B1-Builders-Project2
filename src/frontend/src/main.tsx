import React, { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import { LogOut } from "lucide-react";
import { AdminDashboard } from "./components/AdminDashboard";
import { AuthPanel } from "./components/AuthPanel";
import { BroadcastTheater } from "./components/BroadcastTheater";
import { MemberDashboard } from "./components/MemberDashboard";
import { API_BASE, ROLE_KEY, TOKEN_KEY } from "./config";
import { debugLog, setFrontendDebugEnabled } from "./debug";
import type {
  ApiStatus,
  BroadcastSession,
  FeedbackSummary,
  Mode,
  Occupancy,
  Reservation,
  Role,
  TimeSlot,
  TokenResponse,
  UserRead,
  VideoCacheEntry,
  VideoSession,
  WorkoutCategory,
} from "./types";
import { demoSlotId, isAuthFailure, isSlotCurrentlyActive, labelForCategory, labelForSlot, videoDebugInfo } from "./utils";
import "./styles.css";

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [role, setRole] = useState<Role | "">(
    () => (localStorage.getItem(ROLE_KEY) as Role | null) || "",
  );
  const [user, setUser] = useState<UserRead | null>(null);
  const [mode, setMode] = useState<Mode>("login");
  const [message, setMessage] = useState("Ready");
  const [sessionStatus, setSessionStatus] = useState("");
  const [busy, setBusy] = useState(false);

  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [categories, setCategories] = useState<WorkoutCategory[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [videos, setVideos] = useState<VideoSession[]>([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [occupancy, setOccupancy] = useState<Occupancy[]>([]);
  const [feedbackSummary, setFeedbackSummary] = useState<FeedbackSummary[]>([]);
  const [adminUsers, setAdminUsers] = useState<UserRead[]>([]);
  const [videoCache, setVideoCache] = useState<VideoCacheEntry[]>([]);
  const [activeBroadcast, setActiveBroadcast] = useState<VideoSession | null>(null);
  const [broadcastCountdown, setBroadcastCountdown] = useState<number | null>(null);
  const [broadcastPlaying, setBroadcastPlaying] = useState(false);
  const [broadcastMinimized, setBroadcastMinimized] = useState(false);
  const [broadcastMuted, setBroadcastMuted] = useState(true);
  const [broadcastSession, setBroadcastSession] = useState<BroadcastSession | null>(null);
  const [feedbackByVideo, setFeedbackByVideo] = useState<Record<number, "like" | "dislike">>({});
  const replacementAttemptsRef = useRef(0);
  const playbackConfirmedRef = useRef<Record<number, string>>({});

  const authHeaders = useMemo<Record<string, string>>(
    () => {
      const headers: Record<string, string> = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      return headers;
    },
    [token],
  );

  useEffect(() => {
    void loadDebugConfig();
  }, []);

  useEffect(() => {
    if (token) {
      debugLog("Existing token found. Refreshing dashboard.", { role: role || "member" });
      void refreshApp(token, role || "member");
    }
  }, []);

  useEffect(() => {
    if (broadcastCountdown === null) return;

    if (broadcastCountdown <= 0) {
      debugLog("Broadcast countdown completed. Autoplay requested.", {
        muted: broadcastMuted,
        video: activeBroadcast ? videoDebugInfo(activeBroadcast) : null,
      });
      setBroadcastCountdown(null);
      setBroadcastPlaying(true);
      return;
    }

    debugLog("Broadcast countdown tick.", { count: broadcastCountdown });
    const timer = window.setTimeout(() => {
      setBroadcastCountdown((current) => (current === null ? null : current - 1));
    }, 1000);

    return () => window.clearTimeout(timer);
  }, [broadcastCountdown, broadcastMuted, activeBroadcast]);

  useEffect(() => {
    if (!activeBroadcast || !token) return;

    const syncBroadcast = async () => {
      try {
        const session = await api<BroadcastSession>(
          `/api/broadcast-sessions/${activeBroadcast.id}`,
        );
        setBroadcastSession(session);
        debugLog("Broadcast sync refreshed.", session);
      } catch (error) {
        debugLog("Broadcast sync failed.", error instanceof Error ? error.message : error);
      }
    };

    const timer = window.setInterval(() => {
      void syncBroadcast();
    }, 10000);

    return () => window.clearInterval(timer);
  }, [activeBroadcast?.id, token]);

  async function api<T>(path: string, options: RequestInit = {}, activeToken = token): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(activeToken ? { Authorization: `Bearer ${activeToken}` } : {}),
        ...options.headers,
      },
    });

    if (!response.ok) {
      let detail = `Request failed with status ${response.status}`;
      try {
        const body = await response.json();
        detail = body.detail || detail;
      } catch {
        // Keep the HTTP fallback detail.
      }
      throw new Error(Array.isArray(detail) ? "Please check the form values." : detail);
    }

    if (response.status === 204) {
      return undefined as T;
    }
    return response.json() as Promise<T>;
  }

  async function loadDebugConfig() {
    try {
      const status = await api<ApiStatus>("/api/status", {}, "");
      const nextDebugEnabled =
        status.debug_enabled ||
        import.meta.env.VITE_DEBUG === "true" ||
        localStorage.getItem("fithub_debug") === "true";
      setFrontendDebugEnabled(nextDebugEnabled);
      debugLog("Debug configuration loaded.", { frontendDebugEnabled: nextDebugEnabled, apiDebug: status.debug_enabled });
    } catch {
      setFrontendDebugEnabled(
        import.meta.env.VITE_DEBUG === "true" || localStorage.getItem("fithub_debug") === "true",
      );
    }
  }

  async function refreshApp(activeToken = token, activeRole = role) {
    setBusy(true);
    debugLog("Refreshing app data.", { activeRole });
    try {
      const currentUser = await api<UserRead>("/api/auth/me", {}, activeToken);
      setUser(currentUser);
      if (activeRole === "admin" || currentUser.role === "admin") {
        const [adminOccupancy, summaries, users, cacheEntries] = await Promise.all([
          api<Occupancy[]>("/api/admin/occupancy", {}, activeToken),
          api<FeedbackSummary[]>("/api/admin/feedback-summary", {}, activeToken),
          api<UserRead[]>("/api/admin/users", {}, activeToken),
          api<VideoCacheEntry[]>("/api/admin/video-cache", {}, activeToken),
        ]);
        setOccupancy(adminOccupancy);
        setFeedbackSummary(summaries);
        setAdminUsers(users);
        setVideoCache(cacheEntries);
        debugLog("Admin dashboard data loaded.", {
          occupancyRows: adminOccupancy.length,
          feedbackSummaryRows: summaries.length,
          userRows: users.length,
          videoCacheRows: cacheEntries.length,
        });
      } else {
        const [nextSlots, nextCategories, nextReservations, nextVideos] = await Promise.all([
          api<TimeSlot[]>("/api/time-slots", {}, activeToken),
          api<WorkoutCategory[]>("/api/workout-categories", {}, activeToken),
          api<Reservation[]>("/api/reservations/me", {}, activeToken),
          api<VideoSession[]>("/api/video-sessions", {}, activeToken),
        ]);
        setSlots(nextSlots);
        setCategories(nextCategories);
        setReservations(nextReservations);
        setVideos(nextVideos);
        debugLog("Member dashboard data loaded.", {
          slots: nextSlots.length,
          categories: nextCategories.length,
          reservations: nextReservations.length,
          videos: nextVideos.map(videoDebugInfo),
        });
        setSelectedSlot((current) => current || String(nextSlots[0]?.id || ""));
        setSelectedCategory((current) => current || String(nextCategories[0]?.id || ""));
      }
      setMessage("Dashboard synced");
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Unable to refresh dashboard";
      debugLog("Refresh failed.", detail);
      if (isAuthFailure(detail)) {
        clearSession("Session expired. Please sign in again.");
      } else {
        setMessage(detail);
      }
    } finally {
      setBusy(false);
    }
  }

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") || "");
    const password = String(form.get("password") || "");
    const name = String(form.get("name") || "");
    setBusy(true);

    try {
      const payload =
        mode === "register"
          ? { name, email, password, age: Number(form.get("age") || 0) || undefined }
          : { email, password };
      const endpoint = mode === "register" ? "/api/auth/register" : "/api/auth/login";
      const auth = await api<TokenResponse>(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      localStorage.setItem(TOKEN_KEY, auth.access_token);
      localStorage.setItem(ROLE_KEY, auth.role);
      setToken(auth.access_token);
      setRole(auth.role);
      debugLog("Authentication succeeded.", { mode, role: auth.role });
      setMessage(mode === "register" ? "Member account created" : "Signed in");
      await refreshApp(auth.access_token, auth.role);
    } catch (error) {
      debugLog("Authentication failed.", error instanceof Error ? error.message : error);
      setMessage(error instanceof Error ? error.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  async function reserveSlot(useDemoSlot = false) {
    if (!selectedSlot || !selectedCategory) return;
    setBusy(true);
    try {
      const slotId = useDemoSlot ? demoSlotId(slots) : Number(selectedSlot);
      const workoutCategoryId = Number(selectedCategory);
      debugLog("Reservation requested.", {
        useDemoSlot,
        selectedSlot,
        resolvedSlotId: slotId,
        workoutCategoryId,
      });
      if (!slotId) {
        throw new Error("No available demo slot found.");
      }
      setSessionStatus(
        useDemoSlot
          ? "Demo session selected. Looking for a playable workout video."
          : "Reservation selected.",
      );
      const reservation = await api<Reservation>("/api/reservations", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          time_slot_id: slotId,
          workout_category_id: workoutCategoryId,
        }),
      });
      debugLog("Reservation created or updated.", { slotId, workoutCategoryId, reservation });

      if (!useDemoSlot && !isSlotCurrentlyActive(slots, slotId)) {
        setActiveBroadcast(null);
        setBroadcastSession(null);
        setBroadcastPlaying(false);
        setBroadcastCountdown(null);
        setBroadcastMinimized(false);
        setSessionStatus(
          `${labelForSlot(slots, slotId)} reserved for ${labelForCategory(
            categories,
            workoutCategoryId,
          )}. Broadcast will be prepared when the slot time arrives.`,
        );
        setMessage("Reservation confirmed");
        await refreshApp();
        return;
      }

      setSessionStatus("Checking whether this session is already in progress.");
      const ongoingBroadcast = await findOngoingBroadcast(slotId, workoutCategoryId);
      if (ongoingBroadcast) {
        setSessionStatus("Session has already begun. Joining the ongoing broadcast.");
        await beginBroadcast(ongoingBroadcast.video);
        setMessage("Joined ongoing broadcast");
        await refreshApp();
        return;
      }

      setSessionStatus("Searching for an embeddable workout video. This can take a moment.");
      const video = await api<VideoSession>("/api/video-sessions/recommend", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          time_slot_id: slotId,
          workout_category_id: workoutCategoryId,
        }),
      });
      debugLog("Broadcast recommendation received.", videoDebugInfo(video));
      setSessionStatus(
        `${video.provider} video ready: ${video.title || "Workout broadcast"}. Opening broadcast player.`,
      );
      if (useDemoSlot || isSlotCurrentlyActive(slots, slotId)) {
        await beginBroadcast(video);
      }
      debugLog("Reservation flow completed. Backend created or reused video recommendation.", {
        slotId,
        workoutCategoryId,
      });
      setMessage(useDemoSlot ? "Demo broadcast is ready" : "Reservation confirmed and workout video prepared");
      await refreshApp();
    } catch (error) {
      debugLog("Reservation failed.", error instanceof Error ? error.message : error);
      const detail = error instanceof Error ? error.message : "Reservation failed";
      setSessionStatus(detail);
      setMessage(detail);
    } finally {
      setBusy(false);
    }
  }

  async function findOngoingBroadcast(timeSlotId: number, workoutCategoryId: number) {
    const latestVideos = await api<VideoSession[]>("/api/video-sessions");
    const candidates = latestVideos.filter(
      (video) =>
        video.time_slot_id === timeSlotId &&
        video.workout_category_id === workoutCategoryId,
    );

    for (const video of candidates) {
      try {
        const session = await api<BroadcastSession>(`/api/broadcast-sessions/${video.id}`);
        if (session.status === "active") {
          return { video };
        }
      } catch {
        // No active broadcast for this video; continue checking candidates.
      }
    }
    return null;
  }

  async function beginBroadcast(video: VideoSession) {
    debugLog("Broadcast theater opening.", videoDebugInfo(video));
    const session = await api<BroadcastSession>("/api/broadcast-sessions/start", {
      method: "POST",
      headers: authHeaders,
      body: JSON.stringify({ video_session_id: video.id }),
    });
    debugLog("Shared broadcast session joined.", session);
    setActiveBroadcast(video);
    setBroadcastSession(session);
    setBroadcastMinimized(false);
    setBroadcastMuted(true);
    setBroadcastPlaying(false);
    setBroadcastCountdown(3);
    replacementAttemptsRef.current = 0;
    setSessionStatus(
      `Broadcast synced. ${session.participant_count} participant(s), starting at ${session.playback_offset_seconds}s.`,
    );
  }

  async function handlePlaybackFailure(reason: string) {
    if (!activeBroadcast) return;
    if (replacementAttemptsRef.current >= 2) {
      setSessionStatus("Video could not start after replacement attempts. Please refresh and try again.");
      debugLog("Playback replacement stopped after max attempts.", {
        reason,
        video: videoDebugInfo(activeBroadcast),
      });
      return;
    }

    replacementAttemptsRef.current += 1;
    setSessionStatus("Video did not start. Asking the recommender for another playable video.");
    debugLog("Playback failure detected. Requesting replacement video.", {
      reason,
      attempt: replacementAttemptsRef.current,
      video: videoDebugInfo(activeBroadcast),
    });

    try {
      const updated = await api<VideoSession>(`/api/video-sessions/${activeBroadcast.id}/replace`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({
          failed_video_id: activeBroadcast.youtube_video_id,
          reason,
        }),
      });
      setActiveBroadcast(updated);
      setVideos((current) => current.map((video) => (video.id === updated.id ? updated : video)));
      setBroadcastPlaying(true);
      setBroadcastCountdown(null);
      setSessionStatus(
        `Replacement video loaded: ${updated.title || "Workout broadcast"}. Checking playback now.`,
      );
      debugLog("Replacement video received.", videoDebugInfo(updated));
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Unable to replace video";
      setSessionStatus(detail);
      debugLog("Replacement video request failed.", detail);
    }
  }

  async function handlePlaybackConfirmed(video: VideoSession) {
    if (playbackConfirmedRef.current[video.id] === video.youtube_video_id) return;
    playbackConfirmedRef.current[video.id] = video.youtube_video_id || "";
    replacementAttemptsRef.current = 0;
    setSessionStatus("Video playback confirmed. Broadcast is running.");
    debugLog("Playback confirmed by YouTube IFrame Player API.", videoDebugInfo(video));

    try {
      const updated = await api<VideoSession>(`/api/video-sessions/${video.id}/playable`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ youtube_video_id: video.youtube_video_id }),
      });
      setActiveBroadcast((current) => (current?.id === updated.id ? updated : current));
      setVideos((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    } catch (error) {
      debugLog("Playback confirmation save failed.", error instanceof Error ? error.message : error);
    }
  }

  async function cancelReservation(id: number) {
    setBusy(true);
    try {
      await api<void>(`/api/reservations/${id}`, { method: "DELETE", headers: authHeaders });
      debugLog("Reservation cancelled.", { reservationId: id });
      setReservations((current) => current.filter((reservation) => reservation.id !== id));
      setActiveBroadcast(null);
      setBroadcastSession(null);
      setBroadcastPlaying(false);
      setBroadcastCountdown(null);
      setBroadcastMinimized(false);
      setSessionStatus("Reservation cancelled.");
      setMessage("Reservation cancelled");
      await refreshApp();
    } catch (error) {
      debugLog("Cancellation failed.", error instanceof Error ? error.message : error);
      const detail = error instanceof Error ? error.message : "Cancellation failed";
      setSessionStatus(detail);
      setMessage(detail);
    } finally {
      setBusy(false);
    }
  }

  async function sendFeedback(videoSessionId: number, value: "like" | "dislike") {
    setBusy(true);
    try {
      await api("/api/feedback", {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ video_session_id: videoSessionId, value }),
      });
      debugLog("Feedback saved.", { videoSessionId, value });
      setFeedbackByVideo((current) => ({ ...current, [videoSessionId]: value }));
      setMessage(value === "like" ? "Feedback saved: liked" : "Feedback saved: disliked");
    } catch (error) {
      debugLog("Feedback failed.", error instanceof Error ? error.message : error);
      setMessage(error instanceof Error ? error.message : "Feedback failed");
    } finally {
      setBusy(false);
    }
  }

  async function refreshBroadcasts() {
    setBusy(true);
    try {
      debugLog("Broadcast refresh requested.", {
        reservations: reservations.map((reservation) => ({
          timeSlotId: reservation.time_slot_id,
          workoutCategoryId: reservation.workout_category_id,
        })),
      });
      await Promise.all(
        reservations.map((reservation) =>
          api<VideoSession>("/api/video-sessions/recommend", {
            method: "POST",
            headers: authHeaders,
            body: JSON.stringify({
              time_slot_id: reservation.time_slot_id,
              workout_category_id: reservation.workout_category_id,
            }),
          }),
        ),
      );
      debugLog("Broadcast recommendation refresh completed.");
      setMessage("Workout broadcast refreshed");
      await refreshApp();
    } catch (error) {
      debugLog("Broadcast refresh failed.", error instanceof Error ? error.message : error);
      setMessage(error instanceof Error ? error.message : "Broadcast refresh failed");
    } finally {
      setBusy(false);
    }
  }

  function signOut() {
    clearSession("Signed out");
  }

  function clearSession(nextMessage: string) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    setToken("");
    setRole("");
    setUser(null);
    setReservations([]);
    setVideos([]);
    setAdminUsers([]);
    setActiveBroadcast(null);
    setBroadcastSession(null);
    setBroadcastPlaying(false);
    setBroadcastCountdown(null);
    setBroadcastMinimized(false);
    setFeedbackByVideo({});
    setSessionStatus("");
    setMessage(nextMessage);
  }

  async function exitBroadcastSession() {
    if (!activeBroadcast) return;
    await api<BroadcastSession>(`/api/broadcast-sessions/${activeBroadcast.id}/exit`, {
      method: "POST",
      headers: authHeaders,
    });
    setActiveBroadcast(null);
    setBroadcastSession(null);
    setBroadcastPlaying(false);
    setBroadcastCountdown(null);
    setBroadcastMinimized(false);
    setSessionStatus("Exited broadcast session. You can start the demo slot again after the session is empty.");
    setMessage("Exited broadcast session");
  }

  function scrollToPanel(id: string) {
    const target = document.getElementById(id) || document.getElementById("broadcast");
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function updateUserStatus(userId: number, isActive: boolean) {
    setBusy(true);
    try {
      const updated = await api<UserRead>(`/api/admin/users/${userId}/status`, {
        method: "PATCH",
        headers: authHeaders,
        body: JSON.stringify({ is_active: isActive }),
      });
      setAdminUsers((current) => current.map((user) => (user.id === userId ? updated : user)));
      setMessage(isActive ? "Member account reactivated" : "Member account paused");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to update member account");
    } finally {
      setBusy(false);
    }
  }

  async function deleteUser(userId: number) {
    const confirmed = window.confirm("Delete this member account and its reservations/feedback?");
    if (!confirmed) return;

    setBusy(true);
    try {
      await api<void>(`/api/admin/users/${userId}`, {
        method: "DELETE",
        headers: authHeaders,
      });
      setAdminUsers((current) => current.filter((user) => user.id !== userId));
      setMessage("Member account deleted");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to delete member account");
    } finally {
      setBusy(false);
    }
  }

  async function runVideoCurator() {
    setBusy(true);
    try {
      const result = await api<{ created_pending: number; categories: number }>(
        "/api/admin/video-cache/curate",
        {
          method: "POST",
          headers: authHeaders,
        },
      );
      setMessage(`Curator checked ${result.categories} categories`);
      await refreshApp();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to run video curator");
    } finally {
      setBusy(false);
    }
  }

  const activeBroadcastList = activeBroadcast ? [activeBroadcast] : [];

  return (
    <main className="app-shell">
      <section className="hero">
        <div className="hero__shade" />
        <nav className="nav" aria-label="Main navigation">
          <strong>FitHub AI</strong>
          <button type="button" onClick={() => scrollToPanel("slots")}>
            Slots
          </button>
          <button type="button" onClick={() => scrollToPanel("broadcast")}>
            Broadcast
          </button>
          <button type="button" onClick={() => scrollToPanel("feedback")}>
            Feedback
          </button>
          {user ? (
            <button className="icon-button" type="button" onClick={signOut} title="Sign out">
              <LogOut size={18} />
            </button>
          ) : null}
        </nav>
        <div className={!token ? "hero__layout" : "hero__layout hero__layout--solo"}>
          <div className="hero__content">
            <p className="eyebrow">AI-assisted social workout club</p>
            <h1>Reserve. Move. Improve.</h1>
            <p>
              A single-page dashboard for members to book workout slots, receive curated workout
              sessions, and send feedback that improves future recommendations.
            </p>
            <div className="hero__actions" aria-live="polite">
              <span className={busy ? "status status--busy" : "status"}>{message}</span>
              {user ? <span className="status status--light">{user.name || user.email || user.role}</span> : null}
            </div>
          </div>
          {!token ? (
            <AuthPanel
              mode={mode}
              setMode={setMode}
              submitAuth={submitAuth}
              busy={busy}
            />
          ) : null}
        </div>
      </section>

      {token && role === "admin" ? (
        <AdminDashboard
          user={user}
          occupancy={occupancy}
          feedbackSummary={feedbackSummary}
          users={adminUsers}
          videoCache={videoCache}
          updateUserStatus={updateUserStatus}
          deleteUser={deleteUser}
          runVideoCurator={runVideoCurator}
          refresh={() => refreshApp()}
          busy={busy}
        />
      ) : token ? (
        <MemberDashboard
          user={user}
          slots={slots}
          categories={categories}
          reservations={reservations}
          activeVideos={activeBroadcastList}
          selectedSlot={selectedSlot}
          selectedCategory={selectedCategory}
          sessionStatus={sessionStatus}
          setSelectedSlot={setSelectedSlot}
          setSelectedCategory={setSelectedCategory}
          reserveSlot={reserveSlot}
          cancelReservation={cancelReservation}
          sendFeedback={sendFeedback}
          feedbackByVideo={feedbackByVideo}
          refresh={() => refreshApp()}
          busy={busy}
        />
      ) : null}

      {activeBroadcast && role !== "admin" ? (
        <BroadcastTheater
          video={activeBroadcast}
          countdown={broadcastCountdown}
          playing={broadcastPlaying}
          startAtSeconds={broadcastSession?.playback_offset_seconds || 0}
          syncOffsetSeconds={broadcastSession?.playback_offset_seconds || 0}
          participantCount={broadcastSession?.participant_count || 1}
          muted={broadcastMuted}
          setMuted={setBroadcastMuted}
          minimized={broadcastMinimized}
          minimize={() => setBroadcastMinimized(true)}
          resume={() => setBroadcastMinimized(false)}
          exitSession={exitBroadcastSession}
          onPlaybackFailure={handlePlaybackFailure}
          onPlaybackConfirmed={handlePlaybackConfirmed}
        />
      ) : null}
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
