# Architecture Map

## Слои

1. `Presentation Layer`
   - frontend pages, widgets, shared UI
   - feature screens без AI-логики
2. `Application Layer`
   - lesson runner
   - onboarding flow
   - journey / daily loop flow
  - explicit `daily ritual` layer on top of `daily_loop_plan`, with stages, completion rule, closure rule, and promise
  - `daily word journal` is now a real persisted vocabulary source (`word_journal`) instead of a future idea: the vocabulary hub can capture real-life phrases, and the ritual promise can explicitly keep that capture alive inside the route
  - `You & English` rituals now also have a lightweight decision-memory layer: `word_journal` and `spontaneous_voice` can register as persisted ritual signals in `journey_state.strategy_snapshot`, and recommendation can use that short window to bias the next 1-2 route decisions
   - ritual-aware route context so guided lessons know the canonical daily session arc, not only focus/recommendation data
   - ritual-aware runner/results bridges so the lesson is opened and closed as one connected daily scenario instead of isolated screens
   - explicit `reading_block` support in the lesson engine, so text-first routes can open through reading input instead of reusing listening-only scaffolding
   - standalone `listening` route surface with real listening-attempt memory, trend signals, route governance, and support-step completion, so audio input now participates in shell/navigation/re-entry as a true product vertical
   - standalone `reading` route surface with route governance, support-step completion, and shell/navigation participation, so reading now exists as a real product vertical instead of only an internal lesson block
   - task-driven input orchestration, so `daily_loop_plan` can open through `listening` or `reading` before the guided route when the current day shape and step structure actually call for that input-first start
   - task-driven mission handoff, so `reading/listening` surfaces can explicitly move the learner into `writing/speaking/guided route` as the next route step instead of ending as isolated input pages
   - backend-level `taskDrivenInput` contract inside `daily_loop_plan` and guided `routeContext`, so input-first missions are carried by the same journey/lesson payloads rather than existing only as frontend heuristics
   - persisted task-driven completion flow, so finishing a `reading/listening` input mission updates `routeFollowUpMemory`, `next_best_action`, and the backend route sequence before the learner even lands on the response surface
   - short-window task-driven persistence, so `Task-driven handoff` survives the immediate route-entry into the response surface and biases the next daily-plan focus plus guided `practice mix` toward the connected `input -> response` arc
   - post-lesson task-driven transfer evaluation, so `sessionSummary` and `tomorrowPreview` can distinguish between a clean `input -> response` carry and a fragile transfer that still needs one more protected response pass
   - recommendation and guided `practiceMix` now also consume that transfer evaluation, so fragile `reading/listening -> writing/speaking` carry changes both the next route focus and the actual module weighting of the following guided session
   - multi-day `task_transfer_window` recovery arc, so fragile/usable transfer outcomes now drive a short backend `protect -> stabilize -> widen` window across the next 1-2 route decisions instead of only changing one immediate follow-up
   - completion-driven transfer-window override, so the next `writing/speaking` response pass can directly advance, extend, or close that `task_transfer_window` instead of leaving it to decay only by passive route memory
   - next-day continuity seeding from previous session outcome
   - guided-route template overlay for recommended runs
   - route-aware block composition for support modules and preferred-mode response shape
   - route `practice mix` weighting between learner strategy and lesson block composition
   - post-lesson practice-mix evaluation from block-level scores for next-day continuity
   - continuity UI that surfaces practice-shift signals across dashboard, lesson results, daily loop, and shell re-entry
   - next-day route seeding that feeds practice-shift signals into plan copy, step structure, and guided lesson prompts
   - skill-aware learner-model updates from block-level lesson scores into progress snapshots
   - progress-aware recommendation and adaptive-focus selection when recovery pressure softens
   - adaptive UI surfaces that expose the live learner-model signal behind the chosen route focus
   - multi-day `skillTrajectory` memory from recent progress snapshots that feeds journey snapshot, adaptive alignment, and guided route shaping
   - trajectory-aware recommendation fallback and next-day plan/re-entry shaping when a skill stays weak across several sessions
   - longer-horizon `strategyMemory` that tracks persistent / recurring / emerging pressure across a wider progress window and feeds recommendation, route copy, and guided lesson shaping
   - `routeCadenceMemory` that tracks whether the learner is returning steadily, reopening after a short break, or needs a softer route rescue after missed days
   - cadence-aware adaptive alignment and module rotation so re-entry after missed days changes the actual loop behavior, not just continuity explanation
   - `routeRecoveryMemory` that combines cadence, longer strategy memory, and session outcome into a 2-3 day recovery arc for plan copy, daily steps, and guided lesson context
   - recommendation selection that can defer hard recovery and prefer a connected return when the recovery arc says the learner needs a calmer multi-day re-entry
   - frontend route-priority layer that aligns primary CTAs and route-step emphasis with recovery-aware recommendation selection
   - navigation-bias layer that reorders quick actions and top-level navigation emphasis so side routes stop competing with the protected main path
   - soft-lock navigation protection for `route_rebuild / protected_return`, where side modules stay visible but deferred until the main return path is complete
   - screen-level route governance on secondary skill surfaces, so local coach actions and notices also yield back to the protected main route
   - microflow guard layer on active skill screens, so inner practice actions can be deferred without hiding the whole surface
   - sequence-aware re-entry state on side surfaces, so support modules can reopen in ordered phases (`priority re-entry` vs `sequenced hold`)
   - persisted `routeReentryProgress` in `journey_state.strategy_snapshot`, so sequenced re-entry progression survives reloads/sessions and advances through a backend journey endpoint after actual support-step completion
   - recommendation and daily-plan builders that read active `routeReentryProgress.nextRoute`, so sequenced support progression changes route focus and step composition, not only notices and reopen order
   - adaptive alignment and module rotation that also read active `routeReentryProgress.nextRoute`, so adaptive loop surfaces reflect the exact next support step inside the recovery sequence
   - guided lesson `practice mix` and block composition that also read active `routeReentryProgress.nextRoute`, so sequenced recovery can insert and elevate the exact next support block inside the lesson itself
   - `routeRecoveryMemory.sessionShape` that now also shapes `daily_loop_plan` duration and step compactness, so multi-day recovery arcs alter the actual rhythm of the next day rather than only its explanation
   - frontend `route day shape` surfaces that translate `sessionShape` into visible route-state on dashboard, daily loop, continuity, and intelligence panels
   - secondary-screen governance and shell-level re-entry copy that now also read `route day shape`, so `activity`, `progress`, re-entry prompts and skill-surface notices all speak the same recovery rhythm
   - `RouteMicroflowGuard` surfaces that now also render `route day shape`, so local practice locks stay aligned with the same day rhythm instead of feeling like generic disabled states
   - `AppTopRail` and biased quick actions that now also render `route day shape`, so shell navigation and dashboard actions keep the same recovery-rhythm bias as the content surfaces
   - shell-level route entry orchestration that can redirect fresh re-entry from `dashboard` into `lesson runner`, `daily loop` or the active sequenced support-surface when recovery strategy already has a stronger starting point
   - `RouteEntryNotice` in shell that explains smart re-entry after such redirects, so orchestration stays interpretable rather than feeling like hidden routing logic
