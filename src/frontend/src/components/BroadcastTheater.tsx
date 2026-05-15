import { DoorOpen, Minimize2, Play, Volume2, VolumeX } from "lucide-react";
import type { VideoSession } from "../types";
import { VideoPlayer } from "./VideoPlayer";

type BroadcastTheaterProps = {
  video: VideoSession;
  countdown: number | null;
  playing: boolean;
  startAtSeconds: number;
  syncOffsetSeconds: number;
  participantCount: number;
  muted: boolean;
  setMuted: (value: boolean) => void;
  minimized: boolean;
  minimize: () => void;
  resume: () => void;
  exitSession: () => void;
  onPlaybackFailure: (reason: string) => void;
  onPlaybackConfirmed: (video: VideoSession) => void;
};

export function BroadcastTheater({
  video,
  countdown,
  playing,
  startAtSeconds,
  syncOffsetSeconds,
  participantCount,
  muted,
  setMuted,
  minimized,
  minimize,
  resume,
  exitSession,
  onPlaybackFailure,
  onPlaybackConfirmed,
}: BroadcastTheaterProps) {
  const isCountingDown = countdown !== null;
  const toggleAudio = () => {
    const nextMuted = !muted;
    setMuted(nextMuted);
    window.dispatchEvent(
      new CustomEvent("fithub:broadcast-audio", { detail: { muted: nextMuted } }),
    );
  };

  return (
    <section
      className={minimized ? "broadcast-theater broadcast-theater--minimized" : "broadcast-theater"}
      aria-label="Workout broadcast"
    >
      <div className="broadcast-theater__bar">
        <div>
          <p className="eyebrow">Live broadcast</p>
          <h2>{video.title || "Workout session"}</h2>
          <p className="broadcast-meta">
            Synced at {startAtSeconds}s · {participantCount} participant(s)
          </p>
        </div>
        <div className="broadcast-theater__controls">
          <button className="icon-text" type="button" onClick={toggleAudio}>
            {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
            {muted ? "Unmute" : "Mute"}
          </button>
          <button className="icon-text" type="button" onClick={minimize}>
            <Minimize2 size={18} />
            Minimize
          </button>
          <button className="icon-text icon-text--danger" type="button" onClick={exitSession}>
            <DoorOpen size={18} />
            Exit session
          </button>
        </div>
      </div>
      <div className="broadcast-stage">
        {isCountingDown ? (
          <div className="broadcast-slate" aria-live="assertive">
            <p>The workout session will begin now</p>
            <strong>{countdown}</strong>
          </div>
        ) : (
          <VideoPlayer
            video={video}
            autoPlay={playing}
            muted={muted}
            controls={false}
            startAtSeconds={startAtSeconds}
            syncOffsetSeconds={syncOffsetSeconds}
            onPlaybackFailure={onPlaybackFailure}
            onPlaybackConfirmed={() => onPlaybackConfirmed(video)}
          />
        )}
      </div>
      {minimized ? (
        <button className="broadcast-chip" type="button" onClick={resume}>
          <Play size={17} />
          Resume broadcast
        </button>
      ) : null}
    </section>
  );
}
