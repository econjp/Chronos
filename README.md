# Chronos

Started as enhanced pomodoro/diary, ended as full exec assistant. Develop when free time, mostly weekends. One Python file, runs as a Windows exe. No cloud, no account, nothing sent anywhere.

day file (timer lines plus notes in the go) is basically whole core. Everything else expands on that.

Ended up covering a few different things for me:
- personal assistant for planning and time usage
- health tracking with real insights, not just raw numbers
- diary and notes management
- stats and analysis on time usage

Time tracking: start and stop, autosave, crash recovery etc

Health: pulls Apple Health data (watch to phone to PC), sleep, workouts, steps. Groups days into patterns using k-means clustering, wrote from scratch.

Planning: syncs with calendar, plus some machine learning for auto scheduling and forecasting when deadlines will actually land, and how sure it is about that.

Stats: finds real correlations between tracked items, a small model that predicts how a day is going to go, and flags off-patterns