- persisted `routeEntryMemory` in `journey_state.strategy_snapshot`, updated by shell route visits and reused by frontend re-entry orchestration to avoid over-repeating the same support-surface redirect
- backend recommendation and `daily_loop_plan` now also read `routeEntryMemory`, so repeated reopen attempts on the same support surface can reset the learner into a calmer main-route day before the same sequenced step is suggested again
- guided-route template building now reads that same reset signal and can suppress the repeated support block in favor of a calmer `lesson`-led composition, so the orchestration changes actual session shape, not only the recommendation copy
- `routeRecoveryMemory` and adaptive strategy alignment now also reinterpret repeated re-entry as a short protected reset arc, so the next few sessions can stay in connected main-route mode before the same support surface is reopened again
- frontend `route day shape` and route-intelligence surfaces now expose that reset arc explicitly as `Connected reset`, so shell re-entry, dashboard continuity and secondary screens explain why the product is temporarily favoring the main route over the same support surface
- once that reset has done enough connected main-route passes, frontend day-shape and re-entry surfaces now also expose `support reopen ready`, so the learner can see when the deferred support step is intentionally coming back into the route
- backend journey/recommendation/adaptive layers now also promote that moment into a dedicated `support_reopen_arc`, so the next 2-3 routes can be planned around reintroducing the deferred support step without collapsing back into either hard reset or isolated side-surface behavior
- `support_reopen_arc` now also changes the actual daily-route tempo in `journey_service`, so reopen days stay a bit longer and more controlled than plain `protected_return`, even before the frontend adds a dedicated visual label for that distinction
- `support_reopen_arc` now also reads recent reopen-focused plans, so backend recovery memory can distinguish a first reopen pass from a settling pass and from a widen-ready pass instead of treating every reopen day as the same shape
- frontend route surfaces now also expose those reopen substages through `route day shape`, route-intelligence cards, continuity surfaces, and shell re-entry prompts, so the learner can see whether the route is in first reopen, settling, or widen-ready mode
- frontend route-priority and shell-navigation layers now also consume those reopen substages, so quick-action ordering, top-rail emphasis, and primary CTA routing can bias toward the reopened support surface during `first_reopen / settling_back_in` and then hand priority back to the wider connected route at `ready_to_expand`
- shell route-entry orchestration now also carries that reopen-substage logic into explicit entry sequencing, so auto-redirected re-entry can explain both the immediate starting surface and the next connected surface that should follow it
- follow-up route sequencing is now also surfaced inside dashboard continuity, route-intelligence, daily-loop, and shell re-entry prompt panels, so the same `what comes next` step survives beyond the initial shell redirect
- `journey_state.strategy_snapshot` now also carries persisted `routeFollowUpMemory`, so frontend follow-up hints can reuse one backend-side orchestration signal that updates together with re-entry progression and route-entry memory
- walkthrough surfaces now also reuse that same follow-up signal in `RouteEntryNotice`, dashboard hero, and lesson-results continuity blocks, so entry, decision, and post-session moments all expose one shared `now -> then` route narrative
- onboarding presentation now also exposes proof-lesson handoff continuity directly, so stored welcome-proof signals are not only persisted and applied to drafts, but are also rendered as an explicit `save start -> clarify goal -> open first route` narrative inside the onboarding surface itself
- proof-lesson completion now also carries explicit route-entry state into onboarding, so the very first transition after the live lesson can reuse the same route-bridge language as shell, dashboard, and results instead of feeling like a cold route swap
- onboarding completion now also feeds shell-level entry state, so the first dashboard render after submit can bypass one normal re-entry redirect and present itself as the beginning of the first personal route rather than a cold generic landing
   - persisted `learningBlueprint` now lives inside `journey_state.strategy_snapshot`, so onboarding/profile, learner memory, recovery arc and follow-up sequence are also materialized as one explainable strategy object instead of only influencing route copy indirectly
   - `learningBlueprint` now also reads an explicit `english relationship` slice from onboarding (`relationship goal / emotional barriers / helpful rituals`), so the route can carry not only academic goals, but also the learner's desired inner experience of English
