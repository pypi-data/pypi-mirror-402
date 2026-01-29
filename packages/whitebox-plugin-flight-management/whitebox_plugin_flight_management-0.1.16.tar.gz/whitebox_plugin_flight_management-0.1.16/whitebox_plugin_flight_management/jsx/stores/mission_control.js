import { create } from "zustand";

const { createEventHandlingSlice } = Whitebox.utils;

const createFlightSessionControlSlice = (set, get) => ({
  isReady: false,
  activeFlightSession: null,
  activeKeyMoment: null,

  // During the session, we are tracking key moments separately from the flight
  // session to avoid unnecessary component rerenders when updating the list.
  // This will be used both for flying and playbacks
  sessionKeyMoments: [],

  setSessionKeyMoments: (keyMoments) => {
    const newValues = {
      sessionKeyMoments: keyMoments,
    };

    const activeKeyMoment = keyMoments.find((k) => k.ended_at === null);
    // If there is an active one, set it, tho otherwise we want null too
    newValues.activeKeyMoment = activeKeyMoment || null;

    set(newValues);
  },

  setActiveFlightSession: (session) => {
    const { enterFlightMode } = get();
    const keyMoments = session?.key_moments || [];
    const activeKeyMoment = keyMoments.find((k) => k.ended_at === null);

    set({
      activeFlightSession: session,
      isReady: true,
      sessionKeyMoments: keyMoments,
      activeKeyMoment: activeKeyMoment,
    });
    enterFlightMode(session);
  },

  setActiveKeyMoment: (keyMoment) => {
    set({
      activeKeyMoment: keyMoment,
    });
  },

  isFlightSessionActive: () => {
    const flightSession = get().activeFlightSession;
    return flightSession && flightSession.ended_at === null;
  },

  isKeyMomentActive: () => {
    const keyMoment = get().activeKeyMoment;
    return keyMoment && keyMoment.ended_at === null;
  },

  // region entry management

  startFlightSession: async (flightPlanData = {}) => {
    set({ isReady: false });

    const data = {
      type: "flight.start",
      takeoff_location: flightPlanData.takeoff_location || {},
      arrival_location: flightPlanData.arrival_location || {},
      waypoints: flightPlanData.waypoints || [],
    };
    Whitebox.sockets.send("flight", data);
  },

  endFlightSession: async () => {
    set({ isReady: false });

    const data = {
      type: "flight.end",
    };
    Whitebox.sockets.send("flight", data);
  },

  toggleFlightSession: async (flightPlanData = {}) => {
    const flightSession = get().activeFlightSession;

    if (flightSession && flightSession.ended_at === null) {
      await get().endFlightSession();
    } else {
      await get().startFlightSession(flightPlanData);
    }
  },

  // endregion entry management

  // region key moment management

  recordKeyMoment: () => {
    const data = {
      type: "flight.key_moment.record",
    };
    Whitebox.sockets.send("flight", data);
  },
  finishKeyMoment: () => {
    const data = {
      type: "flight.key_moment.finish",
    };
    Whitebox.sockets.send("flight", data);
  },

  updateKeyMoment: (keyMomentId, updates) => {
    const data = {
      type: "flight.key_moment.update",
      key_moment_id: keyMomentId,
      ...updates,
    };
    Whitebox.sockets.send("flight", data);
  },
  deleteKeyMoment: (keyMomentId) => {
    const data = {
      type: "flight.key_moment.delete",
      key_moment_id: keyMomentId,
    };
    Whitebox.sockets.send("flight", data);
  },

  // endregion key moment management
});

const createFlightManagementSlice = (set, get) => ({
  fetchState: "initial",
  flightSessions: null,

  fetchFlightSessions: async () => {
    const { api } = Whitebox;

    const url = api.getPluginProvidedPath("flight.flight-session-list");
    let data = null;

    try {
      const response = await api.client.get(url);
      data = response.data;
    } catch (e) {
      console.error("Failed to fetch flight sessions", e);
      set({ fetchState: "error" });
      return false;
    }

    set({
      flightSessions: data,
      fetchState: "loaded",
    });
    return true;
  },

  getFlightSessions: () => {
    const flightSessions = get().flightSessions;

    if (flightSessions === null) {
      return [];
    }
    return flightSessions;
  },
})

