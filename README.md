# TimerDiary

Time tracker I built for myself, work on it when I have free time, mostly weekends. One Python file, runs as a Windows exe. No cloud, no account, nothing sent anywhere.

The day file (timer lines plus notes I type as I go) is basically the whole app. Everything else just reads from that.

Ended up covering a few different things for me:
- personal assistant for planning and time usage
- health tracking with real insights, not just raw numbers
- diary and notes
- stats and analysis on how I actually spend my time

Time tracking: start and stop, autosave, crash recovery, day rolls over at 4am instead of midnight.

Health: pulls in Apple Health data (watch to phone to PC), sleep, workouts, steps. Groups days into patterns using k-means clustering I wrote from scratch.

Planning: syncs with your calendar, plus some machine learning for auto scheduling and forecasting when deadlines will actually land, and how sure it is about that.

Stats: finds real correlations between the things you track, a small model that predicts how a day is going to go, and flags anything that looks off.