- dashboard now exposes that `learningBlueprint` as a dedicated strategy panel, and guided lesson route-context now also carries blueprint headline / north-star / pillars so the long-plan logic is visible inside the session itself
- dashboard route-launch handlers now also feed explainable entry state into the lesson runner, so the first `daily route -> lesson runner` jump preserves a shared route narrative instead of switching into an isolated lesson surface without context
- lesson completion and results surfaces now also pass explicit route-entry handoff state into `lesson results`, `lesson runner` follow-up, and `updated dashboard`, so the post-session loop preserves one shared route narrative instead of treating each surface as a separate reset
- runner end-state and discard behavior now also participate in that same route narrative, so the last-block completion hint, draft discard return, and `results -> dashboard` exit all preserve route-context rather than falling back to generic navigation history
- top rail, adaptive route support, activity loop summary, and next-action panels are now also being reworded toward `today's route / next guided step / route home`, so shell-level orchestration keeps the same mentor tone as the core walkthrough surfaces
- support-surface completion handlers now also consume that persisted follow-up memory, so finishing a reopened grammar / vocabulary / speaking / writing / pronunciation / profession step can advance the learner into the next connected surface instead of only refreshing local guidance copy
- backend `journey_service` and recommendation builders now also read `routeFollowUpMemory`, so the same follow-up sequence changes `next_best_action`, daily-plan copy, and recommendation goal instead of staying only a frontend navigation hint
- support-step completion inside `support_reopen_arc` now also advances backend-side reopen substages, so the route can move from `first_reopen` into `settling_back_in` and then `ready_to_expand` based on actual completed follow-up passes, not only on recent daily-plan history
- adaptive alignment, module rotation, recommendation focus-handling, and guided lesson composition now also read those reopen substages, so `settling_back_in` can keep the reopened support lane elevated while `ready_to_expand` hands leadership back to the broader connected route instead of treating every reopen day the same
   - strategy-aware adaptive rotation for `grammar / writing / pronunciation / profession` emphasis
   - continuity-aware lesson template overlay for recommended runs
   - recommendation flow
   - global Liza guidance flow
