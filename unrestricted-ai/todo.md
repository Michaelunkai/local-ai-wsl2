# Reliable local Qwen and Dolphin chats

## Startup internet diagnostics
☑ Implement bounded startup internet diagnostics without preventing offline local chats.
☑ Test success, partial outage, DNS failure and timeout behavior.
☑ Verify the deployed startup check and document its exact scope.

☑ Diagnose the blank replies from saved-chat and Ollama logs.
☑ Verify both installed model variants against the pinned upstream weights.
☑ Add model provenance checks and first-response warmup to the same launcher.
☑ Add visible model-loading feedback to Open WebUI.
☑ Route Dolphin Python execution through the sandbox tool.
☑ Verify twelve consecutive Dolphin replies with recall, file reading and execution.
☑ Inspect the failed long-history summary and its prompt.
☑ Correct conversation compaction without removing earlier facts.
☑ Allow per-chat compaction thresholds and isolate the compaction regression.
☑ Restore stable project networking and supervision, then verify sandbox isolation.
☑ Validate consecutive Dolphin messages after automatic compaction.
☑ Validate consecutive Qwen messages after automatic compaction.
☑ Verify the loading indicator and continued chat in the browser.
☑ Run the updated launcher in Windows PowerShell 5.1.
☑ Update the operating instructions and verification report.
☑ Report the verified result and remaining hardware/model limits.








## Disabled startup-task repair
☑ Inspect startup-task registration and launcher error propagation.
☑ Repair disabled-task handling and failure propagation.
☑ Test disabled-task recovery and repeat startup in PowerShell 5.1.
☑ Record verification and return the full script path.








## Capability expansion
☑ Audit screenshots, current integrations and runtime settings.
☑ Research supported PC, browser and online-research integrations.
☑ Implement compatible capability and configuration improvements in the existing launcher.
☑ Verify PC, browser, research and performance behavior end to end.
☑ Audit remaining requirements and document external dependencies.








☑ Separate visible capability connections and complete the static implementation audit before any further launch or live test.



## Direct PC tool implementation review
☑ Inspect captured Windows tool schemas and existing routing.
☑ Add direct typed PC tools for common file, terminal and UI actions.
☑ Review argument validation, image handling and configuration consistency statically.
☑ Update the requirement audit without lifting the launch hold.






## Research failure review
☑ Inspect research failure handling and ordering.
☑ Correct confirmed research defects.
☑ Verify research changes without live services.

## Dependency startup review
☑ Inspect dependency startup and configuration checks.
☑ Repair confirmed startup defects.
☑ Validate changed startup code without launching services.

## Authorized deployment and live verification
☑ Lift the launch hold with explicit user authorization.
☑ Run the same launcher and repair startup failures.
☑ Verify deployed connections and direct Windows tools.
☑ Verify browser profile 2 connection and browser actions.
☑ Verify both models and persistent multi-turn chats.
☑ Audit integration coverage and record remaining limitations.

## Sandbox timeout investigation
☑ Reproduce the execution timeout and capture boundary evidence.
☑ Fix confirmed execution defects and verify the result; the final concurrent stress run passed all nine jobs.

## Document artifact capability
☑ Resolve pinned document-generation packages.
☑ Add packages to the sandbox and deploy.
☑ Verify Word, spreadsheet, slides and PDF roundtrips.

☑ Verify the same launcher after document capability deployment.

## Sandbox protocol trace
☑ Capture kernel startup and output-message timings without changing production execution.
☑ Record whether the trace establishes the timeout cause.

## Desktop vision verification
☑ Capture a current desktop image for local-model verification.
☑ Verify Qwen interpretation against the captured image.

## Desktop action verification
☑ Verify typing and clicking in a disposable test window through the supported Windows integration, including cleanup and preservation of the existing tab.

## Policy rejection diagnosis
☑ Inspect effective permissions and locate rejection evidence.
☑ Determine the available boundary: effective full access is verified, the shell approval rule is not exposed in project or runtime logs, and the supported Windows integration completes the required actions.
☑ Apply and verify the supported repair through the intended Windows integration; direct and model-driven action workflows passed.
☑ Save a redacted diagnostic report.

## Resumed completion verification
☑ Restore the stack with the exact launcher and verify service health.
☑ Verify desktop launch, typing, and click actions through the intended Windows integration.
☑ Verify both models can perform the desktop action workflow.
☑ Re-run the sandbox execution stress check and preserve any failure evidence.
☑ Re-run the launcher end-to-end after any confirmed fixes.
☑ Reconcile the completion audit against every requested capability.

## Final external-network regression
☑ Reproduce the full-suite search and crawl failure after bridge recovery.
☑ Correct the watchdog test so its Python connectivity probe actually executes.
☑ Add redundant explicit DNS upstreams to every web-facing container.
☑ Verify bridge recovery, public DNS, external HTTPS, local connectivity and sandbox isolation.
☑ Pass all 27 full-stack checks in one post-repair run.
☑ Pass the exact unchanged launcher without rebuilding images and open the default browser.

## Qwen execute_python JSON regression
☑ Capture the failing model call and trace schema, prompt, server and WebUI boundaries.
☑ Add a focused failing regression for truncated execute_python arguments.
☑ Implement one root-cause repair.
☑ Run the focused regression and the affected long-chat/model checks.
☑ Re-run the launcher and record the final result.