const createFlightPlaybackSlice = (set, get) => ({
  playbackFlightSession: null,
  playbackStatus: "stopped",
  playbackTimeLastSet: 0,
  playbackTimeLastSetAt: null,

  _setStopIfEnded: () => {
    // Method used to actually set stop status when the playback stops. As we
    // do not have a centralized forever-running loop that would be checking
    // this, every time an event happens that influences actual playback, we are
    // going to set a timer to check whether the playback finished at the moment
    // when we estimate it to be finished.
    //
    // In practice, that means that when you play the session, or set playback
    // time (seek), using `playbackTimeLastSet`, `playbackTimeLastSetAt` and
    // `getTotalDuration` we can know when to check the store's state. If at
    // that point the session is playing but shouldn't anymore, stop it,
    // otherwise just ignore it. This ensures that multiple timers' effects that
    // call this method do not conflict and that they can be set at any time.
    const {
      getTotalDuration,
      getPlaybackTime,
      playbackStatus,
    } = get();

    const isPlaying = playbackStatus === "playing";
    const playbackReachedEnd = getTotalDuration() === getPlaybackTime();

    if (isPlaying && playbackReachedEnd) {
      set({ playbackStatus: "stopped" });
    }
  },

  _scheduleStopWhenEnded: () => {
    const {
      getTotalDuration,
      getPlaybackTime,
      _setStopIfEnded,
    } = get();

    const remaining = (getTotalDuration() - getPlaybackTime()) * 1000;
    // Add the minimum delay on top of the actual wait time to ensure that we
    // don't end up doing a NOOP by a race condition
    const scheduleIn = remaining + 5;

    setTimeout(_setStopIfEnded, scheduleIn);
  },

  playbackPlay: () => {
    const {
      emit,
      playbackStatus,
      syncPlayers,
      _scheduleStopWhenEnded,
    } = get();

    const setters = {};
    // In case the playback was stopped before this, make sure we play all
    // videos from the top
    if (playbackStatus === "stopped") {
      setters.playbackTimeLastSet = 0;
    }

    set({
      playbackStatus: "playing",
      playbackTimeLastSetAt: new Date(),
      ...setters,
    });
    syncPlayers();

    emit("playback.play");
    _scheduleStopWhenEnded();
  },
  playbackPause: () => {
    const {
      getPlaybackTime,
      syncPlayers,
      emit,
      _emitPlaybackTime,
    } = get();

    // `playbackTimeLastSetAt` is irrelevant when paused, as it's not used until
    // playback starts again
    const playbackTime = getPlaybackTime();
    set({
      playbackStatus: "paused",
      playbackTimeLastSet: playbackTime,
    });
    syncPlayers();

    emit("playback.pause");
    _emitPlaybackTime(playbackTime);
  },
  playbackToggle: () => {
    const { playbackStatus } = get();

    if (playbackStatus === "playing") {
      get().playbackPause();
    } else {
      get().playbackPlay();
    }
  },

  getTotalDuration: () => {
    const playbackFlightSession = get().playbackFlightSession;
    const startedAt = new Date(playbackFlightSession.started_at);
    const endedAt = new Date(playbackFlightSession.ended_at);
    return (endedAt.getTime() - startedAt.getTime()) / 1000;
  },

  getPlaybackTime: () => {
    // Dance with states to be able to always calculate playback time with
    // almost 100% precision
    const {
      playbackStatus,
      playbackTimeLastSet,
      playbackTimeLastSetAt,
      getTotalDuration,
    } = get();
    const totalDuration = getTotalDuration();

    if (playbackStatus === "stopped") {
      return 0;
    } else if (playbackStatus === "paused") {
      return playbackTimeLastSet;
    } else if (playbackStatus === "playing") {
      const now = new Date();
      const sinceLastSet = (now.getTime() - playbackTimeLastSetAt.getTime()) / 1000;

      const calculatedPlaybackTime = playbackTimeLastSet + sinceLastSet;

      if (calculatedPlaybackTime >= totalDuration) {
        return totalDuration;
      } else {
        return calculatedPlaybackTime;
      }
    }
  },

  _emitPlaybackTime: (time) => {
    const {
      playbackFlightSession,
      emit,
    } = get();

    const timeUnix = new Date(
        new Date(playbackFlightSession.started_at).getTime() + (time * 1000),
    );

    emit("playback.time", time, timeUnix);
  },

  setPlaybackTime: (time, unixTime = false) => {
    const {
      playbackFlightSession,
      _emitPlaybackTime,
      _scheduleStopWhenEnded,
    } = get();

    const startedAt = new Date(playbackFlightSession.started_at);
    const endedAt = new Date(playbackFlightSession.ended_at);
    const totalDuration = (endedAt.getTime() - startedAt.getTime()) / 1000;

    let timeToAssign = time;

    if (unixTime) {
      timeToAssign = (time.getTime() - startedAt.getTime()) / 1000;
    }

    const additionalSetters = {};

    if (timeToAssign < 0) {
      timeToAssign = 0;
    } else if (timeToAssign > totalDuration) {
      timeToAssign = totalDuration;
      additionalSetters.playbackStatus = "stopped";
    }

    set({
      playbackTimeLastSet: timeToAssign,
      playbackTimeLastSetAt: new Date(),
      ...additionalSetters,
    });
    _emitPlaybackTime(timeToAssign);
    _scheduleStopWhenEnded();
  },

  playbackReset: () => {},

  // region managing recordings & their players

  registeredPlayers: [],

  registerPlayerRecording: (recording, player, parentElement) => {
    // Register these elements under `registeredPlayers` and return a function
    // to unregister them
    const { unregisterPlayerRecording } = get();

    const element = [recording, player, parentElement];
    set((state) => ({
      registeredPlayers: [...state.registeredPlayers, element],
    }));

    return () => unregisterPlayerRecording(recording, player, parentElement);
  },
  unregisterPlayerRecording: (recording, player, parentElement) => set((state) => ({
        registeredPlayers: state.registeredPlayers.filter(
            ([elRecording, elPlayer, elParentElement]) => {
              return !(
                  recording === elRecording
                  || player === elPlayer
                  || parentElement === elParentElement
              )
            }),
      }),
  ),

  SYNC_PLAYERS_TICK_INTERVAL: 50,
  getPlayerRecordings: () => get().registeredPlayers,

  // This needs to be called periodically, every `SYNC_PLAYERS_TICK_INTERVAL`,
  // every time there any players are rendered in order for the playback to work
  syncPlayers: () => {
    const {
      playbackFlightSession,
      getPlayerRecordings,
      getPlaybackTime,
      playbackStatus,

      SYNC_PLAYERS_TICK_INTERVAL,
      playbackTimeLastSetAt,
      _emitPlaybackTime,
    } = get();

    const boundaryStart = new Date(playbackFlightSession.started_at);

    const players = getPlayerRecordings();
    const playbackTime = getPlaybackTime();
    const playbackActive = playbackStatus === "playing";
    const playbackStopped = playbackStatus === "stopped";

    for (const [recording, player, parentElement] of players) {
      const recordingStart = new Date(recording.started_at);
      const recordingStartRelative = (recordingStart.getTime() - boundaryStart.getTime()) / 1000;
      const recordingEnd = new Date(recording.ended_at);
      const recordingEndRelative = (recordingEnd.getTime() - boundaryStart.getTime()) / 1000;

      const eligibleToPlay = (
          !playbackStopped
          && recordingStartRelative < playbackTime
          && playbackTime < recordingEndRelative
      );

      // In case React did not set player's `ref` yet, skip this iteration
      if (!parentElement.current) {
        continue;
      }

      // If `player` is already invisible, don't do anything. We cannot hook
      // into `paused` status as the played will pause automatically when it
      // reaches the end of the current video (and millisecond differences could
      // cause a race condition). Likewise for the visible status.
      const playerStyle = parentElement.current.style;

      if (!eligibleToPlay) {
        if (playerStyle.display !== "none") {
          playerStyle.display = "none";
          player.pause();
        }
        continue;
      }

      const timeToSeekTo = playbackTime - recordingStartRelative;

      // At this point, we know that the player needs to be shown. If it's not
      // shown at this moment, before actually showing it, we want to adjust the
      // playback time on it so that it immediately shows the proper frame
      // without any flicker-looking behavior.
      //
      // Same thing here as above regarding the visibility
      if (playerStyle.display !== "block") {
        player.currentTime(timeToSeekTo);
        parentElement.current.style.display = "block";
        player.play();
      } else {
        // However, if we continuously do it on every iteration, we can get
        // unintended behavior:
        //
        // - if the player is playing, we may get constant "buffering-like"
        //   display over the video player
        //
        // - if the player is paused, the video might continuously adjust
        //   +/- 1 frame on every iteration, causing the paused video to look
        //   like it's shaking
        //
        // For these reasons, we are going to monitor the playbackTime's last
        // updated time, and prevent updating it indefinitely. This ensures that
        // we still properly update when the user changes playback time within
        // the same video's playback
        const msSinceLastUpdate = (
            new Date().getTime() - playbackTimeLastSetAt.getTime()
        );

        // Double the threshold, ensuring we are executing this at least once
        const threshold = SYNC_PLAYERS_TICK_INTERVAL * 2;

        if (msSinceLastUpdate < threshold) {
          player.currentTime(timeToSeekTo);
        }
      }

      // Lastly, ensure that the player actually plays/pauses as needed
      const playerPaused = player.paused();

      if (playbackActive && playerPaused) {
        player.play();
      } else if (!playbackActive && !playerPaused) {
        player.pause();
      }
    }

    if (playbackActive)
      _emitPlaybackTime(playbackTime);
  },

  // endregion managing recordings & their players
})

const createModeSlice = (set, get) => ({
  // On load, we should be in flight mode
  mode: "flight",

  getFlightSession: () => {
    const {
      activeFlightSession,
      playbackFlightSession,
      mode,
    } = get();

    if (mode === "flight") {
      return activeFlightSession;
    } else if (mode === "playback") {
      return playbackFlightSession;
    }
  },

  enterFlightMode: (flightSession = null) => {
    const emit = get().emit;
    set({
      mode: "flight",
      playbackFlightSession: flightSession,
    });
    emit("mode", "flight", flightSession);
  },
  enterPlaybackMode: (flightSession) => {
    const {
      emit,
      mode,
      playbackReset,
    } = get();

    if (mode !== "playback") {
      playbackReset();
    }

    set({
      mode: "playback",
      playbackFlightSession: flightSession,
      sessionKeyMoments: flightSession.key_moments,
    });
    emit("mode", "playback", flightSession);
  },
});

const useMissionControlStore = create((...a) => ({
  ...createFlightSessionControlSlice(...a),
  ...createFlightManagementSlice(...a),
  ...createFlightPlaybackSlice(...a),
  ...createModeSlice(...a),
  ...createEventHandlingSlice(...a),
}));

export default useMissionControlStore;