3. `Domain Layer`
   - user account
   - user profile
   - onboarding session
   - learner journey state
   - daily loop plan
   - session summary / tomorrow preview continuity snapshot
   - skill trajectory memory inside journey strategy snapshot
   - longer strategy memory inside journey strategy snapshot
   - route cadence memory inside journey strategy snapshot
   - route recovery memory inside journey strategy snapshot
   - lesson
   - mistake
   - progress
   - profession topic
4. `AI Layer`
   - AI orchestrator
   - LLM/STT/TTS/Scoring provider contracts
   - prompts
5. `Data Layer`
   - SQLite + Alembic persistence
   - schemas
   - SQLAlchemy models and repositories
6. `Content Layer`
   - grammar topics
   - profession tracks
   - lesson templates

## Frontend модули

- `app` — router и shell
- `pages` — route-level страницы
- `widgets` — общий каркас приложения
- `widgets/liza` — coach presence и explainable guidance
- `widgets/liza` — coach presence, guidance grids и interactive explain-actions
- `widgets/navigation` — top rail, route continuity и shell-level re-entry prompts
- `features/dashboard`
- `features/daily-loop`
- `features/onboarding`
- `features/lesson-runner`
- `features/grammar`
- `features/listening`
- `features/reading`
- `features/speaking`
- `features/pronunciation`
- `features/writing`
- `features/profession`
- `features/progress`
- `features/mistakes`
- `features/settings`
- `entities/*` — доменные типы
- `shared/*` — UI, API, store, constants, helpers

## Backend модули

- `api/routes` — endpoint groups
- `core` — settings и DI-ready dependencies
- `schemas` — Pydantic contracts
- `services/*` — модульные use-case services
- `repositories/*` — persistence access layer
- `providers/*` — provider abstractions
- `prompts/*` — prompt templates
- `content/*` — учебный контент и lesson configs
- `db` / `models` — база для persistence layer

## Первый инкремент MVP

- onboarding profile setup
- dashboard summary
- proof lesson -> onboarding session -> daily loop handoff
- post-lesson route evaluation for `support_reopen_arc`, so completed reopen lessons can mark the next day as another settling pass or as widen-ready continuity
- short recovery `decision window` memory for widen-ready reopen arcs, so recommendation and daily-plan copy can keep a controlled multi-day expansion bias
- guided lesson payload and exposed `practiceMix` now also normalize against that widening window, so widen-ready reopen days stay `lesson`-led inside the actual block composition rather than only in high-level route copy
- widen-ready `decision window` now also carries its own short-lived substage progression (`first_widening_pass / stabilizing_widening / ready_for_extension`), and that staged memory already feeds journey copy, recommendation, adaptive reasoning, and guided route context across the next few route decisions
- frontend `route day shape`, route-intelligence panels, dashboard continuity, daily-loop surfaces, and shell re-entry prompt now also render those widening substages directly, so controlled expansion is visible to the learner as a real route phase rather than only hidden backend memory
- shell-level re-entry prompt for route continuity outside the dashboard
- route-first secondary surfaces so `activity` and `progress` return into `today route` before launching side flows
- recommendation + lesson build
- grammar topics
- speaking scenarios
- pronunciation drills
- writing review
- profession hub
- mistakes + progress
- provider status
