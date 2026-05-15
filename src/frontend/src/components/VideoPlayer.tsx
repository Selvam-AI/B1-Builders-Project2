import { useEffect, useMemo, useRef, useState } from "react";
import { Play } from "lucide-react";
import { debugLog } from "../debug";
import type { VideoSession } from "../types";
import { videoDebugInfo, playableYouTubeVideoId } from "../utils";
import { loadYouTubeIframeApi, type YouTubePlayer } from "../youtube";

type VideoPlayerProps = {
  video: VideoSession;
  autoPlay?: boolean;
  muted?: boolean;
  controls?: boolean;
  startAtSeconds?: number;
  syncOffsetSeconds?: number;
  onPlaybackFailure: (reason: string) => void;
  onPlaybackConfirmed: () => void;
};

export function VideoPlayer({
  video,
  autoPlay = false,
  muted = true,
  controls = false,
  startAtSeconds = 0,
  syncOffsetSeconds = 0,
  onPlaybackFailure,
  onPlaybackConfirmed,
}: VideoPlayerProps) {
  const playerRef = useRef<YouTubePlayer | null>(null);
  const healthTimerRef = useRef<number | null>(null);
  const playbackStartedRef = useRef(false);
  const failureReportedRef = useRef(false);
  const mutedRef = useRef(muted);
  const syncOffsetRef = useRef(syncOffsetSeconds);
  const onPlaybackFailureRef = useRef(onPlaybackFailure);
  const onPlaybackConfirmedRef = useRef(onPlaybackConfirmed);
  const [validationMessage, setValidationMessage] = useState("Video is buffering. Please wait.");
  const playerElementId = useRef(`youtube-player-${video.id}-${Math.random().toString(36).slice(2)}`);
  const youtubeVideoId = useMemo(() => playableYouTubeVideoId(video), [
    video.youtube_video_id,
    video.workout_category_id,
  ]);

  useEffect(() => {
    mutedRef.current = muted;
    onPlaybackFailureRef.current = onPlaybackFailure;
    onPlaybackConfirmedRef.current = onPlaybackConfirmed;
  }, [muted, onPlaybackFailure, onPlaybackConfirmed]);

  useEffect(() => {
    const player = playerRef.current;
    if (!player) return;
    if (muted) {
      player.mute();
    } else {
      player.unMute();
      player.setVolume(100);
      player.playVideo();
    }
  }, [muted]);

  useEffect(() => {
    const handleAudioToggle = (event: Event) => {
      const nextMuted = Boolean((event as CustomEvent<{ muted: boolean }>).detail?.muted);
      const player = playerRef.current;
      if (!player) return;
      if (nextMuted) {
        player.mute();
        return;
      }
      player.unMute();
      player.setVolume(100);
      player.playVideo();
      debugLog("Broadcast audio explicitly unmuted from user click.");
    };

    window.addEventListener("fithub:broadcast-audio", handleAudioToggle);
    return () => window.removeEventListener("fithub:broadcast-audio", handleAudioToggle);
  }, []);

  useEffect(() => {
    syncOffsetRef.current = syncOffsetSeconds;
    if (syncOffsetSeconds > 0) {
      playerRef.current?.seekTo(Math.floor(syncOffsetSeconds), true);
    }
  }, [syncOffsetSeconds]);

  debugLog("Rendering video player.", {
    ...videoDebugInfo(video),
    youtubeVideoId,
    autoPlay,
    muted,
    controls,
    startAtSeconds,
    syncOffsetSeconds,
  });

  useEffect(() => {
    if (!youtubeVideoId) return;
    let cancelled = false;

    setValidationMessage("Video is buffering. Please wait.");
    playbackStartedRef.current = false;
    failureReportedRef.current = false;

    const reportFailure = (reason: string) => {
      if (failureReportedRef.current) return;
      failureReportedRef.current = true;
      if (healthTimerRef.current !== null) {
        window.clearTimeout(healthTimerRef.current);
        healthTimerRef.current = null;
      }
      setValidationMessage("The selected video did not start. Finding another video.");
      onPlaybackFailureRef.current(reason);
    };

    const clearHealthTimer = () => {
      if (healthTimerRef.current !== null) {
        window.clearTimeout(healthTimerRef.current);
        healthTimerRef.current = null;
      }
    };

    loadYouTubeIframeApi()
      .then(() => {
        if (cancelled || !window.YT) return;
        playerRef.current?.destroy();
        playerRef.current = new window.YT.Player(playerElementId.current, {
          host: "https://www.youtube-nocookie.com",
          videoId: youtubeVideoId,
          playerVars: {
            autoplay: autoPlay ? 1 : 0,
            controls: controls ? 1 : 0,
            disablekb: 1,
            modestbranding: 1,
            origin: window.location.origin,
            playsinline: 1,
            rel: 0,
            start: Math.max(0, Math.floor(startAtSeconds)),
          },
          events: {
            onReady: () => {
              const player = playerRef.current;
              if (!player) return;
              if (mutedRef.current) {
                player.mute();
              } else {
                player.unMute();
                player.setVolume(100);
              }
              if (syncOffsetRef.current > 0) {
                player.seekTo(Math.floor(syncOffsetRef.current), true);
              }
              if (autoPlay) {
                player.playVideo();
              }
              healthTimerRef.current = window.setTimeout(() => {
                if (!playbackStartedRef.current) {
                  reportFailure("YouTube video did not start within 5 seconds.");
                }
              }, 5000);
            },
            onStateChange: (event: { data: number }) => {
              if (event.data === window.YT?.PlayerState?.PLAYING) {
                playbackStartedRef.current = true;
                clearHealthTimer();
                setValidationMessage("");
                onPlaybackConfirmedRef.current();
              }
            },
            onError: (event: { data: number }) => {
              reportFailure(`YouTube player error ${event.data}`);
            },
          },
        });
      })
      .catch(() => reportFailure("YouTube IFrame Player API could not be loaded."));

    return () => {
      cancelled = true;
      clearHealthTimer();
      playerRef.current?.destroy();
      playerRef.current = null;
    };
  }, [
    autoPlay,
    controls,
    startAtSeconds,
    video.id,
    youtubeVideoId,
  ]);

  if (!youtubeVideoId) {
    return (
      <div className="video-player video-player--empty">
        <Play size={28} />
        <span>Playable video pending</span>
      </div>
    );
  }

  return (
    <div className={validationMessage ? "video-player video-player--validating" : "video-player"}>
      <div id={playerElementId.current} title={video.title || "Workout video"} />
      {validationMessage ? (
        <div className="video-player__overlay" aria-live="polite">
          <Play size={28} />
          <span>{validationMessage}</span>
        </div>
      ) : null}
    </div>
  );
}
